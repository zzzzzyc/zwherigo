from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wherigo_sdk.io import load_project
from wherigo_sdk.lua import LuaEmitter
from wherigo_sdk.model.validation import validate_or_raise
from wherigo_sdk.packaging.compiler import CompileRequest, GwcCompiler, resolve_compiler
from wherigo_sdk.packaging.gwz import build_gwz


@dataclass
class BuildResult:
    lua_file: Path
    gwz_file: Path
    gwc_file: Path | None


def build_artifacts(
    project_file: str | Path,
    output_dir: str | Path,
    compiler: GwcCompiler | None = None,
    compiler_kind: str | None = None,
    bridge_path: str | Path | None = None,
    zoneslinker_dll: str | Path | None = None,
) -> BuildResult:
    cartridge = load_project(project_file)
    validate_or_raise(cartridge)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = cartridge.name.replace(":", "")
    lua_path = out_dir / f"{safe_name}.lua"
    gwz_path = out_dir / f"{safe_name}.gwz"
    gwc_path = out_dir / f"{safe_name}.gwc"

    LuaEmitter(cartridge).write_to_file(lua_path)
    build_gwz(lua_path, [m.filename for m in cartridge.media_objects], gwz_path)

    selected_compiler = compiler or resolve_compiler(
        compiler_kind=compiler_kind,
        bridge_path=bridge_path,
        zoneslinker_dll=zoneslinker_dll,
    )
    compiled_gwc: Path | None = None
    if selected_compiler is not None:
        request = CompileRequest(
            lua_file=lua_path,
            output_gwc=gwc_path,
            cartridge_id=cartridge.id,
        )
        compiled_gwc = selected_compiler.compile(request)

    return BuildResult(lua_file=lua_path, gwz_file=gwz_path, gwc_file=compiled_gwc)
