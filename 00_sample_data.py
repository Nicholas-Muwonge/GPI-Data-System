"""
00_sample_data.py — Generate realistic sample patent data
Run this if you cannot download from USPTO, or for fast local testing.
Creates TSV files in data/raw/ that mimic the real PatentsView schema.
"""

import os
import random
import csv
from datetime import date, timedelta

RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

random.seed(42)

# ── Reference data ────────────────────────────────────────────
COUNTRIES = {
    "US": 55, "CN": 18, "JP": 8, "DE": 5, "KR": 4,
    "GB": 3, "FR": 2, "CA": 2, "TW": 1, "UG": 1, "IN": 1,
}

FIRST_NAMES = [
    "James", "Wei", "Yuki", "Hans", "Priya", "Ali", "Sofia",
    "Chen", "Maria", "David", "Aisha", "Robert", "Lin", "Anna",
    "Mohammed", "Sarah", "Kenji", "Erik", "Fatima", "John",
]
LAST_NAMES = [
    "Smith", "Zhang", "Tanaka", "Mueller", "Patel", "Hassan",
    "Rossi", "Wang", "Garcia", "Johnson", "Osei", "Kim",
    "Nakamura", "Schmidt", "Sharma", "Brown", "Liu", "Anderson",
    "Singh", "Williams",
]

COMPANIES = [
    ("Samsung Electronics", "KR"), ("IBM", "US"), ("Apple Inc", "US"),
    ("Huawei Technologies", "CN"), ("Microsoft Corporation", "US"),
    ("Toyota Motor Corporation", "JP"), ("Google LLC", "US"),
    ("Qualcomm Incorporated", "US"), ("Intel Corporation", "US"),
    ("Canon Inc", "JP"), ("LG Electronics", "KR"), ("Sony Corporation", "JP"),
    ("Bosch GmbH", "DE"), ("Siemens AG", "DE"), ("3M Company", "US"),
    ("BASF SE", "DE"), ("Medtronic PLC", "US"), ("Honeywell International", "US"),
    ("General Electric", "US"), ("Amazon Technologies", "US"),
]

TECH_WORDS = [
    "semiconductor", "quantum", "neural", "optical", "wireless",
    "battery", "polymer", "photovoltaic", "autonomous", "distributed",
    "encrypted", "biometric", "nanotechnology", "robotic", "thermal",
]
TECH_NOUNS = [
    "circuit", "device", "system", "method", "apparatus", "network",
    "sensor", "processor", "interface", "module", "structure", "layer",
    "composition", "process", "controller",
]

N_PATENTS   = 5_000
N_INVENTORS = 2_000
N_COMPANIES = len(COMPANIES)


def random_date(start_year=2015, end_year=2023):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def weighted_country():
    pop = list(COUNTRIES.keys())
    wts = list(COUNTRIES.values())
    return random.choices(pop, weights=wts, k=1)[0]


def make_title():
    adj  = random.choice(TECH_WORDS).capitalize()
    noun = random.choice(TECH_NOUNS)
    extra = random.choice(["for mobile devices", "with enhanced efficiency",
                           "using machine learning", "for data processing",
                           "and manufacturing method thereof", ""])
    return f"{adj} {noun} {extra}".strip()


def make_abstract(title):
    sentences = [
        f"A {title.lower()} is disclosed.",
        f"The invention relates to improvements in {random.choice(TECH_WORDS)} technology.",
        f"Methods and systems are provided for {random.choice(TECH_NOUNS)} optimization.",
        f"Embodiments include a {random.choice(TECH_NOUNS)} configured to perform the described functions.",
        f"The disclosed approach offers improved efficiency and reduced power consumption.",
    ]
    return " ".join(random.sample(sentences, k=random.randint(2, 4)))


# ── Build inventors pool ──────────────────────────────────────
inventors = []
used_names = set()
for i in range(1, N_INVENTORS + 1):
    while True:
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        full = f"{fn} {ln}"
        if full not in used_names:
            used_names.add(full)
            break
    inventors.append({
        "inventor_id": f"inv-{i:05d}",
        "disambig_inventor_id": f"inv-{i:05d}",
        "name_first": fn,
        "name_last": ln,
        "country": weighted_country(),
    })

