# -*- coding: utf-8 -*-
"""
09_figures.py — render manuscript figures.

  Fig 1  flow diagram (cohort assembly + never-fed dissection)
  Fig 2  forest plot of primary outcome (infection composite, OW OR) across
         comparisons and prespecified sensitivity analyses
  Fig 3  Aalen-Johansen cumulative incidence of death by feeding group
         (discharge = competing risk)

Outputs PNGs (300 dpi) to analysis/figures/.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

# ---- Figure 1: flow diagram ----
def fig1():
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 9); ax.axis("off")

    def box(x, y, w, h, text, fc="#eef3fb", fs=10, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                    fc=fc, ec="#1f4e79", lw=1.4))
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs,
                weight=weight, wrap=True)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=16, lw=1.3, color="#1f4e79"))

    box(2.4, 7.8, 5.2, 0.9, "Eligible\nMajor abdominal surgery, first surgical ICU stay\nn = 3246", fc="#dbe7f5", fs=10, weight="bold")

    box(0.2, 5.9, 4.3, 0.9, "Excluded — died within 48 h\nn = 117 (3.6%)", fc="#fdecea")
    box(5.5, 5.9, 4.3, 0.9, "Excluded — ICU discharge within 48 h (alive)\nn = 1471 (45.3%)", fc="#fdecea")
    arrow(5.0, 7.75, 2.3, 6.85)
    arrow(5.0, 7.75, 7.7, 6.85)

    box(2.4, 4.6, 5.2, 0.9, "Landmarked cohort (ICU LOS ≥ 48 h)\nn = 1658 (51.1%)", fc="#dbe7f5", fs=10, weight="bold")
    arrow(2.3, 5.85, 3.5, 5.55)
    arrow(7.7, 5.85, 6.5, 5.55)

    box(0.1, 2.6, 3.0, 0.9, "EEN\nfeed ≤ 48 h\nn = 192 (11.6%)", fc="#e2f0d9")
    box(3.5, 2.6, 3.0, 0.9, "Late EN\nfeed > 48 h\nn = 346 (20.9%)", fc="#fff2cc")
    box(6.9, 2.6, 3.0, 0.9, "Never fed\nn = 1120 (67.6%)", fc="#f2f2f2")
    arrow(3.6, 4.55, 1.6, 3.55)
    arrow(5.0, 4.55, 5.0, 3.55)
    arrow(6.4, 4.55, 8.4, 3.55)

    box(5.7, 0.5, 4.0, 1.5,
        "Never-fed dissection\ndied 127 (11.3%)\ntherapeutic NPO 211 (18.8%)\noral recovery 782 (69.8%)",
        fc="#ffffff", fs=9)
    arrow(8.4, 2.55, 7.7, 2.05)

    fig.savefig(os.path.join(OUT, "fig1_flow.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Figure 2: forest plot ----
def fig2():
    # (label, OR, lo, hi)
    A = [
        ("Main (48 h)", 0.60, 0.39, 0.93),
        ("Threshold 24 h", 0.88, 0.53, 1.47),
        ("Threshold 72 h", 0.49, 0.32, 0.74),
        ("Feeding: any record", 0.61, 0.39, 0.94),
        ("Feeding: rate ≥ 20", 0.58, 0.37, 0.89),
        ("Feeding: ONS-inclusive", 0.60, 0.39, 0.93),
        ("ITT (feeding order)", 0.64, 0.44, 0.93),
        ("Same-day surgery", 0.70, 0.37, 1.31),
        ("No contaminant exclusion", 0.60, 0.39, 0.92),
        ("Strict-treated ≥ 3 days", 0.75, 0.46, 1.20),
        ("Strict-treated ≥ 5 days", 0.66, 0.38, 1.16),
        ("PS-trim 0.1–0.9", 0.64, 0.40, 1.00),
    ]
    B = [
        ("Main (48 h)", 1.34, 0.93, 1.95),
        ("Threshold 24 h", 1.76, 1.11, 2.78),
        ("Threshold 72 h", 1.04, 0.73, 1.49),
        ("Feeding: any record", 1.38, 0.96, 2.00),
        ("Feeding: rate ≥ 20", 1.30, 0.89, 1.89),
        ("Feeding: ONS-inclusive", 1.34, 0.93, 1.95),
        ("ITT (feeding order)", 1.56, 1.11, 2.18),
        ("Same-day surgery", 1.37, 0.80, 2.32),
        ("No contaminant exclusion", 1.31, 0.91, 1.89),
        ("Strict-treated ≥ 3 days", 1.36, 0.89, 2.08),
        ("Strict-treated ≥ 5 days", 1.29, 0.78, 2.15),
        ("PS-trim 0.1–0.9", 1.01, 0.60, 1.69),
    ]

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 7.5), sharey=True)

    def draw(ax, rows, title):
        ys = np.arange(len(rows))[::-1]
        for y, (lab, orr, lo, hi) in zip(ys, rows):
            ax.plot([orr], [y], "o", color="#1f4e79", markersize=6, zorder=3)
            ax.plot([lo, hi], [y, y], "-", color="#1f4e79", lw=1.6, zorder=2)
        ax.axvline(1.0, color="grey", ls="--", lw=1)
        ax.set_xscale("log")
        ax.set_yticks(ys)
        ax.set_yticklabels([r[0] for r in rows], fontsize=9)
        ax.set_title(title, fontsize=11, weight="bold")
        ax.set_xlabel("Overlap-weighted odds ratio (95% CI)", fontsize=9)
        ax.set_xlim(0.2, 3.2)
        ax.grid(axis="y", alpha=0.2)
        ax.tick_params(axis="x", labelsize=8)

    draw(axA, A, "A: EEN vs late EN (eventually-fed)")
    draw(axB, B, "B: EEN vs no-EEN (full cohort)")
    fig.suptitle("Primary outcome — treated infection composite", fontsize=12, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(OUT, "fig2_forest.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---- Figure 3: Aalen-Johansen CIF of death ----
def aj_curve(t, cause, horizon=28.0):
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


def fig3():
    import importlib.util
    spec = importlib.util.spec_from_file_location("est", os.path.join(HERE, "02_weighting.py"))
    est = importlib.util.module_from_spec(spec); spec.loader.exec_module(est)
    d = est.load_cohort("cohort.csv").merge(pd.read_csv(os.path.join(HERE, "tte.csv")), on="stay_id", how="left")
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for grp, color in [("EEN", "#1f4e79"), ("late", "#c00000"), ("never", "#7f7f7f")]:
        sub = d[d["grp"] == grp]
        died = sub["deathtime"].notna().to_numpy() & (sub["death_days"].to_numpy() <= 28)
        disch = sub["disch_days"].to_numpy()
        cause = np.where(sub["deathtime"].notna().to_numpy(), 1, 2).astype(int)
        t = np.where(sub["deathtime"].notna().to_numpy(), sub["death_days"].to_numpy(), disch)
        t = np.clip(np.nan_to_num(t, nan=28.0), 0, 28.0)
        cause[(cause == 1) & (sub["death_days"].to_numpy() > 28)] = 0
        cause[(cause == 2) & (disch > 28)] = 0
        ts, cif = aj_curve(t, cause)
        ax.step(ts, cif, where="post", color=color, lw=2, label=f"{grp} (n={len(sub)})")
    ax.set_xlabel("Days since ICU admission", fontsize=10)
    ax.set_ylabel("Cumulative incidence of death", fontsize=10)
    ax.set_xlim(0, 28); ax.set_ylim(0, None)
    ax.legend(fontsize=9, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Death with discharge as competing risk (Aalen–Johansen)", fontsize=11, weight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_cif.png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    print("wrote figures to", OUT)
    for f in sorted(os.listdir(OUT)):
        print("  ", f)
