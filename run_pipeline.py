"""
run_pipeline.py — Run the full pipeline in one command

Usage:
    python run_pipeline.py              # real data, fetched live from USPTO (no download)
    python run_pipeline.py --sample     # use local sample data (fast, no internet)
    python run_pipeline.py --viz        # also generate charts
    python run_pipeline.py --sample --viz
"""

import sys
import subprocess

USE_SAMPLE = "--sample" in sys.argv
MAKE_VIZ   = "--viz"    in sys.argv


def run(script, extra_args=None):
    cmd = [sys.executable, script] + (extra_args or [])
    print(f"\n>>> Running {script} ...")
    subprocess.run(cmd, check=True)


def main():
    print("\n" + "#" * 55)
    print("  GLOBAL PATENT INTELLIGENCE — FULL PIPELINE")
    print("#" * 55)

    if USE_SAMPLE:
        print("\n  Using local sample data (--sample)")
        run("00_sample_data.py")
        run("02_clean.py", ["--sample"])
    else:
        print(f"\n  Fetching live data from USPTO (no download to disk)")
        run("02_clean.py")          # fetches directly from URLs

    run("03_load_db.py")
    run("04_report.py")

    if MAKE_VIZ:
        run("05_visualize.py")

    print("\n" + "#" * 55)
    print("  PIPELINE COMPLETE!")
    print("#" * 55)
    print("""
  Files generated:
    patent_pipeline.db
    data/clean/          <- 5 clean CSVs
    reports/             <- CSV, JSON reports
    reports/charts/      <- PNG charts (if --viz used)

  Launch dashboard:
    streamlit run dashboard.py
""")


if __name__ == "__main__":
    main()
