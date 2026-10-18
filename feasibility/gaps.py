# -*- coding: utf-8 -*-
"""Fill pre-lock gaps:
   (1) infection-composite events by EEN/late/never (landmarked),
   (2) never-group dissection (died / therapeutic-NPO / other),
   (3) reoperation proxy refinement (type + 3-14d window)."""
import duckdb

M = "C:/Users/jiang/Desktop/Enteral Nutrition/mimic-iv"
con = duckdb.connect()

SURGICAL_ICUS = (
    "Surgical Intensive Care Unit (SICU)", "Trauma SICU (TSICU)",
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

CONTAM = (
    "coagulase negative", "coagulase-negative", "epidermidis",
    "corynebacterium", "diphtheroid", "micrococcus", "propionibacterium",
    "bacillus", "viridans",
)
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

def sin(items): return "(" + ", ".join(repr(i) for i in items) + ")"

major9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,2) IN {sin(ICD9_MAJOR)})"
explor9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,3) IN {sin(ICD9_EXPLOR)})"
major10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_MAJOR)})"
explor10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_EXPLOR)})"
any_major = f"({major9} OR {major10})"
any_explor = f"({explor9} OR {explor10})"

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
       o.first_op_date, o.any_explor, a.admission_type, a.deathtime, p.dod
FROM sicu s
JOIN op o ON s.hadm_id = o.hadm_id
LEFT JOIN read_csv_auto('{M}/hosp/admissions.csv.gz') a ON a.hadm_id = s.hadm_id
LEFT JOIN read_csv_auto('{M}/hosp/patients.csv.gz') p ON p.subject_id = s.subject_id
WHERE s.rn = 1 AND o.first_op_date <= CAST(s.intime AS DATE)
""")

con.execute(f"""
CREATE OR REPLACE TEMP TABLE tf AS
SELECT e.stay_id,
       MIN(CASE WHEN e.rate >= 10 OR e.amount >= 20 THEN e.starttime END) AS first_tf
FROM read_csv_auto('{M}/icu/inputevents.csv.gz') e
JOIN read_csv_auto('{M}/icu/d_items.csv.gz') d ON e.itemid = d.itemid
WHERE d.linksto='inputevents' AND d.category='Nutrition - Enteral'
GROUP BY e.stay_id
""")

con.execute("""
CREATE OR REPLACE TEMP TABLE lm AS
SELECT c.stay_id, c.hadm_id, c.subject_id, c.intime, c.los,
       c.deathtime, c.dod, c.any_explor, t.first_tf,
       CASE WHEN t.first_tf <= c.intime + INTERVAL '48' HOUR THEN 'EEN'
            WHEN t.first_tf IS NULL THEN 'never'
            ELSE 'late' END AS grp
FROM cohort c LEFT JOIN tf t USING (stay_id)
WHERE c.los >= 2
""")

# positive culture events (contaminant-excluded) in the 48h..28d window
con.execute(f"""
CREATE OR REPLACE TEMP TABLE pos_events AS
SELECT l.stay_id, l.hadm_id, m.charttime AS cx_time,
       CASE WHEN UPPER(m.spec_type_desc) LIKE 'BLOOD CULTURE%' THEN 1 ELSE 0 END AS is_blood
FROM lm l
JOIN read_csv_auto('{M}/hosp/microbiologyevents.csv.gz') m
  ON l.subject_id = m.subject_id AND l.hadm_id = m.hadm_id
WHERE m.charttime > l.intime + INTERVAL '48' HOUR
  AND m.charttime < l.intime + INTERVAL '28' DAY
  AND m.org_name IS NOT NULL
  AND LOWER(m.org_name) NOT LIKE '%no growth%'
  AND NOT (LOWER(m.org_name) LIKE '%coagulase negative%'
        OR LOWER(m.org_name) LIKE '%coagulase-negative%'
        OR LOWER(m.org_name) LIKE '%epidermidis%'
        OR LOWER(m.org_name) LIKE '%corynebacterium%'
        OR LOWER(m.org_name) LIKE '%diphtheroid%'
        OR LOWER(m.org_name) LIKE '%micrococcus%'
        OR LOWER(m.org_name) LIKE '%propionibacterium%'
        OR LOWER(m.org_name) LIKE '%bacillus%'
        OR LOWER(m.org_name) LIKE '%viridans%')
