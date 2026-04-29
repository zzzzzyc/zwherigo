from __future__ import annotations

from pathlib import Path

from wherigo_sdk.editor import EditorSession
from wherigo_sdk.io import load_project, save_project
from wherigo_sdk.lua import LuaEmitter
from wherigo_sdk.model import Cartridge, Event, Input, Variable


def _base_cartridge(tmp_path: Path) -> Cartridge:
    return Cartridge(
        id="cart-1",
        name="EditorCart",
        file_name=str(tmp_path / "editor.wigi.json"),
        variables=[Variable(id="var-1", name="Score", var_type="number", value=0)],
        inputs=[Input(id="input-1", name="ScoreInput", variable_id="var-1")],
        events=[Event(name="OnStart", object_name="Score", event_type="wig")],
    )


def test_add_and_update_zone_command() -> None:
    cartridge = _base_cartridge(Path("."))
    session = EditorSession(cartridge)
    add_result = session.apply_command(
        {"op": "add", "entity_type": "zone", "payload": {"id": "zone-1", "name": "Z1"}}
    )
    assert add_result.ok
    update_result = session.apply_command(
        {
            "op": "update",
            "entity_type": "zone",
            "entity_id": "zone-1",
            "payload": {"name": "Z2", "description": "new desc"},
        }
    )
    assert update_result.ok
    assert cartridge.zones[0].name == "Z2"


def test_remove_variable_restrict_fails_when_referenced() -> None:
    cartridge = _base_cartridge(Path("."))
    session = EditorSession(cartridge)
    result = session.apply_command(
        {"op": "remove", "entity_type": "variable", "entity_id": "var-1", "mode": "restrict"}
    )
    assert not result.ok
    assert "referenced by" in result.errors[0]
    assert len(cartridge.variables) == 1


def test_remove_variable_cascade_removes_inputs_too() -> None:
    cartridge = _base_cartridge(Path("."))
    session = EditorSession(cartridge)
    result = session.apply_command(
        {"op": "remove", "entity_type": "variable", "entity_id": "var-1", "mode": "cascade"}
    )
    assert result.ok
    assert len(cartridge.variables) == 0
    assert len(cartridge.inputs) == 0


def test_transaction_rollback_on_failure() -> None:
    cartridge = _base_cartridge(Path("."))
    session = EditorSession(cartridge, strict_mode=True)
    session.begin()
    ok_result = session.apply_command(
        {"op": "add", "entity_type": "item", "payload": {"id": "item-1", "name": "I1"}}
    )
    assert ok_result.ok
    bad_result = session.apply_command(
        {
            "op": "add",
            "entity_type": "input",
            "payload": {"id": "input-2", "name": "Broken", "variable_id": "missing"},
        }
    )
    assert not bad_result.ok
    assert len(session.cartridge.items) == 0


def test_rename_updates_event_object_name() -> None:
    cartridge = _base_cartridge(Path("."))
    session = EditorSession(cartridge)
    result = session.apply_command(
        {
            "op": "update",
            "entity_type": "variable",
            "entity_id": "var-1",
            "payload": {"name": "ScoreV2"},
        }
    )
    assert result.ok
    assert cartridge.events[0].object_name == "ScoreV2"


def test_save_and_lua_smoke_after_editor_ops(tmp_path: Path) -> None:
    cartridge = _base_cartridge(tmp_path)
    session = EditorSession(cartridge)
    session.apply_command(
        {"op": "add", "entity_type": "task", "payload": {"id": "task-1", "name": "FirstTask"}}
    )
    project_path = tmp_path / "edited.wigi.json"
    save_project(session.cartridge, project_path)
    loaded = load_project(project_path)
    lua_text = LuaEmitter(loaded).render()
    assert "return cartEditorCart" in lua_text
