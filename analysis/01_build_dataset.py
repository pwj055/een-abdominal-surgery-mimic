# -*- coding: utf-8 -*-
"""
01_build_dataset.py — assemble the analysis-ready target-trial cohort.

One row per landmarked stay (ICU LOS >= 48h). Columns:
  stay/subject/hadm ids, intime, los, age, sex, emergency, site, stoma,
  exploratory-laparotomy, n_major_procs, 0-24h labs (lactate/creat/wbc/plt/bili),
  vasopressor/MV in 0-24h, Elixhauser (diabetes/ckd/cirrhosis),
  exposure (grp EEN/late/never, een48, tf_any, first_tf_hours),
  outcomes (treated_bsi, infection_composite, leak_reop, hosp_death).

Output: analysis/cohort.csv  (small; pandas-ready).
NOTE: full SOFA (GCS/MAP/FiO2 via chartevents) and BMI are a planned 2nd pass.
"""
import os
import duckdb

M = "C:/Users/jiang/Desktop/Enteral Nutrition/mimic-iv"
THRESH = int(os.environ.get("EEN_THRESH", "48"))   # exposure cutoff + landmark (hours)
OUT = os.path.join(os.path.dirname(__file__), "cohort.csv" if THRESH == 48 else f"cohort_{THRESH}h.csv")

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
VASO = (221906, 221289, 222315, 221662, 221749)
MV_ITEM = 225792
LAB_ITEMS = (50813, 50912, 51301, 51265, 50885)   # lactate, creat, wbc, plt, bili

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

def sin(x): return "(" + ", ".join(repr(i) for i in x) + ")"

major9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,2) IN {sin(ICD9_MAJOR)})"
explor9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,3) IN {sin(ICD9_EXPLOR)})"
major10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_MAJOR)})"
explor10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_EXPLOR)})"
any_major = f"({major9} OR {major10})"
any_explor = f"({explor9} OR {explor10})"

# ---- cohort (first surgical ICU stay; major abdo surgery on/before ICU day) ----
con.execute(f"""
CREATE OR REPLACE TEMP TABLE cohort AS
WITH op AS (
  SELECT hadm_id, MIN(chartdate) AS first_op_date,
         MAX(CASE WHEN {any_explor} THEN 1 ELSE 0 END) AS any_explor,
         COUNT(DISTINCT CASE WHEN {any_major} THEN icd_code END) AS n_major_procs,
         MAX(CASE WHEN icd_version = 9 AND SUBSTRING(icd_code,1,2) IN ('42','43') THEN 1
                  WHEN icd_version = 10 AND SUBSTRING(icd_code,1,3) IN ('0DB','0DT','0D1','0DQ')
                       AND SUBSTRING(icd_code,4,1) IN ('5','6','9') THEN 1 ELSE 0 END) AS upper,
         MAX(CASE WHEN icd_version = 9 AND SUBSTRING(icd_code,1,2) IN ('45','46') THEN 1
                  WHEN icd_version = 10 AND SUBSTRING(icd_code,1,3) IN ('0DB','0DT','0D1','0DQ')
                       AND SUBSTRING(icd_code,4,1) IN ('8','E','P','Q') THEN 1 ELSE 0 END) AS lower,
         MAX(CASE WHEN icd_version = 9 AND SUBSTRING(icd_code,1,2) IN ('50','51','52') THEN 1
                  WHEN icd_version = 10 AND SUBSTRING(icd_code,1,2) = '0F' THEN 1 ELSE 0 END) AS hpb,
         MAX(CASE WHEN icd_version = 9 AND SUBSTRING(icd_code,1,3) IN ('461','462') THEN 1 ELSE 0 END) AS stoma
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
       o.first_op_date, o.any_explor, o.n_major_procs, o.upper, o.lower, o.hpb, o.stoma,
       a.admission_type, a.deathtime,
       p.gender, p.anchor_age
FROM sicu s
JOIN op o ON s.hadm_id = o.hadm_id
LEFT JOIN read_csv_auto('{M}/hosp/admissions.csv.gz') a ON a.hadm_id = s.hadm_id
LEFT JOIN read_csv_auto('{M}/hosp/patients.csv.gz') p ON p.subject_id = s.subject_id
WHERE s.rn = 1 AND o.first_op_date <= CAST(s.intime AS DATE) AND s.los * 24 >= {THRESH}
  AND (a.deathtime IS NULL OR a.deathtime > s.intime + INTERVAL '{THRESH}' HOUR)
""")

