# -*- coding: utf-8 -*-
"""Graphical abstract for Critical Care (920 x 300 px).

Three-panel layout: design -> two estimands -> key result.
Output: ../graphical_abstract.png (exactly 920 x 300 px).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

W, H = 920, 300  # pixels
DPI = 100
fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

NAVY = "#12395b"
BLUE = "#2a6f97"
LIGHT = "#eef4f8"
ACCENT = "#c0392b"
GREEN = "#1e7d5a"
GREY = "#444444"

# ---- Title band ----
ax.add_patch(plt.Rectangle((0, H - 40), W, 40, color=NAVY, zorder=1))
ax.text(W / 2, H - 20,
        "Early versus Late Enteral Nutrition after Major Abdominal Surgery in the ICU",
        ha="center", va="center", color="white", fontsize=13.5, fontweight="bold", zorder=2)


def panel(x0, x1, y0=16, y1=H - 54):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                                boxstyle="round,pad=0,rounding_size=10",
                                linewidth=1.4, edgecolor=BLUE, facecolor=LIGHT, zorder=1))


def chip(x, y, text, color):
    ax.text(x, y, text, ha="left", va="center", color="white", fontsize=9.5,
            fontweight="bold", bbox=dict(boxstyle="round,pad=0.35",
                                          fc=color, ec="none"), zorder=3)


# ---- Panel 1: design ----
panel(8, 298)
chip(20, 232, "DESIGN", NAVY)
ax.text(20, 202, "MIMIC-IV  ·  target-trial emulation",
        ha="left", va="center", fontsize=11.5, fontweight="bold", color=NAVY, zorder=3)
ax.text(20, 172, "Major abdominal surgery,\nICU length of stay ≥ 48 h",
        ha="left", va="center", fontsize=10.5, color=GREY, zorder=3, linespacing=1.5)
ax.text(20, 128, "n = 1,658", ha="left", va="center", fontsize=16,
        fontweight="bold", color=ACCENT, zorder=3)
ax.text(20, 96, "48-h landmarked cohort\n(192 EEN · 346 late · 1,120 never)",
        ha="left", va="center", fontsize=9.5, color=GREY, zorder=3, linespacing=1.5)
ax.text(20, 44, "Time zero = ICU admission", ha="left", va="center",
        fontsize=9.5, style="italic", color=GREY, zorder=3)

# ---- Panel 2: two estimands ----
panel(314, 604)
chip(326, 232, "TWO ESTIMANDS", BLUE)
ax.text(326, 196, "A  ·  Timing  (eventually fed, n = 538)",
        ha="left", va="center", fontsize=11.5, fontweight="bold", color=BLUE, zorder=3)
ax.text(326, 168, "EEN ≤ 48 h   vs   late EN > 48 h",
        ha="left", va="center", fontsize=10.5, color=GREY, zorder=3)
ax.plot([326, 588], [140, 140], color=BLUE, lw=1, alpha=0.4, zorder=3)
ax.text(326, 112, "B  ·  Policy  (full cohort, n = 1,658)",
        ha="left", va="center", fontsize=11.5, fontweight="bold", color=BLUE, zorder=3)
ax.text(326, 84, "EEN   vs   no early EN (usual care)",
        ha="left", va="center", fontsize=10.5, color=GREY, zorder=3)
ax.text(326, 44, "Separating timing from policy avoids a\nspurious reversal of effect direction",
        ha="left", va="center", fontsize=9.5, style="italic", color=GREY, zorder=3, linespacing=1.5)

# ---- Panel 3: key result ----
panel(620, 912)
chip(632, 232, "KEY RESULT", GREEN)
ax.text(632, 196, "Earlier feeding → fewer\nantibiotic-treated infections",
        ha="left", va="center", fontsize=11.5, fontweight="bold", color=GREEN, zorder=3, linespacing=1.4)
ax.text(632, 140, "OR 0.60   (95% CI 0.39–0.93)", ha="left", va="center",
        fontsize=15.5, fontweight="bold", color=NAVY, zorder=3)
ax.text(632, 108, "overlap-weighted · comparison A", ha="left", va="center",
        fontsize=9.5, color=GREY, zorder=3)
ax.text(632, 62, "Full-cohort “harm” signal =\nnever-fed confounding, not causal",
        ha="left", va="center", fontsize=10, color=ACCENT, fontweight="bold",
        zorder=3, linespacing=1.4)

out = r"C:\Users\jiang\Desktop\Enteral Nutrition\graphical_abstract.png"
fig.savefig(out, dpi=DPI, facecolor="white")
plt.close(fig)

# Enforce exact dimensions and an opaque RGB (no alpha) file.
from PIL import Image
im = Image.open(out).convert("RGB").resize((W, H), Image.LANCZOS)
im.save(out)
print(f"Saved {out} at {im.size[0]}x{im.size[1]} px ({im.mode})")
