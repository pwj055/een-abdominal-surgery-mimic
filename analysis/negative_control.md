# Negative-control outcome and doubly-robust AIPW

Negative control = treated urinary-tract infection (urine positive culture + systemic antibiotic, same definition as the primary composite but at a site with no plausible EN mechanism). AIPW = augmented inverse-probability weighting (doubly robust; marginal RD/RR/OR).


## infection_composite

| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |

|---|---|---|---|---|---|---|---|---|---|

| A: EEN vs late EN | Crude | 192 | 346 | 54 | 171 | -0.21 (-0.30, -0.13) | 0.57 (0.44, 0.73) | 0.40 (0.27, 0.58) | 0.000 |

| A: EEN vs late EN | OW | 192 | 346 | 54 | 171 | -0.12 (-0.22, -0.02) | 0.73 (0.55, 0.97) | 0.60 (0.39, 0.93) | 0.023 |

| A: EEN vs late EN | IPTW | 192 | 346 | 54 | 171 | -0.09 (-0.20, 0.02) | 0.79 (0.59, 1.07) | 0.68 (0.42, 1.09) | 0.109 |

| A: EEN vs late EN | AIPW | 192 | 346 | 54 | 171 | -0.08 (-0.18, 0.03) | 0.83 (0.63, 1.09) | 0.73 (0.47, 1.14) | 0.164 |


## treated_uti

| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |

|---|---|---|---|---|---|---|---|---|---|

| A: EEN vs late EN | Crude | 192 | 346 | 22 | 65 | -0.07 (-0.13, -0.01) | 0.61 (0.39, 0.96) | 0.56 (0.33, 0.94) | 0.028 |

| A: EEN vs late EN | OW | 192 | 346 | 22 | 65 | -0.02 (-0.09, 0.06) | 0.90 (0.54, 1.49) | 0.88 (0.49, 1.60) | 0.685 |

| A: EEN vs late EN | IPTW | 192 | 346 | 22 | 65 | -0.01 (-0.10, 0.07) | 0.92 (0.54, 1.58) | 0.91 (0.48, 1.72) | 0.763 |

| A: EEN vs late EN | AIPW | 192 | 346 | 22 | 65 | -0.03 (-0.12, 0.06) | 0.83 (0.45, 1.52) | 0.80 (0.40, 1.63) | 0.544 |


## infection_composite

| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |

|---|---|---|---|---|---|---|---|---|---|

| B: EEN vs no-EEN | Crude | 192 | 1466 | 54 | 339 | 0.05 (-0.02, 0.12) | 1.22 (0.95, 1.55) | 1.30 (0.93, 1.82) | 0.126 |

| B: EEN vs no-EEN | OW | 192 | 1466 | 54 | 339 | 0.06 (-0.02, 0.13) | 1.24 (0.95, 1.62) | 1.34 (0.93, 1.95) | 0.118 |

| B: EEN vs no-EEN | IPTW | 192 | 1466 | 54 | 339 | 0.12 (0.02, 0.21) | 1.50 (1.13, 1.99) | 1.76 (1.15, 2.70) | 0.010 |

| B: EEN vs no-EEN | AIPW | 192 | 1466 | 54 | 339 | 0.12 (0.03, 0.21) | 1.52 (1.17, 1.99) | 1.81 (1.21, 2.72) | 0.004 |


## treated_uti

| comparison | method | n_t | n_c | ev_t | ev_c | RD (95% CI) | RR (95% CI) | OR (95% CI) | p (OR) |

|---|---|---|---|---|---|---|---|---|---|

| B: EEN vs no-EEN | Crude | 192 | 1466 | 22 | 152 | 0.01 (-0.04, 0.06) | 1.11 (0.73, 1.68) | 1.12 (0.70, 1.80) | 0.643 |

| B: EEN vs no-EEN | OW | 192 | 1466 | 22 | 152 | 0.03 (-0.03, 0.08) | 1.26 (0.80, 2.01) | 1.30 (0.77, 2.21) | 0.324 |

| B: EEN vs no-EEN | IPTW | 192 | 1466 | 22 | 152 | 0.07 (-0.01, 0.15) | 1.66 (1.03, 2.68) | 1.80 (1.02, 3.19) | 0.043 |

| B: EEN vs no-EEN | AIPW | 192 | 1466 | 22 | 152 | 0.07 (-0.01, 0.15) | 1.67 (1.05, 2.68) | 1.81 (1.03, 3.19) | 0.039 |

