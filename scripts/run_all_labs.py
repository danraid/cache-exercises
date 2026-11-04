"""Run every chapter laboratory using only the Python standard library."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABS = ["chapters/01/helix_ch01.py","chapters/02/helix_ch2.py","chapters/03/helix_prefix.py","chapters/04/helix_kv_lab.py","chapters/05/helix_pages.py","chapters/06/helix_semantic.py","chapters/07/helix_retrieval.py","chapters/08/helix_tool_cache.py","chapters/09/helix_freshness.py","chapters/10/helix_security.py","chapters/11/helix_ch11.py","chapters/12/helix_replay.py"]

if __name__ == "__main__":
    failures = []
    for name in LABS:
        result = subprocess.run([sys.executable, str(ROOT / name)], cwd=ROOT, capture_output=True, text=True)
        print(("PASS" if result.returncode == 0 else "FAIL") + ": " + name)
        if result.returncode:
            failures.append(name)
            print(result.stdout[-2000:] + result.stderr[-2000:])
    print(f"{len(LABS) - len(failures)}/{len(LABS)} passing")
    sys.exit(bool(failures))
