# -*- coding: utf-8 -*-
"""
13_causal_hardening.py — reviewer-requested causal-hardening analyses (A-tier):

  1. Negative-control outcome: treated urinary-tract infection (urine culture +
     systemic antibiotic in [-1d,+2d], >48h & <28d, contaminants excluded) — the
     same definition as the primary composite but at a site with no plausible EN
     mechanism, so a null result supports the specificity of the primary finding.
  2. Doubly-robust AIPW (augmented inverse-probability weighting) RD/RR/OR for the
     primary infection composite and the negative control (marginal, collapsible).
  3. Missing-data: per-covariate missingness + a complete-case OW sensitivity.

Outputs: analysis/negative_control.md, analysis/missing_data.md
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
import duckdb
from scipy.stats import norm
from statsmodels.genmod.families import Binomial, Gaussian, Poisson
from statsmodels.genmod.families.links import Logit, Identity, Log
from statsmodels.genmod.cov_struct import Independence

HERE = os.path.dirname(os.path.abspath(__file__))
M = "D:/physionet/mimic-iv"

CONT = ["age", "n_major_procs", "lactate_max", "creat_max", "wbc_max", "plt_min", "bili_max",
        "gcs_min", "map_min", "fio2_max", "po2_min", "bmi"]
BIN = ["female", "emergency", "stoma", "any_explor", "vaso_24h", "mv_24h",
       "diabetes", "ckd", "cirrhosis"]
SITE = ["hpb", "upper", "lower"]

ABX = (
    "amikacin", "amoxicillin", "ampicillin", "azithromycin", "aztreonam",
    "cefazolin", "cefepime", "cefotaxime", "cefoxitin", "ceftaroline",
    "ceftazidime", "ceftriaxone", "cefuroxime", "cephalexin", "ciprofloxacin",
    "clindamycin", "daptomycin", "doxycycline", "ertapenem", "gentamicin",
    "imipenem", "levofloxacin", "linezolid", "meropenem", "metronidazole",
    "nafcillin", "oxacillin", "penicillin", "piperacillin", "sulfamethoxazole",
    "tobramycin", "trimethoprim", "vancomycin", "tigecycline", "colistin",
    "cefoperazone", "cloxacillin", "moxifloxacin",
)
CONTAM = (
    "coagulase negative", "coagulase-negative", "epidermidis",
    "corynebacterium", "diphtheroid", "micrococcus", "propionibacterium",
    "bacillus", "viridans",
)


def load_cohort():
    d = pd.read_csv(os.path.join(HERE, "cohort.csv"))
    sf = os.path.join(HERE, "sofa_covariates.csv")
    if os.path.exists(sf):
        d = d.merge(pd.read_csv(sf), on="stay_id", how="left")
    return d


def design_matrix(d):
    present = [c for c in CONT if c in d.columns]
    X = d[present].copy()
    for c in present:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    if "lactate_max" in d.columns:
        X["lactate_missing"] = pd.to_numeric(d["lactate_max"], errors="coerce").isna().astype(int)
    for c in present:
        X[c] = X[c].fillna(X[c].median())
    for c in BIN:
        X[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)
    for s in SITE:
        X["site_" + s] = (d["site"] == s).astype(int)
    X = X.astype(float)
    A = d["een48"].to_numpy(int)
    return X, A


def p_from_z(z):
    return float(2 * norm.sf(np.abs(z)))


def w_effect(Y, A, w):
    """Weighted RD / RR / OR via GEE (robust sandwich SE)."""
    Y = np.asarray(Y, float); A = np.asarray(A, int); w = np.asarray(w, float)
    groups = np.arange(len(Y))
    Xd = np.column_stack([np.ones(len(Y)), A])
    rd = sm.GEE(Y, Xd, groups=groups, family=Gaussian(Identity()),
                cov_struct=Independence(), weights=w).fit()
    orm = sm.GEE(Y, Xd, groups=groups, family=Binomial(Logit()),
                 cov_struct=Independence(), weights=w).fit()
    rrm = sm.GEE(Y, Xd, groups=groups, family=Poisson(Log()),
                 cov_struct=Independence(), weights=w).fit()
    z = 1.959964
    return dict(
        rd=(float(rd.params[1]), float(rd.params[1] - z * rd.bse[1]), float(rd.params[1] + z * rd.bse[1])),
        or_=(float(np.exp(orm.params[1])), float(np.exp(orm.params[1] - z * orm.bse[1])),
             float(np.exp(orm.params[1] + z * orm.bse[1]))),
        rr=(float(np.exp(rrm.params[1])), float(np.exp(rrm.params[1] - z * rrm.bse[1])),
            float(np.exp(rrm.params[1] + z * rrm.bse[1]))),
        p_or=p_from_z(orm.params[1] / orm.bse[1]),
    )


def aipw_effect(X, A, Y):
    """Doubly-robust augmented IPW: marginal RD / RR / OR with EIF-based SEs."""
    Y = np.asarray(Y, float); A = np.asarray(A, float)
    Xc = sm.add_constant(X)
    p = np.clip(np.asarray(sm.Logit(A, Xc).fit(disp=0).predict(Xc), float), 1e-6, 1 - 1e-6)
    m1 = sm.Logit(Y[A == 1], Xc[A == 1]).fit(disp=0)
    m0 = sm.Logit(Y[A == 0], Xc[A == 0]).fit(disp=0)
    m1h = np.clip(np.asarray(m1.predict(Xc)), 1e-6, 1 - 1e-6)
    m0h = np.clip(np.asarray(m0.predict(Xc)), 1e-6, 1 - 1e-6)
    mu1 = float(np.mean(A * Y / p - (A - p) / p * m1h))
    mu0 = float(np.mean((1 - A) * Y / (1 - p) + (A - p) / (1 - p) * m0h))
    phi1 = A * (Y - m1h) / p + m1h
    phi0 = (1 - A) * (Y - m0h) / (1 - p) + m0h
    n = len(Y)
    v1 = np.var(phi1, ddof=1) / n
    v0 = np.var(phi0, ddof=1) / n
    cov10 = np.mean((phi1 - phi1.mean()) * (phi0 - phi0.mean())) / n
    z = 1.959964
    rd = mu1 - mu0
    se_rd = np.sqrt(v1 + v0 - 2 * cov10)
    rr = mu1 / mu0
    se_lrr = np.sqrt(v1 / mu1 ** 2 + v0 / mu0 ** 2 - 2 * cov10 / (mu1 * mu0))
    mu1c, mu0c = np.clip(mu1, 1e-6, 1 - 1e-6), np.clip(mu0, 1e-6, 1 - 1e-6)
    or_ = (mu1c / (1 - mu1c)) / (mu0c / (1 - mu0c))
    g1, g0 = 1 / (mu1c * (1 - mu1c)), 1 / (mu0c * (1 - mu0c))
    se_lor = np.sqrt(g1 ** 2 * v1 + g0 ** 2 * v0 - 2 * g1 * g0 * cov10)
    return dict(
        rd=(rd, rd - z * se_rd, rd + z * se_rd),
        rr=(rr, np.exp(np.log(rr) - z * se_lrr), np.exp(np.log(rr) + z * se_lrr)),
        or_=(or_, np.exp(np.log(or_) - z * se_lor), np.exp(np.log(or_) + z * se_lor)),
        p_or=p_from_z(np.log(or_) / se_lor),
        mu1=mu1, mu0=mu0,
    )


def fmt(e, nd=2):
    return f"{e:.{nd}f}"


def fit_ps_robust(X, A):
    """Fit propensity-score logit, dropping constant/near-constant columns that
    collapse in small complete-case subsets (otherwise the Hessian is singular)."""
    Xc = sm.add_constant(X)
    keep = [Xc.columns[0]] + [c for c in Xc.columns[1:] if Xc[c].std(ddof=0) > 1e-8]
    p = np.clip(np.asarray(sm.Logit(A, Xc[keep]).fit(disp=0).predict(Xc[keep]), float),
                1e-6, 1 - 1e-6)
    return p


def add_treated_uti(df):
    """Compute treated UTI (urine positive culture + abx) and attach as a column."""
    con = duckdb.connect()
    contam_sql = " OR ".join(f"LOWER(m.org_name) LIKE '%{c}%'" for c in CONTAM)
    abx_sql = " OR ".join(f"LOWER(r.drug) LIKE '%{a}%'" for a in ABX)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE c AS
    SELECT stay_id, subject_id, hadm_id, intime FROM read_csv_auto('{HERE}/cohort.csv')
    """)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE pu AS
    SELECT c.stay_id, c.hadm_id, m.charttime
    FROM c JOIN read_csv_auto('{M}/hosp/microbiologyevents.csv.gz') m
      ON c.subject_id = m.subject_id AND c.hadm_id = m.hadm_id
    WHERE m.charttime > c.intime + INTERVAL '48' HOUR
      AND m.charttime < c.intime + INTERVAL '28' DAY
      AND UPPER(m.spec_type_desc) LIKE '%URINE%'
      AND m.org_name IS NOT NULL
      AND LOWER(m.org_name) NOT LIKE '%no growth%'
      AND NOT ({contam_sql})
    """)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE tu AS
    SELECT DISTINCT pu.stay_id
    FROM pu JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON pu.hadm_id = r.hadm_id
    WHERE r.starttime BETWEEN pu.charttime - INTERVAL '1' DAY AND pu.charttime + INTERVAL '2' DAY
      AND ({abx_sql})
    """)
    ids = set(con.execute("SELECT stay_id FROM tu").df()["stay_id"])
    con.close()
    df["treated_uti"] = df["stay_id"].isin(ids).astype(int)
    return df


