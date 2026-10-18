# -*- coding: utf-8 -*-
"""Add five recent (2021-2026) references and renumber the reference list in
Vancouver citation order, in both manuscript_criticalcare.md and
20_make_criticalcare_docx.py.

New references (all Crossref-verified):
  7  Weimann 2021 (ESPEN surgery guideline)
  8  Singer 2023 (ESPEN ICU guideline update)
  10 Hernán 2022 (JAMA target-trial-emulation framework)
  11 Cashin 2025 (TARGET reporting statement)
  27 Talebi 2023 (umbrella review of early vs delayed EN/PN)
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
MD = os.path.join(ROOT, "manuscript_criticalcare.md")
PY = os.path.join(HERE, "20_make_criticalcare_docx.py")

# Final 30 references in citation order.
REFS = [
    "Lewis SJ, Egger M, Sylvester PA, Thomas S. Early enteral feeding versus \"nil by mouth\" after gastrointestinal surgery: systematic review and meta-analysis of controlled trials. *BMJ*. 2001;323(7316):773–776. doi: 10.1136/bmj.323.7316.773.",
    "Andersen HK, Lewis SJ, Thomas S. Early enteral nutrition within 24h of colorectal surgery versus later commencement of feeding for postoperative complications. *Cochrane Database Syst Rev*. 2006;(4):CD004080. doi: 10.1002/14651858.CD004080.pub2.",
    "Doig GS, Heighes PT, Simpson F, Sweetman EA, Davies AR. Early enteral nutrition, provided within 24 h of injury or intensive care unit admission, significantly reduces mortality in critically ill patients: a meta-analysis of randomised controlled trials. *Intensive Care Med*. 2009;35(12):2018–2027. doi: 10.1007/s00134-009-1664-4.",
    "Singer P, Blaser AR, Berger MM, et al. ESPEN guideline on clinical nutrition in the intensive care unit. *Clin Nutr*. 2019;38(1):48–79. doi: 10.1016/j.clnu.2018.08.037.",
    "McClave SA, Taylor BE, Martindale RG, et al. Guidelines for the Provision and Assessment of Nutrition Support Therapy in the Adult Critically Ill Patient: Society of Critical Care Medicine (SCCM) and American Society for Parenteral and Enteral Nutrition (A.S.P.E.N.). *JPEN J Parenter Enteral Nutr*. 2016;40(2):159–211. doi: 10.1177/0148607115621863.",
    "Reintam Blaser A, Starkopf J, Alhazzani W, et al. Early enteral nutrition in critically ill patients: ESICM clinical practice guidelines. *Intensive Care Med*. 2017;43(3):380–398. doi: 10.1007/s00134-016-4665-0.",
    "Weimann A, Braga M, Carli F, et al. ESPEN practical guideline: Clinical nutrition in surgery. *Clin Nutr*. 2021;40(7):4745–4761. doi: 10.1016/j.clnu.2021.03.031.",
    "Singer P, Blaser AR, Berger MM, et al. ESPEN practical and partially revised guideline: Clinical nutrition in the intensive care unit. *Clin Nutr*. 2023;42(9):1671–1689. doi: 10.1016/j.clnu.2023.07.011.",
    "Hernán MA, Robins JM. Using Big Data to Emulate a Target Trial When a Randomized Trial Is Not Available. *Am J Epidemiol*. 2016;183(8):758–764. doi: 10.1093/aje/kwv254.",
    "Hernán MA, Wang W, Leaf DE. Target trial emulation: a framework for causal inference from observational data. *JAMA*. 2022;328(24):2446–2447. doi: 10.1001/jama.2022.21383.",
    "Cashin AG, Hansford HJ, Hernán MA, et al. Transparent reporting of observational studies emulating a target trial: the TARGET statement. *JAMA*. 2025;334(12):1084–1093. doi: 10.1001/jama.2025.13350.",
    "Frangakis CE, Rubin DB. Principal stratification in causal inference. *Biometrics*. 2002;58(1):21–29. doi: 10.1111/j.0006-341X.2002.00021.x.",
    "Giobbie-Hurder A, Gelber RD, Regan MM. Challenges of guarantee-time bias. *J Clin Oncol*. 2013;31(23):2963–2969. doi: 10.1200/JCO.2013.49.5283.",
    "Maringe C, Benitez Majano S, Exarchakou A, et al. Reflection on modern methods: trial emulation in the presence of immortal-time bias. Assessing the benefit of major surgery for elderly lung cancer patients using observational data. *Int J Epidemiol*. 2020;49(5):1719–1729. doi: 10.1093/ije/dyaa057.",
    "Johnson AEW, Bulgarelli L, Shen L, et al. MIMIC-IV, a freely accessible electronic health record dataset. *Sci Data*. 2023;10(1):1. doi: 10.1038/s41597-022-01899-x.",
    "Lipsitch M, Tchetgen Tchetgen E, Cohen T. Negative controls: a tool for detecting confounding and bias in observational studies. *Epidemiology*. 2010;21(3):383–388. doi: 10.1097/EDE.0b013e3181d61eeb.",
    "Rosenbaum PR, Rubin DB. The central role of the propensity score in observational studies for causal effects. *Biometrika*. 1983;70(1):41–55. doi: 10.1093/biomet/70.1.41.",
    "Li F, Morgan KL, Zaslavsky AM. Balancing covariates via propensity score weighting. *J Am Stat Assoc*. 2018;113(521):390–400. doi: 10.1080/01621459.2016.1260466.",
    "Cole SR, Hernán MA. Constructing inverse probability weights for marginal structural models. *Am J Epidemiol*. 2008;168(6):656–664. doi: 10.1093/aje/kwn164.",
    "Austin PC. Optimal caliper widths for propensity-score matching when estimating differences in means and differences in proportions in observational studies. *Pharm Stat*. 2011;10(2):150–161. doi: 10.1002/pst.433.",
    "Lunceford JK, Davidian M. Stratification and weighting via the propensity score in estimation of causal treatment effects: a comparative study. *Stat Med*. 2004;23(19):2937–2960. doi: 10.1002/sim.1903.",
    "Zou G. A modified Poisson regression approach to prospective studies with binary data. *Am J Epidemiol*. 2004;159(7):702–706. doi: 10.1093/aje/kwh090.",
    "Fine JP, Gray RJ. A proportional hazards model for the subdistribution of a competing risk. *J Am Stat Assoc*. 1999;94(446):496–509. doi: 10.1080/01621459.1999.10474144.",
    "VanderWeele TJ, Ding P. Sensitivity analysis in observational research: introducing the E-value. *Ann Intern Med*. 2017;167(4):268–274. doi: 10.7326/M16-2607.",
    "Johnson AEW, Pollard TJ, Shen L, et al. MIMIC-III, a freely accessible critical care database. *Sci Data*. 2016;3:160035. doi: 10.1038/sdata.2016.35.",
    "Pollard TJ, Johnson AEW, Raffa JD, Celi LA, Mark RG, Badawi O. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. *Sci Data*. 2018;5:180178. doi: 10.1038/sdata.2018.178.",
    "Talebi S, Zeraattalab-Motlagh S, Vajdi M, et al. Early vs delayed enteral nutrition or parenteral nutrition in hospitalized patients: an umbrella review of systematic reviews and meta-analyses of randomized trials. *Nutr Clin Pract*. 2023;38(3):564–579. doi: 10.1002/ncp.10976.",
    "Lee DS. Training, wages, and sample selection: estimating sharp bounds on treatment effects. *Rev Econ Stud*. 2009;76(3):1071–1102. doi: 10.1111/j.1467-937X.2009.00536.x.",
    "Zhang JL, Rubin DB. Estimation of causal effects via principal stratification when some outcomes are truncated by \"death\". *J Educ Behav Stat*. 2003;28(4):353–368. doi: 10.3102/10769986028004353.",
    "Aalen OO, Johansen S. An empirical transition matrix for non-homogeneous Markov chains based on censored observations. *Scand J Stat*. 1978;5(3):141–150.",
]

# Old reference number -> new reference number (Vancouver first-citation order).
OLD_TO_NEW = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
    7: 9, 8: 12, 9: 13, 10: 14, 11: 15, 12: 16,
    13: 17, 14: 18, 15: 19, 16: 20, 17: 21, 18: 22, 19: 23,
    20: 24, 21: 25, 22: 26, 23: 28, 24: 29, 25: 30,
}

CITE_RE = re.compile(r"\[(\d+)(?:[–-](\d+))?\]")


def remap(text):
    def repl(m):
        n1 = OLD_TO_NEW.get(int(m.group(1)), int(m.group(1)))
        if m.group(2):
            n2 = OLD_TO_NEW.get(int(m.group(2)), int(m.group(2)))
            return f"[{n1}–{n2}]"
        return f"[{n1}]"
    return CITE_RE.sub(repl, text)


def apply_edits(text):
    text = remap(text)
    # B1: extend the society-guidelines cluster to the two newer guidelines.
    text = text.replace("[4–6]", "[4–8]", 1)
    # B2: cite the 2022 JAMA framework alongside the 2016 reference.
    text = text.replace("framework [9]", "framework [9,10]", 1)
    # B3: note TARGET reporting alongside STROBE/RECORD.
    text = text.replace(
        "(Additional Files 1 and 2).",
        "(Additional Files 1 and 2), and follows the TARGET reporting framework for "
        "target-trial-emulation studies [11].",
        1,
    )
    # B4: contextualise the primary result with the recent umbrella review.
    text = text.replace(
        "(RR 0.83, 0.63–1.09). The direction was reproduced",
        "(RR 0.83, 0.63–1.09). This direction is consistent with a recent umbrella review of "
        "early versus delayed nutrition, which likewise reported lower infectious complications "
        "with earlier initiation [27]. The direction was reproduced",
        1,
    )
    return text


# ---- markdown -----------------------------------------------------------------
md = open(MD, encoding="utf-8").read()
md = apply_edits(md)
start = md.index("## References")
end = md.index("## Figure legends")
refs_md = "\n".join(f"{i}. {t}" for i, t in enumerate(REFS, 1))
md = md[:start] + "## References\n\n" + refs_md + "\n\n" + md[end:]
open(MD, "w", encoding="utf-8").write(md)

# ---- docx generator -----------------------------------------------------------
py = open(PY, encoding="utf-8").read()
py = apply_edits(py)
start = py.index("REFS = [")
end = py.index("for i, ref in enumerate(REFS, 1):")
refs_py = "REFS = [\n" + "\n".join("    " + repr(t) + "," for t in REFS) + "\n]"
py = py[:start] + refs_py + "\n" + py[end:]
open(PY, "w", encoding="utf-8").write(py)

print(f"Updated {os.path.basename(MD)} and {os.path.basename(PY)}")
print(f"References now: {len(REFS)}")
print("New refs: 7 Weimann2021, 8 Singer2023, 10 Hernan2022, 11 Cashin2025, 27 Talebi2023")