# ---- exposure: tube feed (category-based) ----
con.execute(f"""
CREATE OR REPLACE TEMP TABLE tf AS
SELECT e.stay_id,
       MIN(CASE WHEN e.rate >= 10 OR e.amount >= 20 THEN e.starttime END) AS first_tf
FROM read_csv_auto('{M}/icu/inputevents.csv.gz') e
JOIN read_csv_auto('{M}/icu/d_items.csv.gz') d ON e.itemid = d.itemid
WHERE d.linksto = 'inputevents' AND d.category = 'Nutrition - Enteral'
GROUP BY e.stay_id
""")

# ---- 0-24h labs ----
con.execute(f"""
CREATE OR REPLACE TEMP TABLE lab AS
SELECT c.stay_id,
       MAX(CASE WHEN le.itemid = 50813 THEN le.valuenum END) AS lactate_max,
       MAX(CASE WHEN le.itemid = 50912 THEN le.valuenum END) AS creat_max,
       MAX(CASE WHEN le.itemid = 51301 THEN le.valuenum END) AS wbc_max,
       MIN(CASE WHEN le.itemid = 51265 THEN le.valuenum END) AS plt_min,
       MAX(CASE WHEN le.itemid = 50885 THEN le.valuenum END) AS bili_max
FROM cohort c
JOIN read_csv_auto('{M}/hosp/labevents.csv.gz') le ON c.hadm_id = le.hadm_id
WHERE le.itemid IN {sin(LAB_ITEMS)}
  AND le.valuenum IS NOT NULL
  AND le.charttime BETWEEN c.intime AND c.intime + INTERVAL '24' HOUR
GROUP BY c.stay_id
""")

# ---- 0-24h vasopressors / MV ----
con.execute(f"""
CREATE OR REPLACE TEMP TABLE vaso AS
SELECT c.stay_id, 1 AS vaso_24h
FROM cohort c
JOIN read_csv_auto('{M}/icu/inputevents.csv.gz') i ON c.stay_id = i.stay_id
WHERE i.itemid IN {sin(VASO)}
  AND i.starttime BETWEEN c.intime AND c.intime + INTERVAL '24' HOUR
GROUP BY c.stay_id
""")
con.execute(f"""
CREATE OR REPLACE TEMP TABLE mv AS
SELECT c.stay_id, 1 AS mv_24h
FROM cohort c
JOIN read_csv_auto('{M}/icu/procedureevents.csv.gz') p ON c.stay_id = p.stay_id
WHERE p.itemid = {MV_ITEM}
  AND p.starttime BETWEEN c.intime AND c.intime + INTERVAL '24' HOUR
GROUP BY c.stay_id
""")

# ---- Elixhauser (diabetes / ckd / cirrhosis) ----
con.execute(f"""
CREATE OR REPLACE TEMP TABLE elix AS
SELECT hadm_id,
       MAX(CASE WHEN (icd_version = 9 AND icd_code LIKE '250%')
                   OR (icd_version = 10 AND (icd_code LIKE 'E10%' OR icd_code LIKE 'E11%')) THEN 1 ELSE 0 END) AS diabetes,
       MAX(CASE WHEN (icd_version = 9 AND icd_code LIKE '585%')
                   OR (icd_version = 10 AND icd_code LIKE 'N18%') THEN 1 ELSE 0 END) AS ckd,
       MAX(CASE WHEN (icd_version = 9 AND (icd_code LIKE '5712%' OR icd_code LIKE '5715%'))
                   OR (icd_version = 10 AND icd_code LIKE 'K74%') THEN 1 ELSE 0 END) AS cirrhosis
FROM read_csv_auto('{M}/hosp/diagnoses_icd.csv.gz')
GROUP BY hadm_id
""")

