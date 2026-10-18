# -*- coding: utf-8 -*-
"""
07_sensitivities.py — remaining prespecified sensitivity analyses (§8.2/8.3/8.5/8.6).

  §8.3 same-day surgery subgroup      (first major op on ICU admission day, ~66%)
  §8.2 feeding definition             (any record / rate>=20 / ONS-wide)
  §8.5 ITT (first-48h feeding order)  (poe 'Nutrition'/'Tubefeeding Order')
  §8.6 BSI contaminant                (no contaminant exclusion)

All reuse the 48h-landmarked cohort + full-SOFA covariate set and the estimator
from 02_weighting.py. For each sensitivity x comparison we report the primary
outcome (infection composite) across OW/IPW/PSM plus death (OW).

Outputs: analysis/sensitivities.md (+ sensitivity_extra.csv for traceability).
"""
import os
import importlib.util
import duckdb
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
M = "D:/physionet/mimic-iv"
THRESH = 48

spec = importlib.util.spec_from_file_location("est", os.path.join(HERE, "02_weighting.py"))
est = importlib.util.module_from_spec(spec)
spec.loader.exec_module(est)

# ---- constants copied from 01 (keep in sync) ----
ICD9_MAJOR = ("42", "43", "45", "46", "50", "51", "52")
ICD10_MAJOR = (
    "0DB5", "0DB6", "0DB8", "0DB9", "0DBE", "0DBP", "0DBQ",
    "0DT5", "0DT6", "0DT8", "0DT9", "0DTE", "0DTP", "0DTQ",
    "0D15", "0D16", "0D18", "0D19", "0D1E", "0D1P",
    "0FB0", "0FB4", "0FB5", "0FBG",
    "0FT0", "0FT4", "0FT5", "0FTG",
    "0DQ5", "0DQ6", "0DQ8", "0DQE",
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

def sin(x): return "(" + ", ".join(repr(i) for i in x) + ")"

major9 = f"(icd_version = 9 AND SUBSTRING(icd_code,1,2) IN {sin(ICD9_MAJOR)})"
major10 = f"(icd_version = 10 AND SUBSTRING(icd_code,1,4) IN {sin(ICD10_MAJOR)})"
any_major = f"({major9} OR {major10})"
abx_clause = " OR ".join(f"LOWER(r.drug) LIKE '%{a}%'" for a in ABX)


# ---- build per-stay variant columns in one duckdb pass ----
def build_extra():
    con = duckdb.connect()
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE cohort AS
    SELECT stay_id, subject_id, hadm_id, intime
    FROM read_csv_auto('{HERE}/cohort.csv')
    """)

    # exposure variants (single inputevents scan; all rows already Enteral-category)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE expvar AS
    SELECT e.stay_id,
           MIN(e.starttime) AS tf_any,
           MIN(CASE WHEN e.rate >= 20 OR e.amount >= 20 THEN e.starttime END) AS tf_rate20,
           MIN(CASE WHEN (e.rate >= 10 OR e.amount >= 20)
                      OR LOWER(d.label) LIKE '%ensure%'
                      OR LOWER(d.label) LIKE '%boost%'
                      OR LOWER(d.label) LIKE '%enlive%'
                      OR LOWER(d.label) LIKE '%beneprotein%'
                    THEN e.starttime END) AS tf_ons
    FROM cohort c
    JOIN read_csv_auto('{M}/icu/inputevents.csv.gz') e ON c.stay_id = e.stay_id
    JOIN read_csv_auto('{M}/icu/d_items.csv.gz') d ON e.itemid = d.itemid
    WHERE d.linksto = 'inputevents' AND d.category = 'Nutrition - Enteral'
    GROUP BY e.stay_id
    """)

    # ITT: first tubefeeding ORDER at/after ICU admission
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE ordervar AS
    SELECT c.stay_id, MIN(p.ordertime) AS first_order
    FROM cohort c
    JOIN read_csv_auto('{M}/hosp/poe.csv.gz') p ON c.hadm_id = p.hadm_id
    WHERE p.order_type = 'Nutrition' AND p.order_subtype = 'Tubefeeding Order'
      AND p.ordertime >= c.intime
    GROUP BY c.stay_id
    """)

    # same-day surgery: first major op on the ICU admission calendar day
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE sameday AS
    SELECT c.stay_id,
           CASE WHEN o.first_date = CAST(c.intime AS DATE) THEN 1 ELSE 0 END AS same_day
    FROM cohort c
    JOIN (
      SELECT hadm_id, MIN(chartdate) AS first_date
      FROM read_csv_auto('{M}/hosp/procedures_icd.csv.gz')
      WHERE {any_major} GROUP BY hadm_id
    ) o ON c.hadm_id = o.hadm_id
    """)

    # BSI without contaminant exclusion (still excludes 'no growth')
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE pos_nc AS
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
    """)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE treated_nc AS
    SELECT DISTINCT pe.stay_id, pe.site
    FROM pos_nc pe
    JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON pe.hadm_id = r.hadm_id
    WHERE r.starttime BETWEEN pe.charttime - INTERVAL '1' DAY AND pe.charttime + INTERVAL '2' DAY
      AND ({abx_clause})
    """)

    # strict-treated: same culture+antibiotic window but require the overlapping
    # antibiotic to be a >=3-day course (stoptime-starttime >=72h, or ongoing) —
    # discriminates genuine treatment from brief perioperative prophylaxis.
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE treated_strict AS
    SELECT DISTINCT pe.stay_id, pe.site
    FROM pos_nc pe
    JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON pe.hadm_id = r.hadm_id
    WHERE r.starttime BETWEEN pe.charttime - INTERVAL '1' DAY AND pe.charttime + INTERVAL '2' DAY
      AND ({abx_clause})
      AND (r.stoptime IS NULL OR r.stoptime - r.starttime >= INTERVAL '72' HOUR)
    """)

    # strict-treated (>=5 days): a stronger treatment-vs-prophylaxis discriminator
    # (a 3-day course may still cover extended perioperative prophylaxis).
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE treated_strict5 AS
    SELECT DISTINCT pe.stay_id, pe.site
    FROM pos_nc pe
    JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON pe.hadm_id = r.hadm_id
    WHERE r.starttime BETWEEN pe.charttime - INTERVAL '1' DAY AND pe.charttime + INTERVAL '2' DAY
      AND ({abx_clause})
      AND (r.stoptime IS NULL OR r.stoptime - r.starttime >= INTERVAL '120' HOUR)
    """)

    con.execute(f"""
    COPY (
      SELECT c.stay_id,
             sd.same_day,
             (EPOCH(ev.tf_any) - EPOCH(c.intime)) / 3600.0     AS tf_any_hrs,
             (EPOCH(ev.tf_rate20) - EPOCH(c.intime)) / 3600.0  AS tf_rate20_hrs,
             (EPOCH(ev.tf_ons) - EPOCH(c.intime)) / 3600.0     AS tf_ons_hrs,
             (EPOCH(ov.first_order) - EPOCH(c.intime)) / 3600.0 AS order_hrs,
             CASE WHEN b.stay_id IS NOT NULL THEN 1 ELSE 0 END AS treated_bsi_nc,
             CASE WHEN t.stay_id IS NOT NULL THEN 1 ELSE 0 END AS infection_composite_nc,
             CASE WHEN bs.stay_id IS NOT NULL THEN 1 ELSE 0 END AS treated_bsi_strict,
             CASE WHEN ts.stay_id IS NOT NULL THEN 1 ELSE 0 END AS infection_composite_strict,
             CASE WHEN bs5.stay_id IS NOT NULL THEN 1 ELSE 0 END AS treated_bsi_strict5,
             CASE WHEN ts5.stay_id IS NOT NULL THEN 1 ELSE 0 END AS infection_composite_strict5
      FROM cohort c
      LEFT JOIN sameday sd USING (stay_id)
      LEFT JOIN expvar ev USING (stay_id)
      LEFT JOIN ordervar ov USING (stay_id)
      LEFT JOIN (SELECT stay_id, 1 AS x FROM treated_nc WHERE site='blood' GROUP BY stay_id) b USING (stay_id)
      LEFT JOIN (SELECT stay_id, 1 AS x FROM treated_nc WHERE site IN ('blood','abdominal','respiratory','wound') GROUP BY stay_id) t USING (stay_id)
      LEFT JOIN (SELECT stay_id, 1 AS x FROM treated_strict WHERE site='blood' GROUP BY stay_id) bs USING (stay_id)
      LEFT JOIN (SELECT stay_id, 1 AS x FROM treated_strict WHERE site IN ('blood','abdominal','respiratory','wound') GROUP BY stay_id) ts USING (stay_id)
      LEFT JOIN (SELECT stay_id, 1 AS x FROM treated_strict5 WHERE site='blood' GROUP BY stay_id) bs5 USING (stay_id)
      LEFT JOIN (SELECT stay_id, 1 AS x FROM treated_strict5 WHERE site IN ('blood','abdominal','respiratory','wound') GROUP BY stay_id) ts5 USING (stay_id)
    ) TO '{HERE}/sensitivity_extra.csv' (HEADER, DELIMITER ',')
    """)
    con.close()


