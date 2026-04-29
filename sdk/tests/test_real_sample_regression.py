from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from wherigo_sdk.packaging.gwz import build_gwz


def test_shougang4_sample_lua_has_expected_runtime_markers() -> None:
    sample_lua = Path("samples/real/shougang4/_cartridge.lua")
    assert sample_lua.exists()
    text = sample_lua.read_text(encoding="utf-8", errors="ignore")
    assert 'require "Wherigo"' in text
    assert "_Urwigo" in text
    assert "Wherigo.MessageBox" in text
    assert "function " in text
    assert len(text) > 5000


def test_shougang4_sample_can_be_repacked_to_gwz(tmp_path: Path) -> None:
    sample_lua = Path("samples/real/shougang4/_cartridge.lua")
    output_gwz = tmp_path / "shougang4.repacked.gwz"
    built = build_gwz(lua_file=sample_lua, media_files=[], output_file=output_gwz)
    assert built.exists()

    with ZipFile(built) as archive:
        members = archive.namelist()
        assert len(members) == 1
        assert "_cartridge.lua" in members
        payload = archive.read("_cartridge.lua")

    assert payload == sample_lua.read_bytes()
