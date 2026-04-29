from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from wherigo_sdk.io import load_project, save_project
from wherigo_sdk.lua import LuaEmitter
from wherigo_sdk.model import (
    Action,
    Cartridge,
    Condition,
    Event,
    Input,
    ScriptGroup,
    Variable,
    collect_validation_errors,
)
from wherigo_sdk.packaging import build_artifacts


def _demo_cartridge(tmp_path: Path) -> Cartridge:
    return Cartridge(
        id="cart-1",
        name="DemoCart",
        file_name=str(tmp_path / "demo.wigi.json"),
        variables=[Variable(id="var-1", name="Score", var_type="number", value=0)],
        inputs=[Input(id="in-1", name="InputName", variable_id="var-1")],
        events=[
            Event(
                name="OnStart",
                object_name="cartDemoCart",
                groups=[
                    ScriptGroup(
                        description="group",
                        comment="comment",
                        lines=[Condition(expr="1 == 1", join="then"), Action(code="print('hello')")],
                    )
                ],
            )
        ],
        author_scripts="function my_author_fn() end",
    )


def test_project_roundtrip(tmp_path: Path) -> None:
    cartridge = _demo_cartridge(tmp_path)
    project_path = tmp_path / "demo.wigi.json"
    save_project(cartridge, project_path)
    loaded = load_project(project_path)
    assert loaded.id == "cart-1"
    assert loaded.variables[0].name == "Score"


def test_lua_emitter_outputs_expected_markers(tmp_path: Path) -> None:
    cartridge = _demo_cartridge(tmp_path)
    lua_text = LuaEmitter(cartridge).render()
    assert "--#LASTCALLBACKKEY=0#--" in lua_text
    assert "function cartDemoCart_OnStart()" in lua_text
    assert "return cartDemoCart" in lua_text


def test_build_artifacts_creates_lua_and_gwz(tmp_path: Path) -> None:
    cartridge = _demo_cartridge(tmp_path)
    project_path = tmp_path / "demo.wigi.json"
    save_project(cartridge, project_path)

    result = build_artifacts(project_path, tmp_path / "out")
    assert result.lua_file.exists()
    assert result.gwz_file.exists()
    with ZipFile(result.gwz_file) as archive:
        assert result.lua_file.name in archive.namelist()


def test_validation_collects_reference_errors() -> None:
    cartridge = Cartridge(
        id="c2",
        name="bad",
        variables=[],
        inputs=[Input(id="in-1", name="BrokenInput", variable_id="missing-var")],
    )
    errors = collect_validation_errors(cartridge)
    assert any("missing variable" in error for error in errors)


def test_json_shape_is_object(tmp_path: Path) -> None:
    project_path = tmp_path / "bad.json"
    project_path.write_text(json.dumps(["not-object"]), encoding="utf-8")
    with pytest.raises(Exception, match="project root must be a JSON object"):
        load_project(project_path)
