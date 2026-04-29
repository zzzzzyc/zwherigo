from __future__ import annotations

from pathlib import Path

from wherigo_sdk.model import Action, Cartridge, Condition


def _lua_name(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in text.strip())
    return cleaned or "unnamed"


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
                "-------------------------------------------------------------------------------",
                "------Builder Generated functions, Do not Edit, this will be overwritten------",
                "-------------------------------------------------------------------------------",
            ]
        )

        for event in [e for e in c.events if e.event_type == "wig"]:
            fn_name = f"{event.object_name}_{event.name}" if event.object_name else event.name
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
