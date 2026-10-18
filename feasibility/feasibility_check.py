# -*- coding: utf-8 -*-
"""
Feasibility check — Early Enteral Nutrition (EEN) after Major Abdominal Surgery
Target trial emulation cohort in MIMIC-IV.

Purpose: produce the go/no-go metrics (F1–F9) BEFORE committing to analysis.
See protocol.md for the locked design decisions this script operationalizes.

Setup
-----
1. Download MIMIC-IV (v3.x) from PhysioNet (requires credentialed access, CITI).
2. Keep the standard folder layout: hosp/  icu/  with *.csv or *.csv.gz (MIMIC-IV v3.x has NO core/).
3. Set MIMIC_DIR below to the parent folder containing those subfolders.
4. pip install duckdb

Run
----
python feasibility_check.py

Nothing here is "final analysis"; it is for go/no-go decisions only.
"""

import os
import sys

import duckdb

# ---------------------------------------------------------------- config
MIMIC_DIR = r"D:/physionet/mimic-iv"  # <-- EDIT ME

CORE = os.path.join(MIMIC_DIR, "core")
HOSP = os.path.join(MIMIC_DIR, "hosp")
ICU = os.path.join(MIMIC_DIR, "icu")

# Manually curated tube-feed itemids (paste here AFTER reviewing F2 output).
# If left as None, the script auto-discovers via d_items keywords.
TF_ITEMIDS_OVERRIDE = None


def f(d, name):
    """Return the (gz-aware) absolute path to a MIMIC csv file."""
    for cand in (name, name + ".gz"):
        p = os.path.join(d, cand)
        if os.path.exists(p):
            return p.replace("\\", "/")
    raise FileNotFoundError(f"{name} not found under {d}")


# ---------------------------------------------------------------- code lists
SURGICAL_ICUS = (
    "Surgical Intensive Care Unit (SICU)",
    "Trauma SICU (TSICU)",
    "Medical/Surgical Intensive Care Unit (MICU/SICU)",
    "Neuro Surgical Intensive Care Unit (Neuro SICU)",
)

# Major abdominal surgery — ICD-9-PCS (stored without decimal: '4351' = 43.51)
ICD9_MAJOR = ("42", "43", "45", "46", "50", "51", "52")
ICD9_EXPLOR = ("541", "545")          # laparotomy / adhesiolysis -> emergency marker
# Major abdominal surgery — ICD-10-PCS (match first 4 chars). PROVISIONAL: validate vs mimic-code.
ICD10_MAJOR = (
    "0DB5", "0DB6", "0DB8", "0DB9", "0DBE", "0DBP", "0DBQ",
    "0DT5", "0DT6", "0DT8", "0DT9", "0DTE", "0DTP", "0DTQ",
    "0D15", "0D16", "0D18", "0D19", "0D1E", "0D1P",
    "0FB0", "0FB4", "0FB5", "0FBG",
    "0FT0", "0FT4", "0FT5", "0FTG",
    "0DQ5", "0DQ6", "0DQ8", "0DQE",
)
ICD10_EXPLOR = ("0WJG",)   # inspection of peritoneal cavity (exploratory laparotomy)

# Tube-feed keyword discovery (label/abbreviation/category), case-insensitive
TF_KEYWORDS = (
    "tube feed", "tube feeding", "enteral", "jevity", "nepro", "osmolite",
    "promote", "nutren", "peptamen", "isosource", "glucerna", "vital",
    "impact", "fibresource", "ensure", "twocal", "two cal", "magnacal",
    "probalance", "compleat", "ng feed", "og feed", "peg", "j-tube",
)
TF_EXCLUDE = (
    "residual", "flush", "aspirate", "discard", "gastric output",
    "stool", "emesis", "vomit", "resid", "parenteral", "tpn",
)

