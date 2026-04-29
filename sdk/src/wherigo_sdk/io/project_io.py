from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wherigo_sdk.errors import ProjectFormatError
from wherigo_sdk.model import (
    Action,
    Cartridge,
    Character,
    Condition,
    Event,
    Input,
    Item,
    MediaObject,
    ScriptGroup,
    Task,
    Variable,
    Zone,
)


def _parse_script_line(raw: Any) -> str | Condition | Action:
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        line_type = raw.get("type")
        if line_type == "condition":
            return Condition(expr=str(raw.get("expr", "")), join=str(raw.get("join", "and")))
        if line_type == "action":
            return Action(code=str(raw.get("code", "")))
        # Round-tripped dataclasses may not preserve explicit type tags.
        if "expr" in raw:
            return Condition(expr=str(raw.get("expr", "")), join=str(raw.get("join", "and")))
        if "code" in raw:
            return Action(code=str(raw.get("code", "")))
    raise ProjectFormatError(f"unsupported script line format: {raw!r}")


def cartridge_from_dict(raw: dict[str, Any]) -> Cartridge:
    try:
        return Cartridge(
            id=str(raw["id"]),
            name=str(raw["name"]),
            file_name=str(raw.get("file_name", "")),
            author_scripts=str(raw.get("author_scripts", "")),
            zones=[Zone(**obj) for obj in raw.get("zones", [])],
            items=[Item(**obj) for obj in raw.get("items", [])],
            characters=[Character(**obj) for obj in raw.get("characters", [])],
            tasks=[Task(**obj) for obj in raw.get("tasks", [])],
            variables=[Variable(**obj) for obj in raw.get("variables", [])],
            inputs=[Input(**obj) for obj in raw.get("inputs", [])],
            media_objects=[MediaObject(**obj) for obj in raw.get("media_objects", [])],
            events=[
                Event(
                    name=str(ev.get("name", "")),
                    object_name=str(ev.get("object_name", "")),
                    event_type=ev.get("event_type", "wig"),
                    callback_key=int(ev.get("callback_key", 0)),
                    lua_script=ev.get("lua_script"),
                    groups=[
                        ScriptGroup(
                            description=str(group.get("description", "")),
                            comment=str(group.get("comment", "")),
                            lines=[_parse_script_line(line) for line in group.get("lines", [])],
                        )
                        for group in ev.get("groups", [])
                    ],
                )
                for ev in raw.get("events", [])
            ],
            extras=dict(raw.get("extras", {})),
        )
    except KeyError as exc:
        raise ProjectFormatError(f"missing required project key: {exc}") from exc


def load_project(path: str | Path) -> Cartridge:
    project_path = Path(path)
    raw = json.loads(project_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ProjectFormatError("project root must be a JSON object")
    cartridge = cartridge_from_dict(raw)
    if not cartridge.file_name:
        cartridge.file_name = str(project_path)
    return cartridge


def save_project(cartridge: Cartridge, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(cartridge.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
