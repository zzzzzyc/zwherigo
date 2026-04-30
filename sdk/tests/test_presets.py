from __future__ import annotations

from wherigo_sdk.io import cartridge_from_dict
from wherigo_sdk.presets import apply_event_preset, list_event_presets


def test_list_event_presets_has_expected_entries() -> None:
    presets = list_event_presets()
    ids = {entry["id"] for entry in presets}
    assert "zone_enter" in ids
    assert "item_use" in ids
    assert len(ids) >= 8


def test_apply_event_preset_adds_template_metadata() -> None:
    result = apply_event_preset(
        "zone_enter",
        {
            "zone_name": "StartZone",
            "message": "欢迎进入",
        },
    )
    assert result.event.name.startswith("进入区域")
    assert result.event.extras["template"]["id"] == "zone_enter"
    assert result.event.extras["template"]["params"]["zone_name"] == "StartZone"
    assert result.event.groups


def test_template_metadata_roundtrip_from_dict() -> None:
    raw = {
        "id": "demo",
        "name": "Demo",
        "events": [
            {
                "name": "E1",
                "object_name": "Start",
                "event_type": "wig",
                "extras": {
                    "editor_mode": "template",
                    "template": {"id": "zone_enter", "version": "1", "params": {"zone_name": "Start", "message": "Hi"}},
                },
            }
        ],
    }
    cartridge = cartridge_from_dict(raw)
    assert cartridge.events[0].extras["template"]["id"] == "zone_enter"
