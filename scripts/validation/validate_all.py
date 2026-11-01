"""Run the repository's configured validation suite."""
import subprocess,sys
def main() -> int: return subprocess.call([sys.executable,"-m","pytest","-q"])
if __name__=="__main__": raise SystemExit(main())
