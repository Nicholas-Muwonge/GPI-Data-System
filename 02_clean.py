"""
02_clean.py — Clean and validate raw PatentsView TSV files with pandas
Outputs clean CSVs to data/clean/ for loading into the database.
"""

import os
import pandas as pd

RAW_DIR   = os.path.join(os.path.dirname(__file__), "data", "raw")
CLEAN_DIR = os.path.join(os.path.dirname(__file__), "data", "clean")
os.makedirs(CLEAN_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────
def load_tsv(filename: str, usecols: list[str]) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing raw file: {path}\n"
            "Run 00_sample_data.py (sample) or 01_ingest.py (real data) first."
        )
    df = pd.read_csv(path, sep="\t", usecols=usecols,
                     dtype=str, low_memory=False)
    print(f"  Loaded  {filename:<45} {len(df):>8,} rows")
    return df


def report_quality(label: str, before: int, after: int):
    dropped = before - after
    pct = dropped / before * 100 if before else 0
    print(f"    {label}: {before:,} → {after:,}  (dropped {dropped:,} / {pct:.1f}%)")


# ── 1. Patents ────────────────────────────────────────────────
def clean_patents() -> pd.DataFrame:
    print("\n[1/5] Cleaning patents …")
    cols = ["patent_id", "title", "abstract", "date"]
    df = load_tsv("g_patent.tsv", cols)

    before = len(df)

    # Rename date column
    df = df.rename(columns={"date": "filing_date"})

    # Drop rows with no patent_id or title
    df = df.dropna(subset=["patent_id", "title"])

    # Parse filing date; coerce bad values to NaT
    df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")
    df = df.dropna(subset=["filing_date"])

    # Extract year
    df["year"] = df["filing_date"].dt.year.astype(int)

    # Keep only plausible years
    df = df[(df["year"] >= 1976) & (df["year"] <= 2030)]

    # Clean text fields
    df["title"]    = df["title"].str.strip().str.replace(r"\s+", " ", regex=True)
    df["abstract"] = (
        df["abstract"]
        .fillna("")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    # Deduplicate
    df = df.drop_duplicates(subset="patent_id")

    # Format date as string for storage
    df["filing_date"] = df["filing_date"].dt.strftime("%Y-%m-%d")

    report_quality("patents", before, len(df))

    out = df[["patent_id", "title", "abstract", "filing_date", "year"]]
    out.to_csv(os.path.join(CLEAN_DIR, "clean_patents.csv"), index=False)
    print(f"    ✓ Saved clean_patents.csv")
    return out


# ── 2. Inventors ──────────────────────────────────────────────
def clean_inventors() -> pd.DataFrame:
    print("\n[2/5] Cleaning inventors …")
    # Support both real PatentsView (has disambig_inventor_id) and sample data
    import pandas as _pd
    _probe = _pd.read_csv(
        os.path.join(RAW_DIR, "g_inventor_disambiguated.tsv"),
        sep="\t", nrows=0,
    )
    has_disambig = "disambig_inventor_id" in _probe.columns
    cols = (["inventor_id", "disambig_inventor_id", "name_first", "name_last", "country"]
            if has_disambig else
            ["inventor_id", "name_first", "name_last", "country"])
    df = load_tsv("g_inventor_disambiguated.tsv", cols)

    before = len(df)

    # Use disambig id as our canonical inventor_id where available
    if "disambig_inventor_id" in df.columns:
        df["inventor_id"] = df["disambig_inventor_id"].fillna(df["inventor_id"])

    # Build full name
    df["name_first"] = df["name_first"].fillna("").str.strip()
    df["name_last"]  = df["name_last"].fillna("").str.strip()
    df["name"]       = (df["name_first"] + " " + df["name_last"]).str.strip()

    # Drop if name is empty
    df = df[df["name"].str.len() > 0]

    # Standardise country codes to uppercase 2-letter ISO
    df["country"] = (
        df["country"]
        .fillna("UNKNOWN")
        .str.strip()
        .str.upper()
        .str[:2]
    )
    df.loc[df["country"] == "", "country"] = "UNKNOWN"

    df = df.drop_duplicates(subset="inventor_id")

    report_quality("inventors", before, len(df))

    out = df[["inventor_id", "name", "country"]]
    out.to_csv(os.path.join(CLEAN_DIR, "clean_inventors.csv"), index=False)
    print(f"    ✓ Saved clean_inventors.csv")
    return out


# ── 3. Companies (Assignees) ──────────────────────────────────
def clean_companies() -> pd.DataFrame:
    print("\n[3/5] Cleaning companies …")
    import pandas as _pd2
    _probe2 = _pd2.read_csv(
        os.path.join(RAW_DIR, "g_assignee_disambiguated.tsv"),
        sep="\t", nrows=0,
    )
    has_d2 = "disambig_assignee_id" in _probe2.columns
    cols = (["assignee_id", "disambig_assignee_id", "organization", "country"]
            if has_d2 else
            ["assignee_id", "organization", "country"])
    df = load_tsv("g_assignee_disambiguated.tsv", cols)

    before = len(df)

    df["company_id"] = (df["disambig_assignee_id"].fillna(df["assignee_id"])
                        if "disambig_assignee_id" in df.columns
                        else df["assignee_id"])
    df["name"]       = df["organization"].fillna("").str.strip()
    df             = df[df["name"].str.len() > 0]

    df["country"] = (
        df["country"]
        .fillna("UNKNOWN")
        .str.strip()
        .str.upper()
        .str[:2]
    )
    df.loc[df["country"] == "", "country"] = "UNKNOWN"

    df = df.drop_duplicates(subset="company_id")

    report_quality("companies", before, len(df))

    out = df[["company_id", "name", "country"]]
    out.to_csv(os.path.join(CLEAN_DIR, "clean_companies.csv"), index=False)
    print(f"    ✓ Saved clean_companies.csv")
    return out


# ── 4. Patent-Inventor relationships ─────────────────────────
def clean_patent_inventors(valid_patents: set, valid_inventors: set) -> pd.DataFrame:
    print("\n[4/5] Cleaning patent-inventor relationships …")
    cols = ["patent_id", "inventor_id", "disambig_inventor_id", "sequence"]
    df = load_tsv("g_patent_inventor.tsv", cols)

    before = len(df)

    df["inventor_id"] = df["disambig_inventor_id"].fillna(df["inventor_id"])
    df = df.dropna(subset=["patent_id", "inventor_id"])

    # Keep only rows where both sides exist in clean tables
    df = df[df["patent_id"].isin(valid_patents) & df["inventor_id"].isin(valid_inventors)]
    df = df.drop_duplicates(subset=["patent_id", "inventor_id"])

    report_quality("patent-inventor links", before, len(df))

    out = df[["patent_id", "inventor_id"]]
    out.to_csv(os.path.join(CLEAN_DIR, "clean_patent_inventors.csv"), index=False)
    print(f"    ✓ Saved clean_patent_inventors.csv")
    return out


# ── 5. Patent-Assignee relationships ─────────────────────────
def clean_patent_assignees(valid_patents: set, valid_companies: set) -> pd.DataFrame:
    print("\n[5/5] Cleaning patent-assignee relationships …")
    import pandas as _pd3
    _probe3 = _pd3.read_csv(
        os.path.join(RAW_DIR, "g_patent_assignee.tsv"), sep="\t", nrows=0,
    )
    has_d3 = "disambig_assignee_id" in _probe3.columns
    cols = (["patent_id", "assignee_id", "disambig_assignee_id", "sequence"]
            if has_d3 else ["patent_id", "assignee_id", "sequence"])
    df = load_tsv("g_patent_assignee.tsv", cols)

    before = len(df)

    df["company_id"] = (df["disambig_assignee_id"].fillna(df["assignee_id"])
                        if "disambig_assignee_id" in df.columns
                        else df["assignee_id"])
    df = df.dropna(subset=["patent_id", "company_id"])

    df = df[df["patent_id"].isin(valid_patents) & df["company_id"].isin(valid_companies)]
    df = df.drop_duplicates(subset=["patent_id", "company_id"])

    report_quality("patent-company links", before, len(df))

    out = df[["patent_id", "company_id"]]
    out.to_csv(os.path.join(CLEAN_DIR, "clean_patent_assignees.csv"), index=False)
    print(f"    ✓ Saved clean_patent_assignees.csv")
    return out


# ── Main ──────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 55)
    print("  PatentsView Data Cleaning")
    print("=" * 55)

    patents   = clean_patents()
    inventors = clean_inventors()
    companies = clean_companies()

    valid_patents   = set(patents["patent_id"])
    valid_inventors = set(inventors["inventor_id"])
    valid_companies = set(companies["company_id"])

    clean_patent_inventors(valid_patents, valid_inventors)
    clean_patent_assignees(valid_patents, valid_companies)

    print(f"\n✅  Cleaning complete.")
    print(f"   Output folder: {CLEAN_DIR}")
    print(f"   Patents:   {len(patents):,}")
    print(f"   Inventors: {len(inventors):,}")
    print(f"   Companies: {len(companies):,}\n")


if __name__ == "__main__":
    main()
