"""ARKHON command line interface."""
from __future__ import annotations
import argparse, json, sys
from arkhon import __version__
def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(prog="arkhon")
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("version"); sub.add_parser("doctor")
    args=parser.parse_args(argv)
    if args.command=="version": print(f"ARKHON {__version__}"); return 0
    if args.command=="doctor":
        ok=sys.version_info >= (3,11)
        print(json.dumps({"product":"ARKHON","python":sys.version.split()[0],"status":"PASS" if ok else "FAIL"},indent=2))
        return 0 if ok else 2
    return 2
if __name__=="__main__": raise SystemExit(main())
