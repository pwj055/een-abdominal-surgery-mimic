# eICU-CRD v2.0 — supportive multicenter triangulation
**Role**: NOT a full external validation. microLab (145 KB) cannot reproduce the
treated-culture infection composite, and eICU has no procedure-code table, so
`apacheadmissiondx` "surgery for …" labels stand in for major abdominal surgery.
**Cohort flow**: GI-surgery APACHE diagnoses (first ICU stay/patient) **4578** → 48-h landmark (ICU LOS ≥ 48 h) **2128**.

## Descriptive (landmarked)
| exposure | n | death % | median ICU LOS (d) | median hospital LOS (d) | median vent days |
|---|---|---|---|---|---|
| EEN | 159 | 8.8 | 3.9 | 10.8 | 3.0 |
| late | 97 | 14.4 | 10.1 | 16.0 | 5.0 |
| never | 1872 | 10.1 | 3.8 | 10.6 | 3.0 |

- Median time-to-first-feed: EEN **13.0 h** vs late **95.3 h**.
- EEN proportion among eventually-fed: 159/256 = 62.1% of fed, 7.5% of all landmarked.

## In-hospital death — EEN vs control
| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |
|---|---|---|---|---|---|---|---|---|---|
| **A: EEN vs late (eventually-fed)** (n=256, max|SMD| raw 0.64 → OW 0.00) |||||||||||
| Crude | 159 | 97 | 14 | 14 | -0.06 (-0.14, 0.03) | 0.61 (0.30, 1.22) | 0.57 (0.26, 1.26) | 0.165 |
| OW | 159 | 97 | 14 | 14 | -0.01 (-0.10, 0.08) | 0.90 (0.42, 1.91) | 0.88 (0.37, 2.09) | 0.778 |
| **B: EEN vs no-EEN (full landmarked cohort)** (n=2128, max|SMD| raw 0.13 → OW 0.00) |||||||||||
| Crude | 159 | 1969 | 14 | 204 | -0.02 (-0.06, 0.03) | 0.85 (0.51, 1.42) | 0.84 (0.47, 1.47) | 0.534 |
| OW | 159 | 1969 | 14 | 204 | -0.02 (-0.06, 0.03) | 0.84 (0.50, 1.40) | 0.82 (0.46, 1.45) | 0.495 |

## Interpretation (supportive only)
- **Feeding structure among documented-fed patients is coherent with MIMIC**: 62% of
fed patients are EEN, and time-to-first-feed separates cleanly (median 13 h vs 95 h),
the same EEN/late split the main analysis relies on.
- **Absolute feeding rate is much lower than MIMIC** (12% fed vs MIMIC-IV 32%), and the
88% "never" share is best explained by under-ascertainment of enteral intake in
`intakeOutput` (sites chart feeding in other cells, in `infusionDrug`, or not at all),
so the eICU "never" group is NOT comparable to MIMIC's never-fed group.
- **In-hospital death is null** in both comparisons (A OW OR 0.88, B OW OR 0.82) —
consistent with MIMIC, where death was a secondary/null endpoint and the primary
finding was the infection composite. eICU cannot reproduce that infection composite
(microLab 145 KB), which is precisely why eICU is supportive, not a validation.
