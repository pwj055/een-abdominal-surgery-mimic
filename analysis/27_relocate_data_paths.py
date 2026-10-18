# -*- coding: utf-8 -*-
"""Relocate hardcoded PhysioNet data paths to D:/physionet/ after consolidating all
raw data under one directory (D:/physionet/mimic-iv, mimic3, eicu).

Data moved on 2026-10-18:
  MIMIC-IV  C:/Users/jiang/Desktop/Enteral Nutrition/mimic-iv -> D:/physionet/mimic-iv
  MIMIC-III D:/mimic3      (raw csv.gz only)                   -> D:/physionet/mimic3
  eICU      D:/eicu                                             -> D:/physionet/eicu

Workspace-generated outputs (e.g. 22_graphical_abstract.py writing to the workspace
root) are intentionally NOT touched.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

OLD_M4 = "C:/Users/jiang/Desktop/Enteral Nutrition/mimic-iv"
NEW_M4 = "D:/physionet/mimic-iv"

M4_FILES = [
    "analysis/01_build_dataset.py",
    "analysis/03_tables.py",
    "analysis/06_sofa_covariates.py",
    "analysis/07_sensitivities.py",
    "analysis/08_competing_risk.py",
    "analysis/11_reviewer_figures.py",
    "analysis/13_causal_hardening.py",
    "analysis/19_outcome_validation.py",
    "feasibility/verify_format.py",
    "feasibility/f5_fix.py",
    "feasibility/gaps.py",
    "feasibility/feasibility_check.py",
]

# (relative_path, old, new) — non-MIMIC-IV edits.
EDITS = [
    ("analysis/14_mimic3_replication.py", '"D:/mimic3"', '"D:/physionet/mimic3"'),
    ("analysis/15_eicu_replication.py", "D:/eicu", "D:/physionet/eicu"),
    ("analysis/README.md", "../mimic-iv/", "D:\\physionet\\mimic-iv\\"),
    ("analysis/README.md", "D:\\mimic3", "D:\\physionet\\mimic3"),
    ("analysis/README.md", "D:\\eicu", "D:\\physionet\\eicu"),
]


def rewrite(rel, old, new):
    path = os.path.join(ROOT, rel)
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    n = txt.count(old)
    if n == 0:
        print(f"  WARN: not found in {rel}: {old!r}")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt.replace(old, new))
    print(f"  {rel}: {n}x  {old!r} -> {new!r}")


if __name__ == "__main__":
    for rel in M4_FILES:
        rewrite(rel, OLD_M4, NEW_M4)
    for rel, old, new in EDITS:
        rewrite(rel, old, new)
    print("done")
