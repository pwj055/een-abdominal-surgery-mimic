# -*- coding: utf-8 -*-
"""Focused follow-up: cohort-restricted F5 + landmarked F4c + emergency subgroup split."""
import duckdb

M = "D:/physionet/mimic-iv"
con = duckdb.connect()

SURGICAL_ICUS = (
    "Surgical Intensive Care Unit (SICU)",
    "Trauma SICU (TSICU)",
    "Medical/Surgical Intensive Care Unit (MICU/SICU)",
    "Neuro Surgical Intensive Care Unit (Neuro SICU)",
)
ICD9_MAJOR = ("42", "43", "45", "46", "50", "51", "52")
ICD9_EXPLOR = ("541", "545")
ICD10_MAJOR = (
    "0DB5", "0DB6", "0DB8", "0DB9", "0DBE", "0DBP", "0DBQ",
    "0DT5", "0DT6", "0DT8", "0DT9", "0DTE", "0DTP", "0DTQ",
    "0D15", "0D16", "0D18", "0D19", "0D1E", "0D1P",
    "0FB0", "0FB4", "0FB5", "0FBG",
    "0FT0", "0FT4", "0FT5", "0FTG",
    "0DQ5", "0DQ6", "0DQ8", "0DQE",
)
ICD10_EXPLOR = ("0WJG",)
ICD9_LEAK = ("9974", "56981", "9983")
ICD10_LEAK = ("K9189", "K632")
ICD10_LEAK_PREFIX = ("T814",)

def sin(items):
    return "(" + ", ".join(repr(i) for i in items) + ")"

major9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,2) IN {sin(ICD9_MAJOR)})"
explor9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,3) IN {sin(ICD9_EXPLOR)})"
major10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_MAJOR)})"
explor10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_EXPLOR)})"
any_major = f"({major9} OR {major10})"
any_explor = f"({explor9} OR {explor10})"
leak9 = f"(icd_version = 9 AND icd_code IN {sin(ICD9_LEAK)})"
leak10 = f"(icd_version = 10 AND (icd_code IN {sin(ICD10_LEAK)} OR SUBSTRING(icd_code,1,4) IN {sin(ICD10_LEAK_PREFIX)}))"

con.execute(f"""
CREATE OR REPLACE TEMP TABLE cohort AS
WITH op AS (
    SELECT hadm_id, MIN(chartdate) AS first_op_date,
           MAX(CASE WHEN {any_explor} THEN 1 ELSE 0 END) AS any_explor
    FROM read_csv_auto('{M}/hosp/procedures_icd.csv.gz')
    WHERE {any_major} OR {any_explor}
    GROUP BY hadm_id
),
sicu AS (
    SELECT stay_id, subject_id, hadm_id, intime, outtime, los,
           ROW_NUMBER() OVER (PARTITION BY subject_id ORDER BY intime) AS rn
    FROM read_csv_auto('{M}/icu/icustays.csv.gz')
    WHERE first_careunit IN {tuple(SURGICAL_ICUS)}
)
SELECT s.stay_id, s.subject_id, s.hadm_id, s.intime, s.outtime, s.los,
       o.first_op_date, o.any_explor, a.admission_type
FROM sicu s
JOIN op o ON s.hadm_id = o.hadm_id
LEFT JOIN read_csv_auto('{M}/hosp/admissions.csv.gz') a ON a.hadm_id = s.hadm_id
WHERE s.rn = 1 AND o.first_op_date <= CAST(s.intime AS DATE)
""")

def q(label, sql):
    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)
    print(con.execute(sql).df().to_string(index=False))

# F5a cohort-restricted, by code
q("F5a-fix — cohort leak codes, broken down by code",
  f"""
  SELECT d.icd_code, COUNT(DISTINCT d.hadm_id) AS n_admissions
  FROM read_csv_auto('{M}/hosp/diagnoses_icd.csv.gz') d
  JOIN cohort c ON d.hadm_id = c.hadm_id
  WHERE {leak9} OR {leak10}
  GROUP BY d.icd_code ORDER BY n_admissions DESC LIMIT 20
  """)

q("F5a-fix — total cohort admissions with ANY leak code",
  f"""
  SELECT COUNT(DISTINCT d.hadm_id) AS n_leak_cohort
  FROM read_csv_auto('{M}/hosp/diagnoses_icd.csv.gz') d
  JOIN cohort c ON d.hadm_id = c.hadm_id
  WHERE {leak9} OR {leak10}
  """)

