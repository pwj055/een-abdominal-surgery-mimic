# Early vs late enteral nutrition after major abdominal surgery (MIMIC-IV)

A target-trial emulation of early (≤48 h) versus late (>48 h) enteral nutrition after
major abdominal surgery in intensive-care patients, using **MIMIC-IV v3.1**, with a
same-center temporal replication in **MIMIC-III v1.4** and supportive multicenter
triangulation in **eICU-CRD v2.0**.

## Registration & manuscript

- **Code repository:** https://github.com/pwj055/een-abdominal-surgery-mimic (MIT license)
- **Registered protocol:** OSF https://osf.io/g39vw — DOI `10.17605/OSF.IO/G39VW`
  (retrospective registration; the analysis plan was finalized before model fitting,
  protocol dated 2026-10-16).
- **Manuscript source:** [manuscript.md](manuscript.md); [STROBE](STROBE_checklist.md) and
  [RECORD](RECORD_checklist.md) checklists in the repo root.

## Headline result (see manuscript for full detail)

Among 1,658 landmarked MIMIC-IV patients (EEN 192 / late EN 346 / never fed 1,120),
Comparison A (EEN vs late EN among those eventually fed) was associated with fewer
antibiotic-treated infections (overlap-weighted OR **0.60**, 95% CI 0.39–0.93), a
direction reproduced almost exactly in MIMIC-III (overlap-weighted OR 0.58, 0.42–0.82).
The treated-urinary-tract-infection negative control nulls in MIMIC-IV (0.88) but only
partially in MIMIC-III (0.67); residual confounding cannot be fully excluded and is
reported honestly. Comparison B (full-cohort policy) shows no infection benefit.

## Repository layout

```
analysis/        # reproducible pipeline (01…16) + generated reports (*.md) + figures/
  README.md      # pipeline documentation and all result tables
protocol.md      # locked study protocol (target-trial specification, §12 analysis log)
manuscript.md    # manuscript source (Markdown)
feasibility/     # pre-analysis feasibility check (F1–F9)
```

## Data

Raw MIMIC-IV, MIMIC-III and eICU-CRD data are **not included** — PhysioNet data-use
agreements prohibit redistribution. Obtain them from PhysioNet (credentialed access):

- MIMIC-IV — https://physionet.org/content/mimiciv/
- MIMIC-III — https://physionet.org/content/mimiciii/
- eICU-CRD — https://physionet.org/content/eicu-crd/

## Reproduce

Requires Python ≥ 3.10 with `duckdb`, `pandas`, `numpy`, `statsmodels`, `scipy`,
`matplotlib` (and `python-docx` for `12_make_docx.py`). Place each dataset as described
in [analysis/README.md](analysis/README.md), then run the numbered scripts in order.
Scripts that read external data take the data directory as a command-line argument.

## License

Code is released under the [MIT License](LICENSE). Analysis output and reports are
provided under CC-BY 4.0.

## Citation

TBA — cite the published paper once available.
