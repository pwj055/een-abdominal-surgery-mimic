# -*- coding: utf-8 -*-
"""
03_tables.py — Table 1 (baseline by exposure group) + never-group 3-way dissection
+ flow-diagram numbers. Reads analysis/cohort.csv; joins patients/diagnoses_icd for
the never dissection (in-hospital death + ileus). Outputs analysis/table1.md + table1.csv.
"""
import os
import numpy as np
import pandas as pd
import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
M = "D:/physionet/mimic-iv"
df = pd.read_csv(os.path.join(HERE, "cohort.csv"))

CONT = [("age", "Age, years"), ("n_major_procs", "Major procedures, n"),
        ("lactate_max", "Lactate max 0-24h, mmol/L"), ("creat_max", "Creatinine max 0-24h, mg/dL"),
        ("wbc_max", "WBC max 0-24h, K/uL"), ("plt_min", "Platelet min 0-24h, K/uL"),
        ("bili_max", "Bilirubin max 0-24h, mg/dL")]
BIN = [("female", "Female"), ("emergency", "Emergency admission"),
       ("stoma", "Stoma"), ("any_explor", "Exploratory laparotomy (index)"),
       ("vaso_24h", "Vasopressor 0-24h"), ("mv_24h", "Mechanical ventilation 0-24h"),
       ("diabetes", "Diabetes"), ("ckd", "CKD"), ("cirrhosis", "Cirrhosis")]
SITE = [("hpb", "HPB"), ("upper", "Upper GI"), ("lower", "Lower GI"), ("other", "Other")]

groups = ["EEN", "late", "never"]


def mean_sd(x):
    x = pd.to_numeric(x, errors="coerce")
    n = int(x.notna().sum())
    return f"{x.mean():.1f} ({x.std():.1f})", n


def n_pct(x):
    x = pd.to_numeric(x, errors="coerce").fillna(0).astype(int)
    return f"{int(x.sum())} ({100 * x.mean():.1f})"


def smd_cont(x, a, b):
    ma, mb = x[a].mean(), x[b].mean()
    va, vb = x[a].var(ddof=1), x[b].var(ddof=1)
    d = np.sqrt((va + vb) / 2)
    return (ma - mb) / d if d > 0 else np.nan


def smd_bin(x, a, b):
    pa, pb = x[a].mean(), x[b].mean()
    d = np.sqrt((pa * (1 - pa) + pb * (1 - pb)) / 2)
    return (pa - pb) / d if d > 0 else np.nan


# ---- Table 1 ----
rows = []
grp_col = df["grp"]
e = grp_col == "EEN"; l = grp_col == "late"; n_ = grp_col == "never"; ne = grp_col != "EEN"

for col, lab in CONT:
    x = pd.to_numeric(df[col], errors="coerce")
    row = {"Characteristic": lab}
    for g, m in [("EEN", e), ("late", l), ("never", n_)]:
        row[g], _ = mean_sd(x[m])
    row["SMD (EEN vs late)"] = f"{smd_cont(x, e, l):.3f}"
    row["SMD (EEN vs no-EEN)"] = f"{smd_cont(x, e, ne):.3f}"
    rows.append(row)

for col, lab in BIN:
    x = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    row = {"Characteristic": lab}
    for g, m in [("EEN", e), ("late", l), ("never", n_)]:
        row[g] = n_pct(x[m])
    row["SMD (EEN vs late)"] = f"{smd_bin(x, e, l):.3f}"
    row["SMD (EEN vs no-EEN)"] = f"{smd_bin(x, e, ne):.3f}"
    rows.append(row)

site_map = {g: None for g in groups}
site_rows = []
for sc, slab in SITE:
    x = (df["site"] == sc).astype(int)
    row = {"Characteristic": f"Site: {slab}"}
    for g, m in [("EEN", e), ("late", l), ("never", n_)]:
        row[g] = n_pct(x[m])
    row["SMD (EEN vs late)"] = f"{smd_bin(x, e, l):.3f}"
    row["SMD (EEN vs no-EEN)"] = f"{smd_bin(x, e, ne):.3f}"
    site_rows.append(row)

tab = pd.DataFrame(rows + site_rows)
tab.to_csv(os.path.join(HERE, "table1.csv"), index=False)

md = ["# Table 1 — Baseline characteristics by feeding group (landmarked cohort)\n\n",
      f"n: EEN {int(e.sum())} / late {int(l.sum())} / never {int(n_.sum())} (total {len(df)})\n\n",
      "| Characteristic | EEN | late | never | SMD (EEN vs late) | SMD (EEN vs no-EEN) |\n",
      "|---|---|---|---|---|---|\n"]
for _, r in tab.iterrows():
    md.append("| " + " | ".join(str(r[c]) for c in
              ["Characteristic", "EEN", "late", "never",
               "SMD (EEN vs late)", "SMD (EEN vs no-EEN)"]) + " |\n")

# ---- never dissection (died / therapeutic-NPO(ileus) / oral recovery) ----
never_ids = df[df["grp"] == "never"][["hadm_id", "subject_id", "hosp_death"]].drop_duplicates()
con = duckdb.connect()
con.register("nv", never_ids)
nd = con.execute(f"""
WITH dx AS (
  SELECT n.hadm_id, n.subject_id, n.hosp_death,
         MAX(CASE WHEN (d.icd_version = 9 AND SUBSTRING(d.icd_code,1,3) = '560')
                    OR (d.icd_version = 10 AND SUBSTRING(d.icd_code,1,3) = 'K56')
              THEN 1 ELSE 0 END) AS ileus
  FROM nv n
  LEFT JOIN read_csv_auto('{M}/hosp/diagnoses_icd.csv.gz') d ON d.hadm_id = n.hadm_id
  GROUP BY n.hadm_id, n.subject_id, n.hosp_death
)
SELECT dx.hadm_id, dx.hosp_death, dx.ileus
FROM dx
""").df()
con.close()

nd["died"] = nd["hosp_death"].astype(int)
nd["subgroup"] = np.where(nd["died"] == 1, "died",
                 np.where(nd["ileus"] == 1, "ileus/obstruction (therapeutic NPO)",
                          "other (presumptive oral recovery)"))
diss = nd.groupby("subgroup").size().rename("n").reset_index()
diss["pct"] = (100 * diss["n"] / diss["n"].sum()).round(1)

md.append("\n\n## Never-fed group 3-way dissection (descriptive only)\n\n")
md.append("| Subgroup | n | % |\n|---|---|---|\n")
for _, r in diss.iterrows():
    md.append(f"| {r['subgroup']} | {r['n']} | {r['pct']} |\n")

# ---- flow diagram numbers ----
md.append("\n\n## Flow diagram (locked feasibility numbers)\n\n")
md.append("- Major abdominal surgery, first surgical ICU stay: **3246**\n")
md.append("- ICU LOS >= 48h (landmarked cohort): **1658**\n")
md.append(f"- EEN (<=48h): {int(e.sum())} | late EN (>48h): {int(l.sum())} | never fed: {int(n_.sum())}\n")

with open(os.path.join(HERE, "table1.md"), "w", encoding="utf-8") as f:
    f.write("".join(md))
print("".join(md))
