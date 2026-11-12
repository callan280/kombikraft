# Offline DMA address geometry

This standalone Python 3.10+ tool calculates nominal Traveo T1G DMA address
patterns from explicit register values. All examples and tests are authored
synthetic inputs. It contains no firmware, captured vehicle requests or device
connection code. It reads only the optional JSON input file or standard input.

```sh
python3 dma_geometry.py --a 0x002f0001 --b 0x18000000 --d 0 --source 0x1000 --destination 0x8000
python3 dma_geometry.py --input request.json --preview 4
python3 -m unittest -v test_dma_geometry.py
```

JSON input contains exactly `a`, `b`, `d`, `source`, `destination`. Values may be
unsigned 32-bit JSON integers or decimal/`0x` strings. Use `--input -` for stdin.
JSON input is limited to 64 KiB. Invalid inputs produce a readable error and
exit status 2. Output addresses are decimal integers.

Supported geometry: MS=0 block or MS=1 burst; transfer widths 1, 2, 4 or 8 bytes;
fixed, incrementing, decrementing and per-block reset addresses. Fixed-address
control takes priority over block reset and decrement; block reset takes
priority over decrement. US/UD completion controls are reported but not applied.
Unaligned addresses and spans crossing the 32-bit address boundary are rejected.
Only the eight documented address-control bits in D are accepted.

The output distinguishes nominal traffic from distinct addressed bytes. It
computes totals and ranges algebraically and emits at most 64 preview pairs;
large counts do not allocate transfer-sized arrays. All other A/B fields are
ignored: this is not complete register validation or a hardware emulator.

The register-field interpretation follows the manufacturer-authored
[S6J32XX platform manual 002-04854 RevH](https://www.infineon.com/assets/row/public/documents/10/57/infineon-32-bit-microcontroller-traveo-family-s6j32xx-series-hardware-manual-platform-part-additionaltechnicalinformation-en.pdf),
chapter 27, address behavior tables and channel configuration registers A/B/D.
This tool neither reads payload memory nor simulates arbitration, protection,
clocks, transfer completion, interrupts or vehicle compatibility.
