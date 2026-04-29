# Python Wherigo SDK

`wherigo_sdk` is a pure Python core SDK for Wherigo tooling.

Current beta-oriented end-to-end features:

- Project model and JSON I/O
- Lua emission for core objects/events
- GWZ packaging with missing-media checks
- GWC compile adapter abstraction
- Build manifest output for generated Lua/GWZ/GWC artifacts
- CLI: `wherigo validate`, `wherigo export-lua`, and `wherigo build`
- Editor API core: command-style CRUD, reference-safe delete, and in-memory transaction

GWC backend options:

- `--compiler legacy-bridge --bridge-path <bridge-exe>`
- Environment variables: `WHERIGO_GWC_COMPILER`, `WHERIGO_GWC_BRIDGE_PATH`
- Setup guide: `docs/gwc-compiler-setup.md`

Editor API quick example:

```python
from wherigo_sdk import EditorSession, load_project, save_project

cart = load_project("project.wigi.json")
session = EditorSession(cart, strict_mode=True)

result = session.apply_command({
    "op": "add",
    "entity_type": "zone",
    "payload": {"id": "zone-001", "name": "StartZone"},
})
if result.ok:
    save_project(session.cartridge, "project.edited.wigi.json")
```

Validation and build quick checks:

```bash
wherigo validate project.wigi.json
wherigo build project.wigi.json -o dist
```

`wherigo validate --json project.wigi.json` prints a machine-readable report with
`valid`, `errors`, `warnings`, and entity counts. Builds write
`<cartridge-name>.build.json` alongside artifacts so editor or CI tooling can
discover the exact files that were produced.
