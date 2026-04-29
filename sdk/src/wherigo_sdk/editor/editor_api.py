from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from typing import Any

from wherigo_sdk.editor.changes import ChangeRecord, OperationResult
from wherigo_sdk.editor.operations import add_entity, remove_entity, update_entity
from wherigo_sdk.editor.references import ReferenceGraph
from wherigo_sdk.model import Cartridge, collect_validation_errors


class EditorSession:
    def __init__(self, cartridge: Cartridge, strict_mode: bool = False):
        self.cartridge = cartridge
        self.strict_mode = strict_mode
        self._tx_snapshot: Cartridge | None = None
        self._change_log: list[ChangeRecord] = []

    def begin(self) -> None:
        if self._tx_snapshot is None:
            self._tx_snapshot = deepcopy(self.cartridge)

    def rollback(self) -> None:
        if self._tx_snapshot is not None:
            self.cartridge = self._tx_snapshot
            self._tx_snapshot = None
            self._change_log = []

    def commit(self) -> list[ChangeRecord]:
        changes = list(self._change_log)
        self._tx_snapshot = None
        self._change_log = []
        return changes

    def apply_command(self, command: dict[str, Any]) -> OperationResult:
        op = str(command.get("op", "")).strip().lower()
        entity_type = str(command.get("entity_type", "")).strip().lower()
        entity_id = str(command.get("entity_id", "")).strip()
        payload = dict(command.get("payload", {}))
        mode = str(command.get("mode", "restrict")).strip().lower()

        if op not in {"add", "update", "remove"}:
            return OperationResult(ok=False, errors=[f"unsupported op '{op}'"])

        if self._tx_snapshot is None:
            self.begin()
            auto_tx = True
        else:
            auto_tx = False

        try:
            changes: list[ChangeRecord] = []
            if op == "add":
                changes.append(add_entity(self.cartridge, entity_type, payload))
            elif op == "update":
                if "name" in payload:
                    old = self._entity_name(entity_type, entity_id)
                    if old and old != payload["name"]:
                        ref_updates = ReferenceGraph(self.cartridge).rename_name_references(
                            old_name=old, new_name=str(payload["name"])
                        )
                        if ref_updates:
                            changes.append(
                                ChangeRecord(
                                    action="rename_refs",
                                    entity_type=entity_type,
                                    entity_id=entity_id,
                                    details={"updated_event_object_names": ref_updates},
                                )
                            )
                changes.append(update_entity(self.cartridge, entity_type, entity_id, payload))
            else:
                errors = self._check_remove_constraints(entity_type, entity_id, mode)
                if errors:
                    raise ValueError("; ".join(errors))
                changes.extend(self._apply_cascade_if_needed(entity_type, entity_id, mode))
                changes.append(remove_entity(self.cartridge, entity_type, entity_id))

            errors = collect_validation_errors(self.cartridge)
            if self.strict_mode and errors:
                raise ValueError("; ".join(errors))

            self._change_log.extend(changes)
            if auto_tx:
                committed = self.commit()
            else:
                committed = changes
            return OperationResult(ok=True, errors=errors, changes=committed)
        except Exception as exc:
            self.rollback()
            return OperationResult(ok=False, errors=[f"{type(exc).__name__}: {exc}"])

    def _entity_name(self, entity_type: str, entity_id: str) -> str | None:
        field_name = {
            "zone": "zones",
            "item": "items",
            "character": "characters",
            "task": "tasks",
            "variable": "variables",
            "input": "inputs",
            "media_object": "media_objects",
        }.get(entity_type)
        if not field_name:
            return None
        for obj in getattr(self.cartridge, field_name):
            if obj.id == entity_id:
                return obj.name
        return None

    def _check_remove_constraints(self, entity_type: str, entity_id: str, mode: str) -> list[str]:
        if mode == "cascade":
            return []
        graph = ReferenceGraph(self.cartridge)
        refs = graph.incoming_references(entity_type, entity_id)
        if not refs:
            return []
        return [
            f"cannot remove {entity_type}:{entity_id}; referenced by "
            + ", ".join(f"{r.source_type}:{r.source_id}.{r.field}" for r in refs)
        ]

    def _apply_cascade_if_needed(
        self, entity_type: str, entity_id: str, mode: str
    ) -> list[ChangeRecord]:
        if mode != "cascade":
            return []
        changes: list[ChangeRecord] = []
        if entity_type == "variable":
            input_ids = [zinput.id for zinput in self.cartridge.inputs if zinput.variable_id == entity_id]
            for input_id in input_ids:
                changes.append(remove_entity(self.cartridge, "input", input_id))
        return changes

    def export_changes(self) -> list[dict[str, Any]]:
        return [asdict(change) for change in self._change_log]
