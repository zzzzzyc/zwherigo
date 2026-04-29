from __future__ import annotations

import json
from dataclasses import dataclass
import re
from pathlib import Path

from wherigo_sdk.io import load_project
from wherigo_sdk.lua import LuaEmitter
from wherigo_sdk.model.validation import validate_or_raise
from wherigo_sdk.packaging.compiler import CompileRequest, GwcCompiler, resolve_compiler
from wherigo_sdk.packaging.gwz import build_gwz

SAFE_ARTIFACT_RE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass
class BuildResult:
    lua_file: Path
    gwz_file: Path
    gwc_file: Path | None
    manifest_file: Path | None = None
    media_files: list[Path] | None = None


def safe_artifact_stem(name: str) -> str:
    stem = SAFE_ARTIFACT_RE.sub("_", name.strip()).strip("._")
    return stem or "cartridge"


def build_artifacts(
    project_file: str | Path,
    output_dir: str | Path,
    compiler: GwcCompiler | None = None,
    compiler_kind: str | None = None,
    bridge_path: str | Path | None = None,
    zoneslinker_dll: str | Path | None = None,
    skip_missing_media: bool = False,
) -> BuildResult:
    cartridge = load_project(project_file)
    validate_or_raise(cartridge)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = safe_artifact_stem(cartridge.name)
    lua_path = out_dir / f"{safe_name}.lua"
    gwz_path = out_dir / f"{safe_name}.gwz"
    gwc_path = out_dir / f"{safe_name}.gwc"
    manifest_path = out_dir / f"{safe_name}.build.json"

    LuaEmitter(cartridge).write_to_file(lua_path)
    project_dir = Path(project_file).parent
    media_paths = [
        Path(media.filename) if Path(media.filename).is_absolute() else project_dir / media.filename
        for media in cartridge.media_objects
    ]
    build_gwz(lua_path, media_paths, gwz_path, allow_missing_media=skip_missing_media)

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

    manifest = {
        "cartridge_id": cartridge.id,
        "cartridge_name": cartridge.name,
        "artifacts": {
            "lua": lua_path.name,
            "gwz": gwz_path.name,
            "gwc": compiled_gwc.name if compiled_gwc else None,
        },
        "media": [path.name for path in media_paths if path.is_file()],
        "missing_media": [str(path) for path in media_paths if not path.is_file()],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return BuildResult(
        lua_file=lua_path,
        gwz_file=gwz_path,
        gwc_file=compiled_gwc,
        manifest_file=manifest_path,
        media_files=media_paths,
    )