# Antibiotics for "treated" BSI (lowercase generic; PROVISIONAL, expand via mimic-code)
ANTIBIOTICS = (
    "amikacin", "amoxicillin", "ampicillin", "azithromycin", "aztreonam",
    "cefazolin", "cefepime", "cefotaxime", "cefoxitin", "ceftaroline",
    "ceftazidime", "ceftriaxone", "cefuroxime", "cephalexin", "ciprofloxacin",
    "clindamycin", "daptomycin", "doxycycline", "ertapenem", "gentamicin",
    "imipenem", "levofloxacin", "linezolid", "meropenem", "metronidazole",
    "nafcillin", "oxacillin", "penicillin", "piperacillin", "sulfamethoxazole",
    "tobramycin", "trimethoprim", "vancomycin", "tigecycline", "colistin",
    "cefoperazone", "cloxacillin", "moxifloxacin",
)

# Blood-culture contaminants to exclude (lowercase)
CONTAMINANTS = (
    "coagulase negative", "coagulase-negative", "epidermidis",
    "corynebacterium", "diphtheroid", "micrococcus", "propionibacterium",
    "bacillus", "viridans",
)

# Anastomotic leak (PROVISIONAL; layered specificity is the real analysis)
# NOTE: MIMIC-IV stores ICD-10-CM codes WITHOUT the decimal point (e.g. 'K9189', 'T814XXA').
# '9983' (disruption of op wound) has 0 rows in v3.1 — kept for completeness.
ICD9_LEAK = ("9974", "56981", "9983")
ICD10_LEAK = ("K9189", "K632")      # exact match
ICD10_LEAK_PREFIX = ("T814",)       # T81.4 family (T814XXA / T8141XA / ...) -> prefix match


def sql_in(expr, items):
    return f"{expr} IN ({', '.join(repr(i) for i in items)})"


def sql_ilike_any(col, items):
    return "(" + " OR ".join(f"LOWER({col}) LIKE '%{i}%'" for i in items) + ")"


# ---------------------------------------------------------------- helpers
def run(con, sql, label):
    print("\n" + "=" * 72)
    print(label)
    print("=" * 72)
    df = con.execute(sql).df()
    print(df.to_string(index=False))
    return df


