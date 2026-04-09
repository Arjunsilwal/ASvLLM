import os
import subprocess
import sys
from datetime import datetime

from analysis_config import EXPECTED_OUTPUTS

PIPELINE = [
    "master_analysis.py",
    "ablation_study.py",
    "mode_prompt_study.py",
    "final_plots.py",
]


def run_script(script_name: str) -> int:
    print(f"\n=== Running: {script_name} ===")
    result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)

    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())

    if result.returncode != 0:
        print(f"[FAIL] {script_name} exited with code {result.returncode}")
    else:
        print(f"[OK] {script_name}")
    return result.returncode


def check_outputs():
    print("\n=== Output Verification ===")
    found = 0
    missing = []
    for path in EXPECTED_OUTPUTS:
        if os.path.exists(path):
            found += 1
            print(f"[FOUND] {path}")
        else:
            missing.append(path)
            print(f"[MISSING] {path}")
    print(f"\nGenerated {found}/{len(EXPECTED_OUTPUTS)} expected outputs.")
    return missing


def main():
    print("ASvLLM Analysis Pipeline")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.executable}")

    failures = []
    for script in PIPELINE:
        if not os.path.exists(script):
            print(f"[SKIP] {script} not found.")
            failures.append((script, "missing script"))
            continue
        rc = run_script(script)
        if rc != 0:
            failures.append((script, f"exit code {rc}"))

    missing_outputs = check_outputs()

    print("\n=== Pipeline Summary ===")
    if not failures:
        print("All scripts executed successfully.")
    else:
        print("Some scripts failed:")
        for s, reason in failures:
            print(f"- {s}: {reason}")

    if not missing_outputs:
        print("All expected outputs are present.")
    else:
        print("Some expected outputs are missing. Check script logs above.")

    if failures or missing_outputs:
        sys.exit(1)


if __name__ == "__main__":
    main()
