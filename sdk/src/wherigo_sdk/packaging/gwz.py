from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def build_gwz(lua_file: str | Path, media_files: list[str | Path], output_file: str | Path) -> Path:
    lua_path = Path(lua_file)
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(lua_path, arcname=lua_path.name)
        for media in media_files:
            media_path = Path(media)
            if media_path.exists():
                archive.write(media_path, arcname=media_path.name)
    return out_path
