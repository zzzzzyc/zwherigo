from __future__ import annotations

from wherigo_sdk.errors import ValidationError
from wherigo_sdk.model.entities import Cartridge


def collect_validation_errors(cartridge: Cartridge) -> list[str]:
    errors: list[str] = []
    if not cartridge.id:
        errors.append("cartridge.id is required")
    if not cartridge.name:
        errors.append("cartridge.name is required")

    known_variable_ids = {var.id for var in cartridge.variables}
    for zinput in cartridge.inputs:
        if zinput.variable_id not in known_variable_ids:
            errors.append(
                f"input '{zinput.name}' references missing variable '{zinput.variable_id}'"
            )

    seen_ids: set[str] = set()
    for collection_name, objects in (
        ("zones", cartridge.zones),
        ("items", cartridge.items),
        ("characters", cartridge.characters),
        ("tasks", cartridge.tasks),
        ("variables", cartridge.variables),
        ("inputs", cartridge.inputs),
        ("media_objects", cartridge.media_objects),
    ):
        for obj in objects:
            obj_id = getattr(obj, "id", "")
            if not obj_id:
                errors.append(f"{collection_name} contains object with empty id")
            elif obj_id in seen_ids:
                errors.append(f"duplicate id '{obj_id}' across cartridge entities")
            else:
                seen_ids.add(obj_id)

    return errors


def validate_or_raise(cartridge: Cartridge) -> None:
    errors = collect_validation_errors(cartridge)
    if errors:
        raise ValidationError(errors)
