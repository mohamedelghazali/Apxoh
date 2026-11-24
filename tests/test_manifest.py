from pathlib import Path

from arkhon.config import load_manifest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_manifest_identity() -> None:
    manifest = load_manifest(REPOSITORY_ROOT)
    assert manifest.name == "Apxoh"
    assert manifest.identifier == "arkhon"
    assert manifest.version
