# 🔬 Global Patent Intelligence Data Pipeline

A complete end-to-end data engineering pipeline that collects, cleans, stores and analyses real-world patent data from the USPTO PatentsView dataset.

---

## Project Structure

```
patent_pipeline/
├── scripts/
│   ├── download_data.py      # Download raw TSV files from USPTO
│   ├── clean_data.py         # Clean & normalise with pandas
│   ├── load_db.py            # Load clean data into SQLite
│   ├── run_queries.py        # Execute all 7 SQL queries
│   ├── generate_reports.py   # Console + CSV + JSON reports
│   └── visualise.py          # 4 matplotlib charts
├── sql/
│   ├── schema.sql            # Database schema (DDL)
│   └── queries.sql           # All 7 analytical SQL queries
├── data/
│   ├── raw/                  # Downloaded TSV files (git-ignored)
│   ├── clean/                # Cleaned CSVs (output of clean_data.py)
│   └── results/              # Query result CSVs (output of run_queries.py)
├── reports/
│   ├── top_inventors.csv
│   ├── top_companies.csv
│   ├── country_trends.csv
│   ├── report.json
│   └── charts/               # PNG chart files
├── dashboard.py              # Streamlit interactive dashboard
├── run_pipeline.py           # Master script — runs everything
└── requirements.txt
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Download the data

```bash
python scripts/download_data.py --year-from 2020 --year-to 2024
```

> If the automatic download fails, visit:  
> https://data.uspto.gov/bulkdata/datasets/pvgpatdis  
> Download these files into `data/raw/`:
> - `g_patent.tsv.zip`
> - `g_inventor_disambiguated.tsv.zip`
> - `g_assignee_disambiguated.tsv.zip`
> - `g_patent_inventor.tsv.zip`
> - `g_patent_assignee.tsv.zip`

### 3. Run the full pipeline

```bash
python run_pipeline.py
```

Or run each step individually:

```bash
python scripts/clean_data.py        # Step 1
python scripts/load_db.py           # Step 2
python scripts/run_queries.py       # Step 3
python scripts/generate_reports.py  # Step 4
python scripts/visualise.py         # Step 5 (charts)
```

### 4. Launch the dashboard

```bash
streamlit run dashboard.py
```

---

## Database Schema

```
patents               inventors             companies
──────────────        ─────────────         ──────────────
patent_id   PK        inventor_id  PK        company_id  PK
title                 name                   name
abstract              country
filing_date
year

patent_relationships
────────────────────────
patent_id    FK → patents
inventor_id  FK → inventors
company_id   FK → companies
```

---

## SQL Queries

| # | Query | Description |
|---|-------|-------------|
| Q1 | Top Inventors | Most patents per inventor |
| Q2 | Top Companies | Most patents per assignee |
| Q3 | Countries | Patent share by country |
| Q4 | Trends | Patents filed per year |
| Q5 | JOIN | Patents + inventors + companies |
| Q6 | CTE | Top inventor per country using `WITH` |
| Q7 | Ranking | Inventor ranking with window functions |

---

## Reports

| File | Type | Description |
|------|------|-------------|
| `reports/top_inventors.csv` | CSV | Top inventors |
| `reports/top_companies.csv` | CSV | Top companies |
| `reports/country_trends.csv` | CSV | Country breakdown |
| `reports/report.json` | JSON | Full summary report |
| `reports/charts/*.png` | PNG | 4 visualisation charts |

---

## Data Source

**PatentsView Granted Patent Disambiguated Data**  
https://data.uspto.gov/bulkdata/datasets/pvgpatdis  
Provided by the United States Patent and Trademark Office (USPTO).

---

## Reproducibility

Anyone can clone this repo and reproduce the full pipeline:

```bash
git clone <your-repo-url>
cd patent_pipeline
pip install -r requirements.txt
python scripts/download_data.py
python run_pipeline.py
```

Raw TSV files are excluded from git (`.gitignore`) due to size; all other outputs are fully reproducible from the source data.
