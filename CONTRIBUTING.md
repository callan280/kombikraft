# Contributing

Keep changes small enough to reproduce and review. Describe the source version,
input, observed output, test command and remaining uncertainty.

- Use synthetic fixtures in public tests. Keep vehicle captures and identifiers
  local, including VINs, coding, precise locations, keys and credentials.
- Keep complete firmware, runtime libraries, VM disks and vehicle backups out
  of Git. Reviewed visual resources belong in the separately attributed asset
  library with hashes, provenance and permission, never an assumed MIT grant.
  Do not add other third-party material without its applicable terms.
- Keep original-source execution, custom preview logic and live observations
  separately labelled. Internal datastore and transport IDs are not CAN IDs.
- A successful hash check proves file identity, not cryptographic acceptance or
  vehicle compatibility. A rendered frame does not prove warning ownership.
- Preserve unknown/invalid values and provider loss; do not replace unavailable
  telemetry with plausible sample readings.
- Changes that touch vehicle deployment need separate, explicit review. This
  research project has no validated replacement-cluster deployment path.

Read [firmware setup](docs/firmware-setup.md) to identify your car's versions
and obtain matching local inputs. Included visuals do not establish another
car's firmware compatibility.

Run Python tests with `python -m unittest discover -s tests`. Browser logic
tests use Node.js where available. Open issues with the applicable firmware
version and reproducible steps, without attaching private firmware or logs.
