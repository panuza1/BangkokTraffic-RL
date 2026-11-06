import shutil
import subprocess
import sys

print(f"Python: {sys.version.split()[0]}", flush=True)
sumo = shutil.which("sumo")
if sumo is None:
    sys.exit("FAIL: sumo is not on PATH; install SUMO and activate its environment")
result = subprocess.run([sumo, "--version"], check=False)
if result.returncode:
    sys.exit(result.returncode)
print("PASS: Python and SUMO are callable")
