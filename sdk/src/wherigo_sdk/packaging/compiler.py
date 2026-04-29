from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from wherigo_sdk.errors import CompileError

ENV_COMPILER = "WHERIGO_GWC_COMPILER"
ENV_BRIDGE_PATH = "WHERIGO_GWC_BRIDGE_PATH"


@dataclass
class CompileRequest:
    lua_file: Path
    output_gwc: Path
    cartridge_id: str
    player_name: str = "Builder"
    user_name: str = "builder"
    device_type: str = "PPC2003"
    engine_version: str = "V0210"


class GwcCompiler(Protocol):
    def compile(self, request: CompileRequest) -> Path:
        ...


class UnsupportedCompiler:
    """Default adapter that makes the missing compile backend explicit."""

    def compile(self, request: CompileRequest) -> Path:
        raise CompileError(
            "No GWC compiler backend is configured. "
            "Provide a custom adapter that bridges legacy ZonesLinker or a native compiler."
        )


@dataclass
class LegacyBridgeCompiler:
    bridge_path: Path
    zoneslinker_dll: Path | None = None
    timeout_seconds: int = 120

    def compile(self, request: CompileRequest) -> Path:
        bridge = Path(self.bridge_path)
        if not bridge.exists():
            raise CompileError(f"Bridge executable not found: {bridge}")

        payload: dict[str, Any] = {
            "lua_path": str(request.lua_file.resolve()),
            "output_gwc": str(request.output_gwc.resolve()),
            "cartridge_id": request.cartridge_id,
            "player_name": request.player_name,
            "user_name": request.user_name,
            "device_type": request.device_type,
            "engine_version": request.engine_version,
        }
        if self.zoneslinker_dll is not None:
            payload["zoneslinker_dll"] = str(self.zoneslinker_dll.resolve())

        try:
            proc = subprocess.run(
                [str(bridge), "--request-json", json.dumps(payload, ensure_ascii=False)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout_seconds,
                check=False,
            )
        except OSError as exc:
            raise CompileError(f"Failed to execute bridge '{bridge}': {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise CompileError(f"Bridge execution timed out after {self.timeout_seconds}s") from exc

        if proc.returncode != 0:
            details = proc.stderr.strip() or proc.stdout.strip() or "(no output)"
            raise CompileError(f"Legacy bridge failed with exit code {proc.returncode}: {details}")

        try:
            response = json.loads(proc.stdout.strip() or "{}")
        except json.JSONDecodeError as exc:
            raise CompileError(f"Bridge returned non-JSON output: {proc.stdout}") from exc

        if not response.get("ok", False):
            raise CompileError(response.get("error", "Legacy bridge reported failure."))

        output_path = Path(str(response.get("output_gwc", request.output_gwc)))
        if not output_path.exists():
            raise CompileError(f"Bridge reported success but output file is missing: {output_path}")
        return output_path


def compiler_from_env() -> GwcCompiler | None:
    compiler_kind = os.getenv(ENV_COMPILER, "").strip().lower()
    if not compiler_kind:
        return None

    if compiler_kind == "legacy-bridge":
        bridge_path = os.getenv(ENV_BRIDGE_PATH, "").strip()
        if not bridge_path:
            raise CompileError(
                f"{ENV_BRIDGE_PATH} is required when {ENV_COMPILER}=legacy-bridge"
            )
        return LegacyBridgeCompiler(bridge_path=Path(bridge_path))

    raise CompileError(f"Unsupported compiler kind in {ENV_COMPILER}: {compiler_kind}")


def resolve_compiler(
    compiler_kind: str | None = None,
    bridge_path: str | Path | None = None,
    zoneslinker_dll: str | Path | None = None,
) -> GwcCompiler | None:
    kind = (compiler_kind or "").strip().lower()
    if not kind:
        return compiler_from_env()
    if kind == "none":
        return None
    if kind == "legacy-bridge":
        if bridge_path is None:
            bridge_env = os.getenv(ENV_BRIDGE_PATH, "").strip()
            if not bridge_env:
                raise CompileError(
                    f"bridge_path is required for compiler '{kind}' "
                    f"or set {ENV_BRIDGE_PATH}"
                )
            bridge_path = bridge_env
        return LegacyBridgeCompiler(
            bridge_path=Path(bridge_path),
            zoneslinker_dll=Path(zoneslinker_dll) if zoneslinker_dll else None,
        )
    raise CompileError(f"Unsupported compiler kind: {kind}")
