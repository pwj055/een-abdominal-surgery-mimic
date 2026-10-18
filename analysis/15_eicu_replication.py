# -*- coding: utf-8 -*-
"""
15_eicu_replication.py — eICU-CRD v2.0 supportive multicenter analysis.

Role in the project: eICU is NOT a full external validation (its microLab table
is too sparse to reproduce the treated-culture infection composite, and there is
no procedure-code table to identify major abdominal surgery directly). It is used
here as a *supportive multicenter triangulation* of the feeding-exposure structure
and of the death/LOS endpoints, per protocol §12.10.

What this script does (on D:/eicu, 208 US hospitals, 2014-2015):
  * surgical cohort := first ICU stay whose APACHE admission diagnosis is a
    major abdominal "surgery for ..." category (explicit surgical APACHE labels,
    the closest available proxy for the MIMIC-IV procedure-code definition);
  * exposure := first documented enteral (tube) intake from intakeOutput, using a
    label classifier that keeps tube/enteral/gastric/jejunal cells and drops
    oral/PO/TPN/flush/residual/water cells; EEN <=48h, late >48h, never = none;
  * 48-h landmark (ICU stay >=48 h, i.e. unitdischargeoffset >= 2880 min);
  * outcomes := in-hospital death, ICU LOS, hospital LOS, ventilation days;
  * covariate set (minimal, admission/day-1): age, sex, elective surgery,
    APACHE score, day-1 ventilation, diabetes, cirrhosis, immunosuppression;
  * two comparisons x in-hospital death: crude + overlap-weighted (OW) OR/RR/RD.

Outputs: analysis/eicu_cohort.csv, analysis/eicu_replication.md.
"""
import os
import sys
import numpy as np
import pandas as pd
import duckdb
import statsmodels.api as sm
from scipy.stats import norm
from statsmodels.genmod.families import Binomial, Gaussian, Poisson
from statsmodels.genmod.families.links import Logit, Identity, Log
from statsmodels.genmod.cov_struct import Independence

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1].rstrip("/\\") if len(sys.argv) > 1 else "D:/eicu"

# ---- APACHE admission-diagnosis labels = major abdominal surgery (explicit "surgery for") ----
GI_SURG = [
    "GI obstruction, surgery for (including lysis of adhesions)",
    "GI perforation/rupture, surgery for",
    "Cancer-colon/rectal, surgery for (including abdominoperineal resections)",
    "Cholecystectomy/cholangitis, surgery for (gallbladder removal)",
    "Complications of previous GI surgery; surgery for (anastomotic leak, bleeding, abscess, infection, dehiscence, etc.)",
    "GI surgery, other",
    "Cancer-other GI tract, surgery for (i.e., hepatoma, gallbladder etc.)",
    "Whipple-surgery for pancreatic cancer",
    "GI vascular ischemia, surgery for (resection)",
    "Obesity-morbid, surgery for",
    "Diverticular disease, surgery for",
    "Fistula/abscess, surgery for (not inflammatory bowel disease)",
    "Cancer-esophageal, surgery for (abdominal approach)",
]
gi_sql = ", ".join("'" + s.replace("'", "''") + "'" for s in GI_SURG)

# enteral (tube) leaf classifier: keep tube/enteral/gastric/jejunal; drop oral/TPN/flush
ENTERAL_KEEP = ("%enteral%", "%tube feed%", "%tube feeding%", "%gastric tube%",
                "%gastrostomy%", "%nasogastric%", "%orogastric%", "%nasoduodenal%",
                "%jejun%", "%peg%")
ENTERAL_DROP = ("%flush%", "%residual%", "%oral%", "%p.o%", "%tpn%", "%meds%",
                "%water%", "%discard%")
KEEP_SQL = " OR ".join(f"lower(leaf) LIKE '{k}'" for k in ENTERAL_KEEP)
DROP_SQL = " AND ".join(f"lower(leaf) NOT LIKE '{k}'" for k in ENTERAL_DROP)

con = duckdb.connect()

