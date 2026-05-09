"""
04_report.py — Generate all required reports
Produces:
  • Console report (terminal output)
  • reports/top_inventors.csv
  • reports/top_companies.csv
  • reports/country_trends.csv
  • reports/summary_report.json
"""

import os
import json
import sqlite3
import pandas as pd

DB_PATH    = os.path.join(os.path.dirname(__file__), "patent_pipeline.db")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


def connect() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}\nRun 03_load_db.py first."
        )
    return sqlite3.connect(DB_PATH)


def query(conn: sqlite3.Connection, sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn)


# ── SQL strings ───────────────────────────────────────────────
SQL_TOTAL_PATENTS = "SELECT COUNT(*) AS n FROM patents"

SQL_TOP_INVENTORS = """
    SELECT
        i.name,
        i.country,
        COUNT(DISTINCT pi.patent_id) AS patents
    FROM inventors i
    JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
    GROUP BY i.inventor_id
    ORDER BY patents DESC
    LIMIT 20
"""

SQL_TOP_COMPANIES = """
    SELECT
        c.name AS company,
        c.country,
        COUNT(DISTINCT pc.patent_id) AS patents
    FROM companies c
    JOIN patent_companies pc ON c.company_id = pc.company_id
    GROUP BY c.company_id
    ORDER BY patents DESC
    LIMIT 20
"""

SQL_COUNTRIES = """
    SELECT
        i.country,
        COUNT(DISTINCT pi.patent_id) AS patents,
        ROUND(
            COUNT(DISTINCT pi.patent_id) * 100.0 /
            (SELECT COUNT(*) FROM patent_inventors), 2
        ) AS share_pct
    FROM inventors i
    JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
    WHERE i.country != 'UNKNOWN'
    GROUP BY i.country
    ORDER BY patents DESC
    LIMIT 20
"""

SQL_YEARLY = """
    SELECT year, COUNT(*) AS patents
    FROM patents
    WHERE year IS NOT NULL
    GROUP BY year
    ORDER BY year
"""

SQL_RANKED = """
    WITH inventor_counts AS (
        SELECT
            i.inventor_id,
            i.name,
            i.country,
            COUNT(DISTINCT pi.patent_id) AS patent_count
        FROM inventors i
        JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
        GROUP BY i.inventor_id
    )
    SELECT
        RANK() OVER (ORDER BY patent_count DESC) AS rank,
        name,
        country,
        patent_count,
        ROUND(patent_count * 100.0 / SUM(patent_count) OVER (), 4) AS pct_of_total
    FROM inventor_counts
    ORDER BY rank
    LIMIT 50
"""


# ── Console report ────────────────────────────────────────────
def print_console_report(total, inventors_df, companies_df, countries_df):
    W = 55
    print("\n" + "=" * W)
    print("  GLOBAL PATENT INTELLIGENCE — REPORT")
    print("=" * W)
    print(f"\n  Total Patents: {total:,}")

    print(f"\n{'─'*W}")
    print("  TOP 10 INVENTORS")
    print(f"{'─'*W}")
    for rank, row in enumerate(inventors_df.head(10).itertuples(), start=1):
        print(f"  {rank:>2}. {row.name:<30} [{row.country}]  {row.patents:,} patents")

    print(f"\n{'─'*W}")
    print("  TOP 10 COMPANIES")
    print(f"{'─'*W}")
    for rank, row in enumerate(companies_df.head(10).itertuples(), start=1):
        print(f"  {rank:>2}. {row.company:<30} [{row.country}]  {row.patents:,} patents")

    print(f"\n{'─'*W}")
    print("  TOP 10 COUNTRIES")
    print(f"{'─'*W}")
    for rank, row in enumerate(countries_df.head(10).itertuples(), start=1):
        print(f"  {rank:>2}. {row.country:<8}  {row.patents:>6,} patents  ({row.share_pct:.1f}%)")

    print(f"\n{'='*W}\n")


# ── CSV exports ───────────────────────────────────────────────
def save_csvs(inventors_df, companies_df, countries_df, yearly_df, ranked_df):
    inventors_df.to_csv(os.path.join(REPORT_DIR, "top_inventors.csv"),   index=False)
    companies_df.to_csv(os.path.join(REPORT_DIR, "top_companies.csv"),   index=False)
    countries_df.to_csv(os.path.join(REPORT_DIR, "country_trends.csv"),  index=False)
    yearly_df.to_csv(   os.path.join(REPORT_DIR, "yearly_trends.csv"),   index=False)
    ranked_df.to_csv(   os.path.join(REPORT_DIR, "ranked_inventors.csv"),index=False)
    print("  ✓ CSV reports saved:")
    for name in ["top_inventors", "top_companies", "country_trends",
                 "yearly_trends", "ranked_inventors"]:
        print(f"      reports/{name}.csv")


# ── JSON report ───────────────────────────────────────────────
def save_json(total, inventors_df, companies_df, countries_df, yearly_df):
    report = {
        "total_patents": int(total),
        "top_inventors": [
            {"rank": i + 1, "name": row.name, "country": row.country,
             "patents": int(row.patents)}
            for i, row in enumerate(inventors_df.head(10).itertuples())
        ],
        "top_companies": [
            {"rank": i + 1, "company": row.company, "country": row.country,
             "patents": int(row.patents)}
            for i, row in enumerate(companies_df.head(10).itertuples())
        ],
        "top_countries": [
            {"rank": i + 1, "country": row.country, "patents": int(row.patents),
             "share_pct": float(row.share_pct)}
            for i, row in enumerate(countries_df.head(10).itertuples())
        ],
        "yearly_trends": [
            {"year": int(row.year), "patents": int(row.patents)}
            for row in yearly_df.itertuples()
        ],
    }
    path = os.path.join(REPORT_DIR, "summary_report.json")
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  ✓ JSON report saved: reports/summary_report.json")
    return report


# ── Main ──────────────────────────────────────────────────────
def main():
    conn = connect()

    total        = query(conn, SQL_TOTAL_PATENTS)["n"].iloc[0]
    inventors_df = query(conn, SQL_TOP_INVENTORS)
    companies_df = query(conn, SQL_TOP_COMPANIES)
    countries_df = query(conn, SQL_COUNTRIES)
    yearly_df    = query(conn, SQL_YEARLY)
    ranked_df    = query(conn, SQL_RANKED)

    conn.close()

    print_console_report(total, inventors_df, companies_df, countries_df)
    save_csvs(inventors_df, companies_df, countries_df, yearly_df, ranked_df)
    save_json(total, inventors_df, companies_df, countries_df, yearly_df)

    print("\n✅  All reports generated.\n")


if __name__ == "__main__":
    main()
