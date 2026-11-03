from __future__ import annotations

import builtins
import json
import runpy
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest

from arkhon.cli import cmd_report, main


def test_cli_inspect_text_json_and_invalid_project(tmp_path: Path, capsys, monkeypatch) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "main.py").write_text("value = 1\n", encoding="utf-8")
    (project / "data.unknownext").write_text("?", encoding="utf-8")
    manifest = SimpleNamespace(name="Apxoh", version="1.0.0")
    monkeypatch.setattr("arkhon.config.get_manifest", lambda: manifest)
    assert main(["inspect", str(project)]) == 0
    output = capsys.readouterr().out
    assert "Languages detected:" in output
    assert "Unknown language files:" in output
    assert main(["inspect", str(project), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["system"] == {"name": "Apxoh", "version": "1.0.0"}
    assert data["profile"]["name"]
    assert main(["inspect", str(tmp_path / "missing")]) == 1
    assert "not a directory" in capsys.readouterr().err


def test_cli_validate_and_import_failure(monkeypatch, capsys) -> None:
    assert main(["validate"]) in {0, 1}
    original_import = builtins.__import__
    def fail_validate(name, *args, **kwargs):
        if name == "scripts.validation.validate_all":
            raise ImportError("validation module absent")
        return original_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", fail_validate)
    assert main(["validate"]) == 1
    assert "not available" in capsys.readouterr().err


def test_cli_doctor_reports_manifest_and_optional_integration_errors(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    for relative in ("VERSION", "manifest/index.yaml", "README.md", "AGENTS.md"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("present", encoding="utf-8")
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        "arkhon.config.load_manifest",
        lambda _root: (_ for _ in ()).throw(ValueError("invalid manifest")),
    )
    monkeypatch.setattr(
        "arkhon.integrations.tsar.adapter.TsarAdapter.health_check",
        lambda _self: (_ for _ in ()).throw(RuntimeError("integration failed")),
    )
    assert main(["doctor"]) == 1
    output = capsys.readouterr().out
    assert "manifest load failed" in output
    assert "optional TSAR integration check failed" in output


def test_cli_audit_rule_load_failure_and_verify_domain_errors(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    fake_root = tmp_path / "repo"
    fake_root.mkdir()
    (fake_root / "rules").write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr("arkhon.cli._repo_root", lambda: fake_root)
    assert main(["audit", str(project)]) == 1
    assert "rule load errors" in capsys.readouterr().err
    assert main(["verify", str(project), "--domain", "unknown"]) == 1
    assert "unknown domain" in capsys.readouterr().err
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _root: None)
    assert main(["verify", str(project), "--domain", "testing"]) == 1


def test_cli_report_unknown_format_and_verify_success(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    with pytest.raises(Exception):
        cmd_report(Namespace(project=str(tmp_path), format="unknown", output=None))
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _root: "a" * 40)
    run = SimpleNamespace(
        run_id="RUN-1",
        status="PASS",
        evidence_id="EVID-1",
        results=[SimpleNamespace(runner="pytest", outcome=SimpleNamespace(value="PASS"))],
    )
    monkeypatch.setattr(
        "arkhon.verification.engine.VerificationEngine.run", lambda *a, **k: run
    )
    assert main(["verify", str(project), "--domain", "testing"]) == 0
    output = capsys.readouterr().out
    assert "RUN-1" in output and "EVID-1" in output


def test_cli_module_entrypoint_exits_with_usage_code() -> None:
    cli_path = Path(__file__).resolve().parents[2] / "src" / "arkhon" / "cli.py"
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(cli_path), run_name="__main__")
    assert exc_info.value.code == 1