# F5b cohort-restricted
q("F5b-fix — cohort admissions with >=2 major procedures",
  f"""
  WITH reop AS (
    SELECT hadm_id, COUNT(DISTINCT chartdate) AS n_dates
    FROM read_csv_auto('{M}/hosp/procedures_icd.csv.gz')
    WHERE {any_major}
    GROUP BY hadm_id HAVING COUNT(DISTINCT chartdate) >= 2
  )
  SELECT COUNT(*) AS n_reoperation_cohort FROM reop r JOIN cohort c ON r.hadm_id = c.hadm_id
  """)

# tf table (category-based, no itemid list)
con.execute(f"""
CREATE OR REPLACE TEMP TABLE tf AS
SELECT e.stay_id,
       MIN(CASE WHEN e.rate >= 10 OR e.amount >= 20 THEN e.starttime END) AS first_tf
FROM read_csv_auto('{M}/icu/inputevents.csv.gz') e
JOIN read_csv_auto('{M}/icu/d_items.csv.gz') d ON e.itemid = d.itemid
WHERE d.linksto = 'inputevents' AND d.category = 'Nutrition - Enteral'
GROUP BY e.stay_id
""")

# landmarked cx events (LOS>=48h) by exposure group
con.execute(f"""
CREATE OR REPLACE TEMP TABLE cx AS
SELECT c.stay_id, MIN(x.charttime) AS first_cx
FROM cohort c
JOIN read_csv_auto('{M}/hosp/microbiologyevents.csv.gz') x
  ON c.subject_id = x.subject_id AND c.hadm_id = x.hadm_id
WHERE UPPER(x.spec_type_desc) LIKE 'BLOOD CULTURE%'
  AND x.org_name IS NOT NULL
  AND LOWER(x.org_name) NOT LIKE '%no growth%'
  AND NOT (LOWER(x.org_name) LIKE '%coagulase negative%'
        OR LOWER(x.org_name) LIKE '%coagulase-negative%'
        OR LOWER(x.org_name) LIKE '%epidermidis%'
        OR LOWER(x.org_name) LIKE '%corynebacterium%'
        OR LOWER(x.org_name) LIKE '%diphtheroid%'
        OR LOWER(x.org_name) LIKE '%micrococcus%'
        OR LOWER(x.org_name) LIKE '%propionibacterium%'
        OR LOWER(x.org_name) LIKE '%bacillus%'
        OR LOWER(x.org_name) LIKE '%viridans%')
GROUP BY c.stay_id
""")

q("F4c-fix — pos-cx (contaminant-excl) in LANDMARKED LOS>=48h, by exposure group",
  f"""
  WITH lm AS (
    SELECT c.*, t.first_tf, cx.first_cx
    FROM cohort c
    LEFT JOIN tf t USING (stay_id)
    LEFT JOIN cx USING (stay_id)
    WHERE c.los >= 2
  )
  SELECT
    CASE WHEN first_tf <= intime + INTERVAL '48' HOUR THEN 'EEN' ELSE 'no-EEN-by-48h' END AS grp,
    COUNT(*) AS n_patients,
    SUM(CASE WHEN first_cx > intime + INTERVAL '48' HOUR
              AND first_cx < intime + INTERVAL '28' DAY THEN 1 ELSE 0 END) AS n_pos_cx_48h_28d
  FROM lm GROUP BY 1
  """)

# emergency subgroup three-way split (landmarked)
q("F3c — emergency/urgent subgroup, LOS>=48h, 3-way split",
  f"""
  WITH lm AS (
    SELECT c.admission_type, c.intime, c.los, t.first_tf
    FROM cohort c LEFT JOIN tf t USING (stay_id)
    WHERE c.los >= 2
      AND c.admission_type IN ('EMERGENCY','URGENT')
  )
  SELECT
    CASE WHEN first_tf <= intime + INTERVAL '48' HOUR THEN 'EEN (<=48h)'
         WHEN first_tf IS NULL THEN 'never fed'
         ELSE 'late EN (>48h)' END AS grp,
    COUNT(*) AS n
  FROM lm GROUP BY 1 ORDER BY 2 DESC
  """)

# also: full landmarked 3-way split + EEN denominator for clarity
q("F3c2 — full cohort LOS>=48h 3-way split (n check)",
  f"""
  WITH lm AS (
    SELECT c.intime, c.los, t.first_tf
    FROM cohort c LEFT JOIN tf t USING (stay_id)
    WHERE c.los >= 2
  )
  SELECT
    CASE WHEN first_tf <= intime + INTERVAL '48' HOUR THEN 'EEN (<=48h)'
         WHEN first_tf IS NULL THEN 'never fed'
         ELSE 'late EN (>48h)' END AS grp,
    COUNT(*) AS n
  FROM lm GROUP BY 1 ORDER BY 2 DESC
  """)

con.close()
print("\nDONE.")
