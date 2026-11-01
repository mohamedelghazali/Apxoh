from pathlib import Path
import yaml
def test_manifest_identity():
    data=yaml.safe_load(Path("manifest.yaml").read_text(encoding="utf-8"))
    assert data["name"]=="arkhon"
