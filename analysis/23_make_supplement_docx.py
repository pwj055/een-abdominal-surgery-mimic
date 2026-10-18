# -*- coding: utf-8 -*-
"""Build the combined Supplementary Material .docx (Tables S1-S15 + Figures S1-S4, Figure 8).

Reads the analysis outputs (markdown + CSV) and embeds the supplementary figures,
producing one uploadable document for the Critical Care submission.
Output: ../Supplementary_Material.docx
"""
import os
import re
import csv

import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
OUT = os.path.abspath(os.path.join(HERE, "..", "Supplementary_Material.docx"))

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(11)
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.line_spacing = 1.0
_rpr = normal.element.get_or_add_rPr()
_rfonts = _rpr.get_or_add_rFonts()
_rfonts.set(qn("w:eastAsia"), "SimSun")


def _style_heading(name, size, bold, italic=False):
    st = doc.styles[name]
    st.font.name = "Times New Roman"
    st.font.size = Pt(size)
    st.font.bold = bold
    st.font.italic = italic
    st.font.color.rgb = RGBColor(0, 0, 0)
    rpr = st.element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), "SimSun")


_style_heading("Heading 1", 14, True)
_style_heading("Heading 2", 12, True)
_style_heading("Heading 3", 11, True, italic=True)


def add_rich(p, text):
    for part in re.split(r"(\*\*.*?\*\*|\*[^*]+?\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            r = p.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            r = p.add_run(part[1:-1]); r.font.name = "Consolas"
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            r = p.add_run(part[1:-1]); r.italic = True
        else:
            p.add_run(part)
    return p


def para(text, align=None, space_after=4, size=None, bold=False):
    p = doc.add_paragraph()
    if align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(space_after)
    add_rich(p, text)
    if size:
        for r in p.runs:
            r.font.size = Pt(size)
    if bold:
        for r in p.runs:
            r.bold = True
    return p


def h1(text):
    p = doc.add_heading(level=1)
    add_rich(p, text)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    return p


def h2(text):
    p = doc.add_heading(level=2)
    add_rich(p, text)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    return p


def h3(text):
    p = doc.add_heading(level=3)
    add_rich(p, text)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    return p


def add_table(headers, rows, font_size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, htxt in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(htxt); r.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i in range(len(headers)):
            val = row[i] if i < len(row) else ""
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            add_rich(p, val)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
    for r in t.rows:
        for c in r.cells:
            for p in c.paragraphs:
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.space_before = Pt(1)
                for run in p.runs:
                    run.font.size = Pt(font_size)
                    run.font.name = "Times New Roman"
    return t


def add_figure(caption, fname, width=6.2):
    para(caption, align="justify", space_after=2)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run()
    run.add_picture(os.path.join(FIG, fname), width=Inches(width))


def is_sep(line):
    return set(line.replace("|", "").replace("-", "").replace(":", "").replace(" ", "")) == set()


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render_md(path):
    """Render a markdown file into the docx (headings, paragraphs, tables)."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("#"):
            level = len(s) - len(s.lstrip("#"))
            text = s.lstrip("#").strip()
            (h1 if level == 1 else h2 if level == 2 else h3)(text)
            i += 1
        elif s.startswith("|"):
            headers = split_row(s)
            i += 1
            if i < n and lines[i].strip().startswith("|") and is_sep(lines[i]):
                i += 1
            rows = []
            while i < n:
                ls = lines[i].strip()
                if ls.startswith("|"):
                    rows.append(split_row(ls)); i += 1
                elif ls == "":
                    j = i
                    while j < n and lines[j].strip() == "":
                        j += 1
                    if j < n and lines[j].strip().startswith("|"):
                        i = j
                    else:
                        break
                else:
                    break
            add_table(headers, rows)
            para("", space_after=2)
        else:
            para(s, align="justify")
            i += 1


# ============================================================================
# Title
# ============================================================================
para("Supplementary Material", align="center", size=16, bold=True, space_after=2)
para("Early versus Late Enteral Nutrition and Infectious Complications after Major Abdominal "
     "Surgery in the Intensive Care Unit: A Target Trial Emulation Using MIMIC-IV",
     align="center", space_after=14)

# ============================================================================
# Table S1 — target-trial spec
# ============================================================================
h1("Table S1. Full target-trial emulation specification")
add_table(
    ["Target-trial component", "Emulation"],
    [
        ["Eligibility", "Adults with major abdominal surgery admitted to a surgical ICU, with ICU length of stay ≥48 h"],
        ["Treatment strategies", "(1) start tube EN within 48 h of ICU admission; (2) defer tube EN beyond 48 h"],
        ["Time zero", "ICU admission"],
        ["Assignment", "Randomization, emulated by adjustment for baseline covariates (overlap weighting)"],
        ["Follow-up", "From the 48-h landmark to 28 days after ICU admission, hospital discharge, or death (whichever occurred first); outcomes were left-truncated at 48 h"],
        ["Primary outcome", "In-hospital treated infection composite after the 48-h landmark and within 28 days of ICU admission"],
        ["Causal contrasts", "(A) timing effect among the eventually-fed; (B) policy effect of an early-feeding strategy"],
    ],
)

# ============================================================================
# Table S2 — enteral-nutrition itemids
# ============================================================================
h1("Table S2. The 112 enteral-nutrition itemids")
items = pd.read_csv(os.path.join(HERE, "feeding_itemids.csv"))
add_table(
    ["itemid", "label", "category"],
    [[str(r["itemid"]), str(r["label"]), str(r["category"])] for _, r in items.iterrows()],
    font_size=8,
)
para(f"The `Nutrition - Enteral` category ({len(items)} items) was used to identify enteral "
     "feeding, avoiding keyword matching that would misclassify parenteral-nutrition items.",
     align="justify", space_after=8)

# ============================================================================
# Table S3 — covariate balance
# ============================================================================
h1("Table S3. Covariate balance before and after weighting")
t1 = pd.read_csv(os.path.join(HERE, "table1.csv"))
s3_rows = []
for _, r in t1.iterrows():
    s3_rows.append([str(r["Characteristic"]), str(r["SMD (EEN vs late)"]),
                    str(r["SMD (EEN vs no-EEN)"])])
add_table(["Covariate", "Unweighted SMD (EEN vs late)", "Unweighted SMD (EEN vs no-EEN)"], s3_rows)
para("Unweighted standardized mean differences (SMD) are from Table 1. After overlap weighting "
     "the maximum |weighted SMD| was < 0.01 in both comparisons (comparison A: raw max 0.81 → "
     "< 0.01; comparison B: raw max 1.02 → < 0.01), and after stabilized/truncated IPTW the "
     "maximum |weighted SMD| was 0.087 in comparison A. Per-covariate after-weighting balance is "
     "shown graphically in Figure 5 (Love plot).", align="justify", space_after=8)

# ============================================================================
# Table S4 — complete estimates
# ============================================================================
h1("Table S4. Complete estimates for all outcomes × methods × sensitivity analyses")
est = pd.read_csv(os.path.join(HERE, "estimates.csv"))
est = est.sort_values(["outcome_label", "comparison", "method"]).reset_index(drop=True)


def ci(row, lo, hi):
    def _f(x):
        return f"{x:.2f}"
    return f"{_f(row[lo])} ({_f(row[hi])})"


s4_rows = []
for _, r in est.iterrows():
    s4_rows.append([
        str(r["outcome_label"]),
        str(r["comparison"]),
        str(r["method"]),
        f"{int(r['ev_t'])}/{int(r['n_t'])} vs {int(r['ev_c'])}/{int(r['n_c'])}",
        ci(r, "or_", "or_hi"),
        ci(r, "rr", "rr_hi"),
        ci(r, "rd", "rd_hi"),
        f"{r['p_or']:.3f}",
    ])
add_table(
    ["Outcome", "Comparison", "Method", "Events (EEN/control)",
     "OR (95% CI)", "RR (95% CI)", "RD (95% CI)", "p (OR)"],
    s4_rows, font_size=8,
)
para("OR = odds ratio; RR = risk ratio; RD = risk difference. Methods: Crude, OW (overlap "
     "weighting, primary), IPTW (stabilized/truncated inverse-probability-of-treatment "
     "weighting), PSM (1:1 propensity-score matching), AIPW (augmented inverse-probability "
     "weighting). The complete grid is stored in `analysis/estimates.csv`.",
     align="justify", space_after=8)

# ============================================================================
# Table S5 — PSM diagnostics
# ============================================================================
h1("Table S5. Propensity-score-matching diagnostics")
render_md(os.path.join(HERE, "psm_diagnostics.md"))

# ============================================================================
# Table S6 — upper-GI exclusion / stratification
# ============================================================================
h1("Table S6. Upper-GI exclusion and stratification")
render_md(os.path.join(HERE, "upper_gi_sensitivity.md"))

# ============================================================================
# Table S7 — ICD procedure codes
# ============================================================================
h1("Table S7. ICD-9-CM / ICD-10-PCS procedure-code list")
add_table(
    ["Definition", "ICD-9-CM", "ICD-10-PCS"],
    [
        ["Major abdominal surgery (procedure prefixes)",
         "42, 43, 45, 46, 50, 51, 52",
         "0DB5, 0DB6, 0DB8, 0DB9, 0DBE, 0DBP, 0DBQ; 0DT5, 0DT6, 0DT8, 0DT9, 0DTE, 0DTP, 0DTQ; 0D15, 0D16, 0D18, 0D19, 0D1E, 0D1P; 0FB0, 0FB4, 0FB5, 0FBG; 0FT0, 0FT4, 0FT5, 0FTG; 0DQ5, 0DQ6, 0DQ8, 0DQE"],
        ["Exploratory laparotomy (leak/reoperation)",
         "54.1 (stored `541`); 54.5 adhesiolysis (stored `545`) excluded",
         "0WJG (relaparotomy)"],
    ],
)
para("Major abdominal procedures comprise esophageal, gastric, intestinal, hepatobiliary, and "
     "pancreatic resection or reconstruction (ICD-9 two-digit roots 42–52; ICD-10 PCS roots 0DB/"
     "0DT/0D1/0FB/0FT/0DQ). The leak/reoperation outcome is exploratory relaparotomy 3–14 days "
     "after the index procedure, excluding adhesiolysis as a proxy for bowel obstruction.",
     align="justify", space_after=8)

# ============================================================================
# Table S8 — never-fed dissection
# ============================================================================
h1("Table S8. Never-fed subgroup dissection (algorithm and counts)")
add_table(
    ["Never-fed category", "Definition", "n (%)"],
    [
        ["In-hospital death", "Hospital death time recorded during the indexed admission", "127 (11.3%)"],
        ["Therapeutic nil-per-os (ileus/obstruction)", "ICD-9 560.x / ICD-10 K56.x", "211 (18.8%)"],
        ["Presumptive oral recovery", "Neither of the above", "782 (69.8%)"],
    ],
)
para("The never-fed group (n = 1,120) is heterogeneous and was described descriptively rather "
     "than treated as a homogeneous comparator.", align="justify", space_after=8)

# ============================================================================
# Table S9 — missing data
# ============================================================================
h1("Table S9. Per-covariate missingness and complete-case sensitivity")
render_md(os.path.join(HERE, "missing_data.md"))

# ============================================================================
# Table S10 — negative control / AIPW
# ============================================================================
h1("Table S10. Doubly-robust AIPW estimates and treated-urinary-tract-infection negative control")
render_md(os.path.join(HERE, "negative_control.md"))

# ============================================================================
# Table S11 — MIMIC-III replication (hard-coded: source markdown tables are malformed)
# ============================================================================
h1("Table S11. MIMIC-III replication (same-center, earlier era)")
para("Temporal/same-center sensitivity check, not external validation: MIMIC-III and MIMIC-IV "
     "are the same hospital (BIDMC) with overlapping years (2001–2012 vs 2008–2019). Deviations "
     "from the MIMIC-IV pipeline: no procedure date (surgery-before-ICU filter dropped; "
     "leak/reoperation skipped), date-granular prescriptions, and BMI omitted (no omr table).",
     align="justify")
para("**Cohort flow.** Eligible (first SICU/TSICU stay + major abdominal ICD-9 procedure): 3590; "
     "died ≤48 h: 83; ICU-discharged ≤48 h: 1009; landmarked (LOS ≥48 h and survival to 48 h): "
     "**2498**.", align="justify")
add_table(
    ["Feeding group", "n", "Infection composite", "Treated UTI", "Death"],
    [
        ["Never", "1820", "585", "235", "188"],
        ["Late EN", "406", "243", "111", "45"],
        ["EEN", "272", "126", "52", "20"],
    ],
)
para("**Overlap-weighted estimates (comparison A).** Infection composite: crude OR 0.58 "
     "(0.42–0.79); OW OR 0.58 (0.42–0.82, p=0.002). Treated-UTI negative control: crude OR 0.63 "
     "(0.43–0.91); OW OR 0.67 (0.45–1.00, p=0.048).", align="justify")
para("**Overlap-weighted estimates (comparison B).** Infection composite: crude OR 1.46 "
     "(1.13–1.88); OW OR 0.89 (0.68–1.17). Treated-UTI negative control: crude OR 1.28 "
     "(0.93–1.77); OW OR 1.11 (0.79–1.58).", align="justify", space_after=8)

# ============================================================================
# Table S12 — three-database harmonization
# ============================================================================
h1("Table S12. Three-database harmonization (MIMIC-IV / MIMIC-III / eICU-CRD)")
render_md(os.path.join(HERE, "three_db_harmonization.md"))

# ============================================================================
# Table S13 — post hoc sensitivities
# ============================================================================
h1("Table S13. Post hoc sensitivity analyses (72-h outcome window; missingness indicators)")
render_md(os.path.join(HERE, "reviewer_sensitivity.md"))

# ============================================================================
# Table S14 — MICE
# ============================================================================
h1("Table S14. Multiple-imputation (MICE, m=25) sensitivity")
render_md(os.path.join(HERE, "mice_sensitivity.md"))

# ============================================================================
# Table S15 — outcome validation
# ============================================================================
h1("Table S15. Primary-endpoint concordance check against ICD-coded infection/sepsis")
render_md(os.path.join(HERE, "outcome_validation.md"))

# ============================================================================
# Supplementary figures
# ============================================================================
h1("Supplementary Figures")
SUPP_FIGURES = [
    ("**Figure S1.** First-feeding-time distribution among eventually-fed patients (EEN ≤48 h vs "
     "late >48 h), with 24/48/72-h thresholds marked.", "supp1_feeding_time.png"),
    ("**Figure S2.** Never-fed group dissection (died / therapeutic NPO / presumptive oral "
     "recovery).", "supp2_never_fed.png"),
    ("**Figure S3.** Infection-composite components by culture site (blood / abdominal / "
     "respiratory / wound) for comparisons A and B.", "supp3_composite_sites.png"),
    ("**Figure S4.** Cumulative incidence of the treated-infection composite by feeding group "
     "(Aalen–Johansen, with in-hospital death and discharge as competing risks, truncated at "
     "28 days).", "supp4_infection_cif.png"),
    ("**Figure 8.** Replication forest plot: infection composite and treated-urinary-tract-"
     "infection negative control, crude and overlap-weighted, MIMIC-IV vs MIMIC-III.",
     "fig8_replication_forest.png"),
]
for caption, fname in SUPP_FIGURES:
    add_figure(caption, fname)

doc.save(OUT)
print(f"Saved {OUT}")
