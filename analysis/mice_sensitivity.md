# Multiple imputation (MICE) sensitivity

Chained-equations imputation (linear 'norm' models, 25 imputations × 15 iterations) for the five covariates with >10% missingness (bilirubin, BMI, FiO2, lactate, PaO2), including the exposure and outcome in the imputation model. PS / OW / IPTW / AIPW refit in each dataset; pooled via Rubin's rules.

| comparison | method | n | RD (95% CI) | RR (95% CI) | OR (95% CI) |

|---|---|---|---|---|---|

| A: EEN vs late EN | OW | 538 | -0.12 (-0.22, -0.02) | 0.72 (0.55, 0.96) | 0.59 (0.38, 0.92) |

| A: EEN vs late EN | IPTW | 538 | -0.11 (-0.22, 0.00) | 0.77 (0.57, 1.03) | 0.64 (0.40, 1.03) |

| A: EEN vs late EN | AIPW | 538 | -0.09 (-0.20, 0.02) | 0.80 (0.61, 1.06) | 0.69 (0.44, 1.08) |

| B: EEN vs no-EEN | OW | 1658 | 0.06 (-0.02, 0.13) | 1.23 (0.94, 1.62) | 1.34 (0.91, 1.95) |

| B: EEN vs no-EEN | IPTW | 1658 | 0.11 (0.01, 0.21) | 1.48 (1.10, 1.99) | 1.72 (1.10, 2.69) |

| B: EEN vs no-EEN | AIPW | 1658 | 0.11 (0.01, 0.22) | 1.49 (1.11, 2.02) | 1.76 (1.12, 2.76) |

