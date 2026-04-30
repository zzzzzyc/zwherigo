from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from wherigo_sdk.errors import PackagingError
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
    validate_project,
)
from wherigo_sdk.packaging import build_artifacts, build_gwz


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
    assert "__wigi_item_caps" not in lua_text
    assert "return cartDemoCart" in lua_text


def test_lua_emitter_includes_item_capability_helpers_when_items_exist() -> None:
    cartridge = Cartridge(
        id="cart-cap",
        name="CapCart",
        items=[],
    )
    cartridge.items.append(
        __import__("wherigo_sdk.model", fromlist=["Item"]).Item(
            id="item-1",
            name="Key Item",
            allow_use=False,
            allow_take=True,
            allow_drop=False,
            allow_give=True,
        )
    )
    lua_text = LuaEmitter(cartridge).render()
    assert "__wigi_item_caps" in lua_text
    assert "function __wigi_can_use" in lua_text
    assert "key_item" in lua_text


def test_build_artifacts_creates_lua_and_gwz(tmp_path: Path) -> None:
    cartridge = _demo_cartridge(tmp_path)
    project_path = tmp_path / "demo.wigi.json"
    save_project(cartridge, project_path)

    result = build_artifacts(project_path, tmp_path / "out")
    assert result.lua_file.exists()
    assert result.gwz_file.exists()
    assert result.manifest_file.exists()
    with ZipFile(result.gwz_file) as archive:
        assert result.lua_file.name in archive.namelist()
    manifest = json.loads(result.manifest_file.read_text(encoding="utf-8"))
    assert manifest["cartridge_id"] == "cart-1"
    assert manifest["artifacts"]["gwz"] == result.gwz_file.name


def test_validation_collects_reference_errors() -> None:
    cartridge = Cartridge(
        id="c2",
        name="bad",
        variables=[],
        inputs=[Input(id="in-1", name="BrokenInput", variable_id="missing-var")],
    )
    errors = collect_validation_errors(cartridge)
    assert any("missing variable" in error for error in errors)


def test_validate_project_returns_beta_summary() -> None:
    report = validate_project(
        Cartridge(
            id="",
            name="../bad:name",
            variables=[Variable(id="dup", name="Score")],
            inputs=[Input(id="dup", name="BrokenInput", variable_id="missing-var")],
        )
    )
    assert not report.ok
    assert "beta" in report.summary().lower()
    assert any("duplicate id" in error for error in report.errors)
    assert any("filename" in warning for warning in report.warnings)


def test_build_artifacts_sanitizes_output_names(tmp_path: Path) -> None:
    cartridge = Cartridge(id="cart-escape", name="../Unsafe:Cart")
    project_path = tmp_path / "unsafe.wigi.json"
    save_project(cartridge, project_path)

    result = build_artifacts(project_path, tmp_path / "out")
    assert result.lua_file.parent == tmp_path / "out"
    assert result.lua_file.name == "Unsafe_Cart.lua"
    assert result.gwz_file.name == "Unsafe_Cart.gwz"


def test_gwz_missing_media_raises_by_default(tmp_path: Path) -> None:
    lua_file = tmp_path / "cart.lua"
    lua_file.write_text("return cart", encoding="utf-8")
    with pytest.raises(PackagingError, match="Media file not found"):
        build_gwz(lua_file=lua_file, media_files=[tmp_path / "missing.png"], output_file=tmp_path / "out.gwz")


def test_gwz_can_skip_missing_media_when_requested(tmp_path: Path) -> None:
    lua_file = tmp_path / "cart.lua"
    lua_file.write_text("return cart", encoding="utf-8")
    output = build_gwz(
        lua_file=lua_file,
        media_files=[tmp_path / "missing.png"],
        output_file=tmp_path / "out.gwz",
        allow_missing_media=True,
    )
    with ZipFile(output) as archive:
        assert archive.namelist() == ["cart.lua"]


def test_lua_emitter_sanitizes_function_names() -> None:
    cartridge = Cartridge(
        id="cart-lua",
        name="123 cart",
        events=[Event(name="On Start!", object_name="Zone One")],
    )
    lua_text = LuaEmitter(cartridge).render()
    assert "function Zone_One_On_Start_()" in lua_text
    assert "return cart_123_cart" in lua_text


def test_json_shape_is_object(tmp_path: Path) -> None:
    project_path = tmp_path / "bad.json"
    project_path.write_text(json.dumps(["not-object"]), encoding="utf-8")
    with pytest.raises(Exception, match="project root must be a JSON object"):
        load_project(project_path)
