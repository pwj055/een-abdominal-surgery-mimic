# -*- coding: utf-8 -*-
"""
10_reviewer_diagnostics.py — reviewer-driven diagnostics (2026-10-17).

Two hard pre-submission questions:
  1. PSM point-estimate anomaly: Comparison A infection composite PSM OR moved
     0.70 -> 0.33 across the landmark-fix re-run (OW/IPTW unchanged ~0.60/0.68).
     Diagnose: matched-pair counts, match success rate, matched-sample event
     counts, matched SMD balance, caliper sensitivity (0.05/0.1/0.2/0.3).
  2. Upper-GI "dominant confounder" claim is asserted in the Discussion but never
     tested. Run: exclude upper-GI; stratify upper-GI vs other.

Reads analysis/cohort.csv (+ sofa_covariates.csv via 02_weighting.load_cohort).
"""
import os
import importlib.util
import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("est", os.path.join(HERE, "02_weighting.py"))
est = importlib.util.module_from_spec(spec)
spec.loader.exec_module(est)

df = est.df  # cohort.csv + sofa_covariates.csv


def or_str(r):
    return f"{r['or_']:.2f} ({r['or_lo']:.2f}–{r['or_hi']:.2f})"


def extract_infection(d):
    """Run run_comparison and return {method: effect_row} for infection_composite."""
    rows, *_ = est.run_comparison(d, "diag")
    out = {}
    for m in rows:
        if m["outcome"] == "infection_composite" and m["method"] != "Crude":
            out[m["method"]] = m
    return out


def core_estimates(d):
    """Robust OW/IPTW/PSM for infection_composite; drops constant covariate cols.

    Needed for site-restricted subsets (e.g. excluding upper-GI makes the
    site_upper dummy constant -> singular Hessian in the full design matrix).
    """
    X, A = est.design_matrix(d)
    const = [c for c in X.columns if X[c].nunique() <= 1]
    if const:
        X = X.drop(columns=const)
    Xc = sm.add_constant(X)
    ps = sm.Logit(A, Xc).fit(disp=0)
    p = np.clip(np.asarray(ps.predict(Xc), dtype=float), 1e-6, 1 - 1e-6)
    ps_logit = np.log(p / (1 - p))
    ow = np.where(A == 1, 1 - p, p)
    p1 = A.mean()
    w_stab = np.where(A == 1, p1 / p, (1 - p1) / (1 - p))
    lo, hi = np.percentile(w_stab, [1, 99])
    w_stab_t = np.clip(w_stab, lo, hi)
    mt, mc = est.greedy_match(ps_logit, A, 0.2 * np.std(ps_logit))
    Y = d["infection_composite"].to_numpy(float)
    return {
        "OW": est.effect_row(Y, A, method_weights=ow),
        "IPTW": est.effect_row(Y, A, method_weights=w_stab_t),
        "PSM": est.effect_row(Y, A, matched=(mt, mc)),
    }, X, A, ow, mt, mc