def main():
    if not os.path.isdir(MIMIC_DIR):
        sys.exit(
            f"\nMIMIC_DIR not found: {MIMIC_DIR}\n"
            "Download MIMIC-IV first (see README.md), then set MIMIC_DIR.\n"
        )

    con = duckdb.connect()

    # ----- paths -----
    icustays_p = f(ICU, "icustays.csv")
    admissions_p = f(HOSP, "admissions.csv")   # MIMIC-IV v3.x: admissions/patients/transfers live under hosp/, no core/
    patients_p = f(HOSP, "patients.csv")
    proc_icd_p = f(HOSP, "procedures_icd.csv")
    diag_icd_p = f(HOSP, "diagnoses_icd.csv")
    d_items_p = f(ICU, "d_items.csv")
    inputevents_p = f(ICU, "inputevents.csv")
    micro_p = f(HOSP, "microbiologyevents.csv")
    rx_p = f(HOSP, "prescriptions.csv")
    lab_p = f(HOSP, "labevents.csv")
    proc_events_p = f(ICU, "procedureevents.csv")

    # ----- shared condition fragments -----
    major9 = f"(icd_version = 9 AND {sql_in('SUBSTRING(icd_code,1,2)', ICD9_MAJOR)})"
    explor9 = f"(icd_version = 9 AND {sql_in('SUBSTRING(icd_code,1,3)', ICD9_EXPLOR)})"
    major10 = f"(icd_version = 10 AND {sql_in('SUBSTRING(icd_code,1,4)', ICD10_MAJOR)})"
    explor10 = f"(icd_version = 10 AND {sql_in('SUBSTRING(icd_code,1,4)', ICD10_EXPLOR)})"
    any_major = f"({major9} OR {major10})"
    any_explor = f"({explor9} OR {explor10})"

    # ================================================================
    # F1 — cohort build (first surgical ICU stay with major abdominal surgery)
    # ================================================================
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE cohort AS
        WITH op AS (
            SELECT hadm_id,
                   MIN(chartdate) AS first_op_date,
                   MAX(CASE WHEN {major9} THEN 1 ELSE 0 END) AS has_icd9,
                   MAX(CASE WHEN {major10} THEN 1 ELSE 0 END) AS has_icd10,
                   MAX(CASE WHEN {any_explor} THEN 1 ELSE 0 END) AS any_explor
            FROM read_csv_auto('{proc_icd_p}')
            WHERE {any_major} OR {any_explor}
            GROUP BY hadm_id
        ),
        sicu AS (
            SELECT stay_id, subject_id, hadm_id, intime, outtime, los,
                   ROW_NUMBER() OVER (PARTITION BY subject_id ORDER BY intime) AS rn
            FROM read_csv_auto('{icustays_p}')
            WHERE first_careunit IN {tuple(SURGICAL_ICUS)}
        )
        SELECT s.stay_id, s.subject_id, s.hadm_id, s.intime, s.outtime, s.los,
               o.first_op_date, o.has_icd9, o.has_icd10, o.any_explor,
               a.admission_type, a.deathtime, p.dod
        FROM sicu s
        JOIN op o ON s.hadm_id = o.hadm_id
        LEFT JOIN read_csv_auto('{admissions_p}') a ON a.hadm_id = s.hadm_id
        LEFT JOIN read_csv_auto('{patients_p}') p ON p.subject_id = s.subject_id
        WHERE s.rn = 1
          AND o.first_op_date <= CAST(s.intime AS DATE)
    """)

    run(con, """
        SELECT COUNT(*) AS n_stays,
               COUNT(DISTINCT subject_id) AS n_patients
        FROM cohort
    """, "F1a — cohort size (major abdominal surgery -> surgical ICU)")

    run(con, """
        SELECT CASE
                 WHEN has_icd10 = 1 THEN 'ICD-10 era'
                 ELSE 'ICD-9 era' END AS era,
               COUNT(*) AS n
        FROM cohort GROUP BY 1 ORDER BY 2 DESC
    """, "F1b — cohort by coding era")

    run(con, """
        SELECT COALESCE(
                 CASE WHEN admission_type IN ('EMERGENCY','URGENT')
                      THEN 'emergency/urgent'
                      ELSE 'elective/other' END, 'missing') AS urgency,
               COUNT(*) AS n
        FROM cohort GROUP BY 1 ORDER BY 2 DESC
    """, "F1c — cohort by urgency (elective vs emergency)")

    run(con, """
        SELECT
          COUNT(*) AS n,
          SUM(CASE WHEN any_explor = 1 THEN 1 ELSE 0 END) AS n_exploratory,
          SUM(CASE WHEN first_op_date = CAST(intime AS DATE) THEN 1 ELSE 0 END) AS n_same_day_surgery,
          ROUND(100.0 * SUM(CASE WHEN first_op_date = CAST(intime AS DATE) THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_same_day,
          ROUND(100.0 * SUM(CASE WHEN los >= 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_los_ge_48h
        FROM cohort
    """, "F1d — exploratory-laparotomy / same-day-surgery / LOS>=48h")

    run(con, """
        SELECT
          COUNT(*) AS n,
          SUM(CASE WHEN deathtime IS NOT NULL
                    AND deathtime < intime + INTERVAL '48' HOUR THEN 1 ELSE 0 END) AS n_died_48h,
          SUM(CASE WHEN deathtime IS NULL AND dod IS NOT NULL
                    AND dod <= CAST(intime AS DATE) + 2 THEN 1 ELSE 0 END) AS n_died_48h_dod_fallback,
          ROUND(100.0 * (SUM(CASE WHEN deathtime IS NOT NULL AND deathtime < intime + INTERVAL '48' HOUR THEN 1 ELSE 0 END)
                + SUM(CASE WHEN deathtime IS NULL AND dod IS NOT NULL AND dod <= CAST(intime AS DATE) + 2 THEN 1 ELSE 0 END)) / COUNT(*), 1) AS pct_died_48h
        FROM cohort
    """, "F1e — 48h mortality (competing-risk / early-death metric, #12)")

    run(con, """
        SELECT
          CASE WHEN (CAST(intime AS DATE) - first_op_date) = 0 THEN '0d (same day)'
               WHEN (CAST(intime AS DATE) - first_op_date) = 1 THEN '1d'
               ELSE '>=2d' END AS op_to_icu_days,
          COUNT(*) AS n
        FROM cohort GROUP BY 1 ORDER BY 1
    """, "F6 — surgery->ICU interval (date-level only, #3)")

    # ================================================================
    # F2 — tube-feed itemid discovery
    # ================================================================
    disc = run(con, f"""
        SELECT d.itemid, d.label, d.category, COUNT(e.stay_id) AS n_rows
        FROM read_csv_auto('{d_items_p}') d
        LEFT JOIN read_csv_auto('{inputevents_p}') e USING (itemid)
        WHERE d.linksto = 'inputevents'
          AND d.category = 'Nutrition - Enteral'
          AND NOT ({sql_ilike_any('d.label', TF_EXCLUDE)})
        GROUP BY d.itemid, d.label, d.category
        ORDER BY n_rows DESC NULLS LAST
        LIMIT 200
    """, "F2 — tube-feed itemids (category='Nutrition - Enteral'; REVIEW & CURATE, then set TF_ITEMIDS_OVERRIDE)")

    if TF_ITEMIDS_OVERRIDE is not None:
        tf_ids = list(TF_ITEMIDS_OVERRIDE)
    else:
        tf_ids = [int(x) for x in disc["itemid"].tolist() if x is not None]
        print(f"\n>>> auto-using {len(tf_ids)} discovered itemids for F3 (eyeball above).")

    if not tf_ids:
        sys.exit("\nNo tube-feed itemids found — review F2 keywords / d_items labels.")

    tf_ids_sql = ", ".join(str(i) for i in tf_ids)

    # ================================================================
    # F3 — exposure timing (48h primary + 24/72h, any-record sensitivity)
    # ================================================================
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE tf AS
        SELECT stay_id,
               MIN(starttime) AS first_tf_any,
               MIN(CASE WHEN rate >= 10 OR amount >= 20 THEN starttime END) AS first_tf_primary,
               MIN(CASE WHEN rate >= 20 THEN starttime END) AS first_tf_high
        FROM read_csv_auto('{inputevents_p}')
        WHERE itemid IN ({tf_ids_sql})
          AND statusdescription IS DISTINCT FROM 'Rewritten'
        GROUP BY stay_id
    """)

    run(con, f"""
        WITH x AS (
          SELECT c.*, t.first_tf_any, t.first_tf_primary, t.first_tf_high
          FROM cohort c LEFT JOIN tf t USING (stay_id)
        )
        SELECT
          COUNT(*) AS n_cohort,
          COUNT(first_tf_any) AS n_any_tf,
          COUNT(first_tf_primary) AS n_primary_tf,
          ROUND(100.0*COUNT(first_tf_primary)/COUNT(*),1) AS pct_any_primary,
          SUM(CASE WHEN first_tf_any IS NULL THEN 1 ELSE 0 END) AS n_never_fed,
          ROUND(100.0*SUM(CASE WHEN first_tf_any IS NULL THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_never_fed,
          SUM(CASE WHEN first_tf_primary <= intime + INTERVAL '24' HOUR THEN 1 ELSE 0 END) AS n_een_24h,
          SUM(CASE WHEN first_tf_primary <= intime + INTERVAL '48' HOUR THEN 1 ELSE 0 END) AS n_een_48h,
          SUM(CASE WHEN first_tf_primary <= intime + INTERVAL '72' HOUR THEN 1 ELSE 0 END) AS n_een_72h,
          ROUND(100.0*SUM(CASE WHEN first_tf_primary <= intime + INTERVAL '48' HOUR THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_een_48h,
          ROUND(100.0*SUM(CASE WHEN first_tf_any <= intime + INTERVAL '48' HOUR THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_een_48h_anyrecord
        FROM x
    """, "F3 — EN initiation proportions (primary def rate>=10 OR amount>=20; + any-record sensitivity)")

    run(con, f"""
        WITH x AS (
          SELECT c.stay_id, t.first_tf_any, t.first_tf_primary, c.intime
          FROM cohort c LEFT JOIN tf t USING (stay_id)
          WHERE c.los >= 2
        )
        SELECT
          CASE WHEN first_tf_primary <= intime + INTERVAL '48' HOUR THEN 'EEN (<=48h)'
               WHEN first_tf_any IS NULL THEN 'never fed'
               ELSE 'late EN (>48h)' END AS grp,
          COUNT(*) AS n,
          ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) AS pct
        FROM x
        GROUP BY 1 ORDER BY 2 DESC
    """, "F3b — 3-way split among LOS>=48h (EEN / late / never, #11)")

    # ================================================================
    # F4 — treated bloodstream infection events after 48h landmark
    # ================================================================
    contaminant_cond = sql_ilike_any("org_name", CONTAMINANTS)

    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE pos_cx AS
        SELECT subject_id, hadm_id, MIN(charttime) AS first_cx
        FROM read_csv_auto('{micro_p}')
        WHERE spec_type_desc LIKE 'BLOOD CULTURE%'
          AND org_name IS NOT NULL
          AND LOWER(org_name) NOT LIKE '%no growth%'
          AND NOT ({contaminant_cond})
        GROUP BY subject_id, hadm_id
    """)

    con.execute("""
        CREATE OR REPLACE TEMP TABLE cx_cohort AS
        SELECT c.stay_id, c.hadm_id, c.intime, x.first_cx
        FROM cohort c JOIN pos_cx x
          ON c.subject_id = x.subject_id AND c.hadm_id = x.hadm_id
        WHERE x.first_cx > c.intime + INTERVAL '48' HOUR
          AND x.first_cx < c.intime + INTERVAL '28' DAY
    """)

    run(con, """
        SELECT COUNT(*) AS n_pos_blood_cx_after_48h,
               COUNT(DISTINCT stay_id) AS n_patients
        FROM cx_cohort
    """, "F4a — positive blood cultures (contaminant-excluded) after 48h landmark")

    run(con, f"""
        SELECT COUNT(DISTINCT cc.stay_id) AS n_treated_bsi
        FROM cx_cohort cc
        JOIN read_csv_auto('{rx_p}') r
          ON cc.hadm_id = r.hadm_id
        WHERE r.starttime BETWEEN cc.first_cx - INTERVAL '1' DAY
                              AND cc.first_cx + INTERVAL '2' DAY
          AND {sql_ilike_any('r.drug', ANTIBIOTICS)}
    """, "F4b — treated BSI (positive cx + antibiotic within window)")

    run(con, f"""
        SELECT
          CASE WHEN t.first_tf_primary <= c.intime + INTERVAL '48' HOUR
               THEN 'EEN' ELSE 'no-EEN-by-48h' END AS grp,
          COUNT(DISTINCT c.stay_id) AS n_patients,
          SUM(CASE WHEN cc.first_cx IS NOT NULL THEN 1 ELSE 0 END) AS n_pos_cx
        FROM cohort c
        LEFT JOIN tf t USING (stay_id)
        LEFT JOIN cx_cohort cc USING (stay_id)
        GROUP BY 1
    """, "F4c — crude pos-cx events by exposure group (event-count feasibility)")

    # ================================================================
    # F5 — anastomotic leak / reoperation counts
    # ================================================================
    leak9 = f"(icd_version = 9 AND {sql_in('icd_code', ICD9_LEAK)})"
    leak10 = f"(icd_version = 10 AND ({sql_in('icd_code', ICD10_LEAK)} OR {sql_in('SUBSTRING(icd_code,1,4)', ICD10_LEAK_PREFIX)}))"

    run(con, f"""
        SELECT COUNT(DISTINCT d.hadm_id) AS n_leak_cohort,
               SUM(CASE WHEN d.icd_version = 9  THEN 1 ELSE 0 END) AS n_icd9,
               SUM(CASE WHEN d.icd_version = 10 THEN 1 ELSE 0 END) AS n_icd10
        FROM read_csv_auto('{diag_icd_p}') d
        JOIN cohort c ON d.hadm_id = c.hadm_id
        WHERE {leak9} OR {leak10}
    """, "F5a — COHORT admissions with an anastomotic-leak / fistula ICD code")

    run(con, f"""
        WITH reop AS (
          SELECT hadm_id, COUNT(DISTINCT chartdate) AS n_major_procs
          FROM read_csv_auto('{proc_icd_p}')
          WHERE {any_major}
          GROUP BY hadm_id
          HAVING COUNT(DISTINCT chartdate) >= 2
        )
        SELECT COUNT(*) AS n_reoperation_cohort
        FROM reop r JOIN cohort c ON r.hadm_id = c.hadm_id
    """, "F5b — COHORT admissions with >=2 major abdominal procedures (reoperation proxy)")

    # ================================================================
    # F7 — key covariate availability in 0-24h window
    # ================================================================
    run(con, f"""
        WITH lab AS (
          SELECT hadm_id,
                 MAX(CASE WHEN itemid = 50813 THEN 1 ELSE 0 END) AS has_lactate,
                 MAX(CASE WHEN itemid = 50912 THEN 1 ELSE 0 END) AS has_creat,
                 MAX(CASE WHEN itemid = 51301 THEN 1 ELSE 0 END) AS has_wbc
          FROM read_csv_auto('{lab_p}')
          WHERE itemid IN (50813, 50912, 51301)
            AND valuenum IS NOT NULL
          GROUP BY hadm_id
        ),
        vaso AS (
          SELECT stay_id, 1 AS has_vaso
          FROM read_csv_auto('{inputevents_p}')
          WHERE itemid IN (221906, 221289, 222315, 221662, 221749)
          GROUP BY stay_id
        ),
        mv AS (
          SELECT stay_id, 1 AS has_mv
          FROM read_csv_auto('{proc_events_p}')
          WHERE itemid = 225792
          GROUP BY stay_id
        )
        SELECT
          ROUND(100.0*AVG(COALESCE(l.has_lactate,0)),1) AS pct_lactate,
          ROUND(100.0*AVG(COALESCE(l.has_creat,0)),1)   AS pct_creatinine,
          ROUND(100.0*AVG(COALESCE(l.has_wbc,0)),1)     AS pct_wbc,
          ROUND(100.0*AVG(COALESCE(v.has_vaso,0)),1)    AS pct_vasopressor,
          ROUND(100.0*AVG(COALESCE(m.has_mv,0)),1)      AS pct_mech_vent
        FROM cohort c
        LEFT JOIN lab l USING (hadm_id)
        LEFT JOIN vaso v USING (stay_id)
        LEFT JOIN mv m USING (stay_id)
    """, "F7 — % of cohort with key covariates available (any value, full stay; refine to 0-24h in analysis)")

    print("\n" + "=" * 72)
    print("DONE. Judge against the thresholds in protocol.md section 9 (F1-F9).")
    print("=" * 72)
    con.close()


if __name__ == "__main__":
    main()
