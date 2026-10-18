# -*- coding: utf-8 -*-
"""
14_mimic3_replication.py — same-center, earlier-era sensitivity replication in MIMIC-III v1.4.

MIMIC-III is the *same hospital* (BIDMC) with partially overlapping years (2001-2012 vs
MIMIC-IV 2008-2019), so this is a temporal/same-center robustness check, NOT a true
external validation. The carevue era (2001-2008) is disjoint from MIMIC-IV.

Mirrors 01_build_dataset.py where the schema allows, with documented deviations:
  * Surgical ICUs = SICU / TSICU (no 'MICU/SICU' combined unit in MIMIC-III).
  * ICD-9 only (no ICD-10); codes stored without a decimal point.
  * PROCEDURES_ICD has NO date -> the "surgery on/before ICU day" filter is DROPPED
    (a surgical-ICU admission carrying a major abdominal procedure is assumed to follow
    the procedure) and the date-dependent leak/reoperation outcome is SKIPPED.
  * PRESCRIPTIONS is date-granular (STARTDATE only) -> the antibiotic window is compared
    on dates, not timestamps.
  * Mechanical ventilation + chart-based SOFA physiology (GCS/MAP/FiO2/PaO2) are
    extracted from CHARTEVENTS/LABEVENTS; BMI is omitted (MIMIC-III has no omr table).
  * Age from DOB (shifted DOB for >89yo -> 91.4).

Outputs: analysis/mimic3_cohort.csv, analysis/mimic3_replication.md
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
M3 = "D:/physionet/mimic3"
OUT = os.path.join(HERE, "mimic3_cohort.csv")

CONT = ["age", "n_major_procs", "lactate_max", "creat_max", "wbc_max", "plt_min", "bili_max",
        "po2_min", "map_min", "fio2_max", "gcs_min"]
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

VASO_MV = (221906, 221289, 222315, 221662, 221749)          # norepi, epi, vaso, dopa, phenyle
VASO_CV = (30047, 30044, 30051, 30043, 30042, 30119, 30120, 30307, 30309)  # levophed, epi, vaso, dopa, dobut, epi-k, levo-k, dopa-drip, epi-drip
TF_CV = (30090, 45700, 46498)                                # 'Tube Feeding', 'REPLETE/FIBER TFEED', 'good start formula'
CHART_ITEMS = (
    720, 223849,              # ventilator mode (carevue / metavision)
    198,                      # carevue GCS total
    220739, 223900, 223901,   # metavision GCS eye / verbal / motor
    52, 456,                  # carevue MAP (arterial / non-invasive)
    220052, 220181,           # metavision MAP (arterial / non-invasive)
    190, 3420, 223835,        # FiO2 (carevue / carevue / metavision)
)


def sin(x):
    return "(" + ", ".join(repr(i) for i in x) + ")"


def build():
    con = duckdb.connect()

    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE op AS
    SELECT hadm_id,
           MAX(CASE WHEN SUBSTRING(icd9_code,1,3) IN ('541','545') THEN 1 ELSE 0 END) AS any_explor,
           COUNT(DISTINCT CASE WHEN SUBSTRING(icd9_code,1,2) IN ('42','43','45','46','50','51','52')
                          THEN icd9_code END) AS n_major_procs,
           MAX(CASE WHEN SUBSTRING(icd9_code,1,2) IN ('42','43') THEN 1 ELSE 0 END) AS upper,
           MAX(CASE WHEN SUBSTRING(icd9_code,1,2) IN ('45','46') THEN 1 ELSE 0 END) AS lower,
           MAX(CASE WHEN SUBSTRING(icd9_code,1,2) IN ('50','51','52') THEN 1 ELSE 0 END) AS hpb,
           MAX(CASE WHEN SUBSTRING(icd9_code,1,3) IN ('461','462') THEN 1 ELSE 0 END) AS stoma
    FROM read_csv_auto('{M3}/PROCEDURES_ICD.csv.gz')
    WHERE SUBSTRING(icd9_code,1,2) IN ('42','43','45','46','50','51','52')
       OR SUBSTRING(icd9_code,1,3) IN ('541','545')
    GROUP BY hadm_id
    """)

    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE sicu AS
    SELECT icustay_id, subject_id, hadm_id, intime, outtime, los,
           ROW_NUMBER() OVER (PARTITION BY subject_id ORDER BY intime) AS rn
    FROM read_csv_auto('{M3}/ICUSTAYS.csv.gz')
    WHERE first_careunit IN ('SICU','TSICU')
    """)

    # eligible (pre-landmark) for the flow count
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE eligible AS
    SELECT s.icustay_id, s.subject_id, s.hadm_id, s.intime, s.outtime, s.los,
           a.deathtime
    FROM sicu s
    JOIN op o ON s.hadm_id = o.hadm_id
    LEFT JOIN read_csv_auto('{M3}/ADMISSIONS.csv.gz') a ON a.hadm_id = s.hadm_id
    WHERE s.rn = 1
    """)
    flow = con.execute("""
        SELECT COUNT(*) AS eligible,
               SUM(CASE WHEN deathtime IS NOT NULL AND deathtime <= intime + INTERVAL '48' HOUR THEN 1 ELSE 0 END) AS died48,
               SUM(CASE WHEN los*24 < 48 AND (deathtime IS NULL OR deathtime > intime + INTERVAL '48' HOUR) THEN 1 ELSE 0 END) AS disch48
        FROM eligible
    """).df().to_dict("records")[0]

    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE cohort AS
    SELECT s.icustay_id, s.subject_id, s.hadm_id, s.intime, s.outtime, s.los,
           o.any_explor, o.n_major_procs, o.upper, o.lower, o.hpb, o.stoma,
           a.admission_type, a.deathtime,
           p.gender,
           CASE WHEN p.dob IS NULL OR EXTRACT(YEAR FROM p.dob) < 1900 THEN 91.4
                ELSE EXTRACT(YEAR FROM s.intime) - EXTRACT(YEAR FROM p.dob) END AS age
    FROM sicu s
    JOIN op o ON s.hadm_id = o.hadm_id
    LEFT JOIN read_csv_auto('{M3}/ADMISSIONS.csv.gz') a ON a.hadm_id = s.hadm_id
    LEFT JOIN read_csv_auto('{M3}/PATIENTS.csv.gz') p ON p.subject_id = s.subject_id
    WHERE s.rn = 1 AND s.los*24 >= 48
      AND (a.deathtime IS NULL OR a.deathtime > s.intime + INTERVAL '48' HOUR)
    """)

    # exposure: metavision 'Nutrition - Enteral' + carevue tube-feeding items
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE tf AS
    SELECT icustay_id, MIN(t) AS first_tf FROM (
      SELECT e.icustay_id, e.starttime AS t
      FROM read_csv_auto('{M3}/INPUTEVENTS_MV.csv.gz') e
      JOIN read_csv_auto('{M3}/D_ITEMS.csv.gz') d ON e.itemid = d.itemid
      WHERE d.category = 'Nutrition - Enteral' AND (e.rate >= 10 OR e.amount >= 20)
      UNION ALL
      SELECT e.icustay_id, e.charttime AS t
      FROM read_csv_auto('{M3}/INPUTEVENTS_CV.csv.gz') e
      WHERE e.itemid IN {sin(TF_CV)} AND (TRY_CAST(e.rate AS DOUBLE) >= 10 OR TRY_CAST(e.amount AS DOUBLE) >= 20)
    ) GROUP BY icustay_id
    """)

    # 0-24h labs (same itemids as MIMIC-IV)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE lab AS
    SELECT c.icustay_id,
           MAX(CASE WHEN le.itemid = 50813 THEN le.valuenum END) AS lactate_max,
           MAX(CASE WHEN le.itemid = 50912 THEN le.valuenum END) AS creat_max,
           MAX(CASE WHEN le.itemid = 51301 THEN le.valuenum END) AS wbc_max,
           MIN(CASE WHEN le.itemid = 51265 THEN le.valuenum END) AS plt_min,
           MAX(CASE WHEN le.itemid = 50885 THEN le.valuenum END) AS bili_max,
           MIN(CASE WHEN le.itemid = 50821 THEN le.valuenum END) AS po2_min
    FROM cohort c
    JOIN read_csv_auto('{M3}/LABEVENTS.csv.gz') le ON c.hadm_id = le.hadm_id
    WHERE le.itemid IN (50813, 50912, 51301, 51265, 50885, 50821)
      AND le.valuenum IS NOT NULL
      AND le.charttime BETWEEN c.intime AND c.intime + INTERVAL '24' HOUR
    GROUP BY c.icustay_id
    """)

    # 0-24h vasopressors (both eras)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE vaso AS
    SELECT v.icustay_id, 1 AS vaso_24h
    FROM (
      SELECT icustay_id, starttime AS t FROM read_csv_auto('{M3}/INPUTEVENTS_MV.csv.gz')
        WHERE itemid IN {sin(VASO_MV)}
      UNION ALL
      SELECT icustay_id, charttime AS t FROM read_csv_auto('{M3}/INPUTEVENTS_CV.csv.gz')
        WHERE itemid IN {sin(VASO_CV)}
    ) v JOIN cohort c ON v.icustay_id = c.icustay_id
    WHERE v.t BETWEEN c.intime AND c.intime + INTERVAL '24' HOUR
    GROUP BY v.icustay_id
    """)

    # single 0-24h CHARTEVENTS scan: ventilator mode + GCS/MAP/FiO2 (SOFA physiology)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE charts AS
    SELECT c.icustay_id, ch.itemid, ch.valuenum, ch.value, ch.charttime
    FROM cohort c
    JOIN read_csv_auto('{M3}/CHARTEVENTS.csv.gz', types={{'VALUE':'VARCHAR'}}) ch
      ON c.icustay_id = ch.icustay_id
    WHERE ch.itemid IN {sin(CHART_ITEMS)}
      AND ch.charttime BETWEEN c.intime AND c.intime + INTERVAL '24' HOUR
    """)

    # 0-24h mechanical ventilation
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE mv AS
    SELECT DISTINCT icustay_id, 1 AS mv_24h
    FROM charts WHERE itemid IN (720, 223849)
    """)

    # 0-24h MAP (min) + FiO2 (max, percent-normalized)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE map_fio AS
    SELECT icustay_id,
           MIN(CASE WHEN itemid IN (52, 456, 220052, 220181) AND valuenum BETWEEN 10 AND 300
                    THEN valuenum END) AS map_min,
           MAX(CASE WHEN itemid IN (190, 3420, 223835) AND valuenum BETWEEN 0.1 AND 100
                    THEN CASE WHEN valuenum > 1 THEN valuenum / 100.0 ELSE valuenum END END) AS fio2_max
    FROM charts GROUP BY icustay_id
    """)

    # 0-24h GCS (min total): carevue total 198 + metavision components summed per minute
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE gcs AS
    SELECT icustay_id, MIN(g) AS gcs_min FROM (
      SELECT icustay_id, TRY_CAST(TRIM(value) AS DOUBLE) AS g
      FROM charts
      WHERE itemid = 198 AND TRY_CAST(TRIM(value) AS DOUBLE) BETWEEN 3 AND 15
      UNION ALL
      SELECT icustay_id, MIN(eye + verbal + motor) AS g
      FROM (
        SELECT icustay_id, DATE_TRUNC('minute', charttime) AS t,
               MAX(CASE WHEN itemid = 220739 THEN valuenum END) AS eye,
               MAX(CASE WHEN itemid = 223900 THEN valuenum END) AS verbal,
               MAX(CASE WHEN itemid = 223901 THEN valuenum END) AS motor
        FROM charts GROUP BY icustay_id, DATE_TRUNC('minute', charttime)
      )
      WHERE eye IS NOT NULL AND verbal IS NOT NULL AND motor IS NOT NULL
      GROUP BY icustay_id
    ) GROUP BY icustay_id
    """)

    # Elixhauser (ICD-9 only)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE elix AS
    SELECT hadm_id,
           MAX(CASE WHEN icd9_code LIKE '250%' THEN 1 ELSE 0 END) AS diabetes,
           MAX(CASE WHEN icd9_code LIKE '585%' THEN 1 ELSE 0 END) AS ckd,
           MAX(CASE WHEN icd9_code LIKE '5712%' OR icd9_code LIKE '5715%' THEN 1 ELSE 0 END) AS cirrhosis
    FROM read_csv_auto('{M3}/DIAGNOSES_ICD.csv.gz')
    GROUP BY hadm_id
    """)

    # positive cultures >48h & <28d, contaminant-excluded
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE pos_events AS
    SELECT c.icustay_id, c.hadm_id, m.charttime,
           CASE WHEN UPPER(m.spec_type_desc) LIKE 'BLOOD CULTURE%' THEN 'blood'
                WHEN UPPER(m.spec_type_desc) LIKE '%PERITONEAL%' OR UPPER(m.spec_type_desc) LIKE '%ABDOMINAL%'
                  OR UPPER(m.spec_type_desc) LIKE '%ASCITES%' OR UPPER(m.spec_type_desc) LIKE '%BILE%'
                  OR UPPER(m.spec_type_desc) LIKE '%ABSCESS%' OR UPPER(m.spec_type_desc) LIKE '%DRAIN%' THEN 'abdominal'
                WHEN UPPER(m.spec_type_desc) LIKE '%TRACHEAL%' OR UPPER(m.spec_type_desc) LIKE '%SPUTUM%'
                  OR UPPER(m.spec_type_desc) LIKE '%BRONCH%' OR UPPER(m.spec_type_desc) LIKE '%BAL%'
                  OR UPPER(m.spec_type_desc) LIKE '%RESPIRATORY%' OR UPPER(m.spec_type_desc) LIKE '%LUNG%' THEN 'respiratory'
                WHEN UPPER(m.spec_type_desc) LIKE '%WOUND%' OR UPPER(m.spec_type_desc) LIKE '%SWAB%'
                  OR UPPER(m.spec_type_desc) LIKE '%TISSUE%' OR UPPER(m.spec_type_desc) LIKE '%SKIN%' THEN 'wound'
                WHEN UPPER(m.spec_type_desc) LIKE '%URINE%' THEN 'urine'
                ELSE 'other' END AS site
    FROM cohort c
    JOIN read_csv_auto('{M3}/MICROBIOLOGYEVENTS.csv.gz') m
      ON c.subject_id = m.subject_id AND c.hadm_id = m.hadm_id
    WHERE m.charttime > c.intime + INTERVAL '48' HOUR
      AND m.charttime < c.intime + INTERVAL '28' DAY
      AND m.org_name IS NOT NULL
      AND LOWER(m.org_name) NOT LIKE '%no growth%'
      AND NOT ({(" OR ".join(f"LOWER(m.org_name) LIKE '%{c}%'" for c in CONTAM))})
    """)

    # treated = antibiotic around the culture (date-granular in MIMIC-III)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE treated AS
    SELECT DISTINCT pe.icustay_id, pe.site
    FROM pos_events pe
    JOIN read_csv_auto('{M3}/PRESCRIPTIONS.csv.gz') r ON pe.hadm_id = r.hadm_id
    WHERE r.startdate BETWEEN pe.charttime - INTERVAL '1' DAY AND pe.charttime + INTERVAL '2' DAY
      AND ({(" OR ".join(f"LOWER(r.drug) LIKE '%{a}%'" for a in ABX))})
    """)

    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE final AS
    SELECT
      c.icustay_id, c.subject_id, c.hadm_id, c.intime, c.los AS icu_los,
      c.age,
      CASE WHEN c.gender = 'F' THEN 1 ELSE 0 END AS female,
      CASE WHEN c.admission_type IN ('EMERGENCY','URGENT') THEN 1 ELSE 0 END AS emergency,
      CASE WHEN c.hpb = 1 THEN 'hpb' WHEN c.upper = 1 THEN 'upper'
           WHEN c.lower = 1 THEN 'lower' ELSE 'other' END AS site,
      c.stoma, c.any_explor, c.n_major_procs,
      l.lactate_max, l.creat_max, l.wbc_max, l.plt_min, l.bili_max, l.po2_min,
      mf.map_min, mf.fio2_max, gc.gcs_min,
      COALESCE(v.vaso_24h, 0) AS vaso_24h,
      COALESCE(m.mv_24h, 0) AS mv_24h,
      COALESCE(e.diabetes, 0) AS diabetes,
      COALESCE(e.ckd, 0) AS ckd,
      COALESCE(e.cirrhosis, 0) AS cirrhosis,
      CASE WHEN t.first_tf <= c.intime + INTERVAL '48' HOUR THEN 'EEN'
           WHEN t.first_tf IS NULL THEN 'never' ELSE 'late' END AS grp,
      CASE WHEN t.first_tf <= c.intime + INTERVAL '48' HOUR THEN 1 ELSE 0 END AS een48,
      CASE WHEN t.first_tf IS NOT NULL THEN 1 ELSE 0 END AS tf_any,
      CASE WHEN t.first_tf IS NOT NULL THEN (EPOCH(t.first_tf) - EPOCH(c.intime)) / 3600.0 END AS first_tf_hours,
      CASE WHEN tb.icustay_id IS NOT NULL THEN 1 ELSE 0 END AS treated_bsi,
      CASE WHEN tc.icustay_id IS NOT NULL THEN 1 ELSE 0 END AS infection_composite,
      CASE WHEN tu.icustay_id IS NOT NULL THEN 1 ELSE 0 END AS treated_uti,
      CASE WHEN c.deathtime IS NOT NULL THEN 1 ELSE 0 END AS hosp_death
    FROM cohort c
    LEFT JOIN tf t USING (icustay_id)
    LEFT JOIN lab l USING (icustay_id)
    LEFT JOIN map_fio mf USING (icustay_id)
    LEFT JOIN gcs gc USING (icustay_id)
    LEFT JOIN vaso v USING (icustay_id)
    LEFT JOIN mv m USING (icustay_id)
    LEFT JOIN elix e USING (hadm_id)
    LEFT JOIN (SELECT icustay_id FROM treated WHERE site='blood' GROUP BY icustay_id) tb USING (icustay_id)
    LEFT JOIN (SELECT icustay_id FROM treated WHERE site IN ('blood','abdominal','respiratory','wound') GROUP BY icustay_id) tc USING (icustay_id)
    LEFT JOIN (SELECT icustay_id FROM treated WHERE site='urine' GROUP BY icustay_id) tu USING (icustay_id)
    """)

    con.execute(f"COPY (SELECT * FROM final) TO '{OUT}' (HEADER, DELIMITER ',')")
    n = con.execute("SELECT COUNT(*) FROM final").fetchone()[0]
    tally = con.execute("""
        SELECT grp, COUNT(*) n, SUM(infection_composite) infect, SUM(treated_uti) uti, SUM(hosp_death) death
        FROM final GROUP BY grp ORDER BY n DESC
    """).df()
    con.close()
    return flow, n, tally


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


