"""Authored synthetic examples; no observed firmware or vehicle request fixtures."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch
from dma_geometry import GeometryError, analyze, main


def request(blocks=2, words=3, width_code=2, mode=1, d=0, source=0x1000, destination=0x8000):
    return dict(a=(words - 1) << 20 | 0xF0000 | blocks - 1,
                b=mode << 28 | width_code << 26, d=d, source=source, destination=destination)


class GeometryTests(unittest.TestCase):
    def test_contiguous_synthetic_copy_geometry(self):
        r = analyze(request())
        self.assertEqual((r["nominal_transfers"], r["nominal_bytes"]), (6, 24))
        self.assertEqual([p["source"] for p in r["preview"]], [0x1000,0x1004,0x1008,0x100c,0x1010,0x1014])
        self.assertEqual(r["destination"]["highest_byte"], 0x8017)

    def test_block_reset_is_not_contiguous_copy(self):
        r = analyze(request(d=1 << 28))
        self.assertEqual([p["source"] for p in r["preview"]], [0x1000,0x1004,0x1008,0x1000,0x1004,0x1008])
        self.assertEqual(r["source"]["distinct_bytes"], 12)
        self.assertEqual(r["nominal_bytes"], 24)

    def test_fixed_overrides_block_and_decrement(self):
        r = analyze(request(d=(0xD << 28) | (0xD << 12)))
        self.assertTrue(all(p["source"] == 0x1000 and p["destination"] == 0x8000 for p in r["preview"]))
        self.assertEqual(r["source"]["distinct_bytes"], 4)

    def test_block_reset_overrides_decrement(self):
        r = analyze(request(d=(0x5 << 28) | (0x5 << 12)))
        self.assertEqual([p["destination"] for p in r["preview"]], [0x8000,0x8004,0x8008,0x8000,0x8004,0x8008])

    def test_decrement(self):
        r = analyze(request(d=(1 << 30) | (1 << 14)))
        self.assertEqual(r["source"]["lowest_byte"], 0xfec)
        self.assertEqual([p["destination"] for p in r["preview"]], [0x8000,0x7ffc,0x7ff8,0x7ff4,0x7ff0,0x7fec])

    def test_widths_and_modes(self):
        for mode in [0, 1]:
            for code, width in enumerate([1,2,4,8]):
                r = analyze(request(mode=mode,width_code=code))
                self.assertEqual(r["nominal_bytes"], 6 * width)

    def test_maximum_count_has_bounded_preview(self):
        r = analyze(request(blocks=65536,words=16,width_code=3), preview=3)
        self.assertEqual(r["nominal_transfers"], 1048576)
        self.assertEqual(len(r["preview"]), 3)
        self.assertTrue(r["preview_truncated"])

    def test_wrap_and_alignment_rejected(self):
        for r in [request(source=0xfffffffc),request(source=0,d=1 << 30),request(source=0x1001)]:
            with self.assertRaises(GeometryError):analyze(r)

    def test_invalid_types_fields_modes_and_reserved_bits(self):
        bad=[request() | {"a":True},request() | {"b":-1},request() | {"source":1 << 32},
             request() | {"a":"junk"},request() | {"d":1},request(mode=2),
             request() | {"extra":1},[1,2,3]]
        for r in bad:
            with self.assertRaises(GeometryError):analyze(r)
        for n in [-1,65,True,1.5]:
            with self.assertRaises(GeometryError):analyze(request(),n)

    def test_cli_and_clear_failure(self):
        r = request(blocks=1,words=1)
        args=[value for k,v in r.items() for value in ["--"+k,hex(v)]]
        out=io.StringIO()
        with contextlib.redirect_stdout(out):self.assertEqual(main(args),0)
        self.assertEqual(json.loads(out.getvalue())["nominal_transfers"],1)
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exc:main(["--a","0"])
        self.assertEqual(exc.exception.code,2)

    def test_json_stdin_and_input_limits(self):
        data=json.dumps(request()).encode()
        out=io.StringIO()
        with patch("sys.stdin",io.TextIOWrapper(io.BytesIO(data))),contextlib.redirect_stdout(out):
            self.assertEqual(main(["--input","-","--preview","0"]),0)
        self.assertEqual(json.loads(out.getvalue())["preview"],[])
        for raw in [b'{"a":0,"a":1}',b' ' * 65537,b'not json']:
            with patch("sys.stdin",io.TextIOWrapper(io.BytesIO(raw))),contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:main(["--input","-"])
            self.assertEqual(exc.exception.code,2)

    def test_decimal_strings_and_no_device_claim(self):
        r=analyze({k:str(v) for k,v in request().items()})
        self.assertFalse(r["limits"]["transfer_executed"])
        self.assertFalse(r["limits"]["vehicle_compatibility_proved"])
        self.assertEqual(analyze(request() | {"a":"0000"})["blocks"],1)


if __name__ == "__main__":
    unittest.main()
