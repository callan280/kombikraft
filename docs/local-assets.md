# Viewer assets

The reviewed repository pack is `assets/viewer-pack`. Run
`kombikraft serve --assets assets/viewer-pack` from the checkout. These resources
have separate attribution; see [asset notices](../ASSET-NOTICE.md).

For other firmware, an asset pack contains `manifest.json` and its listed
files. Keep unreviewed imports outside the checkout or in ignored `private/`.
The format retains its name, `kombikraft-local-assets-v1`:

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

`tools/export_viewer_assets.py` sanitizes metadata and checks an already
assembled pack; it does not extract arbitrary firmware. Adapters for additional
versions remain necessary. Read [firmware setup](firmware-setup.md) before
choosing programming data. Do not attach private firmware or diagnostic captures
to an issue to work around a missing import.

The browser needs WebGL and the matching graphics packages/fonts. Without them
it displays an input error instead of a fallback cluster. A native emulator
also requires separately supplied runtime images and the supported local
backend; a browser preview is not a booted ECU.
