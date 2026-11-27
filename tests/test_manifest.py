from pathlib import Path

from gencode_gov.config import load_manifest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_manifest_identity() -> None:
    manifest = load_manifest(REPOSITORY_ROOT)
    assert manifest.name == "GENCODE-GOV"
    assert manifest.identifier == "gencode-gov"
    assert manifest.version
