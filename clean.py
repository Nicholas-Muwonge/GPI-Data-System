import os, io, sys, zipfile, requests, pandas as pd

CLEAN_DIR  = os.path.join(os.path.dirname(__file__), "data", "clean")
RAW_DIR    = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(CLEAN_DIR, exist_ok=True)

USE_SAMPLE = "--sample" in sys.argv

BASE_URL   = "https://data.uspto.gov/bulkdata/datasets/pvgpatdis"
DATE_FROM  = "2020-01-01"
DATE_TO    = "2023-12-31"

FILE_TYPES = [
    "g_patent",
    "g_inventor_disambiguated",
    "g_assignee_disambiguated",
    "g_patent_inventor",
    "g_patent_assignee",
]


def fetch_remote(file_type: str, usecols: list) -> pd.DataFrame:
    """
    USPTO bulk data flow:
      1. GET /pvgpatdis?fileType=...  → JSON listing with a 'files' array
      2. Each entry has a 'downloadUrl' (the actual zip)
      3. GET downloadUrl → zip containing a .tsv
    """
    params = {
        "fileType":        file_type,
        "fileDataFromDate": DATE_FROM,
        "fileDataToDate":   DATE_TO,
    }

    print(f"  [{file_type}] Fetching file listing ...", flush=True)
    listing_resp = requests.get(BASE_URL, params=params, timeout=60)
    listing_resp.raise_for_status()

    try:
        listing = listing_resp.json()
    except Exception:
        raise RuntimeError(
            f"USPTO did not return JSON for {file_type}.\n"
            f"Response (first 500 chars): {listing_resp.text[:500]}"
        )

    files = []
    if "data" in listing:
        for entry in listing["data"]:
            files.extend(entry.get("files", []))
    elif "files" in listing:
        files = listing["files"]

    if not files:
        raise RuntimeError(
            f"No files found in USPTO listing for {file_type}.\n"
            f"Full response: {listing}"
        )

    download_url = files[0]["downloadUrl"]
    print(f"  [{file_type}] Downloading: {download_url}", flush=True)

    zip_resp = requests.get(download_url, timeout=300, stream=True)
    zip_resp.raise_for_status()

    content = zip_resp.content

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            tsv_name = next(f for f in zf.namelist() if f.endswith(".tsv"))
            with zf.open(tsv_name) as tsv:
                df = pd.read_csv(tsv, sep="\t",
                                 usecols=lambda c: c in usecols,
                                 dtype=str, low_memory=False)
        print(f"  [{file_type}] {len(df):,} rows loaded")
        return df

    except zipfile.BadZipFile:
        print(f"  [{file_type}] Not a zip, trying plain TSV ...", flush=True)
        try:
            df = pd.read_csv(io.BytesIO(content), sep="\t",
                             usecols=lambda c: c in usecols,
                             dtype=str, low_memory=False,
                             compression="infer")
            print(f"  [{file_type}] {len(df):,} rows loaded")
            return df
        except Exception as e:
            raise RuntimeError(
                f"Could not parse response for {file_type} as zip or TSV.\n"
                f"First 300 bytes: {content[:300]}\nError: {e}"
            )


def load_local(file_type: str, usecols: list) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, file_type + ".tsv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing: {path}\nRun 00_sample_data.py first.")
    df = pd.read_csv(path, sep="\t", usecols=lambda c: c in usecols,
                     dtype=str, low_memory=False)
    print(f"  [{file_type}] {len(df):,} rows  (local)")
    return df


def load(file_type: str, usecols: list) -> pd.DataFrame:
    return load_local(file_type, usecols) if USE_SAMPLE else fetch_remote(file_type, usecols)


def report(label, before, after):
    dropped = before - after
    pct = dropped / before * 100 if before else 0
    print(f"    {label}: {before:,} -> {after:,}  (dropped {dropped:,} / {pct:.1f}%)")


def clean_patents(df):
    before = len(df)
    df = df.rename(columns={"date": "filing_date"})
    df = df.dropna(subset=["patent_id", "title"])
    df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")
    df = df.dropna(subset=["filing_date"])
    df["year"] = df["filing_date"].dt.year.astype(int)
    df = df[(df["year"] >= 1976) & (df["year"] <= 2030)]
    df["title"]    = df["title"].str.strip().str.replace(r"\s+", " ", regex=True)
    df["abstract"] = df["abstract"].fillna("").str.strip().str.replace(r"\s+", " ", regex=True)
    df = df.drop_duplicates(subset="patent_id")
    df["filing_date"] = df["filing_date"].dt.strftime("%Y-%m-%d")
    report("patents", before, len(df))
    return df[["patent_id", "title", "abstract", "filing_date", "year"]]

