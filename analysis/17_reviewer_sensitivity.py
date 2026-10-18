# -*- coding: utf-8 -*-
"""
17_reviewer_sensitivity.py — reviewer-requested robustness checks (B-tier):

  B9. Post-48h reverse-causation sensitivity: re-estimate the primary infection
      composite with the outcome window START deferred from 48 h to 72 h (the
      48-h landmarked cohort is unchanged, so no new immortal-time bias). If an
      early infection (48–72 h) were both driving the feeding decision and the
      outcome, this should materially shift the comparison-A estimate.
  B10. Missingness-indicator sensitivity: add a missingness indicator for every
      covariate with >10% missingness (bilirubin, BMI, FiO2, lactate, PaO2) on
      top of median imputation, and re-estimate the primary outcome.

Reuses estimators (design_matrix, w_effect, aipw_effect, fit_ps_robust, ABX,
CONTAM, CONT, BIN, SITE, M) from 13_causal_hardening.py.

Output: analysis/reviewer_sensitivity.md
"""
import importlib
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
c13 = importlib.import_module("13_causal_hardening")
M = c13.M
CONT, BIN, SITE = c13.CONT, c13.BIN, c13.SITE
ABX, CONTAM = c13.ABX, c13.CONTAM

HIGH_MISSING = ["bili_max", "bmi", "fio2_max", "lactate_max", "po2_min"]


def fmt(e, nd=2):
    return f"{e:.{nd}f}"