def or_str(m):
    return f"{m['or_']:.2f} ({m['or_lo']:.2f}, {m['or_hi']:.2f})"


def summarize(d, label):
    """Return {comp: dict} of key estimates for the two co-primary comparisons."""
    out = {}
    for ckey, cfg in est.COMPARISONS.items():
        dd = d if cfg["subset"] is None else d.query(cfg["subset"])
        rows, *_ = est.run_comparison(dd, f"{label} [{cfg['label']}]")
        by = {(m["outcome"], m["method"]): m for m in rows}
        out[ckey.split("_")[0]] = dict(
            n=len(dd), n_t=rows[0]["n_t"], n_c=rows[0]["n_c"],
            inf_ow=or_str(by[("infection_composite", "OW")]),
            inf_iptw=or_str(by[("infection_composite", "IPTW")]),
            inf_psm=or_str(by[("infection_composite", "PSM")]),
            death_ow=or_str(by[("hosp_death", "OW")]),
        )
    return out


def swap_exposure(d, hrs):
    """Override een48/tf_any from a first-feed-hours series (NaN = never)."""
    d = d.copy()
    d["tf_any"] = hrs.notna().astype(int)
    d["een48"] = (hrs <= THRESH).astype(int)
    return d


def main():
    base = est.load_cohort("cohort.csv")
    extra = pd.read_csv(os.path.join(HERE, "sensitivity_extra.csv"))
    d0 = base.merge(extra, on="stay_id", how="left")

    lines = ["# Sensitivity analyses (§8.2 / §8.3 / §8.5 / §8.6)\n\n",
             "48h-landmarked cohort, full-SOFA covariates, OW primary. "
             "A = timing (eventually-fed subset), B = policy (full cohort).\n",
             "OR < 1 = EEN protective. All ORs are for the infection composite except the "
             "Death column.\n\n"]

    def add(title, res):
        lines.append(f"## {title}\n\n")
        lines.append("| Comp | n (EEN/ctl) | Infect OW OR | Infect IPTW OR | Infect PSM OR | Death OW OR |\n")
        lines.append("|---|---|---|---|---|---|\n")
        for comp in ("A", "B"):
            r = res[comp]
            lines.append(f"| {comp} | {r['n']} ({r['n_t']}/{r['n_c']}) | {r['inf_ow']} | "
                         f"{r['inf_iptw']} | {r['inf_psm']} | {r['death_ow']} |\n")
        lines.append("\n")

    # §8.3 same-day surgery subgroup
    d_sd = d0[d0["same_day"] == 1].reset_index(drop=True)
    add("§8.3 Same-day surgery subgroup (first op on ICU day)", summarize(d_sd, "same-day"))

    # §8.2 feeding definition
    defs = [("any record", "tf_any_hrs"), ("rate≥20", "tf_rate20_hrs"), ("ONS-wide", "tf_ons_hrs")]
    for name, col in defs:
        d_v = swap_exposure(d0, pd.to_numeric(d0[col], errors="coerce"))
        add(f"§8.2 Feeding definition — {name}", summarize(d_v, f"feed-{name}"))

    # §8.5 ITT (first-48h feeding order)
    d_itt = swap_exposure(d0, pd.to_numeric(d0["order_hrs"], errors="coerce"))
    add("§8.5 ITT (first-48h tubefeeding ORDER)", summarize(d_itt, "ITT"))

    # §8.6 BSI contaminant — no exclusion
    d_bsi = d0.copy()
    d_bsi["treated_bsi"] = d_bsi["treated_bsi_nc"]
    d_bsi["infection_composite"] = d_bsi["infection_composite_nc"]
    add("§8.6 BSI contaminant — no contaminant exclusion", summarize(d_bsi, "BSI-noContam"))

    # §8.6b strict-treated — antibiotic course >=3 days (exclude brief prophylaxis)
    d_strict = d0.copy()
    d_strict["treated_bsi"] = d_strict["treated_bsi_strict"]
    d_strict["infection_composite"] = d_strict["infection_composite_strict"]
    add("§8.6b Antibiotic course ≥3 days (strict treated)", summarize(d_strict, "strict-treated"))

    # §8.6c strict-treated — antibiotic course >=5 days (stronger treatment discriminator)
    d_strict5 = d0.copy()
    d_strict5["treated_bsi"] = d_strict5["treated_bsi_strict5"]
    d_strict5["infection_composite"] = d_strict5["infection_composite_strict5"]
    add("§8.6c Antibiotic course ≥5 days (strict treated)", summarize(d_strict5, "strict-treated-5d"))

    with open(os.path.join(HERE, "sensitivities.md"), "w", encoding="utf-8") as f:
        f.write("".join(lines))
    print("".join(lines))

    # exposure shift summary (how each feeding definition moves EEN counts)
    print("\nEEN counts by feeding definition (n=1658):")
    for col in ("tf_any_hrs", "tf_rate20_hrs", "tf_ons_hrs"):
        v = pd.to_numeric(d0[col], errors="coerce")
        print(f"  {col}: een48={int((v<=48).sum())}, ever-fed={int(v.notna().sum())}")
    print(f"  ITT order: een48={int((pd.to_numeric(d0['order_hrs'],errors='coerce')<=48).sum())}, "
          f"ever-ordered={int(pd.to_numeric(d0['order_hrs'],errors='coerce').notna().sum())}")


if __name__ == "__main__":
    build_extra()
    main()
