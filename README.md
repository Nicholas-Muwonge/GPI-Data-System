# NICHOLAS' Global Patent Intelligence Data Pipeline

A full end to end data engineering pipeline that collects, cleans, stores and analyzes
real world patent data from the USPTO PatentsView dataset.

---

## Project Structure

```
patent_pipeline/
├── ingest.py             # Download real data from USPTO PatentsView API
├── clean.py              # Clean and validate raw data with pandas
├── load_db.py            # Load clean data into SQLite database
├── report.py             # Generate console, CSV, and JSON reports
├── visualize.py          # Create charts (bonus)
├── dashboard.py             # Interactive Streamlit dashboard
├── run_pipeline.py          # Run entire pipeline in one command
├── requirements.txt
├── sql/
│   ├── schema.sql           # Database schema (DDL)
│   └── queries.sql          # All 7 required analytical queries
├── data/
│   ├── raw/                 # Downloaded/generated TSV files
│   └── clean/               # Cleaned CSV files
└── reports/                 # Output reports and charts
```

---

## Quickstart (Reproducible)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd patent_pipeline

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline 
python run_pipeline.py

# 4. Launch interactive dashboard
streamlit run dashboard.py
```

## Database Schema

```sql
patents          (patent_id, title, abstract, filing_date, year)
inventors        (inventor_id, name, country)
companies        (company_id, name, country)
patent_inventors (patent_id, inventor_id)   
patent_companies (patent_id, company_id)    
```

---

## SQL Queries (Q1–Q7)

All queries are in `sql/queries.sql`:

| # | Query | Technique |
|---|-------|-----------|
| Q1 | Top inventors by patent count | GROUP BY + COUNT |
| Q2 | Top companies by patent portfolio | JOIN + GROUP BY |
| Q3 | Country patent share | Subquery + ROUND |
| Q4 | Yearly patent trends | GROUP BY year |
| Q5 | Patents with inventors & companies | Multi-table JOIN |
| Q6 | Active inventors per country per year | CTE (WITH) |
| Q7 | Rank inventors globally and by country | RANK() + DENSE_RANK() window functions |

---

## Reports Generated

- **Console** — formatted terminal output with totals and top-10 lists
- **`reports/top_inventors.csv`** — top 20 inventors
- **`reports/top_companies.csv`** — top 20 companies  
- **`reports/country_trends.csv`** — country patent share
- **`reports/yearly_trends.csv`** — year-by-year counts
- **`reports/ranked_inventors.csv`** — window function ranking
- **`reports/summary_report.json`** — structured JSON summary

### Bonus: Charts
- `reports/charts/chart_yearly_trend.png`
- `reports/charts/chart_top_inventors.png`
- `reports/charts/chart_top_companies.png`
- `reports/charts/chart_country_share.png`
- `reports/charts/chart_country_trend.png`

---

## Data Source

**USPTO PatentsView — Granted Patent Disambiguated Data**  
https://data.uspto.gov/bulkdata/datasets/pvgpatdis

Files used:
- `g_patent.tsv` — core patent records
- `g_inventor_disambiguated.tsv` — disambiguated inventors
- `g_assignee_disambiguated.tsv` — disambiguated assignees (companies)
- `g_patent_inventor.tsv` — patent ↔ inventor links
- `g_patent_assignee.tsv` — patent ↔ assignee links

---

## Technologies Used

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Scripting and orchestration |
| pandas | Data cleaning and transformation |
| SQLite3 | Relational database storage |
| SQL | Analytical queries (JOINs, CTEs, window functions) |
| matplotlib | Data visualizations |
| Streamlit | Interactive dashboard |
| GitHub | Version control and reproducibility |
