# Editor API (Phase 1)

The editor API offers command-style semantic operations for web or desktop editors.

## Core types

- `EditorSession`: mutable editing session around a `Cartridge`.
- `OperationResult`: operation result contract with `ok/errors/warnings/changes`.
- `ChangeRecord`: normalized change log item for audit and future undo/redo.

## Commands

Each command is a dictionary:

```python
{
  "op": "add|update|remove",
  "entity_type": "zone|item|character|task|variable|input|media_object",
  "entity_id": "required for update/remove",
  "payload": {...},
  "mode": "restrict|cascade"   # optional, remove only
}
```

## Safety behavior

- Remove defaults to `restrict`: referenced entities are not deleted.
- For variable deletion, `cascade` removes dependent inputs.
- Rename updates event `object_name` references when exact matches are found.

## Transactions

- `begin()` starts in-memory transaction.
- `rollback()` restores snapshot.
- `commit()` finalizes and returns collected changes.
- In `strict_mode=True`, validation errors roll back automatically.
