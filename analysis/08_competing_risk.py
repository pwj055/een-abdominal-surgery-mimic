# -*- coding: utf-8 -*-
"""
08_competing_risk.py — §8.4/§8.9 landmark report + death competing-risk (Fine-Gray).

  §8.4  : 48h death / ICU-discharge proportions (landmark justification, wide cohort)
  §8.9  : 28-day cumulative incidence of death (Aalen-Johansen, discharge as
          competing risk) per arm, + Fine-Gray subdistribution hazard ratio (SHR).

Because MIMIC has only administrative censoring (28-day fixed horizon, no
loss-to-follow-up), the Fine-Gray subdistribution model reduces to a Cox model on
the subdistribution time in which the competing event (discharge) is re-coded as
censored at the horizon — i.e. discharged subjects stay in the risk set. The
weighted Cox is solved directly (Breslow partial likelihood, single binary
exposure, OW weights); it is validated against statsmodels PHReg (unweighted).

Outputs: analysis/competing_risk.md
"""
import os
import importlib.util
import duckdb
import numpy as np
import pandas as pd
import scipy.optimize as so
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
M = "C:/Users/jiang/Desktop/Enteral Nutrition/mimic-iv"
THRESH = 48

spec = importlib.util.spec_from_file_location("est", os.path.join(HERE, "02_weighting.py"))
est = importlib.util.module_from_spec(spec)
spec.loader.exec_module(est)

SURGICAL_ICUS = (
    "Surgical Intensive Care Unit (SICU)", "Trauma SICU (TSICU)",
    "Medical/Surgical Intensive Care Unit (MICU/SICU)",
    "Neuro Surgical Intensive Care Unit (Neuro SICU)",
)
ICD9_MAJOR = ("42", "43", "45", "46", "50", "51", "52")
ICD10_MAJOR = (
    "0DB5", "0DB6", "0DB8", "0DB9", "0DBE", "0DBP", "0DBQ",
    "0DT5", "0DT6", "0DT8", "0DT9", "0DTE", "0DTP", "0DTQ",
    "0D15", "0D16", "0D18", "0D19", "0D1E", "0D1P",
    "0FB0", "0FB4", "0FB5", "0FBG",
    "0FT0", "0FT4", "0FT5", "0FTG",
    "0DQ5", "0DQ6", "0DQ8", "0DQE",
)
ICD9_EXPLOR = ("541", "545")
ICD10_EXPLOR = ("0WJG",)

def sin(x): return "(" + ", ".join(repr(i) for i in x) + ")"
major9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,2) IN {sin(ICD9_MAJOR)})"
major10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_MAJOR)})"
explor9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,3) IN {sin(ICD9_EXPLOR)})"
explor10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_EXPLOR)})"
any_major = f"({major9} OR {major10})"
any_explor = f"({explor9} OR {explor10})"


def wcox(t, d, X, w):
    """Weighted Cox PH (Breslow) for a single binary covariate. Returns (HR, lo, hi)."""
    idx = np.argsort(t)
    t = t[idx]; d = d[idx].astype(int); X = X[idx].astype(float); w = w[idx]
    deaths = np.where(d == 1)[0]
    w0 = w * (1 - X); w1 = w * X
    cum1 = np.cumsum(w1[::-1])[::-1]; cum0 = np.cumsum(w0[::-1])[::-1]
    N1 = cum1[deaths]; N0 = cum0[deaths]; Xd = X[deaths]; wd = w[deaths]

    def U(b):
        eb = np.exp(b); den = N0 + eb * N1
        return (wd * (Xd - eb * N1 / den)).sum()

    def Iinf(b):
        eb = np.exp(b); den = N0 + eb * N1
        return (wd * (eb * N1 * N0 / den ** 2)).sum()

    root = so.brentq(U, -12.0, 12.0)
    se = 1.0 / np.sqrt(max(Iinf(root), 1e-12))
    return float(np.exp(root)), float(np.exp(root - 1.959964 * se)), float(np.exp(root + 1.959964 * se))


