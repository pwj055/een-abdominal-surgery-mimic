# MIMIC-III v1.4 replication (same-center, earlier era)

Temporal/same-center sensitivity check, NOT external validation: MIMIC-III and MIMIC-IV are the same hospital (BIDMC) with overlapping years (2001-2012 vs 2008-2019); the carevue era (2001-2008) is disjoint from MIMIC-IV. Deviations from the MIMIC-IV pipeline: no procedure date (surgery-before-ICU filter dropped; leak/reoperation skipped), date-granular prescriptions, and BMI omitted (no omr table); chart-based SOFA physiology (GCS/MAP/FiO2/PaO2), mechanical ventilation, vasopressors, lactate and organ labs are all extracted.

## Cohort flow

- Eligible (first SICU/TSICU stay + major abdominal ICD-9 procedure): 3590

- Died <=48 h: 83.0  |  ICU-discharged <=48 h: 1009.0

- Landmarked (LOS>=48 h & survival to 48 h): **2498**


## Exposure/outcome tallies

| grp | n | infection | treated UTI | death |
|---|---|---|---|---|

| never | 1820 | 585.0 | 235.0 | 188.0 |
| late | 406 | 243.0 | 111.0 | 45.0 |
| EEN | 272 | 126.0 | 52.0 | 20.0 |


## Comparison A and B (overlap weighting, primary infection composite + negative control)

| comparison | outcome | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |

|---|---|---|---|---|---|---|---|---|---|---|


### infection_composite

| A: EEN vs late EN | Crude | 272 | 406 | 126 | 243 | -0.14 (-0.21, -0.06) | 0.77 (0.67, 0.90) | 0.58 (0.42, 0.79) | 0.001 |

| A: EEN vs late EN | OW | 272 | 406 | 126 | 243 | -0.13 (-0.22, -0.05) | 0.78 (0.66, 0.91) | 0.58 (0.42, 0.82) | 0.002 |


### treated_uti

| A: EEN vs late EN | Crude | 272 | 406 | 52 | 111 | -0.08 (-0.15, -0.02) | 0.70 (0.52, 0.94) | 0.63 (0.43, 0.91) | 0.015 |

| A: EEN vs late EN | OW | 272 | 406 | 52 | 111 | -0.07 (-0.15, -0.00) | 0.73 (0.54, 1.00) | 0.67 (0.45, 1.00) | 0.048 |


### infection_composite

| B: EEN vs no-EEN | Crude | 272 | 2226 | 126 | 828 | 0.09 (0.03, 0.15) | 1.25 (1.08, 1.43) | 1.46 (1.13, 1.88) | 0.004 |

| B: EEN vs no-EEN | OW | 272 | 2226 | 126 | 828 | -0.03 (-0.10, 0.04) | 0.94 (0.81, 1.09) | 0.89 (0.68, 1.17) | 0.390 |


### treated_uti

| B: EEN vs no-EEN | Crude | 272 | 2226 | 52 | 346 | 0.04 (-0.01, 0.08) | 1.23 (0.95, 1.60) | 1.28 (0.93, 1.77) | 0.129 |

| B: EEN vs no-EEN | OW | 272 | 2226 | 52 | 346 | 0.02 (-0.04, 0.07) | 1.09 (0.82, 1.45) | 1.11 (0.79, 1.58) | 0.547 |