""")

# treated events = positive cx with antibiotic in [-1d, +2d]
con.execute(f"""
CREATE OR REPLACE TEMP TABLE treated_events AS
SELECT DISTINCT pe.stay_id, pe.is_blood
FROM pos_events pe
JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON pe.hadm_id = r.hadm_id
WHERE r.starttime BETWEEN pe.cx_time - INTERVAL '1' DAY AND pe.cx_time + INTERVAL '2' DAY
  AND ({" OR ".join(f"LOWER(r.drug) LIKE '%{a}%'" for a in ABX)})
""")

def q(label, sql):
    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)
    print(con.execute(sql).df().to_string(index=False))

q("G1 — landmarked groups: treated BSI / treated-any-cx (infection proxy)",
  """
  SELECT l.grp, COUNT(*) AS n,
         SUM(CASE WHEN te.is_blood = 1 THEN 1 ELSE 0 END) AS treated_bsi,
         SUM(CASE WHEN te.stay_id IS NOT NULL THEN 1 ELSE 0 END) AS treated_any_cx
  FROM lm l
  LEFT JOIN treated_events te USING (stay_id)
  GROUP BY l.grp ORDER BY n DESC
  """)

q("G2 — never-group 3-way (died / ileus-obstruction / other)",
  f"""
  WITH nv AS (
    SELECT l.hadm_id, l.deathtime, l.dod,
           MAX(CASE WHEN ((d.icd_version=9 AND SUBSTRING(d.icd_code,1,3)='560')
                       OR (d.icd_version=10 AND SUBSTRING(d.icd_code,1,3)='K56'))
                THEN 1 ELSE 0 END) AS ileus
    FROM lm l
    LEFT JOIN read_csv_auto('{M}/hosp/diagnoses_icd.csv.gz') d ON d.hadm_id = l.hadm_id
    WHERE l.grp='never'
    GROUP BY l.hadm_id, l.deathtime, l.dod
  )
  SELECT
    CASE WHEN deathtime IS NOT NULL OR dod IS NOT NULL THEN 'died'
         WHEN ileus=1 THEN 'ileus/obstruction (therapeutic NPO proxy)'
         ELSE 'other (presumptive oral recovery)' END AS subgroup,
    COUNT(*) AS n
  FROM nv GROUP BY 1 ORDER BY 2 DESC
  """)

q("G3 — reoperation refinement (>=2 major proc dates; 3-14d gap; 2nd=explor)",
  f"""
  WITH opdates AS (
    SELECT hadm_id, chartdate,
           MAX(CASE WHEN {any_explor} THEN 1 ELSE 0 END) AS explor,
           ROW_NUMBER() OVER (PARTITION BY hadm_id ORDER BY chartdate) AS rn
    FROM read_csv_auto('{M}/hosp/procedures_icd.csv.gz')
    WHERE {any_major}
  ),
  reop AS (
    SELECT o1.hadm_id, (o2.chartdate - o1.chartdate) AS gap_days, o2.explor AS second_explor
    FROM opdates o1 JOIN opdates o2
      ON o1.hadm_id = o2.hadm_id AND o1.rn = 1 AND o2.rn = 2
    WHERE o1.chartdate < o2.chartdate
  )
  SELECT
    COUNT(*) AS n_reop_cohort,
    SUM(CASE WHEN gap_days BETWEEN 3 AND 14 THEN 1 ELSE 0 END) AS n_reop_3_14d,
    SUM(CASE WHEN gap_days BETWEEN 3 AND 14 AND second_explor=1 THEN 1 ELSE 0 END) AS n_reop_3_14d_explor
  FROM reop r JOIN cohort c ON r.hadm_id = c.hadm_id
  """)

con.close()
print("\nDONE.")
