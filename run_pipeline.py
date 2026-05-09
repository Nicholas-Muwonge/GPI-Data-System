"""
run_pipeline.py — Run the full pipeline in one command
Usage:
    python run_pipeline.py              # uses sample data (fast, no download)
    python run_pipeline.py --real-data  # download real data from USPTO
    python run_pipeline.py --viz        # also generate charts
"""

import sys
import subprocess


def run(script: str):
    print(f"\n{'▶'*3}  Running {script} …")
    result = subprocess.run([sys.executable, script], check=True)
    return result


def main():
    use_real_data = "--real-data" in sys.argv
    make_viz      = "--viz"       in sys.argv

    print("\n" + "█" * 55)
    print("  GLOBAL PATENT INTELLIGENCE — FULL PIPELINE")
    print("█" * 55)

    # Step 0 / 1: data acquisition
    if use_real_data:
        run("01_ingest.py")
    else:
        print("\n  ℹ  Using sample data (pass --real-data to download from USPTO)")
        run("00_sample_data.py")

    # Step 2: clean
    run("02_clean.py")

    # Step 3: load DB
    run("03_load_db.py")

    # Step 4: reports
    run("04_report.py")

    # Step 5: visualizations (optional)
    if make_viz:
        run("05_visualize.py")
    else:
        print("\n  ℹ  Skipping charts (pass --viz to generate)")

    print("\n" + "█" * 55)
    print("  ✅  PIPELINE COMPLETE!")
    print("█" * 55)
    print("""
  Generated files:
    patent_pipeline.db          ← SQLite database
    data/clean/                 ← 5 clean CSV files
    reports/top_inventors.csv
    reports/top_companies.csv
    reports/country_trends.csv
    reports/yearly_trends.csv
    reports/ranked_inventors.csv
    reports/summary_report.json

  To open the dashboard:
    streamlit run dashboard.py
""")


if __name__ == "__main__":
    main()
