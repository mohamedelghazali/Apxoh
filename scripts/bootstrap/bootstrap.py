"""Bootstrap ARKHON development environment."""
import subprocess,sys
def main() -> int:
    return subprocess.call([sys.executable,"-m","pip","install","-e",".[dev]"])
if __name__=="__main__": raise SystemExit(main())
