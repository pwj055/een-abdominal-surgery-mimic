# -*- coding: utf-8 -*-
"""
02_weighting.py — causal effect estimation on the analysis-ready cohort.

Two co-primary comparisons x four outcomes, three methods each:
  Comparison A (timing):   eventually-fed subset (EEN vs late EN)
  Comparison B (policy):   full landmarked cohort (EEN vs no-EEN)
  Methods: overlap weighting (OW, primary) / stabilized+truncated IPTW / PSM(caliper 0.2)

For each (comparison, outcome, method): weighted risk difference + odds ratio,
with robust sandwich SE (GEE independence, subject-clustered). Also reports
SMD (before/after) and effective sample size (ESS).

Outputs: analysis/results.md (tables) + analysis/estimates.csv (all cells).
"""
import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm
from statsmodels.genmod.families import Binomial, Gaussian, Poisson
from statsmodels.genmod.families.links import Logit, Identity, Log
from statsmodels.genmod.cov_struct import Independence

HERE = os.path.dirname(os.path.abspath(__file__))


def load_cohort(fname):
    d = pd.read_csv(os.path.join(HERE, fname))
    sf = os.path.join(HERE, "sofa_covariates.csv")
    if os.path.exists(sf):
        d = d.merge(pd.read_csv(sf), on="stay_id", how="left")
    return d


df = load_cohort("cohort.csv")

# ---- covariate set (0-24h, prespecified) ----
CONT = ["age", "n_major_procs", "lactate_max", "creat_max", "wbc_max", "plt_min", "bili_max",
        "gcs_min", "map_min", "fio2_max", "po2_min", "bmi"]
BIN = ["female", "emergency", "stoma", "any_explor", "vaso_24h", "mv_24h",
       "diabetes", "ckd", "cirrhosis"]
SITE = ["hpb", "upper", "lower"]   # reference = other

OUTCOMES = {
    "infection_composite": "Infection composite (primary)",
    "treated_bsi": "Treated BSI (key secondary)",
    "leak_reop": "Leak/reoperation (key secondary safety)",
    "hosp_death": "In-hospital death (secondary)",
}
COMPARISONS = {
    "A_timing": dict(subset="tf_any==1", label="A: EEN vs late EN (eventually-fed)"),
    "B_policy": dict(subset=None, label="B: EEN vs no-EEN (full landmarked cohort)"),
}


def design_matrix(d):
    """Return (X DataFrame, A array). Median-imputes continuous; lactate missing indicator."""
    present = [c for c in CONT if c in d.columns]
    X = d[present].copy()
    for c in present:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    if "lactate_max" in d.columns:
        X["lactate_missing"] = pd.to_numeric(d["lactate_max"], errors="coerce").isna().astype(int)
    for c in present:
        med = X[c].median()
        X[c] = X[c].fillna(med)
    for c in BIN:
        X[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)
    for s in SITE:
        X["site_" + s] = (d["site"] == s).astype(int)
    X = X.astype(float)
    A = d["een48"].to_numpy(int)
    return X, A


def smd_table(X, A, w=None):
    """SMD per covariate. If w given, weighted within-arm means/variances."""
    out = {}
    for c in X.columns:
        x = X[c].to_numpy(float)
        if w is None:
            mt, mc = x[A == 1].mean(), x[A == 0].mean()
            vt, vc = x[A == 1].var(ddof=1), x[A == 0].var(ddof=1)
        else:
            wt, wc = w[A == 1], w[A == 0]
            mt = np.sum(wt * x[A == 1]) / np.sum(wt)
            mc = np.sum(wc * x[A == 0]) / np.sum(wc)
            vt = np.sum(wt * (x[A == 1] - mt) ** 2) / np.sum(wt)
            vc = np.sum(wc * (x[A == 0] - mc) ** 2) / np.sum(wc)
        denom = np.sqrt((vt + vc) / 2)
        out[c] = (mt - mc) / denom if denom > 0 else np.nan
    return pd.Series(out)


def ess(w, A):
    return {a: float(np.sum(w[A == a]) ** 2 / np.sum(w[A == a] ** 2)) for a in (0, 1)}


def p_from_z(z):
    """Two-sided Wald p-value from a normal z-statistic."""
    return float(2 * norm.sf(np.abs(z)))


def weighted_effect(Y, A, w, groups):
    """Weighted RD (Gaussian-identity), OR (binomial-logit), RR (modified Poisson)."""
    n = len(Y)
    Xd = np.column_stack([np.ones(n), A])
    rd = sm.GEE(Y, Xd, groups=groups, family=Gaussian(Identity()),
                cov_struct=Independence(), weights=w).fit()
    orm = sm.GEE(Y, Xd, groups=groups, family=Binomial(Logit()),
                 cov_struct=Independence(), weights=w).fit()
    rrm = sm.GEE(Y, Xd, groups=groups, family=Poisson(Log()),
                 cov_struct=Independence(), weights=w).fit()
    return rd, orm, rrm


