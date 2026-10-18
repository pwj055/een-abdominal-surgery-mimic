# -*- coding: utf-8 -*-
"""
19_outcome_validation.py — zero-cost validity check of the primary endpoint.

The primary endpoint is a "treated infection" composite (non-urine positive culture
+ systemic antibiotic in [-1d,+2d], after the 48-h landmark, within 28 days). As a
face/concordance validity check we cross-tabulate it against an independent source —
ICD-coded infection/sepsis diagnoses recorded during the admission (diagnoses_icd).

Neither source is a gold standard (ICD codes are billing diagnoses and may be coded
without a positive culture; the composite requires both a culture and an antibiotic),
so this is reported as concordance, not as sensitivity/specificity against truth.
We report two reference definitions:
  * ICD sepsis/bacteremia (narrow, least ambiguous):
      ICD-10 A40*, A41*, R65.1, R65.2, R78.8 ;  ICD-9 038*, 99591, 99592, 78552
  * ICD any matching-site infection (sepsis + pneumonia + peritonitis/abscess + SSI):
      sepsis (above) + ICD-10 J12*-J18*, K65*, K63.0, K75.0, T81.4*, L02* ;
      ICD-9 481/482/483/485/486, 567*, 540.1, 998.5*

Output: analysis/outcome_validation.md
"""
import os
import sys

import numpy as np
import pandas as pd
import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
M = "D:/physionet/mimic-iv"

# narrow = sepsis/bacteremia
SEPSIS_V10 = ["A40", "A41", "R651", "R652", "R788"]
SEPSIS_V9 = ["038", "99591", "99592", "78552"]
# broad = any matching-site infection (blood/resp/abdominal/wound)
BROAD_V10 = SEPSIS_V10 + ["J12", "J13", "J14", "J15", "J16", "J17", "J18",
                          "K65", "K630", "K750", "T814", "L02"]
BROAD_V9 = SEPSIS_V9 + ["481", "482", "483", "485", "486", "567", "5401", "9985"]


def is_match(code, version, prefixes):
    code = str(code).upper().replace(".", "")
    for p in prefixes:
        if code.startswith(p):
            return 1
    return 0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    df = pd.read_csv(os.path.join(HERE, "cohort.csv"))
    hadms = set(df["hadm_id"].dropna().astype(int))

    con = duckdb.connect()
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE dx AS
    SELECT * FROM read_csv_auto('{M}/hosp/diagnoses_icd.csv.gz')
    """)
    dx = con.execute("SELECT hadm_id, icd_code, icd_version FROM dx").df()
    con.close()
    dx = dx[dx["hadm_id"].isin(hadms)].copy()
    dx["icd_version"] = pd.to_numeric(dx["icd_version"], errors="coerce")

    for label, v10, v9 in [("sepsis", SEPSIS_V10, SEPSIS_V9),
                           ("any_infection", BROAD_V10, BROAD_V9)]:
        v10_set = set(v10); v9_set = set(v9)
        dx[label] = dx.apply(
            lambda r: is_match(r["icd_code"], r["icd_version"],
                               v10_set if r["icd_version"] == 10 else v9_set),
            axis=1)
    dx_agg = dx.groupby("hadm_id")[["sepsis", "any_infection"]].max().reset_index()

    d = df.merge(dx_agg, on="hadm_id", how="left")
    for c in ["sepsis", "any_infection"]:
        d[c] = d[c].fillna(0).astype(int)

    lines = ["# Primary-endpoint concordance check (ICD-coded infection)\n"]
    lines.append("Cross-tabulation of the treated-infection composite (positive non-urine "
                 "culture + systemic antibiotic) against ICD-coded infection/sepsis diagnoses "
                 "recorded during the admission, as a zero-cost face validity check. Neither "
                 "source is a gold standard (ICD codes are billing diagnoses and may be coded "
                 "without a positive culture; the composite requires both a culture and an "
                 "antibiotic), so results are reported as concordance rather than as "
                 "sensitivity/specificity against truth.\n")

    lines.append("\n## ICD code lists used\n")
    lines.append("- **ICD sepsis/bacteremia (narrow):** ICD-10 `A40*`, `A41*`, `R65.1`, `R65.2`, "
                 "`R78.8`; ICD-9 `038*`, `99591`, `99592`, `78552`.\n")
    lines.append("- **ICD any matching-site infection (broad):** sepsis list above plus ICD-10 "
                 "`J12*`–`J18*`, `K65*`, `K63.0`, `K75.0`, `T81.4*`, `L02*`; ICD-9 `481`, `482`, "
                 "`483`, `485`, `486`, `567*`, `540.1`, `998.5*`.\n")

    for label, nice in [("sepsis", "ICD sepsis/bacteremia"),
                        ("any_infection", "ICD any matching-site infection")]:
        tp = int(((d["infection_composite"] == 1) & (d[label] == 1)).sum())
        fp = int(((d["infection_composite"] == 1) & (d[label] == 0)).sum())
        fn = int(((d["infection_composite"] == 0) & (d[label] == 1)).sum())
        tn = int(((d["infection_composite"] == 0) & (d[label] == 0)).sum())
        n = tp + fp + fn + tn
        sens = tp / (tp + fn) if (tp + fn) else np.nan
        spec = tn / (tn + fp) if (tn + fp) else np.nan
        ppv = tp / (tp + fp) if (tp + fp) else np.nan
        npv = tn / (tn + fn) if (tn + fn) else np.nan
        agree = (tp + tn) / n
        po = agree
        pe = ((tp + fp) / n) * ((tp + fn) / n) + ((fn + tn) / n) * ((fp + tn) / n)
        kappa = (po - pe) / (1 - pe) if pe < 1 else np.nan

        lines.append(f"\n## {nice}\n")
        lines.append("| composite \\ ICD | ICD + | ICD − | total |\n|---|---|---|---|\n")
        lines.append(f"| composite + | {tp} | {fp} | {tp + fp} |\n")
        lines.append(f"| composite − | {fn} | {tn} | {fn + tn} |\n")
        lines.append(f"| total | {tp + fn} | {fp + tn} | {n} |\n")
        lines.append("\nAgreement %.1f%%; Cohen's κ = %.3f (treating ICD as reference: "
                     "sensitivity %.1f%%, specificity %.1f%%, PPV %.1f%%, NPV %.1f%%).\n"
                     % (agree * 100, kappa, sens * 100, spec * 100, ppv * 100, npv * 100))

    # overall composite prevalence for context
    prev = d["infection_composite"].mean() * 100
    lines.append(f"\nComposite prevalence in the landmarked cohort (n={len(d)}): "
                 f"{d['infection_composite'].sum()} events ({prev:.1f}%).\n")

    with open(os.path.join(HERE, "outcome_validation.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
