"""
clean_data.py
-------------
Reads raw PatentsView TSV files, cleans and normalises them,
and writes clean CSVs to data/clean/.

Usage:
    python scripts/clean_data.py

Expected input files in data/raw/  (zipped or unzipped):
    g_patent.tsv
    g_inventor_disambiguated.tsv
    g_assignee_disambiguated.tsv
    g_patent_inventor.tsv
    g_patent_assignee.tsv
"""

import os
import zipfile
import glob
import pandas as pd

RAW_DIR   = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clean")

# ── helpers ────────────────────────────────────────────────────────────────────

def unzip_if_needed(raw_dir: str) -> None:
    """Unzip any .zip files in raw_dir that haven't been extracted yet."""
    for zpath in glob.glob(os.path.join(raw_dir, "*.zip")):
        tsv_name = os.path.basename(zpath).replace(".zip", "")
        if not os.path.exists(os.path.join(raw_dir, tsv_name)):
            print(f"  Unzipping {os.path.basename(zpath)} ...")
            with zipfile.ZipFile(zpath, "r") as z:
                z.extractall(raw_dir)


def load_tsv(raw_dir: str, filename: str, usecols: list[str] | None = None) -> pd.DataFrame:
    """Load a TSV from raw_dir, selecting only needed columns."""
    path = os.path.join(raw_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing file: {path}\n"
            "Run  python scripts/download_data.py  first, or download manually."
        )
    print(f"  Loading {filename} ...")
    return pd.read_csv(
        path,
        sep="\t",
        low_memory=False,
        usecols=usecols,
        dtype=str,          # read everything as string; we'll cast later
    )


def save_clean(df: pd.DataFrame, name: str) -> None:
    os.makedirs(CLEAN_DIR, exist_ok=True)
    out = os.path.join(CLEAN_DIR, name)
    df.to_csv(out, index=False)
    print(f"  Saved {out}  ({len(df):,} rows)")


# ── cleaning functions ─────────────────────────────────────────────────────────

def clean_patents(raw_dir: str) -> pd.DataFrame:
    cols = ["patent_id", "patent_title", "patent_abstract", "filing_date"]
    df = load_tsv(raw_dir, "g_patent.tsv", usecols=cols)

    df = df.rename(columns={"patent_title": "title", "patent_abstract": "abstract"})

    # Drop rows with no patent_id or title
    df = df.dropna(subset=["patent_id", "title"])
    df = df.drop_duplicates(subset="patent_id")

    # Normalise titles
    df["title"] = df["title"].str.strip().str.title()

    # Parse dates
    df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")
    df["year"]        = df["filing_date"].dt.year.astype("Int64")

    # Drop rows where filing_date couldn't be parsed
    df = df.dropna(subset=["filing_date"])

    df["filing_date"] = df["filing_date"].dt.strftime("%Y-%m-%d")

    # Truncate very long abstracts (SQLite TEXT is fine, but keeps things tidy)
    df["abstract"] = df["abstract"].str.slice(0, 2000)

    df = df[["patent_id", "title", "abstract", "filing_date", "year"]]
    return df.reset_index(drop=True)


def clean_inventors(raw_dir: str) -> pd.DataFrame:
    cols = ["disambig_inventor_id", "disambig_inventor_name_first",
            "disambig_inventor_name_last", "inventor_country"]
    df = load_tsv(raw_dir, "g_inventor_disambiguated.tsv", usecols=cols)

    df = df.rename(columns={
        "disambig_inventor_id":         "inventor_id",
        "disambig_inventor_name_first": "first_name",
        "disambig_inventor_name_last":  "last_name",
        "inventor_country":             "country",
    })

    df = df.dropna(subset=["inventor_id"])
    df = df.drop_duplicates(subset="inventor_id")

    # Build full name
    df["first_name"] = df["first_name"].fillna("").str.strip()
    df["last_name"]  = df["last_name"].fillna("").str.strip()
    df["name"]       = (df["first_name"] + " " + df["last_name"]).str.strip()
    df["name"]       = df["name"].replace("", pd.NA)
    df = df.dropna(subset=["name"])

    # Normalise country
    df["country"] = df["country"].str.upper().str.strip()
    df["country"] = df["country"].replace({"": pd.NA})

    df = df[["inventor_id", "name", "country"]]
    return df.reset_index(drop=True)


def clean_companies(raw_dir: str) -> pd.DataFrame:
    cols = ["disambig_assignee_id", "disambig_assignee_organization"]
    df = load_tsv(raw_dir, "g_assignee_disambiguated.tsv", usecols=cols)

    df = df.rename(columns={
        "disambig_assignee_id":           "company_id",
        "disambig_assignee_organization": "name",
    })

    df = df.dropna(subset=["company_id", "name"])
    df = df.drop_duplicates(subset="company_id")

    df["name"] = df["name"].str.strip()
    df = df[df["name"] != ""]

    df = df[["company_id", "name"]]
    return df.reset_index(drop=True)


def clean_patent_inventors(raw_dir: str) -> pd.DataFrame:
    cols = ["patent_id", "disambig_inventor_id"]
    df = load_tsv(raw_dir, "g_patent_inventor.tsv", usecols=cols)
    df = df.rename(columns={"disambig_inventor_id": "inventor_id"})
    df = df.dropna()
    df = df.drop_duplicates()
    return df.reset_index(drop=True)


def clean_patent_assignees(raw_dir: str) -> pd.DataFrame:
    cols = ["patent_id", "disambig_assignee_id"]
    df = load_tsv(raw_dir, "g_patent_assignee.tsv", usecols=cols)
    df = df.rename(columns={"disambig_assignee_id": "company_id"})
    df = df.dropna()
    df = df.drop_duplicates()
    return df.reset_index(drop=True)


def build_relationships(pat_inv: pd.DataFrame, pat_ass: pd.DataFrame) -> pd.DataFrame:
    """
    Merge patent–inventor and patent–assignee links into one relationships table.
    A patent may have multiple inventors and multiple assignees; we create
    a row for every (patent_id, inventor_id, company_id) combination.
    Where a patent has no assignee, company_id will be NULL.
    """
    df = pat_inv.merge(pat_ass, on="patent_id", how="left")
    df = df.drop_duplicates()
    return df.reset_index(drop=True)


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Step 1: Unzip raw files ===")
    unzip_if_needed(RAW_DIR)

    print("\n=== Step 2: Clean patents ===")
    patents = clean_patents(RAW_DIR)
    save_clean(patents, "clean_patents.csv")

    print("\n=== Step 3: Clean inventors ===")
    inventors = clean_inventors(RAW_DIR)
    save_clean(inventors, "clean_inventors.csv")

    print("\n=== Step 4: Clean companies ===")
    companies = clean_companies(RAW_DIR)
    save_clean(companies, "clean_companies.csv")

    print("\n=== Step 5: Clean relationship tables ===")
    pat_inv = clean_patent_inventors(RAW_DIR)
    pat_ass = clean_patent_assignees(RAW_DIR)
    relationships = build_relationships(pat_inv, pat_ass)
    save_clean(relationships, "clean_relationships.csv")

    print("\n✅  Cleaning complete.")
    print("Next step:  python scripts/load_db.py")


if __name__ == "__main__":
    main()
