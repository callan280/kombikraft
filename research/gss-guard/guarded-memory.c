/* Offline architectural fixture, GPL-2.0-or-later (QEMU integration).
 * No source firmware or device reply is synthesized. Unknown accesses exit
 * the owned process before returning any value to the guest instruction. */
#include "qemu/osdep.h"
#include "qapi/error.h"
#include "hw/core/qdev.h"
#include "hw/core/cpu.h"
#include "hw/core/qdev-properties.h"
#include "system/memory.h"
#include "system/address-spaces.h"
#include "system/runstate.h"
#include "qobject/qjson.h"
#include "qobject/qdict.h"
#include "qobject/qlist.h"
#include "qemu/module.h"

#define TYPE_KOMBI_GUARD "kombikraft-memory-guard"
OBJECT_DECLARE_SIMPLE_TYPE(KombiGuard, KOMBI_GUARD)
typedef struct GuardRegion {
    MemoryRegion mr;
    MemoryRegion backing;
    uint64_t address;
    uint64_t bias;
    char *name;
    KombiGuard *parent;
} GuardRegion;
struct KombiGuard {
    DeviceState parent_obj;
    MemoryRegion memory;
    MemoryRegion ports;
    GuardRegion regions[32];
    unsigned region_count;
    char *layout;
    char *layout_sha;
    bool test_exit;
    bool prepared;
    bool armed;
};

static G_NORETURN void stop_access(const char *kind, uint64_t address,
                                   unsigned size, uint64_t value,
                                   const char *region)
{
    CPUState *cpu = current_cpu;
    uint64_t pc = cpu ? CPU_GET_CLASS(cpu)->get_pc(cpu) : 0;
    fprintf(stderr, "KOMBI_GUARD {\"event\":\"denied\",\"kind\":\"%s\","
            "\"address\":\"0x%" PRIx64 "\",\"bytes\":%u,"
            "\"value\":\"0x%" PRIx64 "\",\"pc\":\"0x%" PRIx64 "\","
            "\"cpuContext\":%s,\"region\":\"%s\",\"returnedValue\":false}\n",
            kind, address, size, value, pc, cpu ? "true" : "false", region);
    if (cpu && CPU_GET_CLASS(cpu)->dump_state) {
        CPU_GET_CLASS(cpu)->dump_state(cpu, stderr, 0);
    }
    fflush(stderr);
    _exit(86);
}

static uint64_t guard_read(void *opaque, hwaddr address, unsigned size)
{
    stop_access("unmodeled-memory-read", address, size, 0, "unmodeled");
}
static void guard_write(void *opaque, hwaddr address, uint64_t value, unsigned size)
{
    stop_access("unmodeled-memory-write", address, size, value, "unmodeled");
}
static void readonly_write(void *opaque, hwaddr address, uint64_t value, unsigned size)
{
    GuardRegion *region = opaque;
    stop_access("readonly-region-write", region->address + address - region->bias, size, value, region->name);
}
static uint64_t port_read(void *opaque, hwaddr address, unsigned size)
{
    stop_access("unmodeled-port-read", address, size, 0, "ports");
}
static void port_write(void *opaque, hwaddr address, uint64_t value, unsigned size)
{
    KombiGuard *s = opaque;
    if (s->test_exit && address == 0xe8 && size == 1) {
        fprintf(stderr, "KOMBI_GUARD {\"event\":\"authored-test-exit\",\"value\":%" PRIu64 "}\n", value);
        fflush(stderr);
        _exit(value == 0xa5 ? 0 : 87);
    }
    stop_access("unmodeled-port-write", address, size, value, "ports");
}
static const MemoryRegionOps guard_ops = {
    .read = guard_read, .write = guard_write, .endianness = DEVICE_LITTLE_ENDIAN,
    .valid.min_access_size = 1, .valid.max_access_size = 8,
    .valid.unaligned = true,
    .impl.min_access_size = 1, .impl.max_access_size = 8, .impl.unaligned = true,
};
static const MemoryRegionOps readonly_ops = {
    .read = guard_read, .write = readonly_write, .endianness = DEVICE_LITTLE_ENDIAN,
    .valid.min_access_size = 1, .valid.max_access_size = 8,
    .valid.unaligned = true,
    .impl.min_access_size = 1, .impl.max_access_size = 8, .impl.unaligned = true,
};
static const MemoryRegionOps port_ops = {
    .read = port_read, .write = port_write, .endianness = DEVICE_LITTLE_ENDIAN,
    .valid.min_access_size = 1, .valid.max_access_size = 4,
    .impl.min_access_size = 1, .impl.max_access_size = 4,
};

