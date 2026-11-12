#!/usr/bin/env python3
"""Offline Traveo T1G DMA address geometry. No memory or device access."""
import argparse
import json
import sys
from pathlib import Path

U32_MAX = (1 << 32) - 1
MAX_INPUT_BYTES = 65536
MAX_PREVIEW = 64
FIELDS = {"a", "b", "d", "source", "destination"}


class GeometryError(ValueError):
    """Input is invalid or outside the supported geometry subset."""


def u32(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise GeometryError(f"{name} must be an integer or decimal/0x integer string")
    try:
        if isinstance(value, str):
            text = value.strip()
            number = int(text, 16 if text.lower().startswith("0x") else 10)
        else:
            number = value
    except ValueError as exc:
        raise GeometryError(f"{name} is not a valid decimal/0x integer") from exc
    if not 0 <= number <= U32_MAX:
        raise GeometryError(f"{name} must fit an unsigned 32-bit value")
    return number


def side_plan(start, width, blocks, per_block, fixed, reset_block, decrement):
    if fixed:
        kind, unique, stride = "fixed", 1, 0
    elif reset_block:
        kind, unique, stride = "reset_each_block", per_block, width
    else:
        kind, unique = ("decrement" if decrement else "increment"), blocks * per_block
        stride = -width if decrement else width
    last = start + (unique - 1) * stride
    low, high = min(start, last), max(start, last) + width - 1
    if low < 0 or high > U32_MAX:
        raise GeometryError("address span would wrap outside the 32-bit address space")
    return {"behavior": kind, "start": start, "last_distinct_transfer_start": last,
            "lowest_byte": low, "highest_byte": high,
            "distinct_transfer_addresses": unique, "distinct_bytes": unique * width,
            "stride_bytes": stride}


def analyze(request, preview=8):
    if not isinstance(request, dict) or set(request) != FIELDS:
        raise GeometryError("input must contain exactly a, b, d, source, destination")
    if isinstance(preview, bool) or not isinstance(preview, int) or not 0 <= preview <= MAX_PREVIEW:
        raise GeometryError(f"preview must be between 0 and {MAX_PREVIEW}")
    r = {name: u32(request[name], name) for name in FIELDS}
    mode = r["b"] >> 28 & 3
    if mode not in (0, 1):
        raise GeometryError("only MS=0 block and MS=1 burst geometry are supported")
    if r["d"] & ~0xF000F000:
        raise GeometryError("D contains unsupported/reserved bits outside FS/DES/US/FBS/FD/DED/UD/FBD")
    width = 1 << (r["b"] >> 26 & 3)
    if r["source"] % width or r["destination"] % width:
        raise GeometryError(f"source and destination must be aligned to {width} bytes")
    blocks, per_block = (r["a"] & 65535) + 1, (r["a"] >> 20 & 15) + 1
    d = r["d"]
    source = side_plan(r["source"], width, blocks, per_block,
                       bool(d & 1 << 31), bool(d & 1 << 28), bool(d & 1 << 30))
    destination = side_plan(r["destination"], width, blocks, per_block,
                            bool(d & 1 << 15), bool(d & 1 << 12), bool(d & 1 << 14))
    total = blocks * per_block
    def address(side, index):
        offset = index % per_block if side["behavior"] == "reset_each_block" else index
        return side["start"] + offset * side["stride_bytes"]
    pairs = [{"index": i, "source": address(source, i), "destination": address(destination, i)}
             for i in range(min(total, preview))]
    return {"schema": "dma-address-geometry-v1", "mode": "block" if mode == 0 else "burst",
            "blocks": blocks, "transfers_per_block": per_block, "width_bytes": width,
            "nominal_transfers": total, "nominal_bytes": total * width,
            "source": source, "destination": destination, "preview": pairs,
            "preview_truncated": len(pairs) < total,
            "completion_update_controls": {"US": bool(d & 1 << 29), "UD": bool(d & 1 << 13),
                                           "simulated": False},
            "limits": {"geometry_only": True, "register_validity_checked": False,
                       "memory_accessed": False, "transfer_executed": False,
                       "device_readiness_proved": False, "vehicle_compatibility_proved": False}}


def unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise GeometryError(f"duplicate JSON field: {key}")
        out[key] = value
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="JSON file, or - for stdin (maximum 64 KiB)")
    for name in sorted(FIELDS):
        parser.add_argument("--" + name, help="unsigned 32-bit decimal or 0x value")
    parser.add_argument("--preview", type=int, default=8, help="number of address pairs, 0..64 (default 8)")
    args = parser.parse_args(argv)
    direct = {name: getattr(args, name) for name in FIELDS}
    try:
        if args.input:
            if any(value is not None for value in direct.values()):
                raise GeometryError("use --input or the five register/address flags, not both")
            if args.input == "-":
                data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
            else:
                with Path(args.input).open("rb") as stream:
                    data = stream.read(MAX_INPUT_BYTES + 1)
            if len(data) > MAX_INPUT_BYTES:
                raise GeometryError("JSON input exceeds 64 KiB")
            request = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)
        else:
            if any(value is None for value in direct.values()):
                raise GeometryError("provide all five flags: --a --b --d --source --destination")
            request = direct
        result = analyze(request, args.preview)
    except (GeometryError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
