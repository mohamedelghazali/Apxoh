from __future__ import annotations

import builtins
import json
import runpy
import sys
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


def test_cli_report_unknown_format_and_verify_success(tmp_path: Path, monkeypatch, capsys) -> None:
    assert cmd_report(Namespace(project=str(tmp_path), format="unknown", output=None)) == 1
    assert "unknown format" in capsys.readouterr().err
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _root: "a" * 40)
    run = SimpleNamespace(
        run_id="RUN-1",
        domain="testing",
        commit_sha="a" * 40,
        status="PASS",
        evidence_id="EVID-1",
        results=[SimpleNamespace(runner="pytest", outcome=SimpleNamespace(value="PASS"))],
    )
    monkeypatch.setattr("arkhon.verification.engine.VerificationEngine.run", lambda *a, **k: run)
    assert main(["verify", str(project), "--domain", "testing"]) == 0
    output = capsys.readouterr().out
    assert "RUN-1" in output and "EVID-1" in output


def test_cli_module_entrypoint_exits_with_usage_code(monkeypatch) -> None:
    cli_path = Path(__file__).resolve().parents[2] / "src" / "arkhon" / "cli.py"
    monkeypatch.setattr(sys, "argv", [str(cli_path)])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(cli_path), run_name="__main__")
    assert exc_info.value.code == 1


def test_verify_all_runs_security_domain_and_fails_closed(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _root: "a" * 40)
    seen: list[str] = []

    def fake_run(_self, *, domain, commit_sha, runners, project_root):
        seen.append(domain)
        status = "BLOCKED" if domain == "software-security" else "PASS"
        return SimpleNamespace(
            run_id=f"RUN-{domain}",
            domain=domain,
            commit_sha=commit_sha,
            status=status,
            evidence_id=f"EVID-{domain.upper()}",
            results=[],
        )

    monkeypatch.setattr("arkhon.verification.engine.VerificationEngine.run", fake_run)
    assert main(["verify", str(project), "--domain", "all"]) == 1
    assert seen == ["testing", "code-quality", "software-security", "supply-chain"]
    assert "Domain:   software-security" in capsys.readouterr().out


def test_commit_and_worktree_provenance_helpers(tmp_path: Path, monkeypatch) -> None:
    from arkhon.cli import _commit_sha, _working_tree_clean

    monkeypatch.setattr("arkhon.cli.shutil.which", lambda _name: "/usr/bin/git")
    monkeypatch.setattr(
        "arkhon.cli.subprocess.run",
        lambda command, **kwargs: SimpleNamespace(
            stdout="a" * 40 + "\n" if "rev-parse" in command else ""
        ),
    )
    assert _commit_sha(tmp_path) == "a" * 40
    assert _working_tree_clean(tmp_path) is True

    monkeypatch.setattr(
        "arkhon.cli.subprocess.run",
        lambda command, **kwargs: SimpleNamespace(stdout="invalid-sha\n"),
    )
    assert _commit_sha(tmp_path) is None
    assert _working_tree_clean(tmp_path) is False

    monkeypatch.setattr("arkhon.cli.shutil.which", lambda _name: None)
    assert _commit_sha(tmp_path) is None
    assert _working_tree_clean(tmp_path) is False

    monkeypatch.setattr("arkhon.cli.shutil.which", lambda _name: "/usr/bin/git")
    monkeypatch.setattr(
        "arkhon.cli.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("git unavailable")),
    )
    assert _commit_sha(tmp_path) is None
    assert _working_tree_clean(tmp_path) is False


