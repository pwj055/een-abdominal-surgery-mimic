# Reviewer sensitivity analyses (72-h outcome window; missingness indicators)


## B9. Post-48h reverse-causation sensitivity (infection composite, 72-h outcome window)

The 48-h landmarked cohort is unchanged; only the outcome window start is deferred from 48 h to 72 h (events 48–72 h after ICU admission are dropped from the outcome). A spurious protective association driven by early infection would attenuate here.

| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |

|---|---|---|---|---|---|---|---|---|---|

| A: EEN vs late EN | Crude | 192 | 346 | 49 | 158 | -0.20 (-0.28, -0.12) | 0.56 (0.43, 0.73) | 0.41 (0.28, 0.60) | 0.000 |

| A: EEN vs late EN | OW | 192 | 346 | 49 | 158 | -0.09 (-0.19, 0.01) | 0.77 (0.57, 1.03) | 0.67 (0.43, 1.04) | 0.072 |

| A: EEN vs late EN | IPTW | 192 | 346 | 49 | 158 | -0.07 (-0.18, 0.04) | 0.83 (0.61, 1.13) | 0.74 (0.46, 1.20) | 0.220 |

| A: EEN vs late EN | AIPW | 192 | 346 | 49 | 158 | -0.05 (-0.15, 0.05) | 0.88 (0.66, 1.16) | 0.81 (0.52, 1.25) | 0.341 |

| B: EEN vs no-EEN | Crude | 192 | 1466 | 49 | 313 | 0.04 (-0.02, 0.11) | 1.20 (0.92, 1.55) | 1.26 (0.89, 1.79) | 0.189 |

| B: EEN vs no-EEN | OW | 192 | 1466 | 49 | 313 | 0.05 (-0.03, 0.12) | 1.21 (0.91, 1.60) | 1.29 (0.88, 1.89) | 0.196 |

| B: EEN vs no-EEN | IPTW | 192 | 1466 | 49 | 313 | 0.12 (0.02, 0.22) | 1.56 (1.16, 2.09) | 1.84 (1.19, 2.85) | 0.006 |

| B: EEN vs no-EEN | AIPW | 192 | 1466 | 49 | 313 | 0.14 (0.05, 0.23) | 1.65 (1.27, 2.16) | 2.01 (1.35, 3.01) | 0.001 |


## B10. Missingness-indicator sensitivity (primary infection composite)

Median imputation plus a missingness indicator for every covariate with >10% missingness (bilirubin, BMI, FiO2, lactate, PaO2), instead of only lactate.

| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |

|---|---|---|---|---|---|---|---|---|---|

| A: EEN vs late EN | OW | 192 | 346 | 54 | 171 | -0.11 (-0.21, -0.01) | 0.75 (0.57, 0.99) | 0.63 (0.41, 0.98) | 0.039 |

| A: EEN vs late EN | IPTW | 192 | 346 | 54 | 171 | -0.10 (-0.21, 0.01) | 0.78 (0.57, 1.05) | 0.66 (0.41, 1.05) | 0.082 |

| A: EEN vs late EN | AIPW | 192 | 346 | 54 | 171 | -0.09 (-0.19, 0.02) | 0.81 (0.61, 1.07) | 0.70 (0.44, 1.10) | 0.122 |

| B: EEN vs no-EEN | OW | 192 | 1466 | 54 | 339 | 0.07 (-0.01, 0.14) | 1.28 (0.98, 1.68) | 1.41 (0.97, 2.05) | 0.075 |

| B: EEN vs no-EEN | IPTW | 192 | 1466 | 54 | 339 | 0.10 (0.00, 0.20) | 1.43 (1.05, 1.93) | 1.64 (1.05, 2.56) | 0.030 |

| B: EEN vs no-EEN | AIPW | 192 | 1466 | 54 | 339 | 0.09 (-0.01, 0.20) | 1.40 (1.00, 1.95) | 1.58 (0.97, 2.58) | 0.064 |

