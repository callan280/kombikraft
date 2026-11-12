"""Strict local source-bank admission; no downloads or firmware redistribution."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

class FactoryInputError(ValueError):
    """Required local factory input is missing, mismatched, or unadmitted."""

@dataclass(frozen=True)
class SourceBank:
    name: str
    base: int
    sha256: str
    data: bytes

def validate_bank_file(root, relative_file, expected_sha256):
    if not isinstance(relative_file, str) or not relative_file:
        raise FactoryInputError("Bank file must be a nonempty relative path")
    root = Path(root).expanduser().resolve()
    path = (root / relative_file).resolve()
    if Path(relative_file).is_absolute() or not path.is_relative_to(root):
        raise FactoryInputError("Bank file must stay inside the supplied local root")
    if not path.is_file():
        raise FactoryInputError(f"Missing local firmware bank: {relative_file}")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise FactoryInputError(f"Firmware bank hash mismatch: {relative_file}")
    return data

def load_banks(manifest, root):
    """Admit the exact supported profile from a user-supplied JSON bank manifest.

    Format: {"profile": PROFILE, "banks": [{"name", "file", "base", "sha256"}]}.
    Paths are relative to root. Only metadata is shipped with this package.
    """
    from .profile import PROFILE, REQUIRED_BANKS
    try:
        value = json.loads(Path(manifest).expanduser().read_text())
    except (OSError, ValueError) as exc:
        raise FactoryInputError("Cannot read the supplied local bank manifest") from exc
    if not isinstance(value, dict):
        raise FactoryInputError("Manifest must be a JSON object")
    if value.get("profile") != PROFILE:
        raise FactoryInputError(f"Unsupported factory profile; required: {PROFILE}")
    rows = value.get("banks")
    if not isinstance(rows, list):
        raise FactoryInputError("Manifest requires a banks list")
    indexed = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"] or row["name"] in indexed:
            raise FactoryInputError("Invalid or duplicate bank metadata")
        indexed[row.get("name")] = row
    result = []
    for name, base, digest in REQUIRED_BANKS:
        row = indexed.get(name)
        if row is None:
            raise FactoryInputError(f"Manifest is missing required bank: {name}")
        try:
            actual_base = int(str(row["base"]), 0)
            file = row["file"]
        except (KeyError, TypeError, ValueError) as exc:
            raise FactoryInputError(f"Invalid bank metadata: {name}") from exc
        if actual_base != base or row.get("sha256") != digest:
            raise FactoryInputError(f"Bank metadata does not match the supported profile: {name}")
        data = validate_bank_file(root, file, digest)
        result.append(SourceBank(name, base, digest, data))
    return tuple(result)

def manifest_template():
    """Return identity/path metadata for a local import; never firmware bytes."""
    from .profile import PROFILE, REQUIRED_BANKS
    return {"profile": PROFILE, "banks": [
        {"name": name, "file": name, "base": hex(base), "sha256": digest}
        for name, base, digest in REQUIRED_BANKS]}
