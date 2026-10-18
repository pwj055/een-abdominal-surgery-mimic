# -*- coding: utf-8 -*-
"""
16_replication_forest.py — replication forest plot (MIMIC-IV vs MIMIC-III).

Side-by-side replication of the primary finding (treated infection composite)
and of the negative-control outcome (treated UTI), Comparison A (EEN vs late),
crude and overlap-weighted. Numbers are transcribed from results.md /
negative_control.md (MIMIC-IV) and mimic3_replication.md (MIMIC-III).

Output: analysis/figures/fig8_replication_forest.png (300 dpi).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)

BLUE = "#1f4e79"      # MIMIC-IV
RED = "#c0392b"       # MIMIC-III

# (label, OR, lo, hi, db, method)  db: 'IV'|'III'; method: 'crude'|'ow'
PANELS = {
    "Infection composite (primary)": [
        ("MIMIC-IV · Crude", 0.40, 0.27, 0.58, "IV", "crude"),
        ("MIMIC-IV · Overlap-weighted", 0.60, 0.39, 0.93, "IV", "ow"),
        ("MIMIC-III · Crude", 0.58, 0.42, 0.79, "III", "crude"),
        ("MIMIC-III · Overlap-weighted", 0.58, 0.42, 0.82, "III", "ow"),
    ],
    "Treated UTI (negative control)": [
        ("MIMIC-IV · Crude", 0.56, 0.33, 0.94, "IV", "crude"),
        ("MIMIC-IV · Overlap-weighted", 0.88, 0.49, 1.60, "IV", "ow"),
        ("MIMIC-III · Crude", 0.63, 0.43, 0.91, "III", "crude"),
        ("MIMIC-III · Overlap-weighted", 0.67, 0.45, 1.00, "III", "ow"),
    ],
}

fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)

for ax, (title, rows) in zip(axes, PANELS.items()):
    ys = np.arange(len(rows))[::-1]
    for y, (lab, orr, lo, hi, db, method) in zip(ys, rows):
        color = BLUE if db == "IV" else RED
        mfc = color if method == "ow" else "white"
        ax.plot([orr], [y], "o", color=color, markerfacecolor=mfc,
                markeredgecolor=color, markeredgewidth=1.6, markersize=7, zorder=3)
        ax.plot([lo, hi], [y, y], "-", color=color, lw=1.6, zorder=2)
        ax.text(3.05, y, f"{orr:.2f}  ({lo:.2f}–{hi:.2f})", va="center",
                ha="right", fontsize=8.5, color="#333333")
    ax.axvline(1.0, color="grey", ls="--", lw=1)
    ax.set_xscale("log")
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.set_title(title, fontsize=11, weight="bold")
    ax.set_xlabel("Odds ratio (95% CI), EEN vs late EN", fontsize=9)
    ax.set_xlim(0.22, 3.6)
    ax.grid(axis="y", alpha=0.2)
    ax.tick_params(axis="x", labelsize=8)

# legend
from matplotlib.lines import Line2D
handles = [
    Line2D([], [], marker="o", ls="", color=BLUE, markersize=7, label="MIMIC-IV"),
    Line2D([], [], marker="o", ls="", color=RED, markersize=7, label="MIMIC-III"),
    Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor="grey",
           markersize=7, label="Crude"),
    Line2D([], [], marker="o", ls="", markerfacecolor="grey", markeredgecolor="grey",
           markersize=7, label="Overlap-weighted"),
]
fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9)

fig.suptitle("Replication of the primary finding and its negative control (same-center, earlier era)",
             fontsize=12, weight="bold")
fig.tight_layout(rect=[0, 0.06, 1, 0.95])
fig.savefig(os.path.join(OUT, "fig8_replication_forest.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("wrote", os.path.join(OUT, "fig8_replication_forest.png"))
