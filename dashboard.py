"""
dashboard.py
------------
Streamlit interactive dashboard for the Global Patent Intelligence Pipeline.

Usage:
    streamlit run dashboard.py
"""

import os
import json
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
DB_PATH     = os.path.join(BASE_DIR, "patents.db")
RESULTS_DIR = os.path.join(BASE_DIR, "data", "results")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global Patent Intelligence",
    page_icon="🔬",
    layout="wide",
)

# ── helpers ────────────────────────────────────────────────────────────────────

@st.cache_data
def load_result(filename: str) -> pd.DataFrame | None:
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


@st.cache_data
def load_json_report() -> dict | None:
    path = os.path.join(REPORTS_DIR, "report.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


@st.cache_data
def get_db_stats() -> dict:
    if not os.path.exists(DB_PATH):
        return {}
    conn = sqlite3.connect(DB_PATH)
    stats = {}
    for tbl in ("patents", "inventors", "companies", "patent_relationships"):
        try:
            stats[tbl] = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        except Exception:
            stats[tbl] = 0
    conn.close()
    return stats


def make_hbar(df: pd.DataFrame, x_col: str, y_col: str, title: str,
              color: str = "#1a6faf") -> plt.Figure:
    top = df.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(top[y_col].astype(str).str[:35], top[x_col], color=color, edgecolor="none")
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


# ── sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/patent.png", width=64)
st.sidebar.title("Patent Intelligence")
page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview", "🏆 Inventors", "🏢 Companies", "🌍 Countries", "📈 Trends", "🔍 Data Explorer"],
)

# pipeline status
st.sidebar.markdown("---")
st.sidebar.markdown("**Pipeline Status**")
db_ok      = os.path.exists(DB_PATH)
results_ok = os.path.exists(os.path.join(RESULTS_DIR, "q1_top_inventors.csv"))
st.sidebar.success("✅ Database ready"     if db_ok      else "❌ Run load_db.py")
st.sidebar.success("✅ Query results ready" if results_ok else "❌ Run run_queries.py")

# ── pages ──────────────────────────────────────────────────────────────────────

if page == "📊 Overview":
    st.title("🔬 Global Patent Intelligence Dashboard")
    st.markdown("Real-world patent data from **USPTO PatentsView** — cleaned, stored and analysed.")

    report = load_json_report()
    stats  = get_db_stats()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Patents",      f"{stats.get('patents', 0):,}")
    c2.metric("Total Inventors",    f"{stats.get('inventors', 0):,}")
    c3.metric("Total Companies",    f"{stats.get('companies', 0):,}")
    c4.metric("Relationship Rows",  f"{stats.get('patent_relationships', 0):,}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    inv = load_result("q1_top_inventors.csv")
    if inv is not None:
        with col1:
            st.subheader("Top 10 Inventors")
            st.pyplot(make_hbar(inv, "patent_count", "name", ""))

    comp = load_result("q2_top_companies.csv")
    if comp is not None:
        with col2:
            st.subheader("Top 10 Companies")
            st.pyplot(make_hbar(comp, "patent_count", "name", "", color="#2e7d32"))

    trends = load_result("q4_trends_over_time.csv")
    if trends is not None:
        st.subheader("Patent Filings Over Time")
        trends["year"] = trends["year"].astype(int)
        st.line_chart(trends.set_index("year")["patent_count"])


elif page == "🏆 Inventors":
    st.title("🏆 Top Inventors")
    df = load_result("q1_top_inventors.csv")
    if df is None:
        st.warning("No data yet. Run run_queries.py first.")
    else:
        top_n = st.slider("Show top N inventors", 5, 50, 20)
        st.pyplot(make_hbar(df.head(top_n), "patent_count", "name", f"Top {top_n} Inventors"))

        st.subheader("Ranking Table")
        ranking = load_result("q7_ranking.csv")
        if ranking is not None:
            st.dataframe(ranking, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode()
        st.download_button("Download CSV", csv, "top_inventors.csv", "text/csv")


elif page == "🏢 Companies":
    st.title("🏢 Top Companies (Assignees)")
    df = load_result("q2_top_companies.csv")
    if df is None:
        st.warning("No data yet. Run run_queries.py first.")
    else:
        top_n = st.slider("Show top N companies", 5, 50, 20)
        st.pyplot(make_hbar(df.head(top_n), "patent_count", "name",
                            f"Top {top_n} Companies", color="#2e7d32"))
        st.dataframe(df.head(top_n), use_container_width=True)
        csv = df.to_csv(index=False).encode()
        st.download_button("Download CSV", csv, "top_companies.csv", "text/csv")


elif page == "🌍 Countries":
    st.title("🌍 Patents by Country")
    df = load_result("q3_countries.csv")
    if df is None:
        st.warning("No data yet. Run run_queries.py first.")
    else:
        st.bar_chart(df.set_index("country")["patent_count"].head(20))
        st.subheader("Country Detail")
        st.dataframe(df, use_container_width=True)

        cte = load_result("q6_cte_result.csv")
        if cte is not None:
            st.subheader("Top Inventor per Country")
            st.dataframe(cte, use_container_width=True)


elif page == "📈 Trends":
    st.title("📈 Patent Trends Over Time")
    df = load_result("q4_trends_over_time.csv")
    if df is None:
        st.warning("No data yet. Run run_queries.py first.")
    else:
        df["year"] = df["year"].astype(int)
        if len(df) > 1:
            yr_min, yr_max = int(df["year"].min()), int(df["year"].max())
            y1, y2 = st.slider("Year range", yr_min, yr_max, (yr_min, yr_max))
            df = df[(df["year"] >= y1) & (df["year"] <= y2)]

        st.line_chart(df.set_index("year")["patent_count"])
        st.dataframe(df, use_container_width=True)


elif page == "🔍 Data Explorer":
    st.title("🔍 Data Explorer")
    if not os.path.exists(DB_PATH):
        st.error("Database not found. Run load_db.py first.")
    else:
        query = st.text_area(
            "Write a SQL query",
            value="SELECT * FROM patents LIMIT 20",
            height=120,
        )
        if st.button("Run Query"):
            try:
                conn = sqlite3.connect(DB_PATH)
                result = pd.read_sql_query(query, conn)
                conn.close()
                st.success(f"{len(result):,} rows returned")
                st.dataframe(result, use_container_width=True)
                csv = result.to_csv(index=False).encode()
                st.download_button("Download result", csv, "query_result.csv", "text/csv")
            except Exception as e:
                st.error(f"Query error: {e}")

        st.markdown("---")
        st.markdown("**Available tables:** `patents`, `inventors`, `companies`, `patent_relationships`")
        join_result = load_result("q5_join_result.csv")
        if join_result is not None:
            st.subheader("Sample JOIN result (Q5)")
            st.dataframe(join_result.head(50), use_container_width=True)
