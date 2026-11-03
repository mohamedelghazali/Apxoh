"""Bootstrap ARKHON development environment."""

import subprocess
import sys


def main() -> int:
    return subprocess.call(  # noqa: S603 - fixed interpreter and arguments; shell is disabled
        [sys.executable, "-m", "pip", "install", "-e", ".[dev]"]
    )


if __name__ == "__main__":
    raise SystemExit(main())
