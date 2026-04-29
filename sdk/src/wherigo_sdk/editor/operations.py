from __future__ import annotations

from dataclasses import asdict
from typing import Any

from wherigo_sdk.editor.changes import ChangeRecord
from wherigo_sdk.model import Character, Input, Item, MediaObject, Task, Variable, Zone


ENTITY_SPECS: dict[str, tuple[str, type[Any]]] = {
    "zone": ("zones", Zone),
    "item": ("items", Item),
    "character": ("characters", Character),
    "task": ("tasks", Task),
    "variable": ("variables", Variable),
    "input": ("inputs", Input),
    "media_object": ("media_objects", MediaObject),
}


def _entity_collection(cartridge, entity_type: str):
    field_name, _ = ENTITY_SPECS[entity_type]
    return getattr(cartridge, field_name)


def _entity_cls(entity_type: str):
    _, cls = ENTITY_SPECS[entity_type]
    return cls


def _find_entity(cartridge, entity_type: str, entity_id: str):
    collection = _entity_collection(cartridge, entity_type)
    for obj in collection:
        if obj.id == entity_id:
            return obj
    return None


def add_entity(cartridge, entity_type: str, payload: dict[str, Any]) -> ChangeRecord:
    cls = _entity_cls(entity_type)
    collection = _entity_collection(cartridge, entity_type)
    existing = _find_entity(cartridge, entity_type, payload.get("id", ""))
    if existing is not None:
        raise ValueError(f"{entity_type} with id '{existing.id}' already exists")
    entity = cls(**payload)
    collection.append(entity)
    return ChangeRecord(
        action="add",
        entity_type=entity_type,
        entity_id=entity.id,
        after=asdict(entity),
    )


def update_entity(cartridge, entity_type: str, entity_id: str, patch: dict[str, Any]) -> ChangeRecord:
    entity = _find_entity(cartridge, entity_type, entity_id)
    if entity is None:
        raise ValueError(f"{entity_type} with id '{entity_id}' not found")
    before = asdict(entity)
    for key, value in patch.items():
        if hasattr(entity, key):
            setattr(entity, key, value)
    return ChangeRecord(
        action="update",
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=asdict(entity),
    )


def remove_entity(cartridge, entity_type: str, entity_id: str) -> ChangeRecord:
    collection = _entity_collection(cartridge, entity_type)
    for idx, obj in enumerate(collection):
        if obj.id == entity_id:
            before = asdict(obj)
            del collection[idx]
            return ChangeRecord(
                action="remove",
                entity_type=entity_type,
                entity_id=entity_id,
                before=before,
                after=None,
            )
    raise ValueError(f"{entity_type} with id '{entity_id}' not found")
