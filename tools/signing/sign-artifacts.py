"""Sign Apxoh artifacts with Sigstore keyless signing.

Usage:
    python tools/signing/sign-artifacts.py path/to/artifact [path/to/another-artifact]

Requires:
    pip install "sigstore==3.5.1"
    An interactive OIDC login or a supported ambient CI identity.

Bundles are written beside each artifact as <artifact>.sigstore.json.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

try:
    from sigstore.models import ClientTrustConfig
    from sigstore.oidc import Issuer
    from sigstore.sign import SigningContext
except ImportError as exc:  # pragma: no cover - depends on optional dependency
    print("Sigstore is required: python -m pip install sigstore==3.5.1", file=sys.stderr)
    raise SystemExit(2) from exc


def sha256_of(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sign_file(path: Path, context: SigningContext, issuer: Issuer) -> Path:
    """Sign a file and write its Sigstore bundle next to the artifact."""
    token = issuer.identity_token()
    with context.signer(token) as signer:
        bundle = signer.sign_artifact(path.read_bytes())
    bundle_path = path.with_name(path.name + ".sigstore.json")
    bundle_path.write_text(bundle.to_json(), encoding="utf-8")
    return bundle_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Artifacts to sign")
    parser.add_argument(
        "--issuer",
        default=None,
        help="OIDC issuer URL (defaults to the Sigstore trust configuration)",
    )
    args = parser.parse_args(argv)

    invalid = [path for path in args.paths if not path.is_file()]
    if invalid:
        for path in invalid:
            print(f"[FAIL] not a regular file: {path}", file=sys.stderr)
        return 1

    try:
        trust_config = ClientTrustConfig.production()
        issuer_url = args.issuer or trust_config.signing_config.get_oidc_url()
        issuer = Issuer(issuer_url)
        context = SigningContext.from_trust_config(trust_config)

        for path in args.paths:
            bundle_path = sign_file(path, context, issuer)
            print(f"[OK] {path}")
            print(f"     sha256={sha256_of(path)}")
            print(f"     bundle={bundle_path}")
    except Exception as exc:  # OIDC, signing, file I/O, and transparency-log failures
        print(f"[FAIL] signing failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
