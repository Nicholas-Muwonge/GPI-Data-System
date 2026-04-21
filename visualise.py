"""
visualise.py
------------
Generates 4 publication-quality charts from query result CSVs
and saves them to reports/charts/.

Charts produced:
  1. Top 10 Inventors          (horizontal bar)
  2. Top 10 Companies          (horizontal bar)
  3. Patents per Year          (line chart)
  4. Country Share             (pie chart)

Usage:
    python scripts/visualise.py
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # non-interactive backend — safe on servers
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "results")
CHARTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports", "charts")

# ── style ──────────────────────────────────────────────────────────────────────

PALETTE   = ["#1a6faf", "#2196F3", "#42A5F5", "#64B5F6", "#90CAF9",
             "#BBDEFB", "#E3F2FD", "#0D47A1", "#1565C0", "#1976D2"]
BG_COLOR  = "#f7f9fc"
FONT_SIZE = 10
plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        FONT_SIZE,
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "figure.dpi":       150,
})


def load(filename: str) -> pd.DataFrame:
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing: {path}\n"
            "Run  python scripts/run_queries.py  first."
        )
    return pd.read_csv(path)


def save_fig(fig: plt.Figure, filename: str) -> None:
    os.makedirs(CHARTS_DIR, exist_ok=True)
    path = os.path.join(CHARTS_DIR, filename)
    fig.savefig(path, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"  Saved {path}")


# ── chart functions ────────────────────────────────────────────────────────────

def chart_top_inventors(df: pd.DataFrame) -> None:
    top = df.head(10).iloc[::-1]   # reverse for bottom-to-top ordering
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.barh(top["name"], top["patent_count"], color=PALETTE, edgecolor="none", height=0.6)
    ax.bar_label(bars, padding=4, fontsize=9, color="#333")
    ax.set_xlabel("Number of Patents", labelpad=8)
    ax.set_title("Top 10 Inventors by Patent Count", fontsize=13, fontweight="bold", pad=12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.tick_params(axis="y", labelsize=9)
    fig.tight_layout()
    save_fig(fig, "top_inventors.png")


def chart_top_companies(df: pd.DataFrame) -> None:
    top = df.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    bars = ax.barh(top["name"], top["patent_count"], color=PALETTE, edgecolor="none", height=0.6)
    ax.bar_label(bars, padding=4, fontsize=9, color="#333")
    ax.set_xlabel("Number of Patents", labelpad=8)
    ax.set_title("Top 10 Companies by Patent Count", fontsize=13, fontweight="bold", pad=12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    # Truncate long company names
    labels = [t.get_text()[:35] + "…" if len(t.get_text()) > 35 else t.get_text()
              for t in ax.get_yticklabels()]
    ax.set_yticklabels(labels, fontsize=8)
    fig.tight_layout()
    save_fig(fig, "top_companies.png")


def chart_trends(df: pd.DataFrame) -> None:
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)
    df = df.sort_values("year")

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    ax.plot(df["year"], df["patent_count"], color="#1a6faf", linewidth=2.5,
            marker="o", markersize=4, markerfacecolor="white", markeredgewidth=1.5)
    ax.fill_between(df["year"], df["patent_count"], alpha=0.12, color="#1a6faf")

    ax.set_xlabel("Year", labelpad=8)
    ax.set_ylabel("Patents Filed", labelpad=8)
    ax.set_title("Global Patent Filings Over Time", fontsize=13, fontweight="bold", pad=12)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=10))
    fig.tight_layout()
    save_fig(fig, "trends_over_time.png")


def chart_countries(df: pd.DataFrame) -> None:
    top    = df.head(8).copy()
    other  = df.iloc[8:]["patent_count"].sum() if len(df) > 8 else 0
    labels = list(top["country"])
    sizes  = list(top["patent_count"])
    if other > 0:
        labels.append("Other")
        sizes.append(other)

    colors = PALETTE[:len(labels)]

    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor(BG_COLOR)
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.82,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color("white")

    ax.legend(wedges, labels, loc="lower right", fontsize=9,
              frameon=False, bbox_to_anchor=(1.12, 0.0))
    ax.set_title("Patent Share by Country", fontsize=13, fontweight="bold", pad=12)
    fig.tight_layout()
    save_fig(fig, "country_share.png")


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Generating Charts ===")
    chart_top_inventors(load("q1_top_inventors.csv"))
    chart_top_companies(load("q2_top_companies.csv"))
    chart_trends(load("q4_trends_over_time.csv"))
    chart_countries(load("q3_countries.csv"))
    print("\n✅  All charts saved to reports/charts/")
    print("Optional: streamlit run dashboard.py")


if __name__ == "__main__":
    main()