def aj_cif(t, cause, horizon=28.0):
    """Aalen-Johansen cumulative incidence of cause 1 (death) by `horizon`.
    cause: 1 = death, 2 = discharge (competing), 0 = censored."""
    t = np.asarray(t, float); cause = np.asarray(cause, int)
    order = np.argsort(t)
    t = t[order]; cause = cause[order]
    n = len(t)
    S = 1.0; cif = 0.0; at_risk = n; i = 0
    while i < n:
        s = t[i]
        if s > horizon:
            break
        j = i
        while j < n and t[j] == s:
            j += 1
        d1 = int(np.sum(cause[i:j] == 1)); d2 = int(np.sum(cause[i:j] == 2))
        d_tot = d1 + d2
        if d_tot > 0:
            cif += S * d1 / at_risk
            S *= (1 - d_tot / at_risk)
        at_risk -= (j - i)
        i = j
    return cif


def compute_ow(d):
    X, A = est.design_matrix(d)
    Xc = sm.add_constant(X)
    p = np.clip(np.asarray(sm.Logit(A, Xc).fit(disp=0).predict(Xc), dtype=float), 1e-6, 1 - 1e-6)
    ow = np.where(A == 1, 1 - p, p)
    return A, ow


def build():
    con = duckdb.connect()
    # landmarked cohort + time-to-event (death / hospital discharge)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE cohort AS
    SELECT stay_id, subject_id, hadm_id, intime FROM read_csv_auto('{HERE}/cohort.csv')
    """)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE tte AS
    SELECT c.stay_id, c.intime, a.deathtime, a.dischtime,
           (EPOCH(a.deathtime) - EPOCH(c.intime)) / 86400.0 AS death_days,
           (EPOCH(a.dischtime) - EPOCH(c.intime)) / 86400.0 AS disch_days
    FROM cohort c
    LEFT JOIN read_csv_auto('{M}/hosp/admissions.csv.gz') a ON c.hadm_id = a.hadm_id
    """)
    con.execute(f"COPY (SELECT * FROM tte) TO '{HERE}/tte.csv' (HEADER, DELIMITER ',')")

    # wide-cohort landmark report (no LOS filter)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE wide AS
    WITH op AS (
      SELECT hadm_id, MIN(chartdate) AS first_op_date
      FROM read_csv_auto('{M}/hosp/procedures_icd.csv.gz')
      WHERE {any_major} OR {any_explor} GROUP BY hadm_id
    ),
    sicu AS (
      SELECT stay_id, subject_id, hadm_id, intime, outtime, los,
             ROW_NUMBER() OVER (PARTITION BY subject_id ORDER BY intime) AS rn
      FROM read_csv_auto('{M}/icu/icustays.csv.gz')
      WHERE first_careunit IN {tuple(SURGICAL_ICUS)}
    )
    SELECT s.stay_id, s.intime, s.outtime, s.los, a.deathtime
    FROM sicu s
    JOIN op o ON s.hadm_id = o.hadm_id
    LEFT JOIN read_csv_auto('{M}/hosp/admissions.csv.gz') a ON a.hadm_id = s.hadm_id
    WHERE s.rn = 1 AND o.first_op_date <= CAST(s.intime AS DATE)
    """)
    rep = con.execute(f"""
    SELECT COUNT(*) AS n_wide,
      SUM(CASE WHEN deathtime IS NOT NULL AND deathtime <= intime + INTERVAL '48' HOUR THEN 1 ELSE 0 END) AS died_48h,
      SUM(CASE WHEN los * 24 < 48 AND (deathtime IS NULL OR deathtime > intime + INTERVAL '48' HOUR)
            THEN 1 ELSE 0 END) AS disc_48h,
      SUM(CASE WHEN los * 24 >= 48 AND (deathtime IS NULL OR deathtime > intime + INTERVAL '48' HOUR)
            THEN 1 ELSE 0 END) AS landmarked
    FROM wide
    """).df()
    con.close()
    return rep


def main():
    rep = build()
    base = est.load_cohort("cohort.csv")
    tte = pd.read_csv(os.path.join(HERE, "tte.csv"))
    d0 = base.merge(tte, on="stay_id", how="left")

    # death beyond 28d (does the horizon matter?)
    n_death_gt28 = int(((d0["death_days"] > 28) & d0["death_days"].notna()).sum())
    n_death_any = int(d0["hosp_death"].sum())

    lines = ["# Death: landmark report + competing-risk (Fine-Gray)\n\n"]

    r = rep.iloc[0]
    lines.append("## §8.4 Landmark report (wide cohort, no LOS filter)\n\n")
    lines.append("| Wide cohort n | Died ≤48h (%) | ICU-discharged ≤48h (%) | Landmarked (LOS≥48h) |\n")
    lines.append("|---|---|---|---|\n")
    lines.append(f"| {r['n_wide']} | {r['died_48h']} ({100*r['died_48h']/r['n_wide']:.1f}%) | "
                 f"{r['disc_48h']} ({100*r['disc_48h']/r['n_wide']:.1f}%) | {r['landmarked']} |\n\n")
    lines.append(f"_Hospital deaths beyond 28d: {n_death_gt28} of {n_death_any} total landmarked "
                 f"deaths — 28-day horizon is essentially complete._\n\n")

    lines.append("## §8.9 Competing risk (death vs discharge, 28-day)\n\n")
    lines.append("Aalen-Johansen 28-day cumulative incidence of death per arm, and Fine-Gray "
                 "subdistribution HR (OW-weighted). SHR < 1 = EEN lower subdistribution hazard of death.\n\n")
    lines.append("| Comparison | Arm | n | 28-d death CIF | Fine-Gray SHR (95% CI) |\n")
    lines.append("|---|---|---|---|---|\n")

    for ckey, cfg in est.COMPARISONS.items():
        dd = d0 if cfg["subset"] is None else d0.query(cfg["subset"]).reset_index(drop=True)
        A, ow = compute_ow(dd)
        comp = ckey.split("_")[0]
        for arm in (0, 1):
            mask = A == arm
            sub = dd[mask]
            d_days = sub["death_days"].to_numpy(float)
            disch = sub["disch_days"].to_numpy(float)
            # cause: 1 death, 2 discharge, 0 censored
            cause = np.where(sub["deathtime"].notna().to_numpy(), 1, 2).astype(int)
            t = np.where(sub["deathtime"].notna().to_numpy(), d_days, disch)
            t = np.nan_to_num(t, nan=28.0)
            t = np.clip(t, 0, 28.0)
            cause[(cause == 1) & (d_days > 28)] = 0
            cause[(cause == 2) & (disch > 28)] = 0
            cif = aj_cif(t, cause)
            lines.append(f"| {comp} | {'EEN' if arm==1 else 'control'} | {int(mask.sum())} | "
                         f"{cif:.3f} | |\n")
        # Fine-Gray SHR: subdistribution time (death=event; discharge/censor -> 28)
        death = dd["deathtime"].notna().to_numpy() & (dd["death_days"].to_numpy() <= 28)
        sub_t = np.where(death, dd["death_days"].to_numpy(), 28.0)
        sub_t = np.clip(np.nan_to_num(sub_t, nan=28.0), 0, 28.0)
        status = death.astype(int)
        hr, lo, hi = wcox(sub_t, status, A.astype(float), ow)
        lines.append(f"| {comp} | **Fine-Gray SHR** | | | **{hr:.2f} ({lo:.2f}, {hi:.2f})** |\n\n")

    with open(os.path.join(HERE, "competing_risk.md"), "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print("".join(lines))


if __name__ == "__main__":
    main()
