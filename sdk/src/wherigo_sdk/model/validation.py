from __future__ import annotations

from dataclasses import dataclass

from wherigo_sdk.errors import ValidationError
from wherigo_sdk.model.entities import Cartridge


@dataclass(frozen=True)
class ValidationReport:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if self.ok and not self.warnings:
            return "Beta validation passed"
        if self.ok:
            return f"Beta validation passed with {len(self.warnings)} warning(s)"
        return f"Beta validation failed with {len(self.errors)} error(s)"

    def to_dict(self) -> dict[str, object]:
        return {
            "valid": self.ok,
            "summary": self.summary(),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def collect_validation_errors(cartridge: Cartridge) -> list[str]:
    return validate_project(cartridge).errors


def collect_validation_warnings(cartridge: Cartridge) -> list[str]:
    return validate_project(cartridge).warnings


def validate_project(cartridge: Cartridge) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    if not cartridge.id:
        errors.append("cartridge.id is required")
    if not cartridge.name:
        errors.append("cartridge.name is required")
    if cartridge.file_name and any(part == ".." for part in cartridge.file_name.replace("\\", "/").split("/")):
        warnings.append("cartridge.file_name contains parent-directory segments")
    if cartridge.author_scripts and "-- #End Author Functions# --" in cartridge.author_scripts:
        warnings.append("author_scripts contains reserved SDK marker text")
    if any(ch in cartridge.name for ch in ("/", "\\", ":")):
        warnings.append("cartridge.name contains characters that will be normalized in filenames")

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

    for event in cartridge.events:
        if event.event_type not in {"wig", "callback"}:
            errors.append(f"event '{event.name}' has unsupported event_type '{event.event_type}'")
        if event.event_type == "callback" and event.callback_key <= 0:
            errors.append(f"callback event '{event.name}' must have a positive callback_key")
        if not event.name:
            errors.append("events contains object with empty name")
        if event.lua_script and "-- Nothing after this line --" in event.lua_script:
            warnings.append(f"event '{event.name}' lua_script contains reserved SDK marker text")

    return ValidationReport(errors=errors, warnings=warnings)


def validation_report(cartridge: Cartridge) -> dict[str, object]:
    report = validate_project(cartridge)
    counts = {
        "zones": len(cartridge.zones),
        "items": len(cartridge.items),
        "characters": len(cartridge.characters),
        "tasks": len(cartridge.tasks),
        "variables": len(cartridge.variables),
        "inputs": len(cartridge.inputs),
        "media_objects": len(cartridge.media_objects),
        "events": len(cartridge.events),
    }
    payload = report.to_dict()
    payload["counts"] = counts
    return payload


def validate_or_raise(cartridge: Cartridge) -> None:
    errors = collect_validation_errors(cartridge)
    if errors:
        raise ValidationError(errors)