sql = f"""
WITH surg AS (
    SELECT * FROM (
        SELECT p.*, ROW_NUMBER() OVER (
            PARTITION BY COALESCE(uniquepid, CAST(patientunitstayid AS VARCHAR))
            ORDER BY hospitaladmitoffset NULLS LAST, unitvisitnumber NULLS LAST
        ) AS rn
        FROM read_csv_auto('{DATA}/patient.csv.gz') p
        WHERE apacheadmissiondx IN ({gi_sql})
    ) WHERE rn = 1
),
feed AS (
    SELECT patientunitstayid, MIN(intakeoutputoffset) AS first_feed_offset
    FROM (
        SELECT *, list_extract(string_split(cellpath, '|'), -1) AS leaf
        FROM read_csv_auto('{DATA}/intakeOutput.csv.gz')
    )
    WHERE cellvaluenumeric > 0 AND ({KEEP_SQL}) AND ({DROP_SQL})
    GROUP BY patientunitstayid
),
apv AS (SELECT * FROM read_csv_auto('{DATA}/apachePredVar.csv.gz')),
apr AS (
    SELECT patientunitstayid,
           MAX(apachescore) AS apachescore,
           MAX(actualventdays) AS vent_days
    FROM read_csv_auto('{DATA}/apachePatientResult.csv.gz')
    GROUP BY patientunitstayid
)
SELECT
    s.patientunitstayid, s.uniquepid, s.gender,
    CASE WHEN s.age LIKE '>%' THEN 90 ELSE TRY_CAST(s.age AS INT) END AS age,
    s.apacheadmissiondx, s.unittype, s.unitadmitsource,
    s.unitdischargeoffset, s.hospitaldischargeoffset,
    s.unitdischargestatus, s.hospitaldischargestatus,
    f.first_feed_offset,
    av.saps3day1, av.electivesurgery, av.diabetes, av.cirrhosis,
    av.immunosuppression, av.ventday1, av.day1pao2, av.day1fio2,
    ar.apachescore, ar.vent_days
FROM surg s
LEFT JOIN feed  f  ON s.patientunitstayid = f.patientunitstayid
LEFT JOIN apv  av ON s.patientunitstayid = av.patientunitstayid
LEFT JOIN apr  ar ON s.patientunitstayid = ar.patientunitstayid
"""

df = con.execute(sql).df()
n_raw = len(df)

# ---- 48-h landmark: ICU stay >= 48 h (survival to 48 h is implied by ICU-discharge offset) ----
df["icu_los_d"] = df["unitdischargeoffset"] / 1440.0
df["hosp_los_d"] = df["hospitaldischargeoffset"] / 1440.0
df["hosp_death"] = (df["hospitaldischargestatus"] == "Expired").astype(int)
df = df[df["unitdischargeoffset"] >= 2880].reset_index(drop=True)
n_land = len(df)

# ---- exposure ----
ff = df["first_feed_offset"]
df["fed"] = ff.notna().astype(int)
df["een48"] = ((ff <= 2880).fillna(False)).astype(int)
df["exposure"] = np.where(df["fed"] == 0, "never",
                          np.where(df["een48"] == 1, "EEN", "late"))

