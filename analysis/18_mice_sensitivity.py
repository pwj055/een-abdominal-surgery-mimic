# -*- coding: utf-8 -*-
"""
18_mice_sensitivity.py — multiple imputation by chained equations (MICE) for the
five covariates with >10% missingness (bilirubin, BMI, FiO2, lactate, PaO2), as a
robustness check to the missingness-indicator approach.

For each of the two co-primary comparisons we:
  1. impute the five high-missingness continuous covariates via chained linear
     regressions (predictive mean + posterior draw, "norm" method), including the
     exposure and the outcome in the imputation model per standard practice;
  2. refit the propensity-score model and estimate OW / IPTW / AIPW RD·RR·OR in
     each imputed dataset;
  3. pool log-OR / log-RR / RD across m=25 datasets via Rubin's rules.

Reuses load_cohort, w_effect, aipw_effect, CONT/BIN/SITE from 13_causal_hardening.

Output: analysis/mice_sensitivity.md
"""
import importlib
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
c13 = importlib.import_module("13_causal_hardening")
CONT, BIN, SITE = c13.CONT, c13.BIN, c13.SITE

HIGH_MISSING = ["bili_max", "bmi", "fio2_max", "lactate_max", "po2_min"]
M_IMPUTE = 25
M_ITER = 15
SEED = 20261018


def fmt(e, nd=2):
    return f"{e:.{nd}f}"


