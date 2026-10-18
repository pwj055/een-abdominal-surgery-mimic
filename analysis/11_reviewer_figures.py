# -*- coding: utf-8 -*-
"""
11_reviewer_figures.py — reviewer-requested figures (figure review, round 4).

  Fig 4  propensity-score overlap (comparisons A and B), PS-trim region shaded
  Fig 5  Love plot: |SMD| before (raw) vs after OW / IPTW, per covariate
  Fig 6  dose-response threshold gradient (24/48/72 h, OW OR, log scale)
  Fig 7  estimand schematic (Comparison A vs B)

  Supp Fig S1  first-feeding-time distribution (eventually-fed), 24/48/72 h marks
  Supp Fig S2  never-fed dissection (died / therapeutic NPO / oral recovery)
  Supp Fig S3  primary-composite site decomposition (blood/abdo/resp/wound)

Reuses the estimator / covariate machinery from 02_weighting.py and the exact
microbiology definitions (including contaminant exclusion) from 01_build_dataset.py.
"""
import os
import importlib.util
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import statsmodels.api as sm
import duckdb

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)
M = "C:/Users/jiang/Desktop/Enteral Nutrition/mimic-iv"

spec = importlib.util.spec_from_file_location("est", os.path.join(HERE, "02_weighting.py"))
est = importlib.util.module_from_spec(spec)
spec.loader.exec_module(est)

# ---- covariate display labels (02_weighting design-matrix column names) ----
LABELS = {
    "age": "Age", "n_major_procs": "# major procedures",
    "lactate_max": "Lactate (max)", "lactate_missing": "Lactate missing",
    "creat_max": "Creatinine (max)", "wbc_max": "WBC (max)",
    "plt_min": "Platelets (min)", "bili_max": "Bilirubin (max)",
    "gcs_min": "GCS (min)", "map_min": "MAP (min)",
    "fio2_max": "FiO2 (max)", "po2_min": "PaO2 (min)", "bmi": "BMI",
    "female": "Female", "emergency": "Emergency", "stoma": "Stoma",
    "any_explor": "Exploratory index op", "vaso_24h": "Vasopressor (0-24 h)",
    "mv_24h": "Mechanical ventilation", "diabetes": "Diabetes",
    "ckd": "CKD", "cirrhosis": "Cirrhosis",
    "site_hpb": "Site: HPB", "site_upper": "Site: upper GI",
    "site_lower": "Site: lower GI",
}

BLUE = "#1f4e79"; RED = "#c00000"; GREY = "#7f7f7f"


def comparison_data(comp):
    """Load cohort, restrict to comparison A or B, fit PS, return weights + X."""
    d = est.load_cohort("cohort.csv")
    if comp == "A":
        d = d[d["tf_any"] == 1].reset_index(drop=True)
    X, A = est.design_matrix(d)
    Xc = sm.add_constant(X)
    ps = sm.Logit(A, Xc).fit(disp=0)
    p = np.clip(np.asarray(ps.predict(Xc), float), 1e-6, 1 - 1e-6)
    ow = np.where(A == 1, 1 - p, p)
    p1 = A.mean()
    w_stab = np.where(A == 1, p1 / p, (1 - p1) / (1 - p))
    lo, hi = np.percentile(w_stab, [1, 99])
    w_stab_t = np.clip(w_stab, lo, hi)
    return d, p, A, X, ow, w_stab_t


# ---- Figure 4: PS overlap ----
def fig4():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, comp, title in [
        (axes[0], "A", "A: EEN vs late EN (eventually-fed)"),
        (axes[1], "B", "B: EEN vs no-EEN (full cohort)"),
    ]:
        d, p, A, X, ow, w = comparison_data(comp)
        ax.axvspan(0.1, 0.9, color="#f0f0f0", zorder=0, label="PS-trim region [0.1, 0.9]")
        for a, col, lab in [(0, BLUE, "control"), (1, RED, "EEN")]:
            ax.hist(p[A == a], bins=40, density=True, alpha=0.6, color=col, label=lab)
        ax.set_xlabel("Propensity score (P[EEN])")
        ax.set_ylabel("Density")
        ax.set_title(title, fontsize=11, weight="bold")
        ax.legend(fontsize=8, frameon=False, loc="upper center")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Propensity-score overlap (before weighting)", fontsize=12, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT, "fig4_ps_overlap.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Figure 5: Love plot ----