def analyze(d, Ycol, label, rows_out, ev):
    X, A = design_matrix(d)
    Xc = sm.add_constant(X)
    p = np.clip(np.asarray(sm.Logit(A, Xc).fit(disp=0).predict(Xc), float), 1e-6, 1 - 1e-6)
    ow = np.where(A == 1, 1 - p, p)
    p1 = A.mean()
    w_stab = np.where(A == 1, p1 / p, (1 - p1) / (1 - p))
    lo, hi = np.percentile(w_stab, [1, 99])
    w_stab_t = np.clip(w_stab, lo, hi)
    Y = d[Ycol].to_numpy(float)
    ev_t = int(np.sum((A == 1) & (Y == 1))); ev_c = int(np.sum((A == 0) & (Y == 1)))
    n_t = int(np.sum(A == 1)); n_c = int(np.sum(A == 0))
    rows_out.append(dict(label=label, outcome=Ycol, method="Crude",
                         n_t=n_t, n_c=n_c, ev_t=ev_t, ev_c=ev_c,
                         **{k: w_effect(Y, A, np.ones(len(Y)))[k] for k in ("rd", "rr", "or_", "p_or")}))
    for mname, w in [("OW", ow), ("IPTW", w_stab_t)]:
        e = w_effect(Y, A, w)
        rows_out.append(dict(label=label, outcome=Ycol, method=mname,
                             n_t=n_t, n_c=n_c, ev_t=ev_t, ev_c=ev_c, **e))
    a = aipw_effect(X, A, Y)
    rows_out.append(dict(label=label, outcome=Ycol, method="AIPW",
                         n_t=n_t, n_c=n_c, ev_t=ev_t, ev_c=ev_c,
                         rd=a["rd"], rr=a["rr"], or_=a["or_"], p_or=a["p_or"]))
    return ev


