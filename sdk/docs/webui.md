# SDK WebUI

The SDK includes a dependency-light WebUI for local editing and build checks.

```bash
wherigo webui
```

Open `http://127.0.0.1:8765`.

## Features

- Project JSON import/export through the browser.
- Cartridge metadata, zone, item, character, task, variable, input, media, and event editing.
- Live validation using SDK model checks.
- Lua export preview and SDK build output for Lua, GWZ, and build manifest files.
- OSM map editing for zone coordinates.

## OSM coordinate policy

The map uses OpenStreetMap tiles through Leaflet and stores zone coordinates as
plain WGS84 values in `zone.extras.lat`, `zone.extras.lon`, and
`zone.extras.radius`.

No GCJ-02 or other regional offset conversion is applied. If your source data is
already offset by another map provider, convert it before importing.
