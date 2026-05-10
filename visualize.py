import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

DB_PATH   = os.path.join(os.path.dirname(__file__), "patent_pipeline.db")
CHART_DIR = os.path.join(os.path.dirname(__file__), "reports", "charts")
os.makedirs(CHART_DIR, exist_ok=True)

BLUE   = "#2563EB"
GREEN  = "#16A34A"
ORANGE = "#EA580C"
PURPLE = "#7C3AED"
GREY   = "#6B7280"


def connect():
    return sqlite3.connect(DB_PATH)


def q(conn, sql):
    return pd.read_sql_query(sql, conn)


def save(fig, name):
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {name}")


def chart_yearly_trend(conn):
    df = q(conn, """
        SELECT year, COUNT(*) AS patents
        FROM patents WHERE year IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["year"], df["patents"], color=BLUE, linewidth=2.5, marker="o",
            markersize=4)
    ax.fill_between(df["year"], df["patents"], alpha=0.12, color=BLUE)
    ax.set_title("Patent Grants Per Year", fontsize=14, fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Patents Granted")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "chart_yearly_trend.png")


def chart_top_inventors(conn):
    df = q(conn, """
        SELECT i.name, COUNT(DISTINCT pi.patent_id) AS patents
        FROM inventors i
        JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
        GROUP BY i.inventor_id ORDER BY patents DESC LIMIT 10
    """).sort_values("patents")

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(df["name"], df["patents"], color=GREEN, edgecolor="white",
                   linewidth=0.5)
    ax.bar_label(bars, padding=4, fmt="%,.0f", fontsize=9)
    ax.set_title("Top 10 Inventors by Patent Count", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Patents")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "chart_top_inventors.png")


def chart_top_companies(conn):
    df = q(conn, """
        SELECT c.name AS company, COUNT(DISTINCT pc.patent_id) AS patents
        FROM companies c
        JOIN patent_companies pc ON c.company_id = pc.company_id
        GROUP BY c.company_id ORDER BY patents DESC LIMIT 10
    """)

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(df["company"], df["patents"], color=ORANGE, edgecolor="white",
                  linewidth=0.5)
    ax.bar_label(bars, padding=3, fmt="%,.0f", fontsize=9)
    ax.set_title("Top 10 Companies by Patent Portfolio", fontsize=14,
                 fontweight="bold")
    ax.set_ylabel("Number of Patents")
    ax.set_xticklabels(df["company"], rotation=30, ha="right", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "chart_top_companies.png")


def chart_country_share(conn):
    df = q(conn, """
        SELECT i.country, COUNT(DISTINCT pi.patent_id) AS patents
        FROM inventors i
        JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
        WHERE i.country != 'UNKNOWN'
        GROUP BY i.country ORDER BY patents DESC LIMIT 8
    """)

    total   = df["patents"].sum()
    df_top  = df.head(7).copy()
    other   = total - df_top["patents"].sum()
    other_row = pd.DataFrame([{"country": "Other", "patents": other}])
    df_plot = pd.concat([df_top, other_row], ignore_index=True)

    colors = [BLUE, ORANGE, GREEN, PURPLE, "#F59E0B", "#10B981", "#EF4444", GREY]
    fig, ax = plt.subplots(figsize=(7, 7))
    wedges, texts, autotexts = ax.pie(
        df_plot["patents"],
        labels=df_plot["country"],
        autopct="%1.1f%%",
        colors=colors,
        startangle=140,
        pctdistance=0.82,
    )
    for at in autotexts:
        at.set_fontsize(9)
    ax.set_title("Patent Share by Inventor Country", fontsize=14,
                 fontweight="bold", pad=15)
    save(fig, "chart_country_share.png")


def chart_country_trend(conn):
    top5 = q(conn, """
        SELECT i.country
        FROM inventors i
        JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
        WHERE i.country != 'UNKNOWN'
        GROUP BY i.country ORDER BY COUNT(*) DESC LIMIT 5
    """)["country"].tolist()

    rows = []
    for country in top5:
        df = q(conn, f"""
            SELECT p.year, COUNT(DISTINCT pi.patent_id) AS patents
            FROM patents p
            JOIN patent_inventors pi ON p.patent_id = pi.patent_id
            JOIN inventors i         ON pi.inventor_id = i.inventor_id
            WHERE i.country = '{country}' AND p.year IS NOT NULL
            GROUP BY p.year
        """)
        df["country"] = country
        rows.append(df)

    combined = pd.concat(rows).pivot(index="year", columns="country",
                                     values="patents").fillna(0)

    colors = [BLUE, ORANGE, GREEN, PURPLE, "#F59E0B"]
    fig, ax = plt.subplots(figsize=(11, 5))
    combined.plot(kind="bar", ax=ax, color=colors, width=0.75,
                  edgecolor="white", linewidth=0.4)
    ax.set_title("Patent Trends: Top 5 Countries Over Time", fontsize=14,
                 fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Patents")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(title="Country", bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    save(fig, "chart_country_trend.png")


def main():
    print("\n" + "=" * 55)
    print("  Generating Visualizations")
    print("=" * 55)
    conn = connect()
    chart_yearly_trend(conn)
    chart_top_inventors(conn)
    chart_top_companies(conn)
    chart_country_share(conn)
    chart_country_trend(conn)
    conn.close()
    print(f"\n✅  Charts saved to: {CHART_DIR}\n")


if __name__ == "__main__":
    main()