def clean_inventors(df):
    before = len(df)
    if "disambig_inventor_id" in df.columns:
        df["inventor_id"] = df["disambig_inventor_id"].fillna(df["inventor_id"])
    df["name_first"] = df["name_first"].fillna("").str.strip() if "name_first" in df.columns else ""
    df["name_last"]  = df["name_last"].fillna("").str.strip()  if "name_last"  in df.columns else ""
    df["name"]       = (df["name_first"] + " " + df["name_last"]).str.strip()
    df = df[df["name"].str.len() > 0]
    df["country"] = df["country"].fillna("UNKNOWN").str.strip().str.upper().str[:2]
    df.loc[df["country"] == "", "country"] = "UNKNOWN"
    df = df.drop_duplicates(subset="inventor_id")
    report("inventors", before, len(df))
    return df[["inventor_id", "name", "country"]]

def clean_companies(df):
    before = len(df)
    df["company_id"] = (df["disambig_assignee_id"].fillna(df["assignee_id"])
                        if "disambig_assignee_id" in df.columns else df["assignee_id"])
    df["name"] = df["organization"].fillna("").str.strip()
    df = df[df["name"].str.len() > 0]
    df["country"] = df["country"].fillna("UNKNOWN").str.strip().str.upper().str[:2]
    df.loc[df["country"] == "", "country"] = "UNKNOWN"
    df = df.drop_duplicates(subset="company_id")
    report("companies", before, len(df))
    return df[["company_id", "name", "country"]]

def clean_patent_inventors(df, valid_patents, valid_inventors):
    before = len(df)
    if "disambig_inventor_id" in df.columns:
        df["inventor_id"] = df["disambig_inventor_id"].fillna(df["inventor_id"])
    df = df.dropna(subset=["patent_id", "inventor_id"])
    df = df[df["patent_id"].isin(valid_patents) & df["inventor_id"].isin(valid_inventors)]
    df = df.drop_duplicates(subset=["patent_id", "inventor_id"])
    report("patent-inventor links", before, len(df))
    return df[["patent_id", "inventor_id"]]

def clean_patent_assignees(df, valid_patents, valid_companies):
    before = len(df)
    df["company_id"] = (df["disambig_assignee_id"].fillna(df["assignee_id"])
                        if "disambig_assignee_id" in df.columns else df["assignee_id"])
    df = df.dropna(subset=["patent_id", "company_id"])
    df = df[df["patent_id"].isin(valid_patents) & df["company_id"].isin(valid_companies)]
    df = df.drop_duplicates(subset=["patent_id", "company_id"])
    report("patent-company links", before, len(df))
    return df[["patent_id", "company_id"]]


def main():
    mode = "sample data" if USE_SAMPLE else f"USPTO live ({DATE_FROM} to {DATE_TO})"
    print("\n" + "=" * 55)
    print(f"  PatentsView Cleaning  [{mode}]")
    print("=" * 55 + "\n")

    print("[1/5] Patents")
    patents = clean_patents(load("g_patent",
        ["patent_id", "title", "abstract", "date"]))

    print("\n[2/5] Inventors")
    inventors = clean_inventors(load("g_inventor_disambiguated",
        ["inventor_id", "disambig_inventor_id", "name_first", "name_last", "country"]))

    print("\n[3/5] Companies")
    companies = clean_companies(load("g_assignee_disambiguated",
        ["assignee_id", "disambig_assignee_id", "organization", "country"]))

    vp = set(patents["patent_id"])
    vi = set(inventors["inventor_id"])
    vc = set(companies["company_id"])

    print("\n[4/5] Patent-Inventor links")
    patent_inventors = clean_patent_inventors(
        load("g_patent_inventor",
             ["patent_id", "inventor_id", "disambig_inventor_id", "sequence"]), vp, vi)

    print("\n[5/5] Patent-Company links")
    patent_companies = clean_patent_assignees(
        load("g_patent_assignee",
             ["patent_id", "assignee_id", "disambig_assignee_id", "sequence"]), vp, vc)

    print("\n  Saving clean CSVs ...")
    patents.to_csv(          os.path.join(CLEAN_DIR, "clean_patents.csv"),          index=False)
    inventors.to_csv(        os.path.join(CLEAN_DIR, "clean_inventors.csv"),        index=False)
    companies.to_csv(        os.path.join(CLEAN_DIR, "clean_companies.csv"),        index=False)
    patent_inventors.to_csv( os.path.join(CLEAN_DIR, "clean_patent_inventors.csv"), index=False)
    patent_companies.to_csv( os.path.join(CLEAN_DIR, "clean_patent_assignees.csv"), index=False)

    print(f"\n  Patents:{len(patents):,}  Inventors:{len(inventors):,}  Companies:{len(companies):,}")
    print(f"\nDone.\n")


if __name__ == "__main__":
    main()
