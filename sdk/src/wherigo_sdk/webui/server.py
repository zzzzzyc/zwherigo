from __future__ import annotations

import importlib.util
from pathlib import Path

_WEBUI_SERVER_PATH = Path(__file__).resolve().parents[4] / "webui" / "server.py"
_SPEC = importlib.util.spec_from_file_location("zwherigo_webui_server", _WEBUI_SERVER_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Failed to load WebUI server module: {_WEBUI_SERVER_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

WebUiState = _MODULE.WebUiState
WebUiHandler = _MODULE.WebUiHandler
run_webui = _MODULE.run_webui
run = _MODULE.run
main = _MODULE.main

if __name__ == "__main__":
    raise SystemExit(main())
