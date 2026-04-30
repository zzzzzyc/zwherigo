from __future__ import annotations

import os
from pathlib import Path

import pytest

from wherigo_sdk.errors import CompileError
from wherigo_sdk.io import save_project
from wherigo_sdk.model import Cartridge, Input, Variable
from wherigo_sdk.packaging.compiler import (
    ENV_BRIDGE_PATH,
    ENV_COMPILER,
    CompileRequest,
    LegacyBridgeCompiler,
    resolve_compiler,
)
from wherigo_sdk.packaging.pipeline import build_artifacts


def _write_fake_bridge(tmp_path: Path) -> Path:
    script_path = tmp_path / "fake_bridge.py"
    script_path.write_text(
        (
            "import json,sys,pathlib\n"
            "idx = sys.argv.index('--request-json')\n"
            "payload = json.loads(sys.argv[idx+1])\n"
            "out = pathlib.Path(payload['output_gwc'])\n"
            "out.parent.mkdir(parents=True, exist_ok=True)\n"
            "if payload.get('cartridge_id') == 'fail':\n"
            "  print(json.dumps({'ok': False, 'error': 'forced failure'}))\n"
            "  sys.exit(1)\n"
            "out.write_bytes(b'GWC')\n"
            "print(json.dumps({'ok': True, 'output_gwc': str(out)}))\n"
        ),
        encoding="utf-8",
    )
    cmd_path = tmp_path / "fake_bridge"
    cmd_path.write_text(f'#!/bin/sh\npython3 "{script_path}" "$@"\n', encoding="utf-8")
    cmd_path.chmod(0o755)
    return cmd_path


def _demo_cartridge_project(tmp_path: Path, cartridge_id: str) -> Path:
    cartridge = Cartridge(
        id=cartridge_id,
        name="BridgeDemo",
        file_name=str(tmp_path / "bridge-demo.wigi.json"),
        variables=[Variable(id="var-1", name="Score", var_type="number", value=0)],
        inputs=[Input(id="in-1", name="InputName", variable_id="var-1")],
    )
    project = tmp_path / "bridge-demo.wigi.json"
    save_project(cartridge, project)
    return project


def test_legacy_bridge_compiler_success(tmp_path: Path) -> None:
    bridge = _write_fake_bridge(tmp_path)
    lua_file = tmp_path / "cart.lua"
    lua_file.write_text("return cartDemo", encoding="utf-8")
    req = CompileRequest(lua_file=lua_file, output_gwc=tmp_path / "out.gwc", cartridge_id="ok")
    compiler = LegacyBridgeCompiler(bridge_path=bridge)
    output = compiler.compile(req)
    assert output.exists()
    assert output.read_bytes() == b"GWC"


def test_legacy_bridge_compiler_failure_maps_error(tmp_path: Path) -> None:
    bridge = _write_fake_bridge(tmp_path)
    lua_file = tmp_path / "cart.lua"
    lua_file.write_text("return cartDemo", encoding="utf-8")
    req = CompileRequest(lua_file=lua_file, output_gwc=tmp_path / "out.gwc", cartridge_id="fail")
    compiler = LegacyBridgeCompiler(bridge_path=bridge)
    with pytest.raises(CompileError):
        compiler.compile(req)


def test_resolve_compiler_from_env(tmp_path: Path) -> None:
    bridge = _write_fake_bridge(tmp_path)
    os.environ[ENV_COMPILER] = "legacy-bridge"
    os.environ[ENV_BRIDGE_PATH] = str(bridge)
    try:
        compiler = resolve_compiler()
        assert isinstance(compiler, LegacyBridgeCompiler)
    finally:
        os.environ.pop(ENV_COMPILER, None)
        os.environ.pop(ENV_BRIDGE_PATH, None)


def test_build_artifacts_with_bridge_compiler_creates_gwc(tmp_path: Path) -> None:
    bridge = _write_fake_bridge(tmp_path)
    project_path = _demo_cartridge_project(tmp_path, cartridge_id="cart-bridge")
    result = build_artifacts(
        project_file=project_path,
        output_dir=tmp_path / "dist",
        compiler_kind="legacy-bridge",
        bridge_path=bridge,
    )
    assert result.lua_file.exists()
    assert result.gwz_file.exists()
    assert result.gwc_file is not None
    assert result.gwc_file.exists()
