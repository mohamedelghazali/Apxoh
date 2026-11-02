"""Tests for the JSON reporter."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from arkhon.core.errors import EvidenceError
from arkhon.reporting.json_reporter import JsonReporter

def _write_evidence(project:Path,domain:str,evidence_id:str,status:str="PASS")->Path:
    target_dir=project/".arkhon"/"evidence"/domain
    target_dir.mkdir(parents=True,exist_ok=True)
    target=target_dir/f"{evidence_id}.json"
    target.write_text(json.dumps({
        "evidence_id":evidence_id,"source":"arkhon","source_version":"0.1.0.dev1",
        "commit_sha":"a"*40,"executed_at":"2026-11-01T00:00:00Z","status":status,
        "artifacts":[{"path":"x","sha256":"b"*64}],
    }),encoding="utf-8")
    return target

def test_build_fails_with_no_evidence(tmp_path:Path)->None:
    with pytest.raises(EvidenceError,match="no evidence"):
        JsonReporter().build(tmp_path)

def test_build_aggregates_sections(tmp_path:Path)->None:
    _write_evidence(tmp_path,"testing","EVID-ARKHON-1","PASS")
    _write_evidence(tmp_path,"software-security","EVID-TSAR-2","PASS")
    report=JsonReporter().build(tmp_path)
    assert report["sections"]["testing"]["status"]=="PASS"
    assert report["sections"]["security"]["status"]=="PASS"
    assert "EVID-ARKHON-1" in report["sections"]["testing"]["evidence_ids"]

def test_build_final_decision_approved(tmp_path:Path)->None:
    _write_evidence(tmp_path,"testing","EVID-A","PASS")
    assert JsonReporter().build(tmp_path)["final_decision"]=="APPROVED"

def test_build_final_decision_rejected_on_fail(tmp_path:Path)->None:
    _write_evidence(tmp_path,"testing","EVID-A","FAIL")
    assert JsonReporter().build(tmp_path)["final_decision"]=="REJECTED"

def test_build_final_decision_pending_on_blocked(tmp_path:Path)->None:
    _write_evidence(tmp_path,"testing","EVID-A","BLOCKED")
    assert JsonReporter().build(tmp_path)["final_decision"]=="PENDING_EVIDENCE"

def test_write_creates_file(tmp_path:Path)->None:
    _write_evidence(tmp_path,"testing","EVID-A","PASS")
    output=tmp_path/"out"
    path=JsonReporter().write(tmp_path,output)
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8"))["project"]==tmp_path.name
