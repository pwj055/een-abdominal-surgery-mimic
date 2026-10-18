# -*- coding: utf-8 -*-
"""One-off: verify MIMIC-IV v3.1 field formats before the full feasibility run."""
import duckdb

M = "D:/physionet/mimic-iv"

con = duckdb.connect()

def q(label, sql):
    print("\n" + "=" * 70)
    print(label)
    print("=" * 70)
    try:
        print(con.execute(sql).df().to_string(index=False))
    except Exception as e:
        print("ERROR:", e)

# 1. ICD-10 diagnosis code format (decimal point or not?)
q("1a — ICD-10 dx codes containing K91/K63/T81 (with or without dot)",
  f"""
  SELECT icd_code, COUNT(*) AS n
  FROM read_csv_auto('{M}/hosp/diagnoses_icd.csv.gz')
  WHERE icd_version = 10
    AND (icd_code LIKE 'K91%' OR icd_code LIKE 'K63%' OR icd_code LIKE 'T81%')
  GROUP BY icd_code ORDER BY n DESC LIMIT 20
  """)

# 2. blood-culture spec_type_desc distinct values
q("2 — distinct spec_type_desc LIKE '%BLOOD%'",
  f"""
  SELECT spec_type_desc, COUNT(*) AS n
  FROM read_csv_auto('{M}/hosp/microbiologyevents.csv.gz')
  WHERE UPPER(spec_type_desc) LIKE '%BLOOD%'
  GROUP BY spec_type_desc ORDER BY n DESC LIMIT 15
  """)

# 3. inputevents column names
q("3 — inputevents columns",
  f"DESCRIBE SELECT * FROM read_csv_auto('{M}/icu/inputevents.csv.gz') LIMIT 1")

# 4. statusdescription distinct values in inputevents
q("4 — inputevents.statusdescription distinct",
  f"""
  SELECT statusdescription, COUNT(*) AS n
  FROM read_csv_auto('{M}/icu/inputevents.csv.gz')
  GROUP BY statusdescription ORDER BY n DESC LIMIT 15
  """)

# 5. d_items linksto distinct + sample tube-feed labels
q("5 — d_items.linksto distinct",
  f"""
  SELECT linksto, COUNT(*) AS n
  FROM read_csv_auto('{M}/icu/d_items.csv.gz')
  GROUP BY linksto ORDER BY n DESC
  """)

q("6 — sample tube-feed candidate labels (d_items.linksto='inputevents')",
  f"""
  SELECT itemid, label, category
  FROM read_csv_auto('{M}/icu/d_items.csv.gz')
  WHERE linksto = 'inputevents'
    AND (LOWER(label) LIKE '%feed%' OR LOWER(label) LIKE '%enteral%'
         OR LOWER(label) LIKE '%jevity%' OR LOWER(label) LIKE '%nepro%'
         OR LOWER(label) LIKE '%osmolite%' OR LOWER(label) LIKE '%nutren%'
         OR LOWER(label) LIKE '%peptamen%' OR LOWER(label) LIKE '%twocal%'
         OR LOWER(label) LIKE '%glucerna%')
  LIMIT 40
  """)

# 7. icustays first_careunit distinct values
q("7 — icustays.first_careunit distinct (surgical ones matter)",
  f"""
  SELECT first_careunit, COUNT(*) AS n
  FROM read_csv_auto('{M}/icu/icustays.csv.gz')
  GROUP BY first_careunit ORDER BY n DESC LIMIT 25
  """)

# 8. admissions.admission_type distinct
q("8 — admissions.admission_type distinct",
  f"""
  SELECT admission_type, COUNT(*) AS n
  FROM read_csv_auto('{M}/hosp/admissions.csv.gz')
  GROUP BY admission_type ORDER BY n DESC
  """)

con.close()
print("\nDONE.")