def greedy_match(ps_logit, A, caliper):
    t = np.where(A == 1)[0]
    c = np.where(A == 0)[0]
    c = c[np.argsort(ps_logit[c])]
    used = np.zeros(len(c), bool)
    mt, mc = [], []
    for i in t:
        d = np.abs(ps_logit[i] - ps_logit[c])
        mask = (~used) & (d <= caliper)
        if mask.any():
            j = int(np.argmin(np.where(mask, d, 1e9)))
            used[j] = True
            mt.append(i); mc.append(c[j])
    return np.array(mt), np.array(mc)


def ci_normal(est, se, alpha=0.05):
    z = 1.959964
    return est, est - z * se, est + z * se


def effect_row(Y, A, method_weights=None, matched=None):
    """Return dict with RD/RR/OR (95% CI) + Wald p, n_t/n_c, ev_t/ev_c."""
    Y = np.asarray(Y, float); A = np.asarray(A, int)
    if matched is not None:
        mt, mc = matched
        n_t, n_c = len(mt), len(mc)
        ev_t, ev_c = int(Y[mt].sum()), int(Y[mc].sum())
        # OR via McNemar on matched pairs (conditional-logistic equivalent)
        b = int(((Y[mt] == 1) & (Y[mc] == 0)).sum())
        c = int(((Y[mt] == 0) & (Y[mc] == 1)).sum())
        or_ = (b + 0.5) / (c + 0.5)
        se_or = np.sqrt(1.0 / (b + 0.5) + 1.0 / (c + 0.5))
        p_or = p_from_z(np.log(or_) / se_or)
        # RD via paired difference (matched pairs)
        diff = Y[mt] - Y[mc]
        rd = float(diff.mean())
        rd_se = diff.std(ddof=1) / np.sqrt(len(diff)) if len(diff) > 1 else np.nan
        p_rd = p_from_z(rd / rd_se) if rd_se and np.isfinite(rd_se) else np.nan
        # marginal RR within the matched sample (modified Poisson, clustered by pair)
        Ym = np.concatenate([Y[mt], Y[mc]])
        Am = np.concatenate([np.ones(n_t), np.zeros(n_c)])
        grp = np.concatenate([np.arange(n_t), np.arange(n_t)])
        Xm = np.column_stack([np.ones(len(Ym)), Am])
        rrm = sm.GEE(Ym, Xm, groups=grp, family=Poisson(Log()),
                     cov_struct=Independence()).fit()
        return dict(n_t=n_t, n_c=n_c, ev_t=ev_t, ev_c=ev_c,
                    rd=rd, rd_lo=rd - 1.959964 * rd_se, rd_hi=rd + 1.959964 * rd_se,
                    p_rd=p_rd,
                    or_=or_, or_lo=np.exp(np.log(or_) - 1.959964 * se_or),
                    or_hi=np.exp(np.log(or_) + 1.959964 * se_or), p_or=p_or,
                    rr=float(np.exp(rrm.params[1])),
                    rr_lo=float(np.exp(rrm.params[1] - 1.959964 * rrm.bse[1])),
                    rr_hi=float(np.exp(rrm.params[1] + 1.959964 * rrm.bse[1])),
                    p_rr=p_from_z(rrm.params[1] / rrm.bse[1]))
    # weighted
    w = np.asarray(method_weights, float)
    groups = np.arange(len(Y))
    ev_t = int(np.sum((A == 1) & (Y == 1))); ev_c = int(np.sum((A == 0) & (Y == 1)))
    n_t = int(np.sum(A == 1)); n_c = int(np.sum(A == 0))
    rd, orm, rrm = weighted_effect(Y, A, w, groups)
    return dict(n_t=n_t, n_c=n_c, ev_t=ev_t, ev_c=ev_c,
                rd=float(rd.params[1]), rd_lo=float(rd.params[1] - 1.959964 * rd.bse[1]),
                rd_hi=float(rd.params[1] + 1.959964 * rd.bse[1]),
                p_rd=p_from_z(rd.params[1] / rd.bse[1]),
                or_=float(np.exp(orm.params[1])),
                or_lo=float(np.exp(orm.params[1] - 1.959964 * orm.bse[1])),
                or_hi=float(np.exp(orm.params[1] + 1.959964 * orm.bse[1])),
                p_or=p_from_z(orm.params[1] / orm.bse[1]),
                rr=float(np.exp(rrm.params[1])),
                rr_lo=float(np.exp(rrm.params[1] - 1.959964 * rrm.bse[1])),
                rr_hi=float(np.exp(rrm.params[1] + 1.959964 * rrm.bse[1])),
                p_rr=p_from_z(rrm.params[1] / rrm.bse[1]))


