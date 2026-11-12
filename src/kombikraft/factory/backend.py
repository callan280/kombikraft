"""Bounded original-code controller backend using locally admitted source banks.

This executes partial application startup and internal receive fixtures. It does
not boot INTEGRITY, start physical transports, or render the factory cluster.
"""
import struct
import hashlib
from .inputs import FactoryInputError
from .profile import REQUIRED_BANKS
from .platform import FixedClock, PlatformBoundaryError, TrackedMutexes

DATA, STACK, STOP, HEAP = 0x09000000, 0x0A000000, 0x0B000000, 0x0C000000
SIGNALS = {
    "bc": (0x7C, 0x2212B12),
    "leftLamp": (0x1D6, 0x2220848),
    "rightLamp": (0x1D7, 0x222096E),
}
PHASES = (0x2B8F621, 0x2B8F6B6, 0x2B8F73F, 0x2B8F7C8, 0x2B8F862)

class FactoryExecutionError(RuntimeError):
    pass

class OriginalControllerBackend:
    """Single-thread original-code fixture. All readiness gates start cold."""

    def __init__(self, banks):
        try:
            from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
            from unicorn import x86_const as registers
        except ImportError as exc:
            raise FactoryExecutionError("Install the optional factory dependency: unicorn==2.1.4") from exc
        self.r = registers
        self.uc = Uc(UC_ARCH_X86, UC_MODE_64)
        self.regions = []
        self.source_identity = []
        banks = tuple(banks)
        indexed = {bank.name: bank for bank in banks}
        if len(indexed) != len(banks) or len(banks) != len(REQUIRED_BANKS):
            raise FactoryInputError("Backend requires exactly the supported source-bank set")
        for name, base, digest in REQUIRED_BANKS:
            bank = indexed.get(name)
            if bank is None or bank.base != base or bank.sha256 != digest or hashlib.sha256(bank.data).hexdigest() != digest:
                raise FactoryInputError(f"Backend source identity mismatch: {name}")
        ranges = [(bank.base, bank.base + ((len(bank.data) + 4095) & ~4095)) for bank in banks]
        ranges += [(address, address + size) for address, size in
                   [(0x05200000, 0x02A00000), (DATA, 0x20000),
                    (STACK, 0x20000), (STOP, 0x1000), (HEAP, 0x1000000)]]
        merged = []
        for start, end in sorted(ranges):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        for start, end in merged:
            self.uc.mem_map(start, end - start)
        for bank in banks:
            self.uc.mem_write(bank.base, bank.data)
            if bank.name != "26-218c3000.bin":
                self.regions.append((bank.base, bank.base + len(bank.data)))
            self.source_identity.append({"name": bank.name, "sha256": bank.sha256})
        self.heap = HEAP
        self.allocations = {}
        self.guards = set()
        self.mutexes = TrackedMutexes()
        self.clock = FixedClock(self.qword(0x529EEF0))
        self.kernel_semaphores = []
        self.gate_writes = []
        self.diagnostics = []
        self.callback_counts = {}
        self.scheduler_registrations = []
        self.initialized = False
        self.instructions = 0
        self.uc.reg_write(registers.UC_X86_REG_FS_BASE, DATA + 0x18000)
        for address, value in [(DATA + 0x18000, DATA + 0x18100),
                               (DATA + 0x181D8, DATA + 0x18300),
                               (DATA + 0x18460, DATA + 0x18500)]:
            self.uc.mem_write(address, struct.pack("<Q", value))
        for address in (0x7AD6BA0, 0x7AD6BB0, 0x7AD6A40):
            head = self.allocate(0x58)
            self.uc.mem_write(head, struct.pack("<QQQBB", head, head, head, 1, 1))
            self.uc.mem_write(address, struct.pack("<QQ", head, 0))
        self.uc.hook_add(UC_HOOK_CODE, self._code)
        self.uc.hook_add(UC_HOOK_MEM_WRITE, self._write)

    def qword(self, address):
        return struct.unpack("<Q", self.uc.mem_read(address, 8))[0]

    def cstring(self, address):
        out = bytearray()
        for offset in range(2048):
            value = self.uc.mem_read(address + offset, 1)[0]
            if not value:
                return out.decode("utf-8", errors="replace")
            out.append(value)
        raise FactoryExecutionError("Original string exceeded its fixture bound")

    def allocate(self, size):
        if not 0 < size <= 1_000_000:
            raise PlatformBoundaryError("Unadmitted allocation size")
        address = self.heap
        self.heap += (size + 15) & ~15
        if self.heap > HEAP + 0x1000000:
            raise PlatformBoundaryError("Fixture heap exhausted")
        self.allocations[address] = size
        return address

    def _return(self, value=0):
        sp = self.uc.reg_read(self.r.UC_X86_REG_RSP)
        address = self.qword(sp)
        self.uc.reg_write(self.r.UC_X86_REG_RSP, sp + 8)
        self.uc.reg_write(self.r.UC_X86_REG_RAX, value)
        self.uc.reg_write(self.r.UC_X86_REG_RIP, address)

    def _code(self, uc, address, size, _):
        self.instructions += 1
        rdi = uc.reg_read(self.r.UC_X86_REG_RDI)
        rsi = uc.reg_read(self.r.UC_X86_REG_RSI)
        if address == STOP:
            uc.emu_stop()
            return
        if not any(start <= address < end for start, end in self.regions):
            raise FactoryExecutionError(f"Execution outside admitted firmware banks: {address:#x}")
        if address in (0x2212B12, 0x2220848, 0x222096E):
            self.callback_counts[address] = self.callback_counts.get(address, 0) + 1
        if address == 0x2B938F4:
            self.scheduler_registrations.append(rdi)
        if address == 0x3099038:
            uc.mem_write(rsi, self.clock.read(rdi))
            self._return()
        elif address == 0x3098DFC:
            if rdi != 0 or not rsi:
                raise PlatformBoundaryError("Unadmitted semaphore creation")
            handle = 0x60000000 + len(self.kernel_semaphores) * 0x100
            uc.mem_write(rsi, struct.pack("<Q", handle))
            self.kernel_semaphores.append(handle)
            self._return()
        elif address in (0x2AE3034, 0x2AE3324, 0x2AE373D):
            if address == 0x2AE3034:
                status = self.mutexes.initialize(rdi, rsi, bytes(uc.mem_read(rdi, 32)) if rdi else b"")
            elif address == 0x2AE3324:
                status = self.mutexes.acquire(rdi)
            else:
                status = self.mutexes.release(rdi)
            self._return(status)
        elif address in (0x218442D, 0x307BCB4):
            self._return(self.allocate(rdi))
        elif address in (0x2183947, 0x2185F03):
            self._return()
        elif address == 0x307A144:
            self._return(0 if rdi in self.guards else 1)
        elif address == 0x307A27E:
            self.guards.add(rdi)
            self._return()
        elif address in (0x2AF9D30, 0x2AF9D58, 0x2AF9EDD):
            uc.mem_write(rdi, bytes(16))
            self._return()
        elif address == 0x307DEB4:
            message = self.cstring(rsi)
            self.diagnostics.append(message)
            if "RequestReset" in message or "Hmi_Assert" in message:
                raise FactoryExecutionError("Original firmware requested reset/assert")
            self._return()

    def _write(self, uc, access, address, size, value, _):
        if address in (0x795E510, 0x56DAFE4, 0x7AD25F5):
            self.gate_writes.append({"address": hex(address), "size": size, "value": value,
                                     "originalPc": hex(uc.reg_read(self.r.UC_X86_REG_RIP))})

    def _invoke(self, entry, *args):
        self.instructions = 0
        sp = STACK + 0x1FFF8
        self.uc.mem_write(sp, struct.pack("<Q", STOP))
        self.uc.reg_write(self.r.UC_X86_REG_RSP, sp)
        for register, arg in zip((self.r.UC_X86_REG_RDI, self.r.UC_X86_REG_RSI,
                                  self.r.UC_X86_REG_RDX), args):
            self.uc.reg_write(register, arg)
        self.uc.emu_start(entry, STOP, timeout=3_000_000, count=1_500_000)
        if self.uc.reg_read(self.r.UC_X86_REG_RIP) != STOP:
            self.uc.emu_start(self.uc.reg_read(self.r.UC_X86_REG_RIP), STOP,
                              timeout=20_000_000, count=15_000_000)
        if self.uc.reg_read(self.r.UC_X86_REG_RIP) != STOP:
            raise FactoryExecutionError("Original call exceeded its execution budget")
        return {"entry": hex(entry), "instructions": self.instructions,
                "return": self.uc.reg_read(self.r.UC_X86_REG_RAX)}

    def initialize(self):
        if self.initialized:
            raise FactoryExecutionError("Backend already initialized; create a fresh fixture")
        calls = [self._invoke(entry) for entry in
                 (0x21EAF65, 0x2AF99D8, 0x2B9C5B9, 0x2BD477C, 0x2248A3B, 0x21813F4)]
        if tuple(entry for entry in self.scheduler_registrations if entry in PHASES) != PHASES:
            raise FactoryExecutionError("Original scheduler did not register the supported five phases")
        # Explicit fixture registration through original API using source addresses.
        for channel, event, constant in ((0x17, 0x98, 0x38CB558), (0x17, 0x99, 0x38CB559),
                                         (0x39B, 0x13D, 0x38CB6C8), (0x39B, 0x13C, 0x38CB6C7),
                                         (0x39C, 0x13F, 0x38CB6CA), (0x39C, 0x13E, 0x38CB6C9)):
            expected = 1 if event in (0x98, 0x13D, 0x13F) else 0
            if self.uc.mem_read(constant, 1)[0] != expected:
                raise FactoryExecutionError("Original match constant does not match the supported profile")
            self._invoke(0x2B1741E, channel, event, constant)
        self._phases()
        if self.status()["readiness"] != {"rte": 2, "hmi": 1, "api": 1}:
            raise FactoryExecutionError("Original initialization did not raise the expected readiness states")
        self.initialized = True
        return calls

    def _phases(self):
        return [self._invoke(entry) for entry in PHASES]

    def _events(self):
        count = struct.unpack("<H", self.uc.mem_read(0x7AF8A74, 2))[0]
        start = struct.unpack("<H", self.uc.mem_read(0x7AF8A70, 2))[0]
        if count > 1000:
            raise FactoryExecutionError("Original SEM event queue exceeded its bound")
        return [struct.unpack("<H", self.uc.mem_read(0x7AF82A0 + 2 * ((start + i) % 1000), 2))[0]
                for i in range(count)]

    def receive(self, signal, raw, quality=0):
        if not self.initialized:
            raise FactoryExecutionError("Initialize the original backend before replay")
        if signal not in SIGNALS or type(raw) is not int or not 0 <= raw <= 255 or type(quality) is not int or not 0 <= quality <= 255:
            raise FactoryExecutionError("Expected an admitted signal and raw/quality bytes")
        record, callback = SIGNALS[signal]
        before = len(self._events())
        callback_before = self.callback_counts.get(callback, 0)
        self.uc.mem_write(DATA + 0x1000, bytes((raw, quality)))
        call = self._invoke(0x2248CA6, record, DATA + 0x1000, 2)
        phases = self._phases()
        events = self._events()[before:]
        return {"signal": signal, "raw": raw, "quality": quality,
                "receiver": call, "phases": phases, "events": events,
                "callbackCount": self.callback_counts.get(callback, 0) - callback_before}

    def status(self):
        return {"backend": "original-partial-controller-fixture", "fullFactoryStartup": False,
                "physicalTransport": False, "factoryGraphics": False,
                "semActivities": False, "liveF40Coding": False,
                "scheduler": "five original registered callbacks, explicitly invoked",
                "readiness": {"rte": struct.unpack("<I", self.uc.mem_read(0x795E510, 4))[0],
                              "hmi": self.uc.mem_read(0x56DAFE4, 1)[0],
                              "api": self.uc.mem_read(0x7AD25F5, 1)[0]},
                "clock": "deterministic fixture", "source": self.source_identity}
