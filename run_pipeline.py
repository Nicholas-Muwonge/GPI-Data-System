"""
run_pipeline.py
---------------
Master script that runs the entire pipeline in one command:
  1. clean_data.py
  2. load_db.py
  3. run_queries.py
  4. generate_reports.py
  5. visualise.py  (optional, skipped if matplotlib unavailable)

Usage:
    python run_pipeline.py [--skip-viz]
"""

import subprocess
import sys
import os
import argparse

SCRIPTS = os.path.join(os.path.dirname(__file__), "scripts")


def run(script: str, label: str) -> bool:
    path = os.path.join(SCRIPTS, script)
    print(f"\n{'='*60}")
    print(f"  RUNNING: {label}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, path], check=False)
    if result.returncode != 0:
        print(f"\n[ERROR] {label} failed (exit code {result.returncode}). Stopping.")
        return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-viz", action="store_true",
                        help="Skip the visualisation step")
    args = parser.parse_args()

    steps = [
        ("clean_data.py",       "Step 1/4 – Clean Data"),
        ("load_db.py",          "Step 2/4 – Load Database"),
        ("run_queries.py",      "Step 3/4 – Run SQL Queries"),
        ("generate_reports.py", "Step 4/4 – Generate Reports"),
    ]

    if not args.skip_viz:
        steps.append(("visualise.py", "Step 5/5 – Generate Charts"))

    for script, label in steps:
        if not run(script, label):
            sys.exit(1)

    print(f"\n{'='*60}")
    print("  ✅  PIPELINE COMPLETE")
    print(f"{'='*60}")
    print("\n  Reports:  reports/")
    print("  Charts:   reports/charts/")
    print("  Database: patents.db")
    print("\n  Launch dashboard:  streamlit run dashboard.py\n")


if __name__ == "__main__":
    main()
