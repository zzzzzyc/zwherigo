from __future__ import annotations

import argparse
import json
from pathlib import Path

from wherigo_sdk.io import load_project
from wherigo_sdk.lua import LuaEmitter
from wherigo_sdk.model import validate_project
from wherigo_sdk.packaging import ENV_BRIDGE_PATH, ENV_COMPILER, build_artifacts
from wherigo_sdk.webui import run_webui


def _cmd_export_lua(args: argparse.Namespace) -> int:
    cartridge = load_project(args.project)
    output = Path(args.output) if args.output else Path(args.project).with_suffix(".lua")
    LuaEmitter(cartridge).write_to_file(output)
    print(f"Lua exported: {output}")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    result = build_artifacts(
        args.project,
        args.output_dir,
        compiler_kind=args.compiler,
        bridge_path=args.bridge_path,
        zoneslinker_dll=args.zoneslinker_dll,
    )
    print(f"Lua: {result.lua_file}")
    print(f"GWZ: {result.gwz_file}")
    if result.gwc_file:
        print(f"GWC: {result.gwc_file}")
    else:
        print("GWC: skipped (no compiler configured)")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    cartridge = load_project(args.project)
    report = validate_project(cartridge)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"Project is {'valid' if report.ok else 'invalid'}")
        for warning in report.warnings:
            print(f"warning: {warning}")
        for error in report.errors:
            print(f"error: {error}")
    return 0 if report.ok else 1


def _cmd_webui(args: argparse.Namespace) -> int:
    run_webui(host=args.host, port=args.port, root=args.root, open_browser=not args.no_open)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wherigo", description="Wherigo SDK CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    export_lua = sub.add_parser("export-lua", help="Generate Lua from project file")
    export_lua.add_argument("project")
    export_lua.add_argument("-o", "--output")
    export_lua.set_defaults(func=_cmd_export_lua)

    validate = sub.add_parser("validate", help="Validate project structure and references")
    validate.add_argument("project")
    validate.add_argument("--json", action="store_true", help="Emit machine-readable report")
    validate.set_defaults(func=_cmd_validate)

    webui = sub.add_parser("webui", help="Launch the local Material Design WebUI")
    webui.add_argument("--host", default="127.0.0.1")
    webui.add_argument("--port", default=8765, type=int)
    webui.add_argument("--root", default=".", help="Workspace root for project load/save/build")
    webui.add_argument("--no-open", action="store_true", help="Do not open the browser automatically")
    webui.set_defaults(func=_cmd_webui)

    build = sub.add_parser("build", help="Generate Lua/GWZ and optionally GWC artifacts")
    build.add_argument("project")
    build.add_argument("-o", "--output-dir", default="dist")
    build.add_argument(
        "--compiler",
        default=None,
        help=f"Compiler backend (e.g. legacy-bridge, none). "
        f"If omitted, uses env {ENV_COMPILER}.",
    )
    build.add_argument(
        "--bridge-path",
        default=None,
        help=f"Path to legacy bridge executable. If omitted, uses env {ENV_BRIDGE_PATH}.",
    )
    build.add_argument(
        "--zoneslinker-dll",
        default=None,
        help="Optional path to ZonesLinker.dll passed to legacy bridge.",
    )
    build.set_defaults(func=_cmd_build)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
