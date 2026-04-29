# Beta readiness notes

This SDK now treats build and validation behavior as beta-quality API surface.

## Safety hardening

- Build artifact names are normalized from cartridge names and cannot escape the output directory.
- GWZ packaging raises `PackagingError` when a requested media file is missing.
- Use `allow_missing_media=True` only for legacy recovery workflows where partial GWZ output is expected.
- Lua event function names are emitted as valid Lua identifiers, including names that start with digits.

## Validation workflow

Use the CLI before export or build:

```bash
wherigo validate project.wigi.json
```

Programmatic callers can use `validate_project(cartridge)` for a structured result:

```python
from wherigo_sdk import load_project, validate_project

report = validate_project(load_project("project.wigi.json"))
if not report.ok:
    raise SystemExit(report.errors)
```

## Build manifest

`build_artifacts()` now writes `build-manifest.json` beside generated artifacts. The manifest records:

- cartridge id and name
- generated Lua and GWZ paths
- optional GWC path
- packaged media filenames
- missing media filenames when explicitly allowed

This is intended for editor integrations and CI jobs that need a machine-readable summary of a build.