static void guard_realize(DeviceState *dev, Error **errp)
{
    KombiGuard *s = KOMBI_GUARD(dev);
    g_autofree char *contents = NULL;
    g_autofree char *actual_sha = NULL;
    gsize length;
    QObject *parsed;
    QDict *layout;
    QList *regions;
    const QListEntry *entry;
    CPUState *cpu = qemu_get_cpu(0);
    if (!cpu || !cpu->as || !s->layout || !s->layout_sha) {
        error_setg(errp, "guard: CPU0 and reviewed layout/hash required");
        return;
    }
    if (!g_file_get_contents(s->layout, &contents, &length, NULL)) {
        error_setg(errp, "guard: cannot read layout");
        return;
    }
    actual_sha = g_compute_checksum_for_data(G_CHECKSUM_SHA256, (guchar *)contents, length);
    if (strcmp(actual_sha, s->layout_sha)) {
        error_setg(errp, "guard: layout hash mismatch");
        return;
    }
    parsed = qobject_from_json(contents, errp);
    if (!parsed) {
        return;
    }
    layout = qobject_to(QDict, parsed);
    if (!layout || !(regions = qdict_get_qlist(layout, "regions"))) {
        error_setg(errp, "guard: missing regions");
        return;
    }
    memory_region_init_io(&s->memory, OBJECT(s), &guard_ops, s, "kombi-unknown-memory", UINT64_MAX);
    memory_region_init_io(&s->ports, OBJECT(s), &port_ops, s, "kombi-unknown-ports", 65536);
    QLIST_FOREACH_ENTRY(regions, entry) {
        QDict *row = qobject_to(QDict, qlist_entry_obj(entry));
        GuardRegion *r;
        const char *file, *expected;
        uint64_t size;
        bool readonly;
        g_autofree char *data = NULL;
        g_autofree char *loaded_sha = NULL;
        g_autofree char *backing_name = NULL;
        gsize file_size = 0;
        void *backing;
        unsigned i;
        if (!row || s->region_count >= 32) {
            error_setg(errp, "guard: invalid/too many regions");
            return;
        }
        r = &s->regions[s->region_count];
        r->name = g_strdup(qdict_get_str(row, "name"));
        if (strspn(r->name, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-") != strlen(r->name)) {
            error_setg(errp, "guard: unsafe region name");
            return;
        }
        r->address = g_ascii_strtoull(qdict_get_str(row, "address"), NULL, 0);
        size = qdict_get_int(row, "bytes");
        readonly = qdict_get_bool(row, "readonly");
        r->parent = s;
        r->bias = r->address & 4095;
        backing_name = g_strdup_printf("%s-hidden-backing", r->name);
        if (!size || size > 0x1000000 || r->address + size < r->address) {
            error_setg(errp, "guard: invalid region bounds");
            return;
        }
        for (i = 0; i < s->region_count; i++) {
            GuardRegion *other = &s->regions[i];
            uint64_t other_size = memory_region_size(&other->mr);
            if (r->address < other->address + other_size && other->address < r->address + size) {
                error_setg(errp, "guard: overlapping regions");
                return;
            }
        }
        if (readonly) {
            if (!memory_region_init_rom_device(&r->backing, OBJECT(s), &readonly_ops, r, backing_name,
                                               (r->bias + size + 4095) & ~4095ULL, errp)) {
                return;
            }
        } else if (!memory_region_init_ram(&r->backing, OBJECT(s), backing_name,
                                          (r->bias + size + 4095) & ~4095ULL, errp)) {
            return;
        }
        /* Keep RAM-block offset congruent with the guest physical address.
         * Only this exact-size alias is mapped; hidden allocation padding is
         * NEVER exposed as additional allowed guest memory. */
        memory_region_init_alias(&r->mr, OBJECT(s), r->name, &r->backing, r->bias, size);
        backing = (char *)memory_region_get_ram_ptr(&r->backing) + r->bias;
        memset(backing, 0, size);
        file = qdict_get_try_str(row, "file");
        expected = qdict_get_str(row, "sha256");
        if (file) {
            if (!g_file_get_contents(file, &data, &file_size, NULL) || file_size != size) {
                error_setg(errp, "guard: source region size/read mismatch");
                return;
            }
            memcpy(backing, data, size);
        }
        loaded_sha = g_compute_checksum_for_data(G_CHECKSUM_SHA256, backing, size);
        if (strcmp(loaded_sha, expected)) {
            error_setg(errp, "guard: source region hash mismatch");
            return;
        }
        memory_region_add_subregion(&s->memory, r->address, &r->mr);
        fprintf(stderr, "KOMBI_GUARD {\"event\":\"region-loaded\",\"name\":\"%s\","
                "\"address\":\"0x%" PRIx64 "\",\"bytes\":%" PRIu64 ","
                "\"readonly\":%s,\"sha256\":\"%s\"}\n",
                r->name, r->address, size, readonly ? "true" : "false", loaded_sha);
        s->region_count++;
    }
    s->prepared = true;
    fprintf(stderr, "KOMBI_GUARD {\"event\":\"prepared-paused-arm-required\",\"regions\":%u,\"testExit\":%s}\n",
            s->region_count, s->test_exit ? "true" : "false");
    fflush(stderr);
    qobject_unref(parsed);
}

static bool guard_get_armed(Object *obj, Error **errp)
{
    return KOMBI_GUARD(obj)->armed;
}
static void guard_set_armed(Object *obj, bool value, Error **errp)
{
    KombiGuard *s = KOMBI_GUARD(obj);
    CPUState *cpu = qemu_get_cpu(0);
    if (!value || s->armed || !s->prepared || runstate_is_running()) {
        error_setg(errp, "guard: one-way arm requires prepared paused machine");
        return;
    }
    /* CPU-private root also covers its APIC-over-system-memory alias. */
    memory_region_add_subregion_overlap(cpu->as->root, 0, &s->memory, INT_MAX - 1);
    memory_region_add_subregion_overlap(get_system_io(), 0, &s->ports, INT_MAX - 1);
    s->armed = true;
    fprintf(stderr, "KOMBI_GUARD {\"event\":\"armed-before-cont\",\"regions\":%u,\"testExit\":%s}\n",
            s->region_count, s->test_exit ? "true" : "false");
    fflush(stderr);
}

static const Property guard_properties[] = {
    DEFINE_PROP_STRING("layout", KombiGuard, layout),
    DEFINE_PROP_STRING("layout-sha256", KombiGuard, layout_sha),
    DEFINE_PROP_BOOL("authored-test-exit", KombiGuard, test_exit, false),
};
static void guard_class_init(ObjectClass *klass, const void *data)
{
    DeviceClass *device = DEVICE_CLASS(klass);
    device->realize = guard_realize;
    device->user_creatable = true;
    device_class_set_props(device, guard_properties);
    device->desc = "Offline fail-closed exact-memory architectural fixture";
    object_class_property_add_bool(klass, "armed", guard_get_armed, guard_set_armed);
}
static const TypeInfo guard_type = {
    .name = TYPE_KOMBI_GUARD, .parent = TYPE_DEVICE,
    .instance_size = sizeof(KombiGuard), .class_init = guard_class_init,
};
static void guard_register(void) { type_register_static(&guard_type); }
type_init(guard_register)
