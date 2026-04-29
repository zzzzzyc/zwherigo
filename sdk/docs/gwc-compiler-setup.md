# GWC Compiler Setup (Legacy Bridge)

This SDK can compile `.gwc` by delegating to a legacy bridge executable that calls `ZonesLinker`.

## 1) Build the bridge tool

From `python-sdk/tools/legacy_gwc_bridge`:

```powershell
./build.ps1
```

The executable will be produced under `bin/Release/net8.0/`.

## 2) Provide legacy linker dependency

The bridge requires `ZonesLinker.dll` from the legacy Wherigo toolchain.

Supported options:

- Place `ZonesLinker.dll` beside the bridge executable, or
- Pass `--zoneslinker-dll <path>` from CLI.

## 3) Run build with bridge compiler

```powershell
wherigo build project.wigi.json `
  --compiler legacy-bridge `
  --bridge-path C:\path\LegacyGwcBridge.exe `
  --zoneslinker-dll C:\path\ZonesLinker.dll
```

Or use environment variables:

```powershell
$env:WHERIGO_GWC_COMPILER = "legacy-bridge"
$env:WHERIGO_GWC_BRIDGE_PATH = "C:\path\LegacyGwcBridge.exe"
wherigo build project.wigi.json
```

## 4) Troubleshooting

- `Bridge executable not found`: verify `--bridge-path` points to an existing `.exe`.
- `ZonesLinker.dll not found`: provide `--zoneslinker-dll` or copy DLL beside bridge executable.
- `Invalid enum value`: check requested `device_type` / `engine_version` are supported by linker.
- `Bridge returned non-JSON output`: run bridge directly to inspect runtime errors and missing dependencies.