def fig5():
    fig, axes = plt.subplots(1, 2, figsize=(11, 6.8))
    for ax, comp, title in [
        (axes[0], "A", "A: EEN vs late EN"),
        (axes[1], "B", "B: EEN vs no-EEN"),
    ]:
        d, p, A, X, ow, w = comparison_data(comp)
        raw = est.smd_table(X, A)
        ow_s = est.smd_table(X, A, ow)
        ipw_s = est.smd_table(X, A, w)
        order = np.argsort(np.abs(raw.to_numpy()))[::-1]     # largest |SMD| first
        cols = [X.columns[i] for i in order]
        ys = np.arange(len(cols))[::-1]                       # top y = n-1
        ax.axvline(0.1, color="grey", ls="--", lw=1)
        for y, c in zip(ys, cols):
            ax.scatter(abs(raw[c]), y, marker="o", color=RED, s=26, zorder=3)
            ax.scatter(abs(ow_s[c]), y, marker="s", color=BLUE, s=22, zorder=3)
            ax.scatter(abs(ipw_s[c]), y, marker="^", color=GREY, s=22, zorder=3)
        ax.set_yticks(ys)
        ax.set_yticklabels([LABELS.get(c, c) for c in cols], fontsize=8)
        ax.set_xlabel("Absolute standardized mean difference", fontsize=9)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].scatter([], [], marker="o", color=RED, label="Unweighted")
    axes[0].scatter([], [], marker="s", color=BLUE, label="Overlap-weighted")
    axes[0].scatter([], [], marker="^", color=GREY, label="IPTW")
    axes[0].legend(fontsize=8, frameon=False, loc="lower right")
    fig.suptitle("Covariate balance before and after weighting", fontsize=12, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT, "fig5_love_plot.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Figure 6: threshold dose-response gradient ----
def fig6():
    ths = [(24, "cohort_24h.csv"), (48, "cohort.csv"), (72, "cohort_72h.csv")]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4))
    for ax, comp, title in [
        (axes[0], "A", "A: EEN vs late EN"),
        (axes[1], "B", "B: EEN vs no-EEN"),
    ]:
        xs, ors, los, his = [], [], [], []
        for th, fn in ths:
            d = est.load_cohort(fn)
            if comp == "A":
                d = d[d["tf_any"] == 1].reset_index(drop=True)
            rows, *_ = est.run_comparison(d, f"{th}h {comp}")
            by = {(m["outcome"], m["method"]): m for m in rows}
            m = by[("infection_composite", "OW")]
            xs.append(th); ors.append(m["or_"]); los.append(m["or_lo"]); his.append(m["or_hi"])
        xs = np.array(xs, float); ors = np.array(ors); los = np.array(los); his = np.array(his)
        ax.errorbar(xs, ors, yerr=[ors - los, his - ors], fmt="-o", color=BLUE,
                    capsize=4, lw=1.6, markersize=6)
        ax.axhline(1.0, color="grey", ls="--", lw=1)
        ax.set_yscale("log")
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{int(x)} h" for x in xs])
        ax.set_xlabel("Feeding-time threshold (EEN definition)")
        ax.set_ylabel("Overlap-weighted OR (95% CI)")
        ax.set_ylim(0.2, 3.2)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Dose–response gradient across feeding-time thresholds (infection composite)",
                 fontsize=12, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(OUT, "fig6_threshold_gradient.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Figure 7: estimand schematic ----
def fig7():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis("off")

    def box(x, y, w, h, text, fc="#eef3fb", fs=9, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                    fc=fc, ec="#1f4e79", lw=1.3))
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs, weight=weight)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=14, lw=1.3, color="#1f4e79"))

    def span(x1, x2, y, label, color):
        ax.plot([x1, x2], [y, y], color=color, lw=1.8)
        ax.plot([x1, x1], [y - 0.08, y + 0.08], color=color, lw=1.8)
        ax.plot([x2, x2], [y - 0.08, y + 0.08], color=color, lw=1.8)
        ax.text((x1 + x2) / 2, y - 0.18, label, ha="center", va="top", fontsize=9.5,
                color=color, weight="bold")

    box(2.0, 5.9, 6.0, 0.85, "Landmarked cohort (ICU LOS ≥ 48 h, alive at 48 h)\nn = 1658",
        fc="#dbe7f5", fs=10, weight="bold")
    box(0.2, 4.0, 2.7, 0.9, "EEN\nfeed ≤ 48 h\nn = 192", fc="#e2f0d9")
    box(3.65, 4.0, 2.7, 0.9, "Late EN\nfeed > 48 h\nn = 346", fc="#fff2cc")
    box(7.1, 4.0, 2.7, 0.9, "Never fed\nn = 1120", fc="#f2f2f2")
    arrow(5.0, 5.85, 1.55, 4.95)
    arrow(5.0, 5.85, 5.0, 4.95)
    arrow(5.0, 5.85, 8.45, 4.95)

    span(0.2, 6.35, 3.35, "Comparison A — timing effect:  EEN vs late EN (eventually-fed, n = 538)",
         BLUE)
    span(0.2, 9.8, 2.65, "Comparison B — policy effect:  EEN vs no-EEN (full landmarked cohort, n = 1658)",
         RED)
    ax.text(5.0, 1.0, "Comparison A restricts to the eventually-fed subset;\n"
            "Comparison B uses the full landmarked cohort.",
            ha="center", va="center", fontsize=9, style="italic", color="#404040")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig7_estimand.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Supp Fig S1: first-feeding-time distribution ----
