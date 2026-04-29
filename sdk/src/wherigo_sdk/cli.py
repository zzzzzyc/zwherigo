from __future__ import annotations

import argparse
from pathlib import Path

from wherigo_sdk.io import load_project
from wherigo_sdk.lua import LuaEmitter
from wherigo_sdk.packaging import ENV_BRIDGE_PATH, ENV_COMPILER, build_artifacts


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wherigo", description="Wherigo SDK CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    export_lua = sub.add_parser("export-lua", help="Generate Lua from project file")
    export_lua.add_argument("project")
    export_lua.add_argument("-o", "--output")
    export_lua.set_defaults(func=_cmd_export_lua)

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