def fmt(e, nd=2):
    return f"{e:.{nd}f}"


def analyze(df, Ycol, label, rows):
    X, A = design_matrix(df)
    Xc = sm.add_constant(X)
    p = np.clip(np.asarray(sm.Logit(A, Xc).fit(disp=0).predict(Xc), float), 1e-6, 1 - 1e-6)
    ow = np.where(A == 1, 1 - p, p)
    Y = df[Ycol].to_numpy(float)
    ev_t = int(np.sum((A == 1) & (Y == 1))); ev_c = int(np.sum((A == 0) & (Y == 1)))
    n_t = int(np.sum(A == 1)); n_c = int(np.sum(A == 0))
    for mname, w in [("Crude", np.ones(len(Y))), ("OW", ow)]:
        e = w_effect(Y, A, w)
        rows.append(dict(label=label, outcome=Ycol, method=mname,
                         n_t=n_t, n_c=n_c, ev_t=ev_t, ev_c=ev_c, **e))
    return


def main():
    flow, n, tally = build()
    df = pd.read_csv(OUT)

    rows = []
    for cfg in [("A: EEN vs late EN", df.query("tf_any==1")),
                ("B: EEN vs no-EEN", df)]:
        for Ycol in ["infection_composite", "treated_uti"]:
            analyze(cfg[1], Ycol, cfg[0], rows)

    md = ["# MIMIC-III v1.4 replication (same-center, earlier era)\n",
          "Temporal/same-center sensitivity check, NOT external validation: MIMIC-III and "
          "MIMIC-IV are the same hospital (BIDMC) with overlapping years (2001-2012 vs "
          "2008-2019); the carevue era (2001-2008) is disjoint from MIMIC-IV. Deviations from "
          "the MIMIC-IV pipeline: no procedure date (surgery-before-ICU filter dropped; "
          "leak/reoperation skipped), date-granular prescriptions, and BMI omitted (no omr "
          "table); chart-based SOFA physiology (GCS/MAP/FiO2/PaO2), mechanical ventilation, "
          "vasopressors, lactate and organ labs are all extracted.\n",
          f"## Cohort flow\n",
          f"- Eligible (first SICU/TSICU stay + major abdominal ICD-9 procedure): {flow['eligible']}\n",
          f"- Died <=48 h: {flow['died48']}  |  ICU-discharged <=48 h: {flow['disch48']}\n",
          f"- Landmarked (LOS>=48 h & survival to 48 h): **{n}**\n",
          "\n## Exposure/outcome tallies\n",
          "| grp | n | infection | treated UTI | death |\n|---|---|---|---|---|\n",
          "\n".join(f"| {r.grp} | {r.n} | {r.infect} | {r.uti} | {r.death} |" for r in tally.itertuples()),
          "\n\n## Comparison A and B (overlap weighting, primary infection composite + negative control)\n",
          "| comparison | outcome | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |\n",
          "|---|---|---|---|---|---|---|---|---|---|---|\n"]
    cur = None
    for r in rows:
        if r["outcome"] != cur:
            cur = r["outcome"]
            md.append(f"\n### {cur}\n")
        md.append(f"| {r['label']} | {r['method']} | {r['n_t']} | {r['n_c']} | {r['ev_t']} | {r['ev_c']} | "
                  f"{fmt(r['rd'][0])} ({fmt(r['rd'][1])}, {fmt(r['rd'][2])}) | "
                  f"{fmt(r['rr'][0])} ({fmt(r['rr'][1])}, {fmt(r['rr'][2])}) | "
                  f"{fmt(r['or_'][0])} ({fmt(r['or_'][1])}, {fmt(r['or_'][2])}) | {fmt(r['p_or'], 3)} |\n")
    md.append("\n")
    with open(os.path.join(HERE, "mimic3_replication.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
