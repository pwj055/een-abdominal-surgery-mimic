# -*- coding: utf-8 -*-
"""Look up DOIs for the manuscript reference list via Crossref (bibliographic query)."""
import json
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QUERIES = [
    (1, "Lewis Egger Sylvester Thomas Early enteral feeding versus nil by mouth after gastrointestinal surgery 2001 BMJ"),
    (2, "Andersen Lewis Thomas Early enteral nutrition within 24h of colorectal surgery versus later commencement Cochrane"),
    (3, "Doig Heighes Simpson Sweetman Davies Early enteral nutrition provided within 24h injury intensive care admission reduces mortality meta-analysis"),
    (4, "Singer Blaser Berger ESPEN guideline on clinical nutrition in the intensive care unit 2019"),
    (5, "McClave Taylor Martindale Guidelines Provision Assessment Nutrition Support Therapy Adult Critically Ill Patient SCCM ASPEN 2016"),
    (6, "Reintam Blaser Starkopf Alhazzani Early enteral nutrition in critically ill patients ESICM clinical practice guidelines 2017"),
    (7, "Hernan Robins Using Big Data to Emulate a Target Trial When a Randomized Trial Is Not Available"),
    (8, "Frangakis Rubin Principal stratification in causal inference Biometrics 2002"),
    (9, "Giobbie-Hurder Gelber Regan Challenges of guarantee-time bias"),
    (10, "Maringe Benitez Majano Exarchakou trial emulation immortal-time bias major surgery elderly lung cancer"),
    (11, "Johnson Bulgarelli Shen MIMIC-IV a freely accessible electronic health record dataset"),
    (12, "Lipsitch Tchetgen Tchetgen Cohen Negative controls a tool for detecting confounding and bias in observational studies"),
    (13, "Rosenbaum Rubin The central role of the propensity score in observational studies for causal effects Biometrika 1983"),
    (14, "Li Morgan Zaslavsky Balancing covariates via propensity score weighting"),
    (15, "Cole Hernan Constructing inverse probability weights for marginal structural models"),
    (16, "Austin Optimal caliper widths for propensity-score matching when estimating differences in means and differences in proportions"),
    (17, "Lunceford Davidian Stratification and weighting via the propensity score in estimation of causal treatment effects"),
    (18, "Zou A modified Poisson regression approach to prospective studies with binary data"),
    (19, "Fine Gray A proportional hazards model for the subdistribution of a competing risk"),
    (20, "VanderWeele Ding Sensitivity analysis in observational research introducing the E-value"),
    (21, "Johnson Pollard Shen MIMIC-III a freely accessible critical care database"),
    (22, "Pollard Johnson Raffa Celi Mark Badawi eICU Collaborative Research Database freely available multi-center database critical care"),
    (23, "Lee Training wages and sample selection estimating sharp bounds on treatment effects"),
    (24, "Zhang Rubin Estimation of causal effects via principal stratification when some outcomes are truncated by death"),
    (25, "Aalen Johansen An empirical transition matrix for non-homogeneous Markov chains based on censored observations"),
]


def lookup(bib):
    url = ("https://api.crossref.org/works?query.bibliographic="
           + urllib.parse.quote(bib) + "&rows=1&mailto=research@example.org")
    req = urllib.request.Request(url, headers={"User-Agent": "EEN-refcheck/1.0 (mailto:research@example.org)"})
    for attempt in range(5):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=25))
            it = d["message"]["items"][0]
            title = (it.get("title") or [""])[0]
            year = None
            for k in ("published-print", "published-online", "published"):
                if k in it:
                    year = it[k]["date-parts"][0][0]
                    break
            return it.get("DOI"), title, year
        except Exception as e:
            if attempt < 4:
                time.sleep(4 * (attempt + 1))
                continue
            return None, None, repr(e)


for num, bib in QUERIES:
    doi, title, year = lookup(bib)
    print(f"{num:2d}. DOI={doi} | year={year} | {title}")
    time.sleep(1.5)
