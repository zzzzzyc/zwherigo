from __future__ import annotations

import argparse
import json
import mimetypes
import tempfile
import webbrowser
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
    from wherigo_sdk.editor import EditorSession
    from wherigo_sdk.io import load_project, save_project
    from wherigo_sdk.lua import LuaEmitter
    from wherigo_sdk.model import Cartridge, Event, Input, MediaObject, Variable, Zone, validate_project
    from wherigo_sdk.packaging import build_artifacts
    from wherigo_sdk.presets import apply_event_preset, list_event_presets
except ModuleNotFoundError:
    import sys

    sdk_src = Path(__file__).resolve().parents[1] / "sdk" / "src"
    sys.path.insert(0, str(sdk_src))
    sys.modules.pop("wherigo_sdk", None)
    from wherigo_sdk.editor import EditorSession
    from wherigo_sdk.io import load_project, save_project
    from wherigo_sdk.lua import LuaEmitter
    from wherigo_sdk.model import Cartridge, Event, Input, MediaObject, Variable, Zone, validate_project
    from wherigo_sdk.packaging import build_artifacts
    from wherigo_sdk.presets import apply_event_preset, list_event_presets

STATIC_DIR = Path(__file__).resolve().parent


def _demo_cartridge() -> Cartridge:
    return Cartridge(
        id="demo-cart",
        name="OSM Demo Cartridge",
        zones=[
            Zone(
                id="zone-start",
                name="Start Zone",
                description="Drag me on the OSM map; coordinates stay WGS84.",
                extras={"lat": 39.9042, "lon": 116.4074, "radius": 45},
            )
        ],
        variables=[Variable(id="var-score", name="Score", var_type="number", value=0)],
        inputs=[Input(id="input-score", name="Score Input", variable_id="var-score")],
        media_objects=[MediaObject(id="media-cover", name="Cover", filename="cover.png")],
        events=[Event(name="OnStart", object_name="Cart", event_type="wig", lua_script="print('hello osm')")],
    )


def _json_default(value):
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class WebUiState:
    def __init__(self, root: str | Path = ".") -> None:
        self.cartridge = _demo_cartridge()
        self.root = Path(root).expanduser().resolve()
        self.project_path: Path | None = None
        self.build_dir = Path(tempfile.mkdtemp(prefix="wherigo-webui-"))

    def snapshot(self) -> dict[str, object]:
        report = validate_project(self.cartridge)
        return {
            "project_path": str(self.project_path) if self.project_path else None,
            "cartridge": self.cartridge.to_dict(),
            "validation": report.to_dict(),
        }