def psm_diagnosis(d, label):
    X, A = est.design_matrix(d)
    Xc = sm.add_constant(X)
    ps = sm.Logit(A, Xc).fit(disp=0)
    p = np.clip(np.asarray(ps.predict(Xc), dtype=float), 1e-6, 1 - 1e-6)
    ps_logit = np.log(p / (1 - p))
    n_t = int(A.sum())
    n_c = int((1 - A).sum())
    Y = d["infection_composite"].to_numpy(float)
    sd = np.std(ps_logit)

    print(f"\n=== PSM diagnosis — {label} ===")
    print(f"n_t={n_t}, n_c={n_c}, sd(ps_logit)={sd:.3f}")
    print(f"site distribution (treated): {d['site'].loc[A == 1].value_counts().to_dict()}")
    print(f"site distribution (control): {d['site'].loc[A == 0].value_counts().to_dict()}")

    for cal in [0.05, 0.1, 0.2, 0.3]:
        mt, mc = est.greedy_match(ps_logit, A, cal * sd)
        if len(mt) == 0:
            print(f"  caliper {cal}: 0 pairs")
            continue
        idx = np.concatenate([mt, mc])
        ev_t = int(Y[mt].sum())
        ev_c = int(Y[mc].sum())
        b = int(((Y[mt] == 1) & (Y[mc] == 0)).sum())  # EEN event, ctl no event
        c = int(((Y[mt] == 0) & (Y[mc] == 1)).sum())  # EEN no event, ctl event
        or_ = (b + 0.5) / (c + 0.5)
        se = np.sqrt(1.0 / (b + 0.5) + 1.0 / (c + 0.5))
        lo = np.exp(np.log(or_) - 1.959964 * se)
        hi = np.exp(np.log(or_) + 1.959964 * se)
        smd = est.smd_table(X.iloc[idx], A[idx], None)
        site_m = d["site"].iloc[idx].value_counts(normalize=True).round(3).to_dict()
        print(f"  caliper {cal}: pairs={len(mt)}/{n_t} ({100*len(mt)/n_t:.1f}%), "
              f"matched events EEN {ev_t}/{len(mt)} vs ctl {ev_c}/{len(mc)}, "
              f"discordant b={b} c={c}, OR={or_:.2f} ({lo:.2f}–{hi:.2f}), "
              f"max|SMD|={np.abs(smd).max():.3f}")
        print(f"      matched site%: {site_m}")


def main():
    dA = df.query("tf_any == 1").reset_index(drop=True)

    # ---- 1. PSM diagnosis on Comparison A ----
    psm_diagnosis(dA, "Comparison A (eventually-fed, infection composite)")

    # cross-check default OW/IPTW/PSM via the standard pipeline
    print("\n=== Standard pipeline cross-check (Comparison A, infection composite) ===")
    for mname, r in extract_infection(dA).items():
        print(f"  {mname}: OR {or_str(r)}  (n_t={r['n_t']}, n_c={r['n_c']}, "
              f"ev_t={r['ev_t']}, ev_c={r['ev_c']})")

    # ---- 2. upper-GI exclusion / stratification ----
    print("\n=== Upper-GI exclusion (Comparison A, infection composite) ===")
    dA_noUpper = dA.query("site != 'upper'").reset_index(drop=True)
    res, X, A, ow, mt, mc = core_estimates(dA_noUpper)
    for mname, r in res.items():
        print(f"  exclude-upper {mname}: OR {or_str(r)}  (n_t={r['n_t']}, n_c={r['n_c']}, "
              f"ev_t={r['ev_t']}, ev_c={r['ev_c']})")
    if len(mt):
        print(f"      PSM pairs={len(mt)}/{r['n_t']}")

    print("\n=== Upper-GI stratum (Comparison A, infection composite) ===")
    dA_upper = dA.query("site == 'upper'").reset_index(drop=True)
    res_u, _, _, _, mt_u, _ = core_estimates(dA_upper)
    for mname, r in res_u.items():
        print(f"  upper-only {mname}: OR {or_str(r)}  (n_t={r['n_t']}, n_c={r['n_c']}, "
              f"ev_t={r['ev_t']}, ev_c={r['ev_c']})")
    if len(mt_u):
        print(f"      PSM pairs={len(mt_u)}/{res_u['OW']['n_t']}")

    print("\n=== Non-upper-GI stratum (Comparison A, infection composite) ===")
    dA_other = dA.query("site != 'upper'").reset_index(drop=True)
    res_o, _, _, _, mt_o, _ = core_estimates(dA_other)
    for mname, r in res_o.items():
        print(f"  non-upper {mname}: OR {or_str(r)}  (n_t={r['n_t']}, n_c={r['n_c']}, "
              f"ev_t={r['ev_t']}, ev_c={r['ev_c']})")
    if len(mt_o):
        print(f"      PSM pairs={len(mt_o)}/{res_o['OW']['n_t']}")

    print("\n=== Comparison A infection events by site (raw) ===")
    print(dA.groupby("site").agg(
        n=("stay_id", "size"),
        een=("een48", "sum"),
        inf=("infection_composite", "sum")).to_string())


if __name__ == "__main__":
    main()