def run_comparison(d, label, trim=None):
    if trim is not None:
        # overlap restriction: fit full PS, drop observations with PS outside [lo, hi],
        # then re-fit PS on the trimmed sample.
        lo, hi = trim
        d = d.reset_index(drop=True)
        Xf, Af = design_matrix(d)
        Xcf = sm.add_constant(Xf)
        pf = np.clip(np.asarray(sm.Logit(Af, Xcf).fit(disp=0).predict(Xcf)), 1e-6, 1 - 1e-6)
        d = d[(pf >= lo) & (pf <= hi)].reset_index(drop=True)
    X, A = design_matrix(d)
    # PS model (logistic)
    Xc = sm.add_constant(X)
    ps = sm.Logit(A, Xc).fit(disp=0)
    p = np.clip(np.asarray(ps.predict(Xc), dtype=float), 1e-6, 1 - 1e-6)
    ps_logit = np.log(p / (1 - p))

    # weights
    ow = np.where(A == 1, 1 - p, p)
    p1 = A.mean()
    w_ate = np.where(A == 1, 1 / p, 1 / (1 - p))
    w_stab = np.where(A == 1, p1 / p, (1 - p1) / (1 - p))
    lo, hi = np.percentile(w_stab, [1, 99])
    w_stab_t = np.clip(w_stab, lo, hi)
    caliper = 0.2 * np.std(ps_logit)
    mt, mc = greedy_match(ps_logit, A, caliper)

    rows = []
    smd_raw = smd_table(X, A)
    smd_ow = smd_table(X, A, ow)
    smd_ipw = smd_table(X, A, w_stab_t)
    e_ow = ess(ow, A); e_ipw = ess(w_stab_t, A)

    for okey, oname in OUTCOMES.items():
        Y = d[okey].to_numpy(float)
        crude = effect_row(Y, A, method_weights=np.ones(len(Y)))
        crude.update(method="Crude", outcome=okey, outcome_label=oname,
                     comparison=label, smd_before=float("nan"), smd_after=float("nan"),
                     ess_t=float("nan"), ess_c=float("nan"))
        rows.append(crude)
        for mname, w, mtch in [("OW", ow, None), ("IPTW", w_stab_t, None),
                               ("PSM", None, (mt, mc))]:
            r = effect_row(Y, A, method_weights=w, matched=mtch)
            r.update(method=mname, outcome=okey, outcome_label=oname,
                     comparison=label,
                     smd_before=float(np.abs(smd_raw).max()),
                     smd_after=float(np.abs(smd_ow).max()) if mname == "OW"
                     else float(np.abs(smd_ipw).max()) if mname == "IPTW" else float("nan"),
                     ess_t=e_ow[1] if mname == "OW" else e_ipw[1],
                     ess_c=e_ow[0] if mname == "OW" else e_ipw[0])
            rows.append(r)
    return rows, smd_raw, smd_ow, smd_ipw, e_ow, e_ipw, len(d)


def fmt_p(x, digits=3):
    return "NA" if x is None or np.isnan(x) else f"{x:.{digits}f}"


def main():
    all_rows = []
    md = []
    for ckey, cfg in COMPARISONS.items():
        d = df if cfg["subset"] is None else df.query(cfg["subset"])
        for tag, trim in [("", None), (" [PS-trim 0.1-0.9]", (0.1, 0.9))]:
            label = cfg["label"] + tag
            rows, smd_raw, smd_ow, smd_ipw, e_ow, e_ipw, n_used = \
                run_comparison(d, label, trim=trim)
            all_rows += rows
            n_t, n_c = rows[0]["n_t"], rows[0]["n_c"]
            md.append(f"## {label}\n")
            md.append(f"- n = {n_used}  (EEN {n_t} / control {n_c})\n")
            md.append(f"- OW ESS: treated {e_ow[1]:.0f} / control {e_ow[0]:.0f}   |   "
                      f"IPTW ESS: treated {e_ipw[1]:.0f} / control {e_ipw[0]:.0f}\n")
            md.append(f"- max |SMD|: raw {np.abs(smd_raw).max():.3f} -> OW {np.abs(smd_ow).max():.3f}, "
                      f"IPTW {np.abs(smd_ipw).max():.3f}\n\n")
            for m in rows:
                if m["method"] == "Crude":
                    md.append(f"### {m['outcome_label']}\n")
                    md.append("| method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |\n")
                    md.append("|---|---|---|---|---|---|---|---|---|\n")
                md.append(f"| {m['method']} | {m['n_t']} | {m['n_c']} | {m['ev_t']} | {m['ev_c']} | "
                          f"{fmt_p(m['rd'],2)} ({fmt_p(m['rd_lo'],2)}, {fmt_p(m['rd_hi'],2)}) | "
                          f"{fmt_p(m['rr'],2)} ({fmt_p(m['rr_lo'],2)}, {fmt_p(m['rr_hi'],2)}) | "
                          f"{fmt_p(m['or_'],2)} ({fmt_p(m['or_lo'],2)}, {fmt_p(m['or_hi'],2)}) | "
                          f"{fmt_p(m['p_or'],3)} |\n")
            md.append("\n")

    pd.DataFrame(all_rows).to_csv(os.path.join(HERE, "estimates.csv"), index=False)
    with open(os.path.join(HERE, "results.md"), "w", encoding="utf-8") as f:
        f.write("# Causal effect estimates (OW / IPTW / PSM)\n\n" + "".join(md))
    print("".join(md))


if __name__ == "__main__":
    main()
