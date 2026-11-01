from pathlib import Path
def test_foundation_files_exist():
    for p in ["README.md","LICENSE","VERSION","manifest.yaml","pyproject.toml","AGENTS.md"]: assert Path(p).is_file()
