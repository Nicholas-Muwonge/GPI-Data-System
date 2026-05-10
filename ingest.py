import os
import requests
import zipfile
import io
import time

RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

BASE_URL = "https://data.uspto.gov/bulkdata/datasets/pvgpatdis"

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
    tsv_name = name.replace(".zip", "")
    tsv_path = os.path.join(RAW_DIR, tsv_name)

    if os.path.exists(tsv_path):
        print(f"  ✓ Already exists: {tsv_name}  (skipping download)")
        return tsv_path

    print(f"  ↓ Downloading {description} …")
    try:
        resp = requests.get(BASE_URL, params=params, timeout=120, stream=True)
        resp.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            for member in zf.namelist():
                if member.endswith(".tsv"):
                    zf.extract(member, RAW_DIR)
                    extracted = os.path.join(RAW_DIR, member)
                    if extracted != tsv_path:
                        os.rename(extracted, tsv_path)
                    break

        size_mb = os.path.getsize(tsv_path) / 1_048_576
        print(f"    ✓ Saved {tsv_name}  ({size_mb:.1f} MB)")
        time.sleep(1)  
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
