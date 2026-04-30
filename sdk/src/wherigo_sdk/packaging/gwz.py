from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from wherigo_sdk.errors import PackagingError


def _archive_name(path: Path) -> str:
    if path.name in {"", ".", ".."}:
        raise PackagingError(f"invalid archive member path: {path}")
    return path.name


def build_gwz(
    lua_file: str | Path,
    media_files: list[str | Path],
    output_file: str | Path,
    *,
    allow_missing_media: bool = False,
) -> Path:
    lua_path = Path(lua_file)
    if not lua_path.is_file():
        raise PackagingError(f"Lua file not found: {lua_path}")

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    seen_names = {_archive_name(lua_path)}
    with ZipFile(out_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(lua_path, arcname=_archive_name(lua_path))
        for media in media_files:
            media_path = Path(media)
            if not media_path.is_file():
                if not allow_missing_media:
                    raise PackagingError(f"Media file not found: {media_path}")
                continue
            arcname = _archive_name(media_path)
            if arcname in seen_names:
                raise PackagingError(f"Duplicate GWZ archive member name: {arcname}")
            seen_names.add(arcname)
            archive.write(media_path, arcname=arcname)
    return out_path
