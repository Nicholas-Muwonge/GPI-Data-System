"""
01_ingest.py — Download PatentsView granted patent data
Downloads TSV files from USPTO PatentsView bulk data API.
Run this first before any other script.
"""

import os
import requests
import zipfile
import io
import time

# ── Configuration ─────────────────────────────────────────────
RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

BASE_URL = "https://data.uspto.gov/bulkdata/datasets/pvgpatdis"

# Files we need from PatentsView (zipped TSVs)
# We use a small recent slice to keep download size manageable.
# Adjust fileDataFromDate / fileDataToDate for a larger range.
FILES_TO_DOWNLOAD = [
    {
        "name": "g_patent.tsv.zip",
        "description": "Core patent records (id, title, abstract, date)",
        "params": {
            "fileDataFromDate": "2020-01-01",
            "fileDataToDate": "2023-12-31",
            "fileType": "g_patent",
        },
    },
    {
        "name": "g_inventor_disambiguated.tsv.zip",
        "description": "Disambiguated inventor records",
        "params": {
            "fileDataFromDate": "2020-01-01",
            "fileDataToDate": "2023-12-31",
            "fileType": "g_inventor_disambiguated",
        },
    },
    {
        "name": "g_assignee_disambiguated.tsv.zip",
        "description": "Disambiguated assignee (company) records",
        "params": {
            "fileDataFromDate": "2020-01-01",
            "fileDataToDate": "2023-12-31",
            "fileType": "g_assignee_disambiguated",
        },
    },
]


def download_file(name: str, description: str, params: dict) -> str:
    """Download a single PatentsView bulk file and extract the TSV."""
    tsv_name = name.replace(".zip", "")
    tsv_path = os.path.join(RAW_DIR, tsv_name)

    if os.path.exists(tsv_path):
        print(f"  ✓ Already exists: {tsv_name}  (skipping download)")
        return tsv_path

    print(f"  ↓ Downloading {description} …")
    try:
        resp = requests.get(BASE_URL, params=params, timeout=120, stream=True)
        resp.raise_for_status()

        # The API returns a zip — extract inline
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for member in zf.namelist():
                if member.endswith(".tsv"):
                    zf.extract(member, RAW_DIR)
                    extracted = os.path.join(RAW_DIR, member)
                    # Normalise the filename
                    if extracted != tsv_path:
                        os.rename(extracted, tsv_path)
                    break

        size_mb = os.path.getsize(tsv_path) / 1_048_576
        print(f"    ✓ Saved {tsv_name}  ({size_mb:.1f} MB)")
        time.sleep(1)  # polite pause between requests
    except Exception as exc:
        print(f"    ✗ Failed to download {name}: {exc}")
        print("      → Using sample data fallback (run 00_sample_data.py)")
        tsv_path = None

    return tsv_path


def main():
    print("\n" + "=" * 55)
    print("  PatentsView Data Ingestion")
    print("=" * 55)

    downloaded = []
    for file_cfg in FILES_TO_DOWNLOAD:
        path = download_file(**file_cfg)
        if path:
            downloaded.append(path)

    print(f"\n✅  Ingestion complete. {len(downloaded)}/{len(FILES_TO_DOWNLOAD)} files ready.")
    print(f"   Raw data folder: {RAW_DIR}\n")


if __name__ == "__main__":
    main()
