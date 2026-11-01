"""Release gate; deliberately requires explicit version and evidence review."""
def main() -> int:
    print("Release is blocked until release evidence and approvals are supplied.")
    return 2
if __name__=="__main__": raise SystemExit(main())