# ---- outcomes: positive cultures (contaminant-excl) after 48h, <28d ----
con.execute(f"""
CREATE OR REPLACE TEMP TABLE pos_events AS
SELECT c.stay_id, c.hadm_id, m.charttime,
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
JOIN read_csv_auto('{M}/hosp/microbiologyevents.csv.gz') m
  ON c.subject_id = m.subject_id AND c.hadm_id = m.hadm_id
WHERE m.charttime > c.intime + INTERVAL '{THRESH}' HOUR
  AND m.charttime < c.intime + INTERVAL '28' DAY
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

con.execute(f"""
CREATE OR REPLACE TEMP TABLE treated AS
SELECT DISTINCT pe.stay_id, pe.site
FROM pos_events pe
JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON pe.hadm_id = r.hadm_id
WHERE r.starttime BETWEEN pe.charttime - INTERVAL '1' DAY AND pe.charttime + INTERVAL '2' DAY
  AND ({" OR ".join(f"LOWER(r.drug) LIKE '%{a}%'" for a in ABX)})
""")

# ---- leak/reoperation: exploratory relaparotomy (541 / 0WJG) 3-14d after index major op.
#      Adhesiolysis (545) excluded — it proxies SBO, not anastomotic leak. ----
con.execute(f"""
CREATE OR REPLACE TEMP TABLE leak AS
WITH first_op AS (
  SELECT hadm_id, MIN(chartdate) AS first_date
  FROM read_csv_auto('{M}/hosp/procedures_icd.csv.gz')
  WHERE {any_major}
  GROUP BY hadm_id
)
SELECT DISTINCT p.hadm_id, 1 AS leak_reop
FROM read_csv_auto('{M}/hosp/procedures_icd.csv.gz') p
JOIN first_op f ON p.hadm_id = f.hadm_id
WHERE ((p.icd_version = 9 AND SUBSTRING(p.icd_code,1,3) = '541')
    OR (p.icd_version = 10 AND SUBSTRING(p.icd_code,1,4) = '0WJG'))
  AND p.chartdate > f.first_date
  AND (p.chartdate - f.first_date) BETWEEN 3 AND 14
""")

# ---- assemble ----
con.execute(f"""
CREATE OR REPLACE TEMP TABLE final AS
SELECT
  c.stay_id, c.subject_id, c.hadm_id,
  c.intime, c.los AS icu_los,
  c.anchor_age AS age,
  CASE WHEN c.gender = 'F' THEN 1 ELSE 0 END AS female,
  CASE WHEN c.admission_type IN ('EMERGENCY','URGENT') THEN 1 ELSE 0 END AS emergency,
  CASE WHEN c.hpb = 1 THEN 'hpb'
       WHEN c.upper = 1 THEN 'upper'
       WHEN c.lower = 1 THEN 'lower' ELSE 'other' END AS site,
  c.stoma, c.any_explor, c.n_major_procs,
  l.lactate_max, l.creat_max, l.wbc_max, l.plt_min, l.bili_max,
  COALESCE(v.vaso_24h, 0) AS vaso_24h,
  COALESCE(m.mv_24h, 0) AS mv_24h,
  COALESCE(e.diabetes, 0) AS diabetes,
  COALESCE(e.ckd, 0) AS ckd,
  COALESCE(e.cirrhosis, 0) AS cirrhosis,
  CASE WHEN t.first_tf <= c.intime + INTERVAL '{THRESH}' HOUR THEN 'EEN'
       WHEN t.first_tf IS NULL THEN 'never'
       ELSE 'late' END AS grp,
  CASE WHEN t.first_tf <= c.intime + INTERVAL '{THRESH}' HOUR THEN 1 ELSE 0 END AS een48,
  CASE WHEN t.first_tf IS NOT NULL THEN 1 ELSE 0 END AS tf_any,
  CASE WHEN t.first_tf IS NOT NULL
       THEN (EPOCH(t.first_tf) - EPOCH(c.intime)) / 3600.0 END AS first_tf_hours,
  CASE WHEN tb.stay_id IS NOT NULL THEN 1 ELSE 0 END AS treated_bsi,
  CASE WHEN tc.stay_id IS NOT NULL THEN 1 ELSE 0 END AS infection_composite,
  COALESCE(lk.leak_reop, 0) AS leak_reop,
  CASE WHEN c.deathtime IS NOT NULL THEN 1 ELSE 0 END AS hosp_death
FROM cohort c
LEFT JOIN tf t USING (stay_id)
LEFT JOIN lab l USING (stay_id)
LEFT JOIN vaso v USING (stay_id)
LEFT JOIN mv m USING (stay_id)
LEFT JOIN elix e USING (hadm_id)
LEFT JOIN (SELECT stay_id, 1 AS x FROM treated WHERE site = 'blood' GROUP BY stay_id) tb USING (stay_id)
LEFT JOIN (SELECT stay_id, 1 AS x FROM treated WHERE site IN ('blood','abdominal','respiratory','wound') GROUP BY stay_id) tc USING (stay_id)
LEFT JOIN leak lk USING (hadm_id)
""")

con.execute(f"COPY (SELECT * FROM final) TO '{OUT}' (HEADER, DELIMITER ',')")
n = con.execute("SELECT COUNT(*) FROM final").fetchone()[0]
print(f"wrote {n} rows to {OUT}")

# quick column sanity + exposure/outcome tallies
print(con.execute("""
  SELECT grp, COUNT(*) AS n,
         SUM(treated_bsi) AS bsi, SUM(infection_composite) AS infect,
         SUM(leak_reop) AS leak, SUM(hosp_death) AS death
  FROM final GROUP BY grp ORDER BY n DESC
""").df().to_string(index=False))

con.close()
