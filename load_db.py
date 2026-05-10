import os
import sqlite3
import pandas as pd

CLEAN_DIR = os.path.join(os.path.dirname(__file__), "data", "clean")
DB_PATH   = os.path.join(os.path.dirname(__file__), "patent_pipeline.db")
SCHEMA    = os.path.join(os.path.dirname(__file__), "sql", "schema.sql")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def apply_schema(conn: sqlite3.Connection):
    with open(SCHEMA, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    print("  ✓ Schema applied")


def load_table(conn: sqlite3.Connection, csv_file: str, table: str,
               chunksize: int = 10_000):
    path = os.path.join(CLEAN_DIR, csv_file)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing clean file: {path}\nRun 02_clean.py first.")

    total = 0
    for chunk in pd.read_csv(path, dtype=str, chunksize=chunksize):
        chunk = chunk.where(pd.notnull(chunk), None)  
        chunk.to_sql(table, conn, if_exists="append", index=False,
                     method="multi")
        total += len(chunk)

    print(f"  ✓ {table:<25} {total:>8,} rows loaded")
    return total


def main():
    print("\n" + "=" * 55)
    print("  Loading Patent Database")
    print("=" * 55)

  
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"  Removed old database")

    conn = connect()
    apply_schema(conn)

    print("\n  Loading tables …")
    load_table(conn, "clean_patents.csv",          "patents")
    load_table(conn, "clean_inventors.csv",        "inventors")
    load_table(conn, "clean_companies.csv",        "companies")
    load_table(conn, "clean_patent_inventors.csv", "patent_inventors")
    load_table(conn, "clean_patent_assignees.csv", "patent_companies")

    conn.close()

    size_mb = os.path.getsize(DB_PATH) / 1_048_576
    print(f"\n✅  Database ready: {DB_PATH}  ({size_mb:.1f} MB)\n")


if __name__ == "__main__":
    main()
