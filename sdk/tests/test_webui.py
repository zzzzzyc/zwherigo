from __future__ import annotations

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from wherigo_sdk.webui.server import WebUiHandler, WebUiState


def _server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), WebUiHandler)
    server.state = WebUiState()  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


def _get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def test_webui_serves_material_shell_and_project_api() -> None:
    server, base = _server()
    try:
        with urllib.request.urlopen(base + "/", timeout=5) as response:
            html = response.read().decode("utf-8")
        assert "top-app-bar" in html
        assert "地图" in html
        assert "leaflet@1.9.4/dist/leaflet.js" in html
        assert "integrity=" not in html

        state = _get_json(base + "/api/project")
        cartridge = state["cartridge"]
        assert isinstance(cartridge, dict)
        assert cartridge["name"] == "OSM Demo Cartridge"
        assert state["validation"]["valid"] is True
    finally:
        server.shutdown()
        server.server_close()


def test_webui_updates_project_and_builds_downloadable_artifacts() -> None:
    server, base = _server()
    try:
        state = _get_json(base + "/api/project")
        cartridge = state["cartridge"]
        assert isinstance(cartridge, dict)
        cartridge["name"] = "../Web UI:Beta"
        cartridge["media_objects"] = []

        updated = _post_json(base + "/api/project", {"cartridge": cartridge})
        assert updated["cartridge"]["name"] == "../Web UI:Beta"

        built = _post_json(base + "/api/build", {"skip_missing_media": True})
        assert built["lua_file"] == "Web_UI_Beta.lua"
        assert built["gwz_file"] == "Web_UI_Beta.gwz"
        assert built["manifest_file"] == "Web_UI_Beta.build.json"

        with urllib.request.urlopen(base + "/api/download/" + built["manifest_file"], timeout=5) as response:
            manifest = json.loads(response.read().decode("utf-8"))
        assert manifest["artifacts"]["lua"] == "Web_UI_Beta.lua"
    finally:
        server.shutdown()
        server.server_close()


def test_webui_accepts_frontend_project_payload_key() -> None:
    server, base = _server()
    try:
        state = _get_json(base + "/api/project")
        cartridge = state["cartridge"]
        assert isinstance(cartridge, dict)
        cartridge["name"] = "Frontend Payload"
        updated = _post_json(base + "/api/project", {"project": cartridge})
        assert updated["cartridge"]["name"] == "Frontend Payload"
        report = updated["validation"]
        assert report["valid"] is True
    finally:
        server.shutdown()
        server.server_close()


def test_webui_serves_static_assets_without_duplicate_static_prefix() -> None:
    server, base = _server()
    try:
        with urllib.request.urlopen(base + "/static/app.js", timeout=5) as response:
            script = response.read().decode("utf-8")
        assert "地图初始化失败" in script
        assert "function renderMap" in script
    finally:
        server.shutdown()
        server.server_close()


def test_webui_static_dom_ids_match_frontend_script() -> None:
    server, base = _server()
    try:
        with urllib.request.urlopen(base + "/", timeout=5) as response:
            html = response.read().decode("utf-8")
        with urllib.request.urlopen(base + "/static/app.js", timeout=5) as response:
            script = response.read().decode("utf-8")
        for element_id in ("projectId", "projectName", "statusLog"):
            assert f'id="{element_id}"' in html
            assert f'$("{element_id}")' in script
        assert 'id="entityNav"' in html
        assert 'id="entityCardTemplate"' in html
        assert '$("entityNav")' in script or '$("tabs")' not in script
        assert 'id="dirtyState"' in html
        assert ('id="quickZoneEnter"' in html) or ('id="quickAddZoneEnter"' in html)
        assert ('id="quickZoneExit"' in html) or ('id="quickAddZoneExit"' in html)
        assert "cartId" not in script
        assert "cartName" not in script
    finally:
        server.shutdown()
        server.server_close()


def test_webui_preset_endpoints_work() -> None:
    server, base = _server()
    try:
        presets = _get_json(base + "/api/presets")
        assert "presets" in presets
        assert any(entry["id"] == "zone_enter" for entry in presets["presets"])
        preview = _post_json(
            base + "/api/presets/preview",
            {"template_id": "zone_enter", "params": {"zone_name": "Start", "message": "Hi"}},
        )
        assert preview["event"]["name"].startswith("进入区域")
        applied = _post_json(
            base + "/api/presets/apply",
            {"template_id": "zone_enter", "params": {"zone_name": "Start", "message": "Hi"}},
        )
        assert applied["state"]["cartridge"]["events"]
    finally:
        server.shutdown()
        server.server_close()


def test_webui_preset_response_exposes_zone_trigger_metadata() -> None:
    server, base = _server()
    try:
        presets = _get_json(base + "/api/presets")
        zone_enter = next(entry for entry in presets["presets"] if entry["id"] == "zone_enter")
        assert zone_enter["trigger"] == "OnEnter"
        preview = _post_json(
            base + "/api/presets/preview",
            {"template_id": "zone_enter", "params": {"zone_name": "Start", "message": "Hi"}},
        )
        trigger = preview["event"]["extras"]["trigger"]
        assert trigger["kind"] == "zone_on_enter"
        assert trigger["zone_name"] == "Start"
    finally:
        server.shutdown()
        server.server_close()
