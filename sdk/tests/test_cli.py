from __future__ import annotations

import subprocess

from wherigo_sdk.cli import main
from wherigo_sdk.io import save_project
from wherigo_sdk.model import Cartridge, Input, Variable


def test_validate_cli_reports_valid_project(tmp_path, capsys) -> None:
    project = tmp_path / "valid.wigi.json"
    save_project(
        Cartridge(
            id="cart-1",
            name="ValidCart",
            variables=[Variable(id="var-1", name="Score")],
            inputs=[Input(id="input-1", name="ScoreInput", variable_id="var-1")],
        ),
        project,
    )

    assert main(["validate", str(project)]) == 0
    assert "Project is valid" in capsys.readouterr().out


def test_validate_cli_reports_invalid_project(tmp_path, capsys) -> None:
    project = tmp_path / "invalid.wigi.json"
    save_project(
        Cartridge(
            id="cart-1",
            name="InvalidCart",
            inputs=[Input(id="input-1", name="BrokenInput", variable_id="missing")],
        ),
        project,
    )

    assert main(["validate", str(project)]) == 1
    output = capsys.readouterr().out
    assert "Project is invalid" in output
    assert "missing variable" in output


def test_cli_module_entrypoint_runs_validate(tmp_path) -> None:
    project = tmp_path / "valid.wigi.json"
    save_project(Cartridge(id="cart-1", name="ValidCart"), project)

    proc = subprocess.run(
        ["python3", "-m", "wherigo_sdk.cli", "validate", str(project)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "Project is valid" in proc.stdout