# Give a handful of inventors many patents (realistic Zipf-like distribution)
prolific_ids = [inv["inventor_id"] for inv in random.sample(inventors, 50)]

# ── Build companies pool ──────────────────────────────────────
company_rows = []
for i, (name, country) in enumerate(COMPANIES, start=1):
    company_rows.append({
        "assignee_id": f"asgn-{i:04d}",
        "disambig_assignee_id": f"asgn-{i:04d}",
        "organization": name,
        "country": country,
        "assignee_type": "2",  # 2 = US corporation in PV schema
    })

# ── Generate patents and relationship rows ────────────────────
patent_rows = []
inventor_rel_rows = []   # g_patent_inventor style
assignee_rel_rows = []   # g_patent_assignee style

for p in range(1, N_PATENTS + 1):
    pid = f"US{10_000_000 + p}"
    filing = random_date()
    title = make_title()

    patent_rows.append({
        "patent_id": pid,
        "type": "utility",
        "number": str(10_000_000 + p),
        "country": "US",
        "date": filing.isoformat(),
        "abstract": make_abstract(title),
        "title": title,
        "kind": "B2",
        "num_claims": random.randint(1, 25),
        "filename": f"ipg{filing.strftime('%y%m%d')}.xml",
        "withdrawn": 0,
    })

    # Assign 1-4 inventors; prolific inventors appear more often
    n_inv = random.choices([1, 2, 3, 4], weights=[40, 35, 18, 7])[0]
    chosen_inventors = []
    if random.random() < 0.3 and prolific_ids:
        chosen_inventors.append(random.choice(prolific_ids))
        n_inv -= 1
    chosen_inventors += [inv["inventor_id"] for inv in random.sample(inventors, min(n_inv, len(inventors)))]

    for seq, inv_id in enumerate(chosen_inventors, start=1):
        inventor_rel_rows.append({
            "patent_id": pid,
            "inventor_id": inv_id,
            "disambig_inventor_id": inv_id,
            "sequence": seq,
        })

    # Assign 0-2 assignees (some patents have none)
    if random.random() < 0.85:
        n_asgn = random.choices([1, 2], weights=[85, 15])[0]
        # Large companies get more patents
        weights = [30 if c["organization"] in
                   {"Samsung Electronics","IBM","Google LLC","Microsoft Corporation","Apple Inc"}
                   else 5 for c in company_rows]
        chosen_companies = random.choices(company_rows, weights=weights, k=n_asgn)
        seen = set()
        for seq, comp in enumerate(chosen_companies, start=1):
            if comp["assignee_id"] not in seen:
                seen.add(comp["assignee_id"])
                assignee_rel_rows.append({
                    "patent_id": pid,
                    "assignee_id": comp["assignee_id"],
                    "disambig_assignee_id": comp["disambig_assignee_id"],
                    "sequence": seq,
                })


def write_tsv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✓ {os.path.basename(path)}  ({len(rows):,} rows)")


if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  Generating Sample PatentsView Data")
    print("=" * 55)

    write_tsv(
        os.path.join(RAW_DIR, "g_patent.tsv"),
        patent_rows,
        ["patent_id","type","number","country","date","abstract","title",
         "kind","num_claims","filename","withdrawn"],
    )
    write_tsv(
        os.path.join(RAW_DIR, "g_inventor_disambiguated.tsv"),
        inventors,
        ["inventor_id","disambig_inventor_id","name_first","name_last","country"],
    )
    write_tsv(
        os.path.join(RAW_DIR, "g_assignee_disambiguated.tsv"),
        company_rows,
        ["assignee_id","disambig_assignee_id","organization","country","assignee_type"],
    )
    write_tsv(
        os.path.join(RAW_DIR, "g_patent_inventor.tsv"),
        inventor_rel_rows,
        ["patent_id","inventor_id","disambig_inventor_id","sequence"],
    )
    write_tsv(
        os.path.join(RAW_DIR, "g_patent_assignee.tsv"),
        assignee_rel_rows,
        ["patent_id","assignee_id","disambig_assignee_id","sequence"],
    )

    print(f"\n✅  Sample data ready in: {RAW_DIR}\n")
