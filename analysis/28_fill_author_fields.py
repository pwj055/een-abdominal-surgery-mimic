# -*- coding: utf-8 -*-
"""Fill the remaining title-page / Declarations fields in both manuscript tracks.

Corresponding author = Yehong Han <jianghao-163@163.com>; funding = No funding;
competing interests = none; authors' contributions = standard draft (user to edit).
Also drops the unfindable PhysioNet DUA "(certificate number [ ])" parenthetical
(BMC does not require it), from §2.2 and the Declarations in each track.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

CORR = "**Corresponding author.** Yehong Han, jianghao-163@163.com"
COI = "The authors declare that they have no competing interests."
FUND = "No funding."
CONTRIB = ("Peiwu Jiang and Yehong Han conceived and designed the study. Peiwu Jiang "
           "performed the data analysis and drafted the manuscript. Yao Xu and Yantao "
           "Zhang contributed to data interpretation and critically revised the "
           "manuscript. Yehong Han supervised the work. All authors read and approved "
           "the final manuscript.")

# per-file (old, new) pairs; each old must occur exactly once in that file.
EDITS = {
    "manuscript_criticalcare.md": [
        ("**Corresponding author.** [ ]", CORR),
        ("### Competing interests\n\n[ ]", "### Competing interests\n\n" + COI),
        ("### Funding\n\n[ ]", "### Funding\n\n" + FUND),
        ("### Authors' contributions\n\n[ ]", "### Authors' contributions\n\n" + CONTRIB),
    ],
    "manuscript.md": [
        ("**Corresponding author.** [ ]", CORR),
        ("**Competing interests.** [ ]", "**Competing interests.** " + COI),
        ("**Funding.** [ ]", "**Funding.** " + FUND),
        ("**Authors' contributions.** [ ]", "**Authors' contributions.** " + CONTRIB),
    ],
    "analysis/20_make_criticalcare_docx.py": [
        ("**Corresponding author.** [ ]", CORR),
        ("**Competing interests.** [ ]", "**Competing interests.** " + COI),
        ("**Funding.** [ ]", "**Funding.** " + FUND),
        ("**Authors' contributions.** [ ]", "**Authors' contributions.** " + CONTRIB),
    ],
    "analysis/12_make_docx.py": [
        ("**Corresponding author.** [ ]", CORR),
        ("**Competing interests.** [ ]", "**Competing interests.** " + COI),
        ("**Funding.** [ ]", "**Funding.** " + FUND),
        ("**Authors' contributions.** [ ]", "**Authors' contributions.** " + CONTRIB),
    ],
}

CERT = " (certificate number [ ])"

for rel, pairs in EDITS.items():
    path = os.path.join(ROOT, rel)
    txt = open(path, encoding="utf-8").read()
    for old, new in pairs:
        n = txt.count(old)
        if n != 1:
            print(f"  WARN {rel}: {n}x (expected 1) for {old!r}")
            continue
        txt = txt.replace(old, new)
        print(f"  {rel}: filled {old!r}")
    c = txt.count(CERT)
    txt = txt.replace(CERT, "")
    if c:
        print(f"  {rel}: removed {c}x ' (certificate number [ ])'")
    open(path, "w", encoding="utf-8").write(txt)
print("done")