def main():
    df = add_treated_uti(load_cohort())
    rows = []
    for cfg in [("A", df.query("tf_any==1"), "A: EEN vs late EN"),
                ("B", df, "B: EEN vs no-EEN")]:
        for Ycol in ["infection_composite", "treated_uti"]:
            analyze(cfg[1], Ycol, cfg[2], rows, None)

    # ---- negative control + AIPW markdown ----
    md = ["# Negative-control outcome and doubly-robust AIPW\n"]
    md.append("Negative control = treated urinary-tract infection (urine positive culture + "
              "systemic antibiotic, same definition as the primary composite but at a site with "
              "no plausible EN mechanism). AIPW = augmented inverse-probability weighting "
              "(doubly robust; marginal RD/RR/OR).\n")
    cur = None
    for r in rows:
        if r["outcome"] != cur:
            cur = r["outcome"]
            md.append(f"\n## {cur}\n")
            md.append("| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |\n")
            md.append("|---|---|---|---|---|---|---|---|---|---|\n")
        md.append(f"| {r['label']} | {r['method']} | {r['n_t']} | {r['n_c']} | {r['ev_t']} | {r['ev_c']} | "
                  f"{fmt(r['rd'][0])} ({fmt(r['rd'][1])}, {fmt(r['rd'][2])}) | "
                  f"{fmt(r['rr'][0])} ({fmt(r['rr'][1])}, {fmt(r['rr'][2])}) | "
                  f"{fmt(r['or_'][0])} ({fmt(r['or_'][1])}, {fmt(r['or_'][2])}) | {fmt(r['p_or'], 3)} |\n")
    with open(os.path.join(HERE, "negative_control.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    # ---- missing data ----
    d = load_cohort()
    md2 = ["# Missing data\n"]
    md2.append("## Per-covariate missingness (landmarked cohort, n=%d)\n" % len(d))
    md2.append("| covariate | n | missing (%) |\n|---|---|---|\n")
    for c in CONT:
        if c in d.columns:
            x = pd.to_numeric(d[c], errors="coerce")
            md2.append(f"| {c} | {int(x.notna().sum())} | {100*x.isna().mean():.1f}% |\n")
    md2.append("\n## Complete-case OW sensitivity (infection composite)\n")
    md2.append("| comparison | n (complete-case) | EEN events | OW OR (95% CI) | p |\n|---|---|---|---|---|\n")
    for cfg in [("A: EEN vs late EN", d.query("tf_any==1")),
                ("B: EEN vs no-EEN", d)]:
        cc = cfg[1].dropna(subset=[c for c in CONT if c in cfg[1].columns])
        X, A = design_matrix(cc)
        p = fit_ps_robust(X, A)
        ow = np.where(A == 1, 1 - p, p)
        Y = cc["infection_composite"].to_numpy(float)
        e = w_effect(Y, A, ow)
        ev_t = int(np.sum((A == 1) & (Y == 1)))
        md2.append(f"| {cfg[0]} | {len(cc)} | {ev_t} | "
                   f"{fmt(e['or_'][0])} ({fmt(e['or_'][1])}, {fmt(e['or_'][2])}) | {fmt(e['p_or'], 3)} |\n")
    with open(os.path.join(HERE, "missing_data.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md2) + "\n")

    print("\n".join(md))
    print("\n" + "\n".join(md2))


if __name__ == "__main__":
    main()
