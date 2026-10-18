# -*- coding: utf-8 -*-
"""
05_threshold_sensitivity.py — 24/48/72h exposure-threshold + landmark sensitivity.

Reuses run_comparison from 02_weighting.py. Focuses on the primary outcome
(infection composite) across OW/IPW/PSM, plus in-hospital death (OW), for both
co-primary comparisons. Outputs analysis/threshold_sensitivity.md.
"""
import os
import importlib.util
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("est", os.path.join(HERE, "02_weighting.py"))
est = importlib.util.module_from_spec(spec)
spec.loader.exec_module(est)


def or_str(m):
    return f"{m['or_']:.2f} ({m['or_lo']:.2f}, {m['or_hi']:.2f})"


def run_one(thresh_h, fname):
    d = est.load_cohort(fname)
    out = []
    for ckey, cfg in est.COMPARISONS.items():
        dd = d if cfg["subset"] is None else d.query(cfg["subset"])
        rows, *_ = est.run_comparison(dd, f"{thresh_h}h {cfg['label']}")
        by = {(m["outcome"], m["method"]): m for m in rows}
        n_t, n_c = rows[0]["n_t"], rows[0]["n_c"]
        row = {"threshold": thresh_h, "comp": ckey.split("_")[0],
               "n": len(dd), "n_t": n_t, "n_c": n_c,
               "inf_ow": or_str(by[("infection_composite", "OW")]),
               "inf_iptw": or_str(by[("infection_composite", "IPTW")]),
               "inf_psm": or_str(by[("infection_composite", "PSM")]),
               "death_ow": or_str(by[("hosp_death", "OW")])}
        out.append(row)
    return out


def main():
    rows = []
    for th, fn in [(24, "cohort_24h.csv"), (48, "cohort.csv"), (72, "cohort_72h.csv")]:
        rows += run_one(th, fn)
    tab = pd.DataFrame(rows)
    md = ["# Threshold sensitivity (24 / 48 / 72 h) — infection composite (primary)\n\n",
          "EEN = fed within threshold; landmark = same threshold (immortal-time-safe).\n",
          "OR < 1 = EEN protective. Comparison A = timing (eventually-fed), B = policy (full cohort).\n\n",
          "| Threshold | Comp | n (EEN/ctl) | Infect OW OR | Infect IPTW OR | Infect PSM OR | Death OW OR |\n",
          "|---|---|---|---|---|---|---|\n"]
    for _, r in tab.iterrows():
        md.append(f"| {r['threshold']}h | {r['comp']} | {r['n']} ({r['n_t']}/{r['n_c']}) | "
                  f"{r['inf_ow']} | {r['inf_iptw']} | {r['inf_psm']} | {r['death_ow']} |\n")
    with open(os.path.join(HERE, "threshold_sensitivity.md"), "w", encoding="utf-8") as f:
        f.write("".join(md))
    print("".join(md))


if __name__ == "__main__":
    main()
