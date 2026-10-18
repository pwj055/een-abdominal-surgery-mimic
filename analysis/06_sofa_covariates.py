# -*- coding: utf-8 -*-
"""
06_sofa_covariates.py — 2nd-pass severity covariates (0-24h, SOFA components + BMI).

Adds to the PS model the remaining SOFA inputs + nutritional status:
  gcs_min   (neuro)   = min total GCS (eye 220739 + verbal 223900 + motor 223901,
                        summed at the same charttime-minute, worst over 0-24h)
  map_min   (cardio)  = min MAP (invasive 220052 / non-invasive 220181) over 0-24h
  fio2_max  (resp)    = max FiO2 (223835) over 0-24h
  po2_min   (resp)    = min PaO2 (50821) over 0-24h
  bmi       (nutrition)= first BMI in omr

Computed once for the 24h-cohort stays (superset of 48h/72h) — these covariates
depend only on intime, not the feeding threshold, so they are reused by all
threshold analyses. Output: analysis/sofa_covariates.csv.
"""
import os
import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
M = "D:/physionet/mimic-iv"
OUT = os.path.join(HERE, "sofa_covariates.csv")

GCS_EYE, GCS_VERBAL, GCS_MOTOR = 220739, 223900, 223901
MAP_ART, MAP_NIBP = 220052, 220181
FIO2 = 223835
PO2 = 50821

con = duckdb.connect()

# all stays from the 24h cohort (superset of 48h/72h)
con.execute(f"""
CREATE OR REPLACE TEMP TABLE cohort AS
SELECT stay_id, subject_id, hadm_id, intime
FROM read_csv_auto('{HERE}/cohort_24h.csv')
""")

# single chartevents scan for the 6 vital items, 0-24h
con.execute(f"""
CREATE OR REPLACE TEMP TABLE ce AS
SELECT c.stay_id, ce.charttime, ce.itemid, ce.valuenum
FROM cohort c
JOIN read_csv_auto('{M}/icu/chartevents.csv.gz') ce ON c.stay_id = ce.stay_id
WHERE ce.itemid IN ({GCS_EYE}, {GCS_VERBAL}, {GCS_MOTOR}, {MAP_ART}, {MAP_NIBP}, {FIO2})
  AND ce.valuenum IS NOT NULL
  AND ce.charttime BETWEEN c.intime AND c.intime + INTERVAL '24' HOUR
""")

con.execute(f"""
CREATE OR REPLACE TEMP TABLE map_fio AS
SELECT stay_id,
       MIN(CASE WHEN itemid IN ({MAP_ART}, {MAP_NIBP}) THEN valuenum END) AS map_min,
       MAX(CASE WHEN itemid = {FIO2} THEN valuenum END) AS fio2_max
FROM ce GROUP BY stay_id
""")

con.execute(f"""
CREATE OR REPLACE TEMP TABLE gcs AS
SELECT stay_id, MIN(eye + verbal + motor) AS gcs_min
FROM (
  SELECT stay_id, DATE_TRUNC('minute', charttime) AS t,
         MAX(CASE WHEN itemid = {GCS_EYE} THEN valuenum END) AS eye,
         MAX(CASE WHEN itemid = {GCS_VERBAL} THEN valuenum END) AS verbal,
         MAX(CASE WHEN itemid = {GCS_MOTOR} THEN valuenum END) AS motor
  FROM ce GROUP BY stay_id, DATE_TRUNC('minute', charttime)
)
WHERE eye IS NOT NULL AND verbal IS NOT NULL AND motor IS NOT NULL
GROUP BY stay_id
""")

con.execute(f"""
CREATE OR REPLACE TEMP TABLE po2 AS
SELECT c.stay_id, MIN(le.valuenum) AS po2_min
FROM cohort c
JOIN read_csv_auto('{M}/hosp/labevents.csv.gz') le ON c.hadm_id = le.hadm_id
WHERE le.itemid = {PO2} AND le.valuenum IS NOT NULL
  AND le.charttime BETWEEN c.intime AND c.intime + INTERVAL '24' HOUR
GROUP BY c.stay_id
""")

con.execute(f"""
CREATE OR REPLACE TEMP TABLE bmi AS
SELECT subject_id, TRY_CAST(result_value AS DOUBLE) AS bmi
FROM (
  SELECT subject_id, result_value, chartdate, seq_num,
         ROW_NUMBER() OVER (PARTITION BY subject_id ORDER BY chartdate, seq_num) AS rn
  FROM read_csv_auto('{M}/hosp/omr.csv.gz')
  WHERE LOWER(result_name) LIKE '%bmi%'
    AND TRY_CAST(result_value AS DOUBLE) IS NOT NULL
)
WHERE rn = 1
""")

con.execute(f"""
COPY (
  SELECT c.stay_id,
         g.gcs_min, m.map_min, m.fio2_max, p.po2_min, b.bmi
  FROM cohort c
  LEFT JOIN gcs g USING (stay_id)
  LEFT JOIN map_fio m USING (stay_id)
  LEFT JOIN po2 p USING (stay_id)
  LEFT JOIN bmi b ON b.subject_id = c.subject_id
) TO '{OUT}' (HEADER, DELIMITER ',')
""")

n = con.execute("SELECT COUNT(*) FROM read_csv_auto('{OUT}')".replace('{OUT}', OUT)).fetchone()[0]
print(f"wrote {n} rows to {OUT}")
print(con.execute(f"""
  SELECT COUNT(*) AS n,
         ROUND(100.0*SUM(CASE WHEN gcs_min IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*),1) AS gcs_pct,
         ROUND(100.0*SUM(CASE WHEN map_min IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*),1) AS map_pct,
         ROUND(100.0*SUM(CASE WHEN fio2_max IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*),1) AS fio2_pct,
         ROUND(100.0*SUM(CASE WHEN po2_min IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*),1) AS po2_pct,
         ROUND(100.0*SUM(CASE WHEN bmi IS NOT NULL THEN 1 ELSE 0 END)/COUNT(*),1) AS bmi_pct
  FROM read_csv_auto('{OUT}')
""").df().to_string(index=False))

con.close()