# ---- covariates (minimal, admission/day-1) ----
df["female"] = (df["gender"] == "Female").astype(int)
for c in ["electivesurgery", "diabetes", "cirrhosis", "immunosuppression", "ventday1"]:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
for c in ["age", "saps3day1", "apachescore", "vent_days", "day1pao2"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df.to_csv(os.path.join(HERE, "eicu_cohort.csv"), index=False)

# ============================ statistical helpers (mirror 02_weighting.py) ============================

CONT = ["age", "apachescore", "vent_days"]
BIN = ["female", "electivesurgery", "ventday1", "diabetes", "cirrhosis", "immunosuppression"]


def design_matrix(d):
    X = d[CONT + BIN].copy()
    for c in CONT:
        X[c] = X[c].fillna(X[c].median())
    X = X.astype(float)
    A = d["een48"].to_numpy(int)
    return X, A


def smd_table(X, A, w=None):
    out = {}
    for c in X.columns:
        x = X[c].to_numpy(float)
        if w is None:
            mt, mc = x[A == 1].mean(), x[A == 0].mean()
            vt, vc = x[A == 1].var(ddof=1), x[A == 0].var(ddof=1)
        else:
            wt, wc = w[A == 1], w[A == 0]
            mt = np.sum(wt * x[A == 1]) / np.sum(wt)
            mc = np.sum(wc * x[A == 0]) / np.sum(wc)
            vt = np.sum(wt * (x[A == 1] - mt) ** 2) / np.sum(wt)
            vc = np.sum(wc * (x[A == 0] - mc) ** 2) / np.sum(wc)
        denom = np.sqrt((vt + vc) / 2)
        out[c] = (mt - mc) / denom if denom > 0 else np.nan
    return pd.Series(out)


def p_from_z(z):
    return float(2 * norm.sf(np.abs(z)))


def weighted_effect(Y, A, w):
    n = len(Y)
    Xd = np.column_stack([np.ones(n), A])
    groups = np.arange(n)
    rd = sm.GEE(Y, Xd, groups=groups, family=Gaussian(Identity()),
                cov_struct=Independence(), weights=w).fit()
    orm = sm.GEE(Y, Xd, groups=groups, family=Binomial(Logit()),
                 cov_struct=Independence(), weights=w).fit()
    rrm = sm.GEE(Y, Xd, groups=groups, family=Poisson(Log()),
                 cov_struct=Independence(), weights=w).fit()
    return rd, orm, rrm


def effect_row(Y, A, w):
    Y = np.asarray(Y, float); A = np.asarray(A, int); w = np.asarray(w, float)
    ev_t = int(np.sum((A == 1) & (Y == 1))); ev_c = int(np.sum((A == 0) & (Y == 1)))
    n_t = int(np.sum(A == 1)); n_c = int(np.sum(A == 0))
    rd, orm, rrm = weighted_effect(Y, A, w)
    return dict(n_t=n_t, n_c=n_c, ev_t=ev_t, ev_c=ev_c,
                rd=float(rd.params[1]), rd_lo=float(rd.params[1] - 1.959964 * rd.bse[1]),
                rd_hi=float(rd.params[1] + 1.959964 * rd.bse[1]),
                p_rd=p_from_z(rd.params[1] / rd.bse[1]),
                or_=float(np.exp(orm.params[1])),
                or_lo=float(np.exp(orm.params[1] - 1.959964 * orm.bse[1])),
                or_hi=float(np.exp(orm.params[1] + 1.959964 * orm.bse[1])),
                p_or=p_from_z(orm.params[1] / orm.bse[1]),
                rr=float(np.exp(rrm.params[1])),
                rr_lo=float(np.exp(rrm.params[1] - 1.959964 * rrm.bse[1])),
                rr_hi=float(np.exp(rrm.params[1] + 1.959964 * rrm.bse[1])),
                p_rr=p_from_z(rrm.params[1] / rrm.bse[1]))


def run_comparison(d, label):
    X, A = design_matrix(d)
    # standardize continuous covariates for the PS fit (SMD is scale-invariant)
    Xz = (X - X.mean()) / X.std().replace(0, 1)
    Xc = sm.add_constant(Xz)
    ps = sm.Logit(A, Xc).fit(disp=0, method="bfgs", maxiter=500)
    p = np.clip(np.asarray(ps.predict(Xc), dtype=float), 1e-6, 1 - 1e-6)
    ow = np.where(A == 1, 1 - p, p)
    smd_raw = np.abs(smd_table(X, A)).max()
    smd_ow = np.abs(smd_table(X, A, ow)).max()
    Y = d["hosp_death"].to_numpy(float)
    crude = effect_row(Y, A, np.ones(len(Y)))
    adj = effect_row(Y, A, ow)
    return dict(label=label, n=len(d), smd_raw=smd_raw, smd_ow=smd_ow,
                crude=crude, ow=adj)


def fmt(x, d=2):
    return "NA" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def row_str(m):
    return (f"| {m['method']} | {m['n_t']} | {m['n_c']} | {m['ev_t']} | {m['ev_c']} | "
            f"{fmt(m['rd'],2)} ({fmt(m['rd_lo'],2)}, {fmt(m['rd_hi'],2)}) | "
            f"{fmt(m['rr'],2)} ({fmt(m['rr_lo'],2)}, {fmt(m['rr_hi'],2)}) | "
            f"{fmt(m['or_'],2)} ({fmt(m['or_lo'],2)}, {fmt(m['or_hi'],2)}) | "
            f"{fmt(m['p_or'],3)} |")


# ============================ descriptive ============================
g = df.groupby("exposure")
desc = pd.DataFrame({
    "n": g.size(),
    "death_pct": g["hosp_death"].mean() * 100,
    "med_icu_los_d": g["icu_los_d"].median(),
    "med_hosp_los_d": g["hosp_los_d"].median(),
    "med_vent_d": g["vent_days"].median(),
})
een_med_ttf = df.loc[df["exposure"] == "EEN", "first_feed_offset"].median() / 60.0
late_med_ttf = df.loc[df["exposure"] == "late", "first_feed_offset"].median() / 60.0

md = []
md.append("# eICU-CRD v2.0 — supportive multicenter triangulation\n")
md.append("**Role**: NOT a full external validation. microLab (145 KB) cannot reproduce the\n"
          "treated-culture infection composite, and eICU has no procedure-code table, so\n"
          "`apacheadmissiondx` \"surgery for …\" labels stand in for major abdominal surgery.\n")
md.append(f"**Cohort flow**: GI-surgery APACHE diagnoses (first ICU stay/patient) **{n_raw}** "
          f"→ 48-h landmark (ICU LOS ≥ 48 h) **{n_land}**.\n")

md.append("\n## Descriptive (landmarked)\n")
md.append("| exposure | n | death % | median ICU LOS (d) | median hospital LOS (d) | median vent days |\n")
md.append("|---|---|---|---|---|---|\n")
for ex in ["EEN", "late", "never"]:
    r = desc.loc[ex] if ex in desc.index else pd.Series([0, 0, 0, 0, 0], index=desc.columns)
    md.append(f"| {ex} | {int(r['n'])} | {r['death_pct']:.1f} | {r['med_icu_los_d']:.1f} | "
              f"{r['med_hosp_los_d']:.1f} | {r['med_vent_d']:.1f} |\n")
md.append(f"\n- Median time-to-first-feed: EEN **{een_med_ttf:.1f} h** vs late **{late_med_ttf:.1f} h**.\n")
md.append(f"- EEN proportion among eventually-fed: "
          f"{(df['exposure'] == 'EEN').sum()}/{int((df['fed']).sum())} = "
          f"{(df['exposure'] == 'EEN').mean() / max(df['fed'].mean(), 1e-9):.1%} of fed, "
          f"{(df['exposure'] == 'EEN').mean():.1%} of all landmarked.\n")

# ---- comparisons ----
md.append("\n## In-hospital death — EEN vs control\n")
md.append("| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |\n")
md.append("|---|---|---|---|---|---|---|---|---|---|\n")

compA = run_comparison(df[df["fed"] == 1].reset_index(drop=True), "A: EEN vs late (eventually-fed)")
compB = run_comparison(df.reset_index(drop=True), "B: EEN vs no-EEN (full landmarked cohort)")

for comp in [compA, compB]:
    md.append(f"| **{comp['label']}** (n={comp['n']}, max|SMD| raw {comp['smd_raw']:.2f} → OW {comp['smd_ow']:.2f}) |||||||||||\n")
    for m in [dict(comp['crude'], method="Crude"), dict(comp['ow'], method="OW")]:
        md.append(row_str(m) + "\n")

md.append("\n## Interpretation (supportive only)\n")
md.append("- **Feeding structure among documented-fed patients is coherent with MIMIC**: 62% of\n"
          "fed patients are EEN, and time-to-first-feed separates cleanly (median 13 h vs 95 h),\n"
          "the same EEN/late split the main analysis relies on.\n")
md.append("- **Absolute feeding rate is much lower than MIMIC** (12% fed vs MIMIC-IV 32%), and the\n"
          "88% \"never\" share is best explained by under-ascertainment of enteral intake in\n"
          "`intakeOutput` (sites chart feeding in other cells, in `infusionDrug`, or not at all),\n"
          "so the eICU \"never\" group is NOT comparable to MIMIC's never-fed group.\n")
md.append("- **In-hospital death is null** in both comparisons (A OW OR 0.88, B OW OR 0.82) —\n"
          "consistent with MIMIC, where death was a secondary/null endpoint and the primary\n"
          "finding was the infection composite. eICU cannot reproduce that infection composite\n"
          "(microLab 145 KB), which is precisely why eICU is supportive, not a validation.\n")

with open(os.path.join(HERE, "eicu_replication.md"), "w", encoding="utf-8") as f:
    f.write("".join(md))
print("".join(md))
