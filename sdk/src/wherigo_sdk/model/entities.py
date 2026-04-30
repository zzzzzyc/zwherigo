from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Union


@dataclass
class Condition:
    expr: str
    join: str = "and"


@dataclass
class Action:
    code: str


ScriptLine = Union[Condition, Action, str]


@dataclass
class ScriptGroup:
    description: str = ""
    comment: str = ""
    lines: list[ScriptLine] = field(default_factory=list)


@dataclass
class Event:
    name: str
    object_name: str = ""
    event_type: Literal["wig", "callback"] = "wig"
    callback_key: int = 0
    lua_script: str | None = None
    groups: list[ScriptGroup] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class MediaObject:
    id: str
    name: str
    filename: str
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Zone:
    id: str
    name: str
    description: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Item:
    id: str
    name: str
    description: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Character:
    id: str
    name: str
    description: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    id: str
    name: str
    description: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Variable:
    id: str
    name: str
    var_type: Literal["string", "number", "boolean"] = "string"
    value: Any = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Input:
    id: str
    name: str
    variable_id: str
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Cartridge:
    id: str
    name: str
    file_name: str = ""
    author_scripts: str = ""
    zones: list[Zone] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    characters: list[Character] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    variables: list[Variable] = field(default_factory=list)
    inputs: list[Input] = field(default_factory=list)
    media_objects: list[MediaObject] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
