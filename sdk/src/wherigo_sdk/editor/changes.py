from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import asdict
from typing import Any


@dataclass
class ChangeRecord:
    action: str
    entity_type: str
    entity_id: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    changes: list[ChangeRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