def test_assess_blocks_malformed_rule_declarations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    rules = [
        SimpleNamespace(
            id="BAD-ID",
            domain="code-quality",
            status="active",
            enforcement="blocking",
            raw={"scope": {"project_types": ["universal"]}},
        ),
        SimpleNamespace(
            id="SE-CQ-901",
            domain="code-quality",
            status="active",
            enforcement="blocking",
            raw={"scope": {"project_types": []}},
        ),
        SimpleNamespace(
            id="SE-CQ-902",
            domain="code-quality",
            status="active",
            enforcement="blocking",
            raw={
                "scope": {"project_types": ["universal"]},
                "verification": {"methods": []},
                "human_review": "invalid",
            },
        ),
        SimpleNamespace(
            id="SE-CQ-903",
            domain="code-quality",
            status="active",
            enforcement="unknown-level",
            raw={
                "scope": {"project_types": ["universal"]},
                "verification": {"methods": []},
            },
        ),
    ]
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _root: "a" * 40)
    monkeypatch.setattr("arkhon.cli._working_tree_clean", lambda _root: True)
    monkeypatch.setattr(
        "arkhon.rules.loader.load_rules_dir", 
        lambda _path: SimpleNamespace(ok=True, rules=rules, errors=[]))

    assert main(["assess", str(project)]) == 1
    out = capsys.readouterr().out
    assert "BAD-ID: BLOCKED (invalid rule identifier)" in out
    assert "SE-CQ-901: BLOCKED (invalid project scope)" in out
    assert "SE-CQ-902: BLOCKED (human_review declaration is malformed)" in out
    assert "SE-CQ-903: BLOCKED" in out

def test_assess_handles_runner_contract_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
    project = tmp_path / "project"
    project.mkdir()
    rule = SimpleNamespace(
        id="SE-CQ-904",
        domain="code-quality",
        status="active",
        enforcement="blocking",
        raw={
            "scope": {"project_types": ["universal"]},
            "verification": {"methods": ["zero-type-errors-check"]},
        },
    )
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _root: "a" * 40)
    monkeypatch.setattr("arkhon.cli._working_tree_clean", lambda _root: True)
    monkeypatch.setattr(
        "arkhon.rules.loader.load_rules_dir",
        lambda _path: SimpleNamespace(ok=True, rules=[rule], errors=[]))

    monkeypatch.setattr(
        "arkhon.verification.methods.resolve_methods",
        lambda _ids: [
            ("zero-type-errors-check", SimpleNamespace(
                runner="unregistered-runner",
                allowed_domains=frozenset({"code-quality"}),
            ))
        ],
    )
    assert main(["assess", str(project)]) == 1
    assert "BLOCKED" in capsys.readouterr().out

    monkeypatch.setattr(
        "arkhon.verification.methods.resolve_methods",
        lambda _ids: [
            ("zero-type-errors-check", SimpleNamespace(
                runner="mypy",
                allowed_domains=frozenset({"code-quality"}),
            ))
        ],
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.MypyRunner.run",
        lambda *_a, **_k: "invalid",
    )
    assert main(["assess", str(project)]) == 1
    assert "BLOCKED" in capsys.readouterr().out

    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.MypyRunner.run",
        lambda *_a, **_k: RunnerResult(
            runner="mypy",
            outcome=RunnerOutcome.PASS,
            artifacts=(),
        ),
    )
    assert main(["assess", str(project)]) == 1
    assert "BLOCKED" in capsys.readouterr().out

    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.MypyRunner.run",
        lambda *_a, **_k: RunnerResult(
            runner="mypy",
            outcome=RunnerOutcome.PASS,
            artifacts=(project / "missing.txt",),
        ),
    )
    assert main(["assess", str(project)]) == 1
    assert "BLOCKED" in capsys.readouterr().out

