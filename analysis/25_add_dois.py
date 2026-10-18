# -*- coding: utf-8 -*-
"""Append verified DOIs to the Critical Care reference list (markdown + docx generator)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

# (unique page/article-number suffix including trailing period, DOI) — 24 of 25 refs.
# Ref 25 (Aalen & Johansen 1978, Scand J Stat) has no Crossref DOI and is left unchanged.
DOI_PAIRS = [
    ("773–776.", "10.1136/bmj.323.7316.773"),
    ("CD004080.", "10.1002/14651858.CD004080.pub2"),
    ("2018–2027.", "10.1007/s00134-009-1664-4"),
    ("48–79.", "10.1016/j.clnu.2018.08.037"),
    ("159–211.", "10.1177/0148607115621863"),
    ("380–398.", "10.1007/s00134-016-4665-0"),
    ("758–764.", "10.1093/aje/kwv254"),
    ("21–29.", "10.1111/j.0006-341X.2002.00021.x"),
    ("2963–2969.", "10.1200/JCO.2013.49.5283"),
    ("1719–1729.", "10.1093/ije/dyaa057"),
    ("10(1):1.", "10.1038/s41597-022-01899-x"),
    ("383–388.", "10.1097/EDE.0b013e3181d61eeb"),
    ("41–55.", "10.1093/biomet/70.1.41"),
    ("390–400.", "10.1080/01621459.2016.1260466"),
    ("656–664.", "10.1093/aje/kwn164"),
    ("150–161.", "10.1002/pst.433"),
    ("2937–2960.", "10.1002/sim.1903"),
    ("702–706.", "10.1093/aje/kwh090"),
    ("496–509.", "10.1080/01621459.1999.10474144"),
    ("268–274.", "10.7326/M16-2607"),
    ("160035.", "10.1038/sdata.2016.35"),
    ("180178.", "10.1038/sdata.2018.178"),
    ("1071–1102.", "10.1111/j.1467-937X.2009.00536.x"),
    ("353–368.", "10.3102/10769986028004353"),
]

TARGETS = [
    os.path.join(ROOT, "manuscript_criticalcare.md"),
    os.path.join(HERE, "20_make_criticalcare_docx.py"),
]

for path in TARGETS:
    with open(path, encoding="utf-8") as f:
        txt = f.read()
    applied = 0
    for suffix, doi in DOI_PAIRS:
        new = f"{suffix} doi: {doi}."
        if suffix in txt:
            txt = txt.replace(suffix, new, 1)
            applied += 1
        else:
            print(f"  WARN: suffix not found in {os.path.basename(path)}: {suffix}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"{os.path.basename(path)}: applied {applied}/{len(DOI_PAIRS)} DOIs")
