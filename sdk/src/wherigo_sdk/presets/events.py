from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from wherigo_sdk.model import Action, Condition, Event, ScriptGroup


@dataclass
class PresetApplyResult:
    event: Event
    template_id: str
    template_version: str
    params: dict[str, Any]


_TEMPLATE_VERSION = "1"

_PRESETS: dict[str, dict[str, Any]] = {
    "zone_enter": {
        "label": "进入区域时触发",
        "description": "玩家进入目标区域时弹出提示并执行动作。",
        "target_types": ["zone"],
        "trigger": "OnEnter",
        "params": [
            {"key": "zone_name", "label": "区域名称", "type": "string", "required": True},
            {"key": "message", "label": "提示文本", "type": "string", "required": True},
        ],
    },
    "zone_exit": {
        "label": "离开区域时触发",
        "description": "玩家离开区域时弹出提示。",
        "target_types": ["zone"],
        "trigger": "OnExit",
        "params": [
            {"key": "zone_name", "label": "区域名称", "type": "string", "required": True},
            {"key": "message", "label": "提示文本", "type": "string", "required": True},
        ],
    },
    "item_use": {
        "label": "物品可用",
        "description": "当物品被使用时执行逻辑。",
        "target_types": ["item"],
        "params": [
            {"key": "item_name", "label": "物品名称", "type": "string", "required": True},
            {"key": "message", "label": "提示文本", "type": "string", "required": True},
        ],
    },
    "task_complete": {
        "label": "任务完成",
        "description": "当任务完成时给出反馈。",
        "target_types": ["task"],
        "params": [
            {"key": "task_name", "label": "任务名称", "type": "string", "required": True},
            {"key": "message", "label": "完成提示", "type": "string", "required": True},
        ],
    },
    "score_increment": {
        "label": "计分增加",
        "description": "给指定变量增加分数并提示。",
        "target_types": ["variable"],
        "params": [
            {"key": "variable_name", "label": "变量名称", "type": "string", "required": True},
            {"key": "delta", "label": "增加值", "type": "number", "required": True},
            {"key": "message", "label": "提示文本", "type": "string", "required": False},
        ],
    },
    "dialog_hint": {
        "label": "提示对话",
        "description": "显示一个提示对话框。",
        "target_types": ["zone", "item", "task", "character"],
        "params": [
            {"key": "target_name", "label": "目标对象名", "type": "string", "required": True},
            {"key": "title", "label": "标题", "type": "string", "required": True},
            {"key": "message", "label": "内容", "type": "string", "required": True},
        ],
    },
    "conditional_gate": {
        "label": "条件分支",
        "description": "按变量条件走不同提示分支。",
        "target_types": ["zone", "item", "task"],
        "params": [
            {"key": "target_name", "label": "目标对象名", "type": "string", "required": True},
            {"key": "condition_expr", "label": "条件表达式", "type": "string", "required": True},
            {"key": "on_true", "label": "成立提示", "type": "string", "required": True},
            {"key": "on_false", "label": "不成立提示", "type": "string", "required": True},
        ],
    },
    "one_shot_unlock": {
        "label": "一次性触发",
        "description": "执行一次后标记变量避免重复触发。",
        "target_types": ["zone", "item", "task"],
        "params": [
            {"key": "target_name", "label": "目标对象名", "type": "string", "required": True},
            {"key": "flag_variable", "label": "标记变量", "type": "string", "required": True},
            {"key": "message", "label": "提示文本", "type": "string", "required": True},
        ],
    },
}


def list_event_presets() -> list[dict[str, Any]]:
    result = []
    for preset_id, preset in _PRESETS.items():
        result.append(
            {
                "id": preset_id,
                "version": _TEMPLATE_VERSION,
                "label": preset["label"],
                "description": preset["description"],
                "target_types": preset["target_types"],
                "trigger": preset.get("trigger"),
                "params": preset["params"],
            }
        )
    return result


def apply_event_preset(preset_id: str, params: dict[str, Any]) -> PresetApplyResult:
    if preset_id not in _PRESETS:
        raise ValueError(f"unknown preset '{preset_id}'")
    normalized = _normalize_params(_PRESETS[preset_id]["params"], params)
    event = _build_event(preset_id, normalized)
    event.extras = dict(event.extras or {})
    event.extras["template"] = {
        "id": preset_id,
        "version": _TEMPLATE_VERSION,
        "params": normalized,
    }
    return PresetApplyResult(
        event=event,
        template_id=preset_id,
        template_version=_TEMPLATE_VERSION,
        params=normalized,
    )


