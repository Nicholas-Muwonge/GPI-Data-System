"""
load_db.py
----------
Creates (or recreates) the SQLite database and loads clean CSV files into it.

Usage:
    python scripts/load_db.py
"""

import os
import sqlite3
import pandas as pd

CLEAN_DIR  = os.path.join(os.path.dirname(__file__), "..", "data", "clean")
DB_PATH    = os.path.join(os.path.dirname(__file__), "..", "patents.db")
SCHEMA_SQL = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")

CHUNK_SIZE = 50_000  # rows per SQLite insert batch


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    print("  Applying schema ...")
    with open(SCHEMA_SQL, "r") as f:
        conn.executescript(f.read())
    conn.commit()


def load_csv_to_table(
    conn: sqlite3.Connection,
    csv_filename: str,
    table_name: str,
    dtype: dict | None = None,
) -> None:
    path = os.path.join(CLEAN_DIR, csv_filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing clean file: {path}\n"
            "Run  python scripts/clean_data.py  first."
        )

    print(f"  Loading {csv_filename} → {table_name} ...")
    total = 0
    for chunk in pd.read_csv(path, dtype=dtype, chunksize=CHUNK_SIZE):
        chunk.to_sql(table_name, conn, if_exists="append", index=False)
        total += len(chunk)

    print(f"    {total:,} rows inserted.")


def main():
    # Remove old DB so we start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"  Removed existing {DB_PATH}")

    conn = get_connection()

    print("\n=== Step 1: Create schema ===")
    apply_schema(conn)

    print("\n=== Step 2: Load patents ===")
    load_csv_to_table(conn, "clean_patents.csv", "patents",
                      dtype={"patent_id": str, "year": "Int64"})

    print("\n=== Step 3: Load inventors ===")
    load_csv_to_table(conn, "clean_inventors.csv", "inventors",
                      dtype={"inventor_id": str})

    print("\n=== Step 4: Load companies ===")
    load_csv_to_table(conn, "clean_companies.csv", "companies",
                      dtype={"company_id": str})

    print("\n=== Step 5: Load relationships ===")
    load_csv_to_table(conn, "clean_relationships.csv", "patent_relationships",
                      dtype={"patent_id": str, "inventor_id": str, "company_id": str})

    conn.close()

    size_mb = os.path.getsize(DB_PATH) / 1_048_576
    print(f"\n✅  Database ready: {DB_PATH}  ({size_mb:.1f} MB)")
    print("Next step:  python scripts/run_queries.py")


if __name__ == "__main__":
    main()
