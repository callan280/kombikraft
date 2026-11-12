# Contributing

Keep changes small enough to reproduce and review. Describe the source version,
input, observed output, test command and remaining uncertainty.

- Use synthetic fixtures in public tests. Keep vehicle captures and identifiers
  local, including VINs, coding, precise locations, keys and credentials.
- Do not commit BMW firmware, extracted graphics/fonts, decompiled source,
  captured proprietary shaders/Lua, VM disks, or third-party cover art.
- Keep original-source execution, custom preview logic and live observations
  separately labelled. Internal datastore and transport IDs are not CAN IDs.
- A successful hash check proves file identity, not cryptographic acceptance or
  vehicle compatibility. A rendered frame does not prove warning ownership.
- Preserve unknown/invalid values and provider loss; do not replace unavailable
  telemetry with plausible sample readings.
- Changes that touch vehicle deployment need separate, explicit review. This
  initial project has no vehicle-write path.

Run Python tests with `python -m unittest discover -s tests`. Browser logic
tests use Node.js where available. Open issues with the applicable firmware
version and reproducible steps, without attaching private firmware or logs.
