from pathlib import Path


def test_foundation_files_exist() -> None:
    required = [
        "README.md",
        "LICENSE",
        "VERSION",
        "manifest/index.yaml",
        "pyproject.toml",
        "AGENTS.md",
    ]
    for path in required:
        assert Path(path).is_file(), f"missing foundation file: {path}"