def _normalize_params(specs: list[dict[str, Any]], raw: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for spec in specs:
        key = str(spec["key"])
        required = bool(spec.get("required", False))
        value = raw.get(key)
        if required and (value is None or str(value).strip() == ""):
            raise ValueError(f"missing required param '{key}'")
        if spec.get("type") == "number":
            if value in (None, ""):
                params[key] = 0
            else:
                params[key] = float(value)
        else:
            params[key] = str(value or "")
    return params


def _build_event(preset_id: str, params: dict[str, Any]) -> Event:
    builder = {
        "zone_enter": _zone_enter,
        "zone_exit": _zone_exit,
        "item_use": _item_use,
        "task_complete": _task_complete,
        "score_increment": _score_increment,
        "dialog_hint": _dialog_hint,
        "conditional_gate": _conditional_gate,
        "one_shot_unlock": _one_shot_unlock,
    }[preset_id]
    return builder(params)


def _zone_enter(params: dict[str, Any]) -> Event:
    event = Event(
        name=f"进入区域: {params['zone_name']}",
        object_name=params["zone_name"],
        groups=[
            ScriptGroup(
                description="进入区域触发",
                lines=[Action(code=f'Wherigo.MessageBox("{params["message"]}")')],
            )
        ],
    )
    event.extras["wf_trigger"] = {"scope": "zone", "name": "OnEnter"}
    event.extras["trigger"] = {"kind": "zone_on_enter", "zone_name": params["zone_name"]}
    return event


def _zone_exit(params: dict[str, Any]) -> Event:
    event = Event(
        name=f"离开区域: {params['zone_name']}",
        object_name=params["zone_name"],
        groups=[
            ScriptGroup(
                description="离开区域触发",
                lines=[Action(code=f'Wherigo.MessageBox("{params["message"]}")')],
            )
        ],
    )
    event.extras["wf_trigger"] = {"scope": "zone", "name": "OnExit"}
    event.extras["trigger"] = {"kind": "zone_on_exit", "zone_name": params["zone_name"]}
    return event


def _item_use(params: dict[str, Any]) -> Event:
    event = Event(
        name=f"物品使用: {params['item_name']}",
        object_name=params["item_name"],
        groups=[
            ScriptGroup(
                description="物品使用逻辑",
                lines=[Action(code=f'Wherigo.MessageBox("{params["message"]}")')],
            )
        ],
    )
    event.extras["trigger"] = {"kind": "item_on_use", "item_name": params["item_name"]}
    return event


def _task_complete(params: dict[str, Any]) -> Event:
    event = Event(
        name=f"任务完成: {params['task_name']}",
        object_name=params["task_name"],
        groups=[
            ScriptGroup(
                description="任务完成反馈",
                lines=[Action(code=f'Wherigo.MessageBox("{params["message"]}")')],
            )
        ],
    )
    event.extras["trigger"] = {"kind": "task_on_complete", "task_name": params["task_name"]}
    return event


def _score_increment(params: dict[str, Any]) -> Event:
    message = params.get("message") or "分数已更新"
    event = Event(
        name=f"计分增加: {params['variable_name']}",
        object_name=params["variable_name"],
        groups=[
            ScriptGroup(
                description="计分变量更新",
                lines=[
                    Action(code=f'{params["variable_name"]} = {params["variable_name"]} + {int(params["delta"])}'),
                    Action(code=f'Wherigo.MessageBox("{message}")'),
                ],
            )
        ],
    )
    event.extras["trigger"] = {"kind": "variable_update", "variable_name": params["variable_name"]}
    return event


def _dialog_hint(params: dict[str, Any]) -> Event:
    event = Event(
        name=f"提示对话: {params['title']}",
        object_name=params["target_name"],
        groups=[
            ScriptGroup(
                description="提示对话",
                lines=[Action(code=f'Wherigo.MessageBox("{params["title"]}: {params["message"]}")')],
            )
        ],
    )
    event.extras["trigger"] = {"kind": "dialog_hint", "target_name": params["target_name"]}
    return event


def _conditional_gate(params: dict[str, Any]) -> Event:
    event = Event(
        name=f"条件分支: {params['target_name']}",
        object_name=params["target_name"],
        groups=[
            ScriptGroup(
                description="条件分支",
                lines=[
                    Condition(expr=params["condition_expr"], join="and"),
                    Action(code=f'Wherigo.MessageBox("{params["on_true"]}")'),
                    Action(code="else"),
                    Action(code=f'Wherigo.MessageBox("{params["on_false"]}")'),
                    Action(code="end"),
                ],
            )
        ],
    )
    event.extras["trigger"] = {"kind": "conditional_gate", "target_name": params["target_name"]}
    return event


def _one_shot_unlock(params: dict[str, Any]) -> Event:
    event = Event(
        name=f"一次性触发: {params['target_name']}",
        object_name=params["target_name"],
        groups=[
            ScriptGroup(
                description="一次性触发",
                lines=[
                    Condition(expr=f"not {params['flag_variable']}", join="and"),
                    Action(code=f'{params["flag_variable"]} = true'),
                    Action(code=f'Wherigo.MessageBox("{params["message"]}")'),
                ],
            )
        ],
    )
    event.extras["trigger"] = {"kind": "one_shot_unlock", "target_name": params["target_name"]}
    return event