class WebUiHandler(BaseHTTPRequestHandler):
    server_version = "WherigoWebUI/0.1"

    @property
    def state(self) -> WebUiState:
        return self.server.state  # type: ignore[attr-defined]

    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/project":
            self._send_json(self.state.snapshot())
            return
        if parsed.path == "/api/export-lua":
            self._send_text(LuaEmitter(self.state.cartridge).render(), "text/x-lua; charset=utf-8")
            return
        if parsed.path == "/api/presets":
            self._send_json({"presets": list_event_presets()})
            return
        if parsed.path.startswith("/api/download/"):
            self._send_download(parsed.path.removeprefix("/api/download/"))
            return
        self._send_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
            if parsed.path == "/api/project":
                self.state.cartridge = _cartridge_from_payload(payload)
                self.state.project_path = None
                self._send_json(self.state.snapshot())
                return
            if parsed.path == "/api/validate":
                cartridge = _cartridge_from_payload(payload)
                self._send_json({"report": validate_project(cartridge).to_dict()})
                return
            if parsed.path == "/api/load":
                path = self._resolve_workspace_path(payload.get("path"))
                self.state.cartridge = load_project(path)
                self.state.project_path = path
                self._send_json(self.state.snapshot())
                return
            if parsed.path == "/api/save":
                path = self._resolve_workspace_path(payload.get("path") or self.state.project_path)
                if not path:
                    self._send_error(400, "save path is required")
                    return
                self.state.project_path = save_project(self.state.cartridge, path)
                self._send_json(self.state.snapshot())
                return
            if parsed.path == "/api/command":
                result = EditorSession(self.state.cartridge, strict_mode=False).apply_command(payload)
                self._send_json({"result": result.to_dict(), "state": self.state.snapshot()})
                return
            if parsed.path == "/api/presets/apply":
                self._apply_preset(payload)
                return
            if parsed.path == "/api/presets/preview":
                self._preview_preset(payload)
                return
            if parsed.path == "/api/build":
                if "project" in payload or "cartridge" in payload:
                    self.state.cartridge = _cartridge_from_payload(payload)
                self._build(payload)
                return
            self._send_error(404, "unknown endpoint")
        except Exception as exc:
            self._send_error(400, f"{type(exc).__name__}: {exc}")

    def _build(self, payload: dict[str, object]) -> None:
        project_path = self.state.build_dir / "webui-project.wigi.json"
        save_project(self.state.cartridge, project_path)
        result = build_artifacts(
            project_path,
            self.state.build_dir,
            compiler_kind=str(payload.get("compiler") or "none"),
            skip_missing_media=bool(payload.get("skip_missing_media", True)),
        )
        self._send_json(
            {
                "lua_file": result.lua_file.name,
                "gwz_file": result.gwz_file.name,
                "gwc_file": result.gwc_file.name if result.gwc_file else None,
                "manifest_file": result.manifest_file.name if result.manifest_file else None,
                "download_base": "/api/download/",
            }
        )

    def _apply_preset(self, payload: dict[str, object]) -> None:
        template_id = str(payload.get("template_id", "")).strip()
        params = payload.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("params must be an object")
        result = apply_event_preset(template_id, params)
        self.state.cartridge.events.append(result.event)
        self._send_json(
            {
                "result": {"ok": True, "errors": [], "changes": []},
                "event": asdict(result.event),
                "state": self.state.snapshot(),
            }
        )

    def _preview_preset(self, payload: dict[str, object]) -> None:
        template_id = str(payload.get("template_id", "")).strip()
        params = payload.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("params must be an object")
        result = apply_event_preset(template_id, params)
        self._send_json({"event": asdict(result.event)})

    def _send_static(self, request_path: str) -> None:
        if request_path in {"", "/"}:
            rel = "index.html"
        else:
            rel = unquote(request_path.lstrip("/"))
            if rel.startswith("static/"):
                rel = rel[7:]
        path = (STATIC_DIR / rel).resolve()
        if not path.is_file() or STATIC_DIR.resolve() not in path.parents:
            self._send_error(404, "static file not found")
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def _resolve_workspace_path(self, value: object) -> Path:
        text = str(value or "").strip()
        if not text:
            raise ValueError("path is required")
        path = Path(text).expanduser()
        if not path.is_absolute():
            path = self.state.root / path
        return path

    def _send_download(self, name: str) -> None:
        safe_name = Path(unquote(name)).name
        path = (self.state.build_dir / safe_name).resolve()
        if not path.is_file() or self.state.build_dir.resolve() not in path.parents:
            self._send_error(404, "download not found")
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
        self.send_header("Content-Length", str(path.stat().st_size))
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        data = json.loads(raw or "{}")
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _send_json(self, payload: object) -> None:
        body = json.dumps(payload, default=_json_default, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text: str, content_type: str) -> None:
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str) -> None:
        body = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _cartridge_from_payload(payload: dict[str, object]) -> Cartridge:
    raw = payload.get("cartridge", payload.get("project", payload))
    if not isinstance(raw, dict):
        raise ValueError("cartridge payload must be an object")
    from wherigo_sdk.io.project_io import cartridge_from_dict

    return cartridge_from_dict(raw)


def run_webui(
    host: str = "127.0.0.1",
    port: int = 8765,
    root: str | Path = ".",
    open_browser: bool = False,
) -> None:
    server = ThreadingHTTPServer((host, port), WebUiHandler)
    server.state = WebUiState(root=root)  # type: ignore[attr-defined]
    url = f"http://{host}:{port}"
    print(f"Wherigo WebUI: {url}")
    if open_browser:
        webbrowser.open(url)
    server.serve_forever()


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    run_webui(host=host, port=port)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wherigo-webui", description="运行 Wherigo SDK WebUI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--root", default=".")
    parser.add_argument("--open", action="store_true", help="在默认浏览器打开 WebUI")
    args = parser.parse_args(argv)
    run_webui(args.host, args.port, root=args.root, open_browser=args.open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
