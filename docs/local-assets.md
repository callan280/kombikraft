# Local assets

An asset pack is a private directory containing `manifest.json` and the files
listed by that manifest. Keep it outside the checkout or inside ignored
`private/`. The format is `kombikraft-local-assets-v1`:

```json
{
  "schema": "kombikraft-local-assets-v1",
  "entries": [
    {"route": "/design/assets/example.png", "file": "files/example.png", "sha256": "64 lowercase hex characters"}
  ]
}
```

Only relative regular-file paths within the pack are admitted; symlinks,
duplicate routes, path traversal and changed file bytes are rejected. This
checks local file identity. It does not prove BMW signature acceptance, correct
vehicle coding or asset rights.

The existing private research pipeline can assemble a reviewed asset pack from
locally extracted materials. Public extraction adapters for each supported
firmware family are still needed. Do not download a random firmware bundle or
attach private source material to an issue to work around a missing import.

The browser needs WebGL and the matching graphics packages/fonts. Without them
it displays an input error instead of a fallback cluster. A native emulator
also requires separately supplied runtime images and the supported local
backend; a browser preview is not a booted ECU.
