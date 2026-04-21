"""
download_data.py
----------------
Downloads PatentsView Granted Patent Disambiguated Data files from USPTO.
Run this first before any other script.

Usage:
    python scripts/download_data.py [--year-from 2020] [--year-to 2024]
"""

import os
import sys
import argparse
import requests
from tqdm import tqdm

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

# PatentsView bulk data base URL
BASE_URL = "https://data.uspto.gov/bulkdata/datasets/pvgpatdis"

# The specific TSV files we need from the PatentsView dataset
FILES_NEEDED = [
    "g_patent.tsv.zip",
    "g_inventor_disambiguated.tsv.zip",
    "g_assignee_disambiguated.tsv.zip",
    "g_patent_inventor.tsv.zip",
    "g_patent_assignee.tsv.zip",
]


def get_file_list(year_from: int, year_to: int) -> list[dict]:
    """Fetch the list of available files from the USPTO API."""
    print(f"Fetching file list for {year_from}–{year_to} ...")
    params = {
        "fileDataFromDate": f"{year_from}-01-01",
        "fileDataToDate":   f"{year_to}-12-31",
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # The API returns a list of file metadata objects
    return data.get("files", data) if isinstance(data, dict) else data


def download_file(url: str, dest_path: str) -> None:
    """Stream-download a file with a progress bar."""
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=os.path.basename(dest_path)
    ) as bar:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            bar.update(len(chunk))


def main():
    parser = argparse.ArgumentParser(description="Download PatentsView data files.")
    parser.add_argument("--year-from", type=int, default=2020, help="Start year (default 2020)")
    parser.add_argument("--year-to",   type=int, default=2024, help="End year   (default 2024)")
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)

    try:
        file_list = get_file_list(args.year_from, args.year_to)
    except Exception as e:
        print(f"[ERROR] Could not fetch file list from USPTO API: {e}")
        print("Please download the files manually from:")
        print("  https://data.uspto.gov/bulkdata/datasets/pvgpatdis")
        print(f"Place the zip files in:  {RAW_DIR}/")
        sys.exit(1)

    # Match returned files against the ones we need
    to_download = []
    for file_info in file_list:
        name = file_info.get("fileName") or file_info.get("name", "")
        url  = file_info.get("downloadUrl") or file_info.get("url", "")
        if any(needed in name for needed in FILES_NEEDED):
            to_download.append((name, url))

    if not to_download:
        print("[WARN] No matching files found via API. Check USPTO portal manually.")
        sys.exit(1)

    print(f"\nDownloading {len(to_download)} file(s) to {RAW_DIR}/\n")
    for name, url in to_download:
        dest = os.path.join(RAW_DIR, name)
        if os.path.exists(dest):
            print(f"  [SKIP] {name} already exists.")
            continue
        print(f"  Downloading {name} ...")
        download_file(url, dest)

    print("\nAll downloads complete.")
    print("Next step:  python scripts/clean_data.py")


if __name__ == "__main__":
    main()
