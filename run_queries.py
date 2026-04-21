"""
run_queries.py
--------------
Executes all 7 analytical SQL queries against patents.db and saves
the results to data/results/ as CSV files.

Usage:
    python scripts/run_queries.py
"""

import os
import sqlite3
import pandas as pd

DB_PATH     = os.path.join(os.path.dirname(__file__), "..", "patents.db")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "results")


def get_connection() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}\n"
            "Run  python scripts/load_db.py  first."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def run_query(conn: sqlite3.Connection, sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn)


def save_result(df: pd.DataFrame, filename: str) -> None:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  Saved {path}  ({len(df):,} rows)")


# ── SQL strings ────────────────────────────────────────────────────────────────

Q1_TOP_INVENTORS = """
SELECT
    i.inventor_id,
    i.name,
    i.country,
    COUNT(DISTINCT pr.patent_id) AS patent_count
FROM inventors i
JOIN patent_relationships pr ON i.inventor_id = pr.inventor_id
GROUP BY i.inventor_id, i.name, i.country
ORDER BY patent_count DESC
LIMIT 20
"""

Q2_TOP_COMPANIES = """
SELECT
    c.company_id,
    c.name,
    COUNT(DISTINCT pr.patent_id) AS patent_count
FROM companies c
JOIN patent_relationships pr ON c.company_id = pr.company_id
GROUP BY c.company_id, c.name
ORDER BY patent_count DESC
LIMIT 20
"""

Q3_COUNTRIES = """
SELECT
    i.country,
    COUNT(DISTINCT pr.patent_id) AS patent_count,
    ROUND(
        COUNT(DISTINCT pr.patent_id) * 100.0 /
        (SELECT COUNT(DISTINCT patent_id) FROM patent_relationships), 2
    ) AS share_pct
FROM inventors i
JOIN patent_relationships pr ON i.inventor_id = pr.inventor_id
WHERE i.country IS NOT NULL
GROUP BY i.country
ORDER BY patent_count DESC
LIMIT 20
"""

Q4_TRENDS = """
SELECT year, COUNT(*) AS patent_count
FROM patents
WHERE year IS NOT NULL
GROUP BY year
ORDER BY year ASC
"""

Q5_JOIN = """
SELECT
    p.patent_id,
    p.title,
    p.year,
    p.filing_date,
    i.name        AS inventor_name,
    i.country     AS inventor_country,
    c.name        AS company_name
FROM patents p
JOIN patent_relationships pr ON p.patent_id = pr.patent_id
JOIN inventors i             ON pr.inventor_id = i.inventor_id
LEFT JOIN companies c        ON pr.company_id = c.company_id
ORDER BY p.year DESC, p.patent_id
LIMIT 500
"""

Q6_CTE = """
WITH inventor_patent_counts AS (
    SELECT
        i.inventor_id, i.name, i.country,
        COUNT(DISTINCT pr.patent_id) AS patent_count
    FROM inventors i
    JOIN patent_relationships pr ON i.inventor_id = pr.inventor_id
    WHERE i.country IS NOT NULL
    GROUP BY i.inventor_id, i.name, i.country
),
country_max AS (
    SELECT country, MAX(patent_count) AS max_patents
    FROM inventor_patent_counts
    GROUP BY country
)
SELECT
    ipc.country,
    ipc.name     AS top_inventor,
    ipc.patent_count
FROM inventor_patent_counts ipc
JOIN country_max cm
  ON ipc.country = cm.country AND ipc.patent_count = cm.max_patents
ORDER BY ipc.patent_count DESC
LIMIT 30
"""

Q7_RANKING = """
SELECT
    inventor_id, name, country, patent_count,
    RANK()       OVER (ORDER BY patent_count DESC) AS global_rank,
    DENSE_RANK() OVER (ORDER BY patent_count DESC) AS dense_rank,
    RANK()       OVER (PARTITION BY country ORDER BY patent_count DESC) AS country_rank,
    ROUND(patent_count * 100.0 / SUM(patent_count) OVER (), 4) AS share_pct
FROM (
    SELECT
        i.inventor_id, i.name, i.country,
        COUNT(DISTINCT pr.patent_id) AS patent_count
    FROM inventors i
    JOIN patent_relationships pr ON i.inventor_id = pr.inventor_id
    GROUP BY i.inventor_id, i.name, i.country
) sub
ORDER BY global_rank
LIMIT 50
"""


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    conn = get_connection()

    queries = [
        (Q1_TOP_INVENTORS, "q1_top_inventors.csv",  "Q1 – Top Inventors"),
        (Q2_TOP_COMPANIES, "q2_top_companies.csv",  "Q2 – Top Companies"),
        (Q3_COUNTRIES,     "q3_countries.csv",       "Q3 – Countries"),
        (Q4_TRENDS,        "q4_trends_over_time.csv","Q4 – Trends Over Time"),
        (Q5_JOIN,          "q5_join_result.csv",     "Q5 – JOIN Query"),
        (Q6_CTE,           "q6_cte_result.csv",      "Q6 – CTE Query"),
        (Q7_RANKING,       "q7_ranking.csv",          "Q7 – Ranking Query"),
    ]

    for sql, filename, label in queries:
        print(f"\n=== {label} ===")
        df = run_query(conn, sql)
        save_result(df, filename)

    conn.close()
    print("\n✅  All queries complete.")
    print("Next step:  python scripts/generate_reports.py")


if __name__ == "__main__":
    main()
