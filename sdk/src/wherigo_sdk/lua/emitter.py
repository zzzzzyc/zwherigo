from __future__ import annotations

from pathlib import Path

from wherigo_sdk.model import Action, Cartridge, Condition


def _lua_name(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text.strip())
    if not cleaned:
        return "unnamed"
    if cleaned[0].isdigit():
        return f"_{cleaned}"
    return cleaned


def _lua_item_key(text: str) -> str:
    return _lua_name(text).lower()


class LuaEmitter:
    """Thin emitter that follows legacy section ordering."""

    def __init__(self, cartridge: Cartridge):
        self.cartridge = cartridge

    def render(self) -> str:
        c = self.cartridge
        cart_name = f"cart{_lua_name(c.name)}"
        out: list[str] = []
        out.extend(
            [
                "--",
                "-- Builder Generated Lua (thin mode)",
                "--",
                "",
                "-- Item capability defaults derived from editor model.",
                "-- These helpers are consumed by template-generated events.",
                "-------------------------------------------------------------------------------",
                "------Builder Generated functions, Do not Edit, this will be overwritten------",
                "-------------------------------------------------------------------------------",
            ]
        )
        out.extend(self._render_item_capability_helpers())
        out.append("")

        for event in [e for e in c.events if e.event_type == "wig"]:
            object_name = _lua_name(event.object_name)
            event_name = _lua_name(event.name)
            fn_name = f"{object_name}_{event_name}" if event.object_name else event_name
            out.append(f"function {fn_name}()")
            out.extend(self._render_event_body(event))
            out.append("end")
            out.append("")

        out.extend(
            [
                "------End Builder Generated functions, Do not Edit, this will be overwritten------",
                "-------------------------------------------------------------------------------",
                "------Builder Generated callbacks, Do not Edit, this will be overwritten------",
                "-------------------------------------------------------------------------------",
            ]
        )
        last_callback = max((e.callback_key for e in c.events if e.event_type == "callback"), default=0)
        out.append(f"--#LASTCALLBACKKEY={last_callback}#--")

        for event in [e for e in c.events if e.event_type == "callback"]:
            out.append(f"{cart_name}.MsgBoxCBFuncs.MsgBoxCB{event.callback_key} = function(action)")
            out.extend(self._render_event_body(event))
            out.append("end")
            out.append("")

        out.extend(
            [
                "------End Builder Generated callbacks, Do not Edit, this will be overwritten------",
                "-- #Author Functions Go Here# --",
            ]
        )
        if c.author_scripts:
            out.append(c.author_scripts)
        out.extend(["-- #End Author Functions# --", "-- Nothing after this line --", f"return {cart_name}", ""])
        return "\n".join(out)

    def write_to_file(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(), encoding="utf-8")
        return path

    def _render_event_body(self, event) -> list[str]:
        if event.lua_script:
            return [event.lua_script]

        body: list[str] = []
        for group in event.groups:
            body.append(f"-- #GroupDescription={group.description} --")
            body.append(f"-- #Comment={group.comment} --")
            open_if = False
            cond_buffer: list[str] = []
            for line in group.lines:
                if isinstance(line, Condition):
                    cond_buffer.append(line.expr)
                    if line.join == "else":
                        body.append(f"elseif {line.expr} then")
                    elif line.join in ("and", "or"):
                        continue
                    else:
                        body.append(f"if {' and '.join(cond_buffer)} then")
                        cond_buffer.clear()
                        open_if = True
                elif isinstance(line, Action):
                    if cond_buffer:
                        body.append(f"if {' and '.join(cond_buffer)} then")
                        cond_buffer.clear()
                        open_if = True
                    body.append(line.code)
                elif isinstance(line, str):
                    if cond_buffer:
                        body.append(f"if {' and '.join(cond_buffer)} then")
                        cond_buffer.clear()
                        open_if = True
                    body.append(line)
            if cond_buffer:
                body.append(f"if {' and '.join(cond_buffer)} then")
                open_if = True
            if open_if:
                body.append("end")
        return body

    def _render_item_capability_helpers(self) -> list[str]:
        if not self.cartridge.items:
            return []
        lines: list[str] = ["local __wigi_item_caps = {"]
        for item in self.cartridge.items:
            safe_key = _lua_item_key(item.name or item.id)
            lines.append(
                "  "
                + f'{safe_key} = {{ visible={self._lua_bool(item.visible)}, active={self._lua_bool(item.active)}, enabled={self._lua_bool(item.enabled)}, '
                + f'take={self._lua_bool(item.allow_take)}, drop={self._lua_bool(item.allow_drop)}, use={self._lua_bool(item.allow_use)}, give={self._lua_bool(item.allow_give)} }},'
            )
        lines.extend(
            [
                "}",
                "local function __wigi_key(name)",
                "  return string.gsub(string.lower(tostring(name or \"\")), \"[^%w]\", \"_\")",
                "end",
                "local function __wigi_can_use(item_name, action_name)",
                "  local caps = __wigi_item_caps[__wigi_key(item_name)]",
                "  if not caps then return true end",
                "  if not caps.visible or not caps.active or not caps.enabled then return false end",
                "  if action_name == \"take\" then return caps.take end",
                "  if action_name == \"drop\" then return caps.drop end",
                "  if action_name == \"use\" then return caps.use end",
                "  if action_name == \"give\" then return caps.give end",
                "  return true",
                "end",
            ]
        )
        return lines

    @staticmethod
    def _lua_bool(value: bool) -> str:
        return "true" if value else "false"
