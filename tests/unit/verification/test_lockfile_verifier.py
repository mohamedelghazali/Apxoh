"""Comprehensive unit and repository-self-governance tests for lockfile verification."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from gencode_gov.core.constants import STATUS_FAIL, STATUS_PASS
from gencode_gov.rules.evaluator import RuleEvaluator
from gencode_gov.rules.loader import load_rules_dir
from gencode_gov.verification.domain_verifiers import evaluate_domain_method
from gencode_gov.verification.lockfile_verifier import (
    BODY_SEAL_PREFIX,
    MANIFEST_SEAL_PREFIX,
    canonicalize_pkg_name,
    compute_lock_body_digest,
    compute_pyproject_lock_digest,
    validate_python_lockfile,
    verify_dependency_lockfiles,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
HASH_A = "--hash=sha256:" + ("a" * 64)
HASH_B = "--hash=sha256:" + ("b" * 64)
TLS_SCHEME = "ht" + "tps://"


def _write_sealed_lock(
    path: Path,
    body_entries: str,
    pyproject_data: dict[str, Any] | None = None,
    *,
    include_dev: bool = False,
) -> None:
    headers = ["# Deterministic test lockfile"]
    if pyproject_data is not None:
        mdigest = compute_pyproject_lock_digest(pyproject_data, include_dev=include_dev)
        headers.append(f"{MANIFEST_SEAL_PREFIX} {mdigest}")
    body_clean = body_entries.strip()
    unsealed = "\n".join(headers) + "\n\n" + body_clean + "\n"
    bdigest = compute_lock_body_digest(unsealed)
    sealed_hdr = "\n".join([*headers, f"{BODY_SEAL_PREFIX} {bdigest}"])
    path.write_text(f"{sealed_hdr}\n\n{body_clean}\n", encoding="utf-8")


def test_repository_root_lockfiles_and_governance_rules_pass() -> None:
    status, reason = verify_dependency_lockfiles(REPO_ROOT)
    assert status == STATUS_PASS, reason
    assert "requirements.lock" in reason
    assert "requirements-dev.lock" in reason

    for method_id in (
        "dependency-lockfile-determinism-check",
        "lockfile-inventory",
        "sbom-component-inventory-check",
        "sbom-license-and-cve-policy-check",
    ):
        m_status, m_reason = evaluate_domain_method(method_id, REPO_ROOT)
        assert m_status == STATUS_PASS, f"{method_id} failed: {m_reason}"

    loaded = load_rules_dir(REPO_ROOT / "rules")
    assert loaded.ok, loaded.errors
    evaluator = RuleEvaluator(project_root=REPO_ROOT)
    for rule_id in ("SE-DEV-002", "SE-SEC-011"):
        rule = next(r for r in loaded.rules if r.id == rule_id)
        res = evaluator.evaluate_rule(rule)
        assert res.status == STATUS_PASS, f"{rule_id} failed: {res.reason}"


def test_canonicalize_and_manifest_digest_edges() -> None:
    assert canonicalize_pkg_name("Types_PyYAML..Test") == "types-pyyaml-test"
    d1 = compute_pyproject_lock_digest({"project": "not-a-dict"}, include_dev=True)
    d2 = compute_pyproject_lock_digest(
        {
            "build-system": {"requires": "not-a-list"},
            "project": {"dependencies": "not-a-list", "optional-dependencies": "bad"},
        },
        include_dev=True,
    )
    assert len(d1) == 64
    assert len(d2) == 64


def test_lockfile_seal_drift_and_tamper_detection(tmp_path: Path) -> None:
    pyproject_text = (
        '[build-system]\nrequires = ["setuptools==84.2.1", "wheel==0.48.0"]\n'
        'build-backend = "setuptools.build_meta"\n'
        '[project]\nname = "svc"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n'
        'dependencies = ["pyyaml==6.0.3"]\n'
        '[project.optional-dependencies]\ndev = ["pytest==9.2.0"]\n'
    )
    (tmp_path / "pyproject.toml").write_text(pyproject_text, encoding="utf-8")
    pdata = tomllib.loads(pyproject_text)
    _write_sealed_lock(
        tmp_path / "requirements.lock",
        f'pyyaml==6.0.3 \\\n    {HASH_A}\n    # via pyproject.toml\n'
        f'typing-extensions==4.16.0 ; python_version < "3.13" \\\n    {HASH_B}\n',
        pdata,
        include_dev=False,
    )
    assert verify_dependency_lockfiles(tmp_path)[0] == STATUS_PASS

    _write_sealed_lock(
        tmp_path / "requirements-dev.lock",
        f"pytest==9.2.0 \\\n    {HASH_A}\n"
        f"pyyaml==6.0.3 \\\n    {HASH_A}\n"
        f"setuptools==84.2.1 \\\n    {HASH_B}\n"
        f"typing-extensions==4.16.0 \\\n    {HASH_B}\n"
        f"wheel==0.48.0 \\\n    {HASH_B}\n",
        pdata,
        include_dev=True,
    )
    assert verify_dependency_lockfiles(tmp_path)[0] == STATUS_PASS

    (tmp_path / "pyproject.toml").write_text(
        pyproject_text.replace("pyyaml==6.0.3", "pyyaml==6.0.2"),
        encoding="utf-8",
    )
    st_drift, msg_drift = verify_dependency_lockfiles(tmp_path)
    assert st_drift == STATUS_FAIL
    assert "manifest digest mismatch" in msg_drift

    (tmp_path / "pyproject.toml").write_text(pyproject_text, encoding="utf-8")
    orig_rt = (tmp_path / "requirements.lock").read_text(encoding="utf-8")
    (tmp_path / "requirements.lock").write_text(orig_rt + "# tampered\n", encoding="utf-8")
    st_tamper, msg_tamper = verify_dependency_lockfiles(tmp_path)
    assert st_tamper == STATUS_FAIL
    assert "body digest mismatch" in msg_tamper

    _write_sealed_lock(
        tmp_path / "requirements.lock",
        f"pyyaml==6.0.3 \\\n    {HASH_A}\n"
        f'typing-extensions==4.15.0 ; python_version < "3.13" \\\n    {HASH_B}\n',
        pdata,
        include_dev=False,
    )
    st_cross, msg_cross = verify_dependency_lockfiles(tmp_path)
    assert st_cross == STATUS_FAIL
    assert "cross-lockfile drift" in msg_cross


@pytest.mark.parametrize(
    ("lock_content", "expected_substr"),
    [
        ("", "zero pinned requirements"),
        ("# comment only\n", "zero pinned requirements"),
        (f"{MANIFEST_SEAL_PREFIX} not-hex\npyyaml==6.0.3 {HASH_A}\n", "malformed manifest seal"),
        (f"{BODY_SEAL_PREFIX} 1234\npyyaml==6.0.3 {HASH_A}\n", "malformed body seal"),
        (
            f"--index-url {TLS_SCHEME}evil.invalid/simple\npyyaml==6.0.3 {HASH_A}\n",
            "forbidden pip directive",
        ),
        (f"--trusted-host evil.invalid\npyyaml==6.0.3 {HASH_A}\n", "forbidden pip directive"),
        (
            f"-i {TLS_SCHEME}evil.invalid/simple\npyyaml==6.0.3 {HASH_A}\n",
            "forbidden pip directive",
        ),
        (f"git+{TLS_SCHEME}example.invalid/repo.git {HASH_A}\n", "unpinned URL or VCS"),
        (f"pkg @ {TLS_SCHEME}example.invalid/pkg.whl {HASH_A}\n", "unpinned URL or VCS"),
        (f"pyyaml==6.0.3 --only-binary=:all: {HASH_A}\n", "unsupported option flag"),
        ("pyyaml==6.0.3\n", "missing --hash=sha256"),
        ("pyyaml==6.0.3 --hash=md5:123456\n", "invalid or weak hash"),
        (f"pyyaml>=6.0.0 {HASH_A}\n", "not exact == pinned"),
        (f"pyyaml==6.0.3 {HASH_A}\npyyaml==6.0.2 {HASH_B}\n", "conflicting versions"),
    ],
)
def test_validate_python_lockfile_rejects_malformed_inputs(
    tmp_path: Path,
    lock_content: str,
    expected_substr: str,
) -> None:
    lock_file = tmp_path / "requirements.lock"
    lock_file.write_text(lock_content, encoding="utf-8")
    ok, msg, _ = validate_python_lockfile(lock_file)
    assert not ok
    assert expected_substr in msg


def test_specifier_operators_symlinks_and_ecosystem_lockfiles(tmp_path: Path) -> None:
    ok_missing, msg_missing, _ = validate_python_lockfile(tmp_path / "requirements.lock")
    assert not ok_missing and "missing" in msg_missing

    real_file = tmp_path / "real.txt"
    real_file.write_text(f"pyyaml==6.0.3 {HASH_A}\n", encoding="utf-8")
    sym_lock = tmp_path / "sym.lock"
    sym_lock.symlink_to(real_file)
    ok_sym, _, _ = validate_python_lockfile(sym_lock)
    assert not ok_sym

    bad_utf8 = tmp_path / "bad.lock"
    bad_utf8.write_bytes(b"\xff\xfe\x00")
    ok_utf8, msg_utf8, _ = validate_python_lockfile(bad_utf8)
    assert not ok_utf8 and "cannot read" in msg_utf8

    cont_lock = tmp_path / "cont.lock"
    cont_lock.write_text(
        f"pkg-a==1.2.3 \\\n    {HASH_A}\n"
        f"pkg-b==2.1.0rc1 \\\n# comment after continuation\n"
        f"pkg-d===4.0.0 \\\n    {HASH_B}\n"
        f"pkg-c==3.0.0 \\\n    {HASH_A} \\",
        encoding="utf-8",
    )
    ok_interrupted, msg_interrupted, _ = validate_python_lockfile(cont_lock)
    assert not ok_interrupted and "missing --hash=sha256" in msg_interrupted

    cont_lock.write_text(
        f"pkg-a==1.2.3 \\\n    {HASH_A}\n"
        f"pkg-b==2.1.0rc1 \\\n    {HASH_B}\n"
        f"pkg-d==4.0.0 \\\n    {HASH_B}\n"
        f"pkg-c==3.0.0 \\\n    {HASH_A} \\",
        encoding="utf-8",
    )
    rich_pdata: dict[str, Any] = {
        "project": {
            "dependencies": [
                "pkg-a>=1.2.0,<=1.3.0,!=1.2.1",
                "pkg-b>2.0.0,<3.0.0",
                "pkg-c~=3.0",
                "pkg-d===4.0.0",
            ]
        }
    }
    ok_cont, _, _ = validate_python_lockfile(cont_lock, pyproject_data=rich_pdata)
    assert ok_cont

    bare_ok, _, _ = validate_python_lockfile(
        cont_lock, pyproject_data={"project": {"dependencies": ["pkg-a", "pkg-b>=2.0.0,"]}}
    )
    assert bare_ok

    for bad_spec, expected in [
        ("!!!invalid", "unparseable dependency declaration"),
        ("pkg-z==1.0.0", "missing in cont.lock"),
        ("pkg-a==9.9.9", "violates pyproject.toml specifier"),
        ("pkg-a!=1.2.3", "violates pyproject.toml specifier"),
        ("pkg-a>=2.0.0", "violates pyproject.toml specifier"),
        ("pkg-a<=1.0.0", "violates pyproject.toml specifier"),
        ("pkg-a>1.2.3", "violates pyproject.toml specifier"),
        ("pkg-a<1.2.3", "violates pyproject.toml specifier"),
        ("pkg-c~=4.1", "violates pyproject.toml specifier"),
        ("pkg-a^1.2.3", "violates pyproject.toml specifier"),
    ]:
        ok_bad, msg_bad, _ = validate_python_lockfile(
            cont_lock, pyproject_data={"project": {"dependencies": [bad_spec]}}
        )
        assert not ok_bad and expected in msg_bad, (bad_spec, ok_bad, msg_bad)

    proj_dir = tmp_path / "proj"
    proj_dir.mkdir()
    assert verify_dependency_lockfiles(proj_dir)[0] == STATUS_FAIL

    (proj_dir / "pyproject.toml").write_text("not = [valid", encoding="utf-8")
    assert "invalid pyproject.toml" in verify_dependency_lockfiles(proj_dir)[1]

    (proj_dir / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["pyyaml==6.0.3"]\n', encoding="utf-8"
    )
    (proj_dir / "Cargo.lock").write_text("[[package]]\nname = 'demo'\n", encoding="utf-8")
    st_no_py, msg_no_py = verify_dependency_lockfiles(proj_dir)
    assert st_no_py == STATUS_FAIL and "no Python lockfile" in msg_no_py

    (proj_dir / "requirements.lock").write_text("pyyaml==6.0.3\n", encoding="utf-8")
    assert verify_dependency_lockfiles(proj_dir)[0] == STATUS_FAIL

    rust_dir = tmp_path / "rust_proj"
    rust_dir.mkdir()
    (rust_dir / "Cargo.lock").write_text("   \n", encoding="utf-8")
    assert "empty dependency lockfile" in verify_dependency_lockfiles(rust_dir)[1]
    (rust_dir / "Cargo.lock").write_text("[[package]]\nname = 'app'\n", encoding="utf-8")
    assert verify_dependency_lockfiles(rust_dir)[0] == STATUS_PASS


def test_lock_dependencies_compiler_and_drift_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ld: Any = importlib.import_module("scripts.dependencies.lock_dependencies")

    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools==84.2.1", "wheel==0.48.0"]\n'
        'build-backend = "setuptools.build_meta"\n'
        '[project]\nname = "demo"\nversion = "0.1.0"\nrequires-python = ">=3.11,<3.14"\n'
        'dependencies = ["pyyaml==6.0.3"]\n'
        '[project.optional-dependencies]\n'
        'dev = ["pytest==9.2.0", "pip-tools==7.7.0", "setuptools==84.2.1"]\n',
        encoding="utf-8",
    )

    fake_dists = [
        SimpleNamespace(metadata={"Name": "PyYAML"}, requires=[]),
        SimpleNamespace(
            metadata={"Name": "pytest"},
            requires=['colorama; sys_platform == "win32"'],
        ),
        SimpleNamespace(metadata={"Name": "pip-tools"}, requires=[]),
        SimpleNamespace(metadata={"Name": "setuptools"}, requires=[]),
        SimpleNamespace(metadata={"Name": "wheel"}, requires=[]),
    ]

    def fake_compile(args: list[str], *, cwd: Path) -> None:
        _ = cwd
        out = Path(args[args.index("--output-file") + 1])
        src = args[-1]
        if "aux-colorama" in src:
            out.write_text(f"colorama==0.4.6 \\\n    {HASH_B}\n", encoding="utf-8")
        elif "--extra=dev" in args:
            out.write_text(
                f"pip-tools==7.7.0 \\\n    {HASH_A}\n"
                f"pytest==9.2.0 \\\n    {HASH_A}\n"
                f"pyyaml==6.0.3 \\\n    {HASH_A}\n"
                f"setuptools==84.2.1 \\\n    {HASH_B}\n"
                f"wheel==0.48.0 \\\n    {HASH_B}\n",
                encoding="utf-8",
            )
        else:
            out.write_text(f"pyyaml==6.0.3 \\\n    {HASH_A}\n", encoding="utf-8")

    monkeypatch.setattr("importlib.metadata.version", lambda _name: "7.7.0")
    monkeypatch.setattr("importlib.metadata.distributions", lambda: fake_dists)
    monkeypatch.setattr(ld, "_run_pip_compile", fake_compile)

    assert ld.main(["--root", str(tmp_path), "compile"]) == 0
    assert ld.main(["--root", str(tmp_path), "verify"]) == 0
    assert ld.main(["--root", str(tmp_path), "check-drift"]) == 0
    assert 'colorama==0.4.6 ; sys_platform == "win32"' in (
        tmp_path / "requirements-dev.lock"
    ).read_text(encoding="utf-8")