def supp1():
    d = est.load_cohort("cohort.csv")
    fed = d[d["tf_any"] == 1].copy()
    hrs = pd.to_numeric(fed["first_tf_hours"], errors="coerce")
    een = fed["een48"] == 1
    late = ~een
    cap = 240.0
    beyond = int((hrs[late] > cap).sum())
    bins = np.arange(0, cap + 12, 12)
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.hist(np.clip(hrs[een], 0, cap), bins=bins, color=BLUE, alpha=0.6,
            label=f"EEN (≤ 48 h, n = {int(een.sum())})")
    ax.hist(np.clip(hrs[late], 0, cap), bins=bins, color=RED, alpha=0.6,
            label=f"Late (> 48 h, n = {int(late.sum())})")
    for th, lab in [(24, "24 h"), (48, "48 h"), (72, "72 h")]:
        ax.axvline(th, color="grey", ls="--", lw=1)
        ax.text(th, ax.get_ylim()[1] * 0.96, lab, rotation=90, va="top", ha="right", fontsize=8)
    if beyond:
        ax.text(0.98, 0.95, f"{beyond} late feeds > 240 h truncated", transform=ax.transAxes,
                ha="right", va="top", fontsize=8, color=GREY)
    ax.set_xlabel("First enteral-feed time since ICU admission (h)")
    ax.set_ylabel("Number of patients")
    ax.legend(fontsize=9, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Timing of first enteral feed (eventually-fed, n = 538)", fontsize=11, weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "supp1_feeding_time.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Supp Fig S2: never-fed dissection ----
def supp2():
    cats = ["Died", "Therapeutic NPO\n(ileus)", "Oral recovery"]
    counts = [463, 146, 511]
    pcts = [41.3, 13.0, 45.6]
    fig, ax = plt.subplots(figsize=(6, 4.2))
    bars = ax.bar(cats, counts, color=[RED, "#fff2cc", "#7fbf7f"], width=0.62)
    for bar, n, p in zip(bars, counts, pcts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 8,
                f"n = {n} ({p}%)", ha="center", fontsize=10)
    ax.set_ylabel("Number of patients")
    ax.set_ylim(0, 560)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Never-fed group dissection (n = 1120)", fontsize=11, weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "supp2_never_fed.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Supp Fig S3: primary-composite site decomposition ----
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


def supp3():
    abx_clause = " OR ".join(f"LOWER(r.drug) LIKE '%{a}%'" for a in ABX)
    con = duckdb.connect()
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE cohort AS
    SELECT stay_id, subject_id, hadm_id, intime, een48, tf_any
    FROM read_csv_auto('{HERE}/cohort.csv')
    """)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE pos AS
    SELECT c.stay_id, c.hadm_id, c.een48, c.tf_any, m.charttime,
           CASE WHEN UPPER(m.spec_type_desc) LIKE 'BLOOD CULTURE%' THEN 'blood'
                WHEN UPPER(m.spec_type_desc) LIKE '%PERITONEAL%' OR UPPER(m.spec_type_desc) LIKE '%ABDOMINAL%'
                  OR UPPER(m.spec_type_desc) LIKE '%ASCITES%' OR UPPER(m.spec_type_desc) LIKE '%BILE%'
                  OR UPPER(m.spec_type_desc) LIKE '%ABSCESS%' OR UPPER(m.spec_type_desc) LIKE '%DRAIN%' THEN 'abdominal'
                WHEN UPPER(m.spec_type_desc) LIKE '%TRACHEAL%' OR UPPER(m.spec_type_desc) LIKE '%SPUTUM%'
                  OR UPPER(m.spec_type_desc) LIKE '%BRONCH%' OR UPPER(m.spec_type_desc) LIKE '%BAL%'
                  OR UPPER(m.spec_type_desc) LIKE '%RESPIRATORY%' OR UPPER(m.spec_type_desc) LIKE '%LUNG%' THEN 'respiratory'
                WHEN UPPER(m.spec_type_desc) LIKE '%WOUND%' OR UPPER(m.spec_type_desc) LIKE '%SWAB%'
                  OR UPPER(m.spec_type_desc) LIKE '%TISSUE%' OR UPPER(m.spec_type_desc) LIKE '%SKIN%' THEN 'wound'
                END AS site
    FROM cohort c
    JOIN read_csv_auto('{M}/hosp/microbiologyevents.csv.gz') m
      ON c.subject_id = m.subject_id AND c.hadm_id = m.hadm_id
    WHERE m.charttime > c.intime + INTERVAL '48' HOUR
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
    SELECT DISTINCT pe.stay_id, pe.een48, pe.tf_any, pe.site
    FROM pos pe
    JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON pe.hadm_id = r.hadm_id
    WHERE r.starttime BETWEEN pe.charttime - INTERVAL '1' DAY AND pe.charttime + INTERVAL '2' DAY
      AND ({abx_clause})
    """)
    tab = con.execute("""
    SELECT site,
           SUM(CASE WHEN een48 = 1 THEN 1 ELSE 0 END) AS een,
           SUM(CASE WHEN een48 = 0 AND tf_any = 1 THEN 1 ELSE 0 END) AS late,
           SUM(CASE WHEN een48 = 0 THEN 1 ELSE 0 END) AS no_een
    FROM (SELECT DISTINCT stay_id, site, een48, tf_any FROM treated)
    WHERE site IS NOT NULL
    GROUP BY site
    """).fetchdf()
    con.close()

    order = ["blood", "abdominal", "respiratory", "wound"]
    tab = tab.set_index("site").reindex(order).fillna(0).astype(int)
    nice = {"blood": "Blood", "abdominal": "Abdominal", "respiratory": "Respiratory", "wound": "Wound"}
    x = np.arange(4); w = 0.38
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    for ax, arm, lab, color, title in [
        (axes[0], "late", "Late EN", "#c00000", "A: EEN vs late EN"),
        (axes[1], "no_een", "No EEN", "#c00000", "B: EEN vs no-EEN"),
    ]:
        ax.bar(x - w/2, tab["een"], w, color=BLUE, label="EEN")
        ax.bar(x + w/2, tab[arm], w, color=color, label=lab)
        ax.set_xticks(x)
        ax.set_xticklabels([nice[s] for s in tab.index], fontsize=9)
        ax.set_ylabel("Patients with ≥ 1 treated positive culture")
        ax.set_title(title, fontsize=11, weight="bold")
        ax.legend(fontsize=8, frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Infection-composite components by culture site", fontsize=12, weight="bold")
    fig.text(0.5, -0.02, "A patient may contribute to more than one site, so columns do not sum to the composite count.",
             ha="center", fontsize=8, style="italic", color="#404040")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    fig.savefig(os.path.join(OUT, "supp3_composite_sites.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def _aj_cif(t, cause, horizon=28.0):
    """Aalen–Johansen CIF of cause 1 with cause 2 as the competing event."""
    t = np.asarray(t, float); cause = np.asarray(cause, int)
    order = np.argsort(t); t = t[order]; cause = cause[order]
    n = len(t); S = 1.0; cif = 0.0; at_risk = n; i = 0
    times = [0.0]; cifs = [0.0]
    while i < n:
        s = t[i]
        if s > horizon:
            break
        j = i
        while j < n and t[j] == s:
            j += 1
        d1 = int(np.sum(cause[i:j] == 1)); d2 = int(np.sum(cause[i:j] == 2))
        d_tot = d1 + d2
        if d_tot > 0:
            cif += S * d1 / at_risk
            S *= (1 - d_tot / at_risk)
            times.append(s); cifs.append(cif)
        at_risk -= (j - i)
        i = j
    times.append(horizon); cifs.append(cif)
    return np.array(times), np.array(cifs)


def _infection_first_times():
    """First treated-positive-composite-culture time (days from intime) per stay."""
    abx_clause = " OR ".join(f"LOWER(r.drug) LIKE '%{a}%'" for a in ABX)
    con = duckdb.connect()
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE cohort AS
    SELECT stay_id, subject_id, hadm_id, intime FROM read_csv_auto('{HERE}/cohort.csv')
    """)
    con.execute(f"""
    CREATE OR REPLACE TEMP TABLE pos AS
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
                END AS site
    FROM cohort c
    JOIN read_csv_auto('{M}/hosp/microbiologyevents.csv.gz') m
      ON c.subject_id = m.subject_id AND c.hadm_id = m.hadm_id
    WHERE m.charttime > c.intime + INTERVAL '48' HOUR
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
    df = con.execute(f"""
    SELECT c.stay_id, MIN((EPOCH(p.charttime) - EPOCH(c.intime)) / 86400.0) AS inf_days
    FROM cohort c
    JOIN pos p ON c.stay_id = p.stay_id
    JOIN read_csv_auto('{M}/hosp/prescriptions.csv.gz') r ON p.hadm_id = r.hadm_id
    WHERE p.site IS NOT NULL
      AND r.starttime BETWEEN p.charttime - INTERVAL '1' DAY AND p.charttime + INTERVAL '2' DAY
      AND ({abx_clause})
    GROUP BY c.stay_id, c.intime
    """).fetchdf()
    con.close()
    return df


def supp4_infection_cif():
    inf = _infection_first_times()
    d = est.load_cohort("cohort.csv").merge(
        pd.read_csv(os.path.join(HERE, "tte.csv")), on="stay_id", how="left"
    ).merge(inf, on="stay_id", how="left")
    d["inf_days"] = pd.to_numeric(d["inf_days"], errors="coerce")

    fig, ax = plt.subplots(figsize=(7, 5.5))
    cif28 = {}
    for grp, color in [("EEN", BLUE), ("late", RED), ("never", GREY)]:
        sub = d[d["grp"] == grp]
        inf_d = sub["inf_days"].to_numpy(float)
        death = sub["death_days"].to_numpy(float)
        disch = sub["disch_days"].to_numpy(float)
        inf_d = np.where(np.isnan(inf_d), np.inf, inf_d)
        death = np.where(np.isnan(death), np.inf, death)
        disch = np.where(np.isnan(disch), np.inf, disch)
        comp = np.minimum(death, disch)
        t = np.full(len(sub), 28.0)
        cause = np.zeros(len(sub), int)
        inf_first = (inf_d <= 28) & (inf_d < comp)
        t[inf_first] = inf_d[inf_first]; cause[inf_first] = 1
        comp_first = (~inf_first) & (comp <= 28)
        t[comp_first] = comp[comp_first]; cause[comp_first] = 2
        ts, cif = _aj_cif(t, cause, 28.0)
        cif28[grp] = cif[-1]
        ax.step(ts, cif, where="post", color=color, lw=2,
                label=f"{grp} (n={len(sub)}; 28-d CIF {cif[-1]*100:.1f}%)")
    ax.set_xlabel("Days since ICU admission")
    ax.set_ylabel("Cumulative incidence of treated infection")
    ax.set_xlim(0, 28); ax.set_ylim(0, None)
    ax.legend(fontsize=9, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Treated-infection composite with death/discharge as competing risks",
                 fontsize=11, weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "supp4_infection_cif.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  supp4 28-day infection CIF (EEN/late/never):",
          " / ".join(f"{g}={cif28[g]*100:.1f}%" for g in ("EEN", "late", "never")))


if __name__ == "__main__":
    fig4()
    fig5()
    fig6()
    fig7()
    supp1()
    supp2()
    supp3()
    supp4_infection_cif()
    print("wrote reviewer figures to", OUT)
    for f in sorted(os.listdir(OUT)):
        print("  ", f)