def add_infection_window(df, hours):
    """Attach infection composite counted from `hours` after ICU intime (instead of 48h)."""
    contam_sql = " OR ".join(f"LOWER(m.org_name) LIKE '%{c}%'" for c in CONTAM)
    abx_sql = " OR ".join(f"LOWER(r.drug) LIKE '%{a}%'" for a in ABX)
    con = duckdb.connect()
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE c AS
    SELECT stay_id, subject_id, hadm_id, intime FROM read_csv_auto('{HERE}/cohort.csv')
    """)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE pos_events AS
    SELECT c.stay_id, c.hadm_id, m.charttime,
      CASE
        WHEN UPPER(m.spec_type_desc) LIKE '%BLOOD%' THEN 'blood'
        WHEN UPPER(m.spec_type_desc) LIKE '%PERITONEAL%' OR UPPER(m.spec_type_desc) LIKE '%ASCITES%'
          OR UPPER(m.spec_type_desc) LIKE '%BILE%' OR UPPER(m.spec_type_desc) LIKE '%ABSCESS%'
          OR UPPER(m.spec_type_desc) LIKE '%DRAIN%' THEN 'abdominal'
        WHEN UPPER(m.spec_type_desc) LIKE '%TRACHEAL%' OR UPPER(m.spec_type_desc) LIKE '%SPUTUM%'
          OR UPPER(m.spec_type_desc) LIKE '%BRONCH%' OR UPPER(m.spec_type_desc) LIKE '%BAL%'
          OR UPPER(m.spec_type_desc) LIKE '%RESPIRATORY%' OR UPPER(m.spec_type_desc) LIKE '%LUNG%' THEN 'respiratory'
        WHEN UPPER(m.spec_type_desc) LIKE '%WOUND%' OR UPPER(m.spec_type_desc) LIKE '%SWAB%'
          OR UPPER(m.spec_type_desc) LIKE '%TISSUE%' OR UPPER(m.spec_type_desc) LIKE '%SKIN%' THEN 'wound'
        WHEN UPPER(m.spec_type_desc) LIKE '%URINE%' THEN 'urine'
        ELSE 'other' END AS site
    FROM c JOIN read_csv_auto('{M}/hosp/microbiologyevents.csv.gz') m
      ON c.subject_id = m.subject_id AND c.hadm_id = m.hadm_id
    WHERE m.charttime > c.intime + INTERVAL '{hours}' HOUR
      AND m.charttime < c.intime + INTERVAL '28' DAY
      AND m.org_name IS NOT NULL
      AND LOWER(m.org_name) NOT LIKE '%no growth%'
      AND NOT ({contam_sql})
    """)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE treated AS
    SELECT DISTINCT pe.stay_id, pe.site
    FROM pos_events pe
    JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON pe.hadm_id = r.hadm_id
    WHERE r.starttime BETWEEN pe.charttime - INTERVAL '1' DAY AND pe.charttime + INTERVAL '2' DAY
      AND ({abx_sql})
    """)
    inf = con.execute("""
    SELECT stay_id, 1 AS x FROM treated
    WHERE site IN ('blood','abdominal','respiratory','wound') GROUP BY stay_id
    """).df()
    con.close()
    df["infection_72h"] = df["stay_id"].isin(set(inf["stay_id"])).astype(int)
    return df


def design_matrix_mi(d):
    """As design_matrix, but a missingness indicator for every >10%-missing covariate."""
    present = [c for c in CONT if c in d.columns]
    X = d[present].copy()
    for c in present:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    for c in HIGH_MISSING:
        if c in present:
            X[c + "_missing"] = X[c].isna().astype(int)
    for c in present:
        X[c] = X[c].fillna(X[c].median())
    for c in BIN:
        X[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)
    for s in SITE:
        X["site_" + s] = (d["site"] == s).astype(int)
    X = X.astype(float)
    return X, d["een48"].to_numpy(int)


def main():
    df = c13.load_cohort()

    # ---- B9: 72-h outcome window (reverse-causation sensitivity) ----
    df = add_infection_window(df, 72)
    rows = []
    for cfg in [("A", df.query("tf_any==1"), "A: EEN vs late EN"),
                ("B", df, "B: EEN vs no-EEN")]:
        c13.analyze(cfg[1], "infection_72h", cfg[2], rows, None)

    md = ["# Reviewer sensitivity analyses (72-h outcome window; missingness indicators)\n"]

    md.append("\n## B9. Post-48h reverse-causation sensitivity (infection composite, 72-h outcome window)\n")
    md.append("The 48-h landmarked cohort is unchanged; only the outcome window start is deferred "
              "from 48 h to 72 h (events 48–72 h after ICU admission are dropped from the outcome). "
              "A spurious protective association driven by early infection would attenuate here.\n")
    md.append("| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |\n")
    md.append("|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        md.append(f"| {r['label']} | {r['method']} | {r['n_t']} | {r['n_c']} | {r['ev_t']} | {r['ev_c']} | "
                  f"{fmt(r['rd'][0])} ({fmt(r['rd'][1])}, {fmt(r['rd'][2])}) | "
                  f"{fmt(r['rr'][0])} ({fmt(r['rr'][1])}, {fmt(r['rr'][2])}) | "
                  f"{fmt(r['or_'][0])} ({fmt(r['or_'][1])}, {fmt(r['or_'][2])}) | {fmt(r['p_or'], 3)} |\n")

    # ---- B10: missingness-indicator sensitivity ----
    md.append("\n## B10. Missingness-indicator sensitivity (primary infection composite)\n")
    md.append("Median imputation plus a missingness indicator for every covariate with >10% "
              "missingness (bilirubin, BMI, FiO2, lactate, PaO2), instead of only lactate.\n")
    md.append("| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |\n")
    md.append("|---|---|---|---|---|---|---|---|---|---|\n")
    for cfg in [("A: EEN vs late EN", df.query("tf_any==1")),
                ("B: EEN vs no-EEN", df)]:
        d = cfg[1]
        X, A = design_matrix_mi(d)
        p = c13.fit_ps_robust(X, A)
        ow = np.where(A == 1, 1 - p, p)
        p1 = A.mean()
        w_stab = np.where(A == 1, p1 / p, (1 - p1) / (1 - p))
        lo, hi = np.percentile(w_stab, [1, 99])
        w_stab_t = np.clip(w_stab, lo, hi)
        Y = d["infection_composite"].to_numpy(float)
        for mname, w in [("OW", ow), ("IPTW", w_stab_t)]:
            e = c13.w_effect(Y, A, w)
            ev_t = int(np.sum((A == 1) & (Y == 1)))
            ev_c = int(np.sum((A == 0) & (Y == 1)))
            n_t = int(np.sum(A == 1)); n_c = int(np.sum(A == 0))
            md.append(f"| {cfg[0]} | {mname} | {n_t} | {n_c} | {ev_t} | {ev_c} | "
                      f"{fmt(e['rd'][0])} ({fmt(e['rd'][1])}, {fmt(e['rd'][2])}) | "
                      f"{fmt(e['rr'][0])} ({fmt(e['rr'][1])}, {fmt(e['rr'][2])}) | "
                      f"{fmt(e['or_'][0])} ({fmt(e['or_'][1])}, {fmt(e['or_'][2])}) | {fmt(e['p_or'], 3)} |\n")
        a = c13.aipw_effect(X, A, Y)
        md.append(f"| {cfg[0]} | AIPW | {n_t} | {n_c} | {ev_t} | {ev_c} | "
                  f"{fmt(a['rd'][0])} ({fmt(a['rd'][1])}, {fmt(a['rd'][2])}) | "
                  f"{fmt(a['rr'][0])} ({fmt(a['rr'][1])}, {fmt(a['rr'][2])}) | "
                  f"{fmt(a['or_'][0])} ({fmt(a['or_'][1])}, {fmt(a['or_'][2])}) | {fmt(a['p_or'], 3)} |\n")

    with open(os.path.join(HERE, "reviewer_sensitivity.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