def design_matrix_mi(d):
    """Design matrix without the (now all-zero) missingness indicators."""
    present = [c for c in CONT if c in d.columns]
    X = d[present].copy()
    for c in present:
        X[c] = pd.to_numeric(X[c], errors="coerce").fillna(X[c].median())
    for c in BIN:
        X[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(float)
    for s in SITE:
        X["site_" + s] = (d["site"] == s).astype(float)
    return X.astype(float), d["een48"].to_numpy(int)


def mice_impute(d, rng):
    """One chained-equations imputation pass; returns a copy of d with the five
    high-missingness covariates fully imputed."""
    present = [c for c in CONT if c in d.columns]
    X = d[present + list(BIN)].copy()
    for s in SITE:
        X["site_" + s] = (d["site"] == s).astype(float)
    X["een48"] = d["een48"]
    X["infection_composite"] = d["infection_composite"]
    for c in X.columns:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    X = X.astype(float)
    miss_vars = [c for c in HIGH_MISSING if c in present]
    for c in present:
        X[c] = X[c].fillna(X[c].median())

    for _ in range(M_ITER):
        for c in miss_vars:
            obs = d[c].notna().to_numpy()
            if obs.all():
                continue
            pred = [x for x in X.columns if x != c]
            Xo = X.loc[obs, pred].to_numpy(float)
            y = X.loc[obs, c].to_numpy(float)
            Xm = X.loc[~obs, pred].to_numpy(float)
            Xo_c = np.column_stack([np.ones(len(Xo)), Xo])
            Xm_c = np.column_stack([np.ones(len(Xm)), Xm])
            A = Xo_c.T @ Xo_c + np.eye(Xo_c.shape[1]) * 1e-6
            beta = np.linalg.solve(A, Xo_c.T @ y)
            resid = y - Xo_c @ beta
            dof = max(len(y) - Xo_c.shape[1], 1)
            s2 = float(resid @ resid) / dof
            sigma2 = dof * s2 / rng.chisquare(dof)
            cov = sigma2 * np.linalg.inv(A)
            cov = (cov + cov.T) / 2 + np.eye(cov.shape[0]) * 1e-10
            beta_draw = beta + np.linalg.cholesky(cov) @ rng.standard_normal(len(beta))
            X.loc[~obs, c] = Xm_c @ beta_draw + rng.normal(0, np.sqrt(sigma2), len(Xm))

    out = d.copy()
    for c in miss_vars:
        out[c] = X[c].to_numpy()
    return out


def se_log(lo, hi):
    return (np.log(hi) - np.log(lo)) / (2 * 1.959964)


def se_lin(lo, hi):
    return (hi - lo) / (2 * 1.959964)


def rubin_log(ests, ses):
    ests = np.asarray(ests, float); ses = np.asarray(ses, float)
    m = len(ests)
    theta = np.log(ests).mean()
    W = (ses ** 2).mean()
    B = np.log(ests).var(ddof=1) if m > 1 else 0.0
    T = W + (1 + 1.0 / m) * B
    se = np.sqrt(T)
    return np.exp(theta), np.exp(theta - 1.959964 * se), np.exp(theta + 1.959964 * se)


def rubin_lin(ests, ses):
    ests = np.asarray(ests, float); ses = np.asarray(ses, float)
    m = len(ests)
    theta = ests.mean()
    W = (ses ** 2).mean()
    B = ests.var(ddof=1) if m > 1 else 0.0
    T = W + (1 + 1.0 / m) * B
    se = np.sqrt(T)
    return theta, theta - 1.959964 * se, theta + 1.959964 * se


def main():
    df = c13.load_cohort()
    rng = np.random.default_rng(SEED)
    lines = ["# Multiple imputation (MICE) sensitivity\n"]
    lines.append(f"Chained-equations imputation (linear 'norm' models, {M_IMPUTE} imputations × "
                 f"{M_ITER} iterations) for the five covariates with >10% missingness "
                 "(bilirubin, BMI, FiO2, lactate, PaO2), including the exposure and outcome in the "
                 "imputation model. PS / OW / IPTW / AIPW refit in each dataset; pooled via "
                 "Rubin's rules.\n")
    lines.append("| comparison | method | n | RD (95% CI) | RR (95% CI) | OR (95% CI) |\n")
    lines.append("|---|---|---|---|---|---|\n")

    for cfg in [("A: EEN vs late EN", df.query("tf_any==1")),
                ("B: EEN vs no-EEN", df)]:
        d0 = cfg[1].reset_index(drop=True)
        acc = {"OW": {"or": [], "rr": [], "rd": [], "so": [], "sr": [], "sd": []},
               "IPTW": {"or": [], "rr": [], "rd": [], "so": [], "sr": [], "sd": []},
               "AIPW": {"or": [], "rr": [], "rd": [], "so": [], "sr": [], "sd": []}}
        for _ in range(M_IMPUTE):
            dimp = mice_impute(d0, rng)
            X, A = design_matrix_mi(dimp)
            Y = dimp["infection_composite"].to_numpy(float)
            Xc = sm.add_constant(X)
            p = np.clip(np.asarray(sm.Logit(A, Xc).fit(disp=0).predict(Xc), float),
                        1e-6, 1 - 1e-6)
            ow = np.where(A == 1, 1 - p, p)
            p1 = A.mean()
            w_stab = np.where(A == 1, p1 / p, (1 - p1) / (1 - p))
            lo, hi = np.percentile(w_stab, [1, 99])
            w_iptw = np.clip(w_stab, lo, hi)
            for mname, w in [("OW", ow), ("IPTW", w_iptw)]:
                e = c13.w_effect(Y, A, w)
                acc[mname]["or"].append(e["or_"][0]); acc[mname]["so"].append(se_log(e["or_"][1], e["or_"][2]))
                acc[mname]["rr"].append(e["rr"][0]); acc[mname]["sr"].append(se_log(e["rr"][1], e["rr"][2]))
                acc[mname]["rd"].append(e["rd"][0]); acc[mname]["sd"].append(se_lin(e["rd"][1], e["rd"][2]))
            a = c13.aipw_effect(X, A, Y)
            acc["AIPW"]["or"].append(a["or_"][0]); acc["AIPW"]["so"].append(se_log(a["or_"][1], a["or_"][2]))
            acc["AIPW"]["rr"].append(a["rr"][0]); acc["AIPW"]["sr"].append(se_log(a["rr"][1], a["rr"][2]))
            acc["AIPW"]["rd"].append(a["rd"][0]); acc["AIPW"]["sd"].append(se_lin(a["rd"][1], a["rd"][2]))
        for mname in ["OW", "IPTW", "AIPW"]:
            rd = rubin_lin(acc[mname]["rd"], acc[mname]["sd"])
            rr = rubin_log(acc[mname]["rr"], acc[mname]["sr"])
            or_ = rubin_log(acc[mname]["or"], acc[mname]["so"])
            lines.append(f"| {cfg[0]} | {mname} | {len(d0)} | "
                         f"{fmt(rd[0])} ({fmt(rd[1])}, {fmt(rd[2])}) | "
                         f"{fmt(rr[0])} ({fmt(rr[1])}, {fmt(rr[2])}) | "
                         f"{fmt(or_[0])} ({fmt(or_[1])}, {fmt(or_[2])}) |\n")

    with open(os.path.join(HERE, "mice_sensitivity.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
