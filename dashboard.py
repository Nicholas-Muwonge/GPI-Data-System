import os
import json
import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

DB_PATH    = os.path.join(os.path.dirname(__file__), "patent_pipeline.db")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")

st.set_page_config(
    page_title="NICHOLAS' GPI",
    page_icon="🔬",
    layout="wide",
)

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def run_query(sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, get_conn())


st.sidebar.title("🔬 Nicholas' Patent Intelligence")
st.sidebar.markdown("Nicholas' GPI Dashboard")

page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview", "👤 Inventors", "🏢 Companies", "🌍 Countries", "📈 Trends"],
)

year_range = st.sidebar.slider(
    "Filing Year Range",
    min_value=1976,
    max_value=2030,
    value=(2015, 2023),
)

if page == "📊 Overview":
    st.title("📊 NICHOLAS' Global Patent Intelligence")
    st.markdown("---")

    total_patents   = run_query("SELECT COUNT(*) AS n FROM patents")["n"].iloc[0]
    total_inventors = run_query("SELECT COUNT(*) AS n FROM inventors")["n"].iloc[0]
    total_companies = run_query("SELECT COUNT(*) AS n FROM companies")["n"].iloc[0]
    total_countries = run_query(
        "SELECT COUNT(DISTINCT country) AS n FROM inventors WHERE country != 'UNKNOWN'"
    )["n"].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Patents",   f"{total_patents:,}")
    c2.metric("Inventors",       f"{total_inventors:,}")
    c3.metric("Companies",       f"{total_companies:,}")
    c4.metric("Countries",       f"{total_countries:,}")

    st.markdown("---")

    yearly = run_query(f"""
        SELECT year, COUNT(*) AS patents FROM patents
        WHERE year BETWEEN {year_range[0]} AND {year_range[1]}
        GROUP BY year ORDER BY year
    """)
    st.subheader("Patents per Year")
    st.line_chart(yearly.set_index("year")["patents"])

    json_path = os.path.join(REPORT_DIR, "summary_report.json")
    if os.path.exists(json_path):
        with open(json_path) as f:
            summary = json.load(f)
        st.markdown("---")
        st.subheader("Summary JSON")
        st.json(summary)


elif page == "👤 Inventors":
    st.title("👤 Top Inventors")

    top_n = st.slider("Show top N inventors", 5, 50, 20)

    df = run_query(f"""
        SELECT i.name, i.country,
               COUNT(DISTINCT pi.patent_id) AS patents
        FROM inventors i
        JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
        JOIN patents p           ON pi.patent_id = p.patent_id
        WHERE p.year BETWEEN {year_range[0]} AND {year_range[1]}
        GROUP BY i.inventor_id
        ORDER BY patents DESC
        LIMIT {top_n}
    """)
    df.insert(0, "Rank", range(1, len(df) + 1))

    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots(figsize=(9, max(4, top_n * 0.35)))
    ax.barh(df["name"][::-1], df["patents"][::-1], color="#2563EB")
    ax.set_xlabel("Patents")
    ax.set_title(f"Top {top_n} Inventors")
    ax.spines[["top", "right"]].set_visible(False)
    st.pyplot(fig)

    csv = df.to_csv(index=False).encode()
    st.download_button("⬇ Download CSV", csv, "top_inventors.csv", "text/csv")


elif page == "🏢 Companies":
    st.title("🏢 Top Companies")

    top_n = st.slider("Show top N companies", 5, 30, 15)

    df = run_query(f"""
        SELECT c.name AS company, c.country,
               COUNT(DISTINCT pc.patent_id) AS patents
        FROM companies c
        JOIN patent_companies pc ON c.company_id = pc.company_id
        JOIN patents p           ON pc.patent_id = p.patent_id
        WHERE p.year BETWEEN {year_range[0]} AND {year_range[1]}
        GROUP BY c.company_id
        ORDER BY patents DESC
        LIMIT {top_n}
    """)
    df.insert(0, "Rank", range(1, len(df) + 1))

    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df["company"], df["patents"], color="#EA580C", edgecolor="white")
    ax.set_xticklabels(df["company"], rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Patents")
    ax.set_title(f"Top {top_n} Companies by Patent Count")
    ax.spines[["top", "right"]].set_visible(False)
    st.pyplot(fig)

    csv = df.to_csv(index=False).encode()
    st.download_button("⬇ Download CSV", csv, "top_companies.csv", "text/csv")


elif page == "🌍 Countries":
    st.title("🌍 Patent Production by Country")

    df = run_query(f"""
        SELECT i.country,
               COUNT(DISTINCT pi.patent_id) AS patents,
               ROUND(COUNT(DISTINCT pi.patent_id) * 100.0 /
                     (SELECT COUNT(*) FROM patent_inventors), 2) AS share_pct
        FROM inventors i
        JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
        JOIN patents p           ON pi.patent_id = p.patent_id
        WHERE i.country != 'UNKNOWN'
          AND p.year BETWEEN {year_range[0]} AND {year_range[1]}
        GROUP BY i.country
        ORDER BY patents DESC
        LIMIT 20
    """)
    df.insert(0, "Rank", range(1, len(df) + 1))

    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(df["country"], df["patents"], color="#16A34A", edgecolor="white")
    ax.set_xlabel("Country")
    ax.set_ylabel("Patents")
    ax.set_title("Top 20 Countries by Patent Count")
    ax.spines[["top", "right"]].set_visible(False)
    st.pyplot(fig)

    csv = df.to_csv(index=False).encode()
    st.download_button("⬇ Download CSV", csv, "country_trends.csv", "text/csv")


elif page == "📈 Trends":
    st.title("📈 Innovation Trends")

    st.subheader("Year-over-Year Growth")
    yearly = run_query(f"""
        SELECT year, COUNT(*) AS patents FROM patents
        WHERE year BETWEEN {year_range[0]} AND {year_range[1]}
        GROUP BY year ORDER BY year
    """)
    yearly["yoy_growth"] = yearly["patents"].pct_change() * 100
    st.dataframe(yearly.style.format({"yoy_growth": "{:.1f}%"}),
                 use_container_width=True)
    st.line_chart(yearly.set_index("year")[["patents", "yoy_growth"]])

    st.subheader("Country Activity Over Time (Top 5)")
    top5 = run_query("""
        SELECT i.country
        FROM inventors i
        JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
        WHERE i.country != 'UNKNOWN'
        GROUP BY i.country ORDER BY COUNT(*) DESC LIMIT 5
    """)["country"].tolist()

    rows = []
    for c in top5:
        df = run_query(f"""
            SELECT p.year, COUNT(DISTINCT pi.patent_id) AS patents
            FROM patents p
            JOIN patent_inventors pi ON p.patent_id = pi.patent_id
            JOIN inventors i         ON pi.inventor_id = i.inventor_id
            WHERE i.country = '{c}'
              AND p.year BETWEEN {year_range[0]} AND {year_range[1]}
            GROUP BY p.year
        """)
        df["country"] = c
        rows.append(df)

    if rows:
        combined = pd.concat(rows).pivot(
            index="year", columns="country", values="patents"
        ).fillna(0)
        st.line_chart(combined)
