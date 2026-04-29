from __future__ import annotations

from dataclasses import dataclass

from wherigo_sdk.model import Cartridge


@dataclass
class Reference:
    source_type: str
    source_id: str
    field: str
    target_type: str
    target_id: str


class ReferenceGraph:
    def __init__(self, cartridge: Cartridge):
        self.cartridge = cartridge

    def incoming_references(self, target_type: str, target_id: str) -> list[Reference]:
        refs: list[Reference] = []
        if target_type == "variable":
            for zinput in self.cartridge.inputs:
                if zinput.variable_id == target_id:
                    refs.append(
                        Reference(
                            source_type="input",
                            source_id=zinput.id,
                            field="variable_id",
                            target_type=target_type,
                            target_id=target_id,
                        )
                    )
        return refs

    def rename_name_references(self, old_name: str, new_name: str) -> int:
        updated = 0
        for event in self.cartridge.events:
            if event.object_name == old_name:
                event.object_name = new_name
                updated += 1
        return updated