def test_assess_method_status_mappings_for_mypy_tsar_and_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from arkhon.verification.runners.base import RunnerOutcome, RunnerResult
    project = tmp_path / "project"
    project.mkdir()
    artifact = project / "evidence.json"
    artifact.write_text("{}", encoding="utf-8")
    rules = [
        SimpleNamespace(
            id="SE-CQ-910",
            domain="code-quality",
            status="active",
            enforcement="blocking",
            raw={
                "scope": {"project_types": ["universal"]},
                "verification": {
                    "methods": ["zero-type-errors-check", "unmapped-method"],
                },
            },
        ),
        SimpleNamespace(
            id="SE-SEC-910",
            domain="software-security",
            status="active",
            enforcement="blocking",
            raw={
                "scope": {"project_types": ["universal"]},
                "verification": {
                    "methods": ["tsar-audit-invocation", "evidence-integrity-check"],
                },
            },
        ),
    ]
    impls = [
        ("zero-type-errors-check", SimpleNamespace(
            runner="mypy",
            allowed_domains=frozenset({"code-quality"}),
        )),
        ("tsar-audit-invocation", SimpleNamespace(
            runner="tsar",
            allowed_domains=frozenset({"software-security"}),
        )),
        ("evidence-integrity-check", SimpleNamespace(
            runner="tsar",
            allowed_domains=frozenset({"software-security"}),
        )),
        ("unmapped-method", SimpleNamespace(
          runner="mypy",
            allowed_domains=frozenset({"code-quality"}),
        )),
    ]
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _root: "a" * 40)
    monkeypatch.setattr("arkhon.cli._working_tree_clean", lambda _root: True)
    monkeypatch.setattr(
        "arkhon.rules.loader.load_rules_dir",
        lambda _path: SimpleNamespace(ok=True, rules=rules, errors=[]))
    monkeypatch.setattr("arkhon.verification.methods.resolve_methods", lambda _ids: impls)
    monkeypatch.setattr(
        "arkhon.verification.runners.mypy_runner.MypyRunner.run",
        lambda *_a, **_k: RunnerResult(
            runner="mypy",
            outcome=RunnerOutcome.PASS,
            artifacts=(artifact,),
        ),
    )
    monkeypatch.setattr(
        "arkhon.verification.runners.tsar_runner.TsarRunner.run",
        lambda *_a, **_k: RunnerResult(
            runner="tsar",
            outcome=RunnerOutcome.PASS,
            artifacts=(artifact,),
        ),
    )

    assert main(["assess", str(project)]) == 1
    out1 = capsys.readouterr().out
    assert "[PASS] zero-type-errors-check" in out1
    assert "[BLOCKED] unmapped-method" in out1
    assert "[PASS] tsar-audit-invocation" in out1
    assert "[PASS] evidence-integrity-check" in out1

    monkeypatch.setattr(
        "arkhon.verification.runners.tsar_runner.TsarRunner.run",
        lambda *_a, **_k: RunnerResult(
            runner="tsar",
            outcome=RunnerOutcome.FAIL,
            reason="critical finding",
            artifacts=(artifact,),
        ),
    )
    assert main(["assess", str(project)]) == 1
    out2 = capsys.readouterr().out
    assert "[FAIL] tsar-audit-invocation" in out2
    assert "[PASS] evidence-integrity-check" in out2
    assert "critical finding" in out2

def test_assess_handles_symlink_summary_and_gate_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from arkhon.core.errors import GateError
    project = tmp_path / "project"
    project.mkdir()
    rule = SimpleNamespace(
        id="SE-CQ-920",
        domain="code-quality",
        status="active",
        enforcement="blocking",
        raw={
            "scope": {"project_types": ["universal"]},
            "verification": {"methods": []},
        },
    )
    monkeypatch.setattr("arkhon.cli._commit_sha", lambda _root: "a" * 40)
    monkeypatch.setattr("arkhon.cli._working_tree_clean", lambda _root: True)
    monkeypatch.setattr(
        "arkhon.rules.loader.load_rules_dir",
        lambda _path: SimpleNamespace(ok=True, rules=[rule], errors=[]))

    orig_is_symlink = Path.is_symlink

    def _fake_is_symlink(self: Path) -> bool:
        if self.name == "SE-CQ-920.json":
            return True
        return orig_is_symlink(self)

    monkeypatch.setattr(Path, "is_symlink", _fake_is_symlink)
    assert main(["assess", str(project)]) == 1
    assert "SE-CQ-920: BLOCKED" in capsys.readouterr().out

    monkeypatch.setattr(Path, "is_symlink", orig_is_symlink)

    def _raise_gate_error(*_args: object, **_kwargs: object) -> object:
        raise GateError("gate failure")

    monkeypatch.setattr("arkhon.assessment.gates.evaluate_all_gates", _raise_gate_error)
    assert main(["assess", str(project)]) == 1
    err = capsys.readouterr().err
    assert "[FAIL] rule outcomes cannot be evaluated safely: gate failure" in err




