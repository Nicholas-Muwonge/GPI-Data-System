"""
generate_reports.py
-------------------
Generates three types of reports from query result CSVs:
  A. Console report (printed to terminal)
  B. CSV exports  (reports/top_inventors.csv, top_companies.csv, country_trends.csv)
  C. JSON report  (reports/report.json)

Usage:
    python scripts/generate_reports.py
"""

import os
import json
import sqlite3
import pandas as pd

DB_PATH     = os.path.join(os.path.dirname(__file__), "..", "patents.db")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "results")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")


# ── helpers ────────────────────────────────────────────────────────────────────

def load_result(filename: str) -> pd.DataFrame:
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing result file: {path}\n"
            "Run  python scripts/run_queries.py  first."
        )
    return pd.read_csv(path)


def save_report_csv(df: pd.DataFrame, filename: str) -> None:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  [CSV] Saved {path}")


def get_total_patents() -> int:
    if not os.path.exists(DB_PATH):
        return 0
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.execute("SELECT COUNT(*) FROM patents")
    total = cur.fetchone()[0]
    conn.close()
    return total


# ── A. Console Report ──────────────────────────────────────────────────────────

def print_console_report(
    total: int,
    inventors: pd.DataFrame,
    companies: pd.DataFrame,
    countries: pd.DataFrame,
    trends:    pd.DataFrame,
) -> None:
    w = 56
    sep  = "=" * w
    dash = "-" * w

    print(f"\n{sep}")
    print(f"{'GLOBAL PATENT INTELLIGENCE REPORT':^{w}}")
    print(sep)
    print(f"  Total Patents Indexed : {total:>12,}")
    if not trends.empty:
        print(f"  Year Range            : {int(trends['year'].min())} – {int(trends['year'].max())}")
    print(dash)

    # Top Inventors
    print(f"\n  {'TOP 10 INVENTORS BY PATENT COUNT'}")
    print(f"  {'Rank':<6}{'Name':<30}{'Country':<10}{'Patents':>7}")
    print(f"  {'-'*4:<6}{'-'*28:<30}{'-'*7:<10}{'-'*7:>7}")
    for i, row in inventors.head(10).iterrows():
        country = str(row.get("country", "—") or "—")[:8]
        print(f"  {i+1:<6}{str(row['name']):<30}{country:<10}{int(row['patent_count']):>7,}")

    # Top Companies
    print(f"\n  {'TOP 10 COMPANIES BY PATENT COUNT'}")
    print(f"  {'Rank':<6}{'Company':<36}{'Patents':>7}")
    print(f"  {'-'*4:<6}{'-'*34:<36}{'-'*7:>7}")
    for i, row in companies.head(10).iterrows():
        name = str(row["name"])[:34]
        print(f"  {i+1:<6}{name:<36}{int(row['patent_count']):>7,}")

    # Top Countries
    print(f"\n  {'TOP 10 COUNTRIES BY PATENT COUNT'}")
    print(f"  {'Rank':<6}{'Country':<14}{'Patents':>9}{'Share %':>9}")
    print(f"  {'-'*4:<6}{'-'*12:<14}{'-'*9:>9}{'-'*8:>9}")
    for i, row in countries.head(10).iterrows():
        share = f"{float(row.get('share_pct', 0)):.2f}%"
        print(f"  {i+1:<6}{str(row['country']):<14}{int(row['patent_count']):>9,}{share:>9}")

    # Yearly trend summary
    if not trends.empty:
        print(f"\n  {'PATENT TRENDS (last 5 years)'}")
        print(f"  {'Year':<8}{'Patents':>10}")
        print(f"  {'-'*6:<8}{'-'*10:>10}")
        for _, row in trends.tail(5).iterrows():
            print(f"  {int(row['year']):<8}{int(row['patent_count']):>10,}")

    print(f"\n{sep}\n")


# ── B. CSV Exports ─────────────────────────────────────────────────────────────

def export_csvs(
    inventors: pd.DataFrame,
    companies: pd.DataFrame,
    countries: pd.DataFrame,
) -> None:
    print("\n=== B. CSV Exports ===")
    save_report_csv(inventors, "top_inventors.csv")
    save_report_csv(companies, "top_companies.csv")
    save_report_csv(countries, "country_trends.csv")


# ── C. JSON Report ─────────────────────────────────────────────────────────────

def export_json(
    total:     int,
    inventors: pd.DataFrame,
    companies: pd.DataFrame,
    countries: pd.DataFrame,
    trends:    pd.DataFrame,
) -> None:
    print("\n=== C. JSON Report ===")

    def to_records(df: pd.DataFrame) -> list[dict]:
        return [
            {k: (None if pd.isna(v) else (int(v) if isinstance(v, float) and v == int(v) else v))
             for k, v in row.items()}
            for row in df.to_dict("records")
        ]

    report = {
        "total_patents": total,
        "top_inventors": [
            {"name": r["name"], "country": r.get("country"), "patents": int(r["patent_count"])}
            for r in to_records(inventors.head(20))
        ],
        "top_companies": [
            {"name": r["name"], "patents": int(r["patent_count"])}
            for r in to_records(companies.head(20))
        ],
        "top_countries": [
            {
                "country": r["country"],
                "patents": int(r["patent_count"]),
                "share":   float(r.get("share_pct", 0)) / 100,
            }
            for r in to_records(countries.head(20))
        ],
        "yearly_trends": [
            {"year": int(r["year"]), "patents": int(r["patent_count"])}
            for r in to_records(trends)
        ],
    }

    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, "report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  [JSON] Saved {out_path}")


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    inventors = load_result("q1_top_inventors.csv")
    companies = load_result("q2_top_companies.csv")
    countries = load_result("q3_countries.csv")
    trends    = load_result("q4_trends_over_time.csv")
    total     = get_total_patents()

    print("\n=== A. Console Report ===")
    print_console_report(total, inventors, companies, countries, trends)

    export_csvs(inventors, companies, countries)
    export_json(total, inventors, companies, countries, trends)

    print("\n✅  Reports complete.")
    print("Optional: python scripts/visualise.py   (charts)")
    print("Optional: streamlit run dashboard.py    (web dashboard)")


if __name__ == "__main__":
    main()
