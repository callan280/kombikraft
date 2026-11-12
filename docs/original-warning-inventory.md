# Original warning inventory research

This optional command runs recovered Check Control IDs through the existing
original receiver, supplier, datastore phases and registered widget consumer.
It requires the exact supported GSS 160.002.002 14-bank local import. No firmware
is included. The packaged catalogue records 966 recovered ID aliases from 967 ROM
metadata rows; the last row has no recovered ID. It is not an inventory of every
possible fault, persistent lamp or warning on a particular vehicle.

Inspect the catalogue without running original code:

```sh
python -m kombikraft.research.check_control_inventory --catalogue
```

Exercise an explicit subset, including a collection and a formatted-text case:

```sh
python -m kombikraft.research.check_control_inventory \
  --manifest cc-inputs.json --root /path/to/local/banks \
  --ids 14 37 79 212 281 286 2051 --output warning-review
```

Omit `--ids` to exercise all 966 recovered IDs. Each single-ID internal fixture is
followed by a real original clear. This is a long CPU-only experiment. The source
machine runs on an isolated child process's main thread, using the existing
declared platform adapters. Source failure stops the experiment; it is not
retried or replaced with an authored warning. Existing output directories are
refused. Partial failure leaves a failed receipt and any completed observations.

`cases.ndjson` preserves the actual original text, descriptor references, source
palettes, collection slots and clear output. `receipt.json` records its digest,
source identity, configuration and category counts. Static text templates are
kept alongside computed output: formatting a placeholder such as `%0` is done by
the original source, not this command. A differing placeholder result is an
observation, not proof of the formatter's upstream dependencies or every value.

Language ordinal 2 is an explicit source fixture. Variant 1/bank 1 are the retained
source defaults, not verified coding for a connected car. The experiment does
not render pixels, determine warning priority, test acknowledgement/persistence,
decode raw CAN, contact either ECU, or authorize installation. The simulator's
separate 16-popup asset contract is unchanged by this command.
