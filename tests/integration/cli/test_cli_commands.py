"""Integration tests for Apxoh CLI commands."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from arkhon.cli import main

def test_version_default(capsys:pytest.CaptureFixture[str])->None:
    assert main(["version"])==0
    assert capsys.readouterr().out.startswith("Apxoh ")

def test_version_json(capsys:pytest.CaptureFixture[str])->None:
    assert main(["version","--json"])==0
    data=json.loads(capsys.readouterr().out)
    assert data["name"]=="Apxoh"
    assert data["identifier"]=="arkhon"

def test_doctor(capsys:pytest.CaptureFixture[str])->None:
    rc=main(["doctor"])
    assert "Apxoh doctor" in capsys.readouterr().out
    assert rc in (0,1)

def test_validate(capsys:pytest.CaptureFixture[str])->None:
    assert main(["validate"]) in (0,1)

def test_inspect_requires_dir(capsys:pytest.CaptureFixture[str],tmp_path:Path)->None:
    rc=main(["inspect",str(tmp_path/"missing")])
    assert rc==1
    assert "not a directory" in capsys.readouterr().err

def test_inspect_on_project(capsys:pytest.CaptureFixture[str],tmp_path:Path)->None:
    (tmp_path/"src").mkdir()
    (tmp_path/"src"/"main.py").write_text("x = 1\n",encoding="utf-8")
    rc=main(["inspect",str(tmp_path),"--json"])
    assert rc==0
    data=json.loads(capsys.readouterr().out)
    assert "python" in data["languages"]["detected"]
    assert data["profile"]["name"]

def test_report_writes_json(capsys:pytest.CaptureFixture[str],tmp_path:Path)->None:
    evidence=tmp_path/".arkhon"/"evidence"/"testing"
    evidence.mkdir(parents=True)
    (evidence/"EVID-A.json").write_text(json.dumps({
        "evidence_id":"EVID-A","source":"arkhon","source_version":"0.1.0.dev1",
        "commit_sha":"a"*40,"executed_at":"2026-11-01T00:00:00Z","status":"PASS",
        "artifacts":[{"path":"x","sha256":"b"*64}],
    }),encoding="utf-8")
    output=tmp_path/"reports"
    rc=main(["report",str(tmp_path),"--format","json","--output",str(output)])
    assert rc==0
    assert (output/"report.json").is_file()
    assert "report written" in capsys.readouterr().out
