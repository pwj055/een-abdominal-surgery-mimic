# Primary-endpoint concordance check (ICD-coded infection)

Cross-tabulation of the treated-infection composite (positive non-urine culture + systemic antibiotic) against ICD-coded infection/sepsis diagnoses recorded during the admission, as a zero-cost face validity check. Neither source is a gold standard (ICD codes are billing diagnoses and may be coded without a positive culture; the composite requires both a culture and an antibiotic), so results are reported as concordance rather than as sensitivity/specificity against truth.


## ICD code lists used

- **ICD sepsis/bacteraemia (narrow):** ICD-10 `A40*`, `A41*`, `R65.1`, `R65.2`, `R78.8`; ICD-9 `038*`, `99591`, `99592`, `78552`.

- **ICD any matching-site infection (broad):** sepsis list above plus ICD-10 `J12*`–`J18*`, `K65*`, `K63.0`, `K75.0`, `T81.4*`, `L02*`; ICD-9 `481`, `482`, `483`, `485`, `486`, `567*`, `540.1`, `998.5*`.


## ICD sepsis/bacteraemia

| composite \ ICD | ICD + | ICD − | total |
|---|---|---|---|

| composite + | 208 | 185 | 393 |

| composite − | 357 | 908 | 1265 |

| total | 565 | 1093 | 1658 |


Agreement 67.3%; Cohen's κ = 0.215 (treating ICD as reference: sensitivity 36.8%, specificity 83.1%, PPV 52.9%, NPV 71.8%).


## ICD any matching-site infection

| composite \ ICD | ICD + | ICD − | total |
|---|---|---|---|

| composite + | 319 | 74 | 393 |

| composite − | 548 | 717 | 1265 |

| total | 867 | 791 | 1658 |


Agreement 62.5%; Cohen's κ = 0.267 (treating ICD as reference: sensitivity 36.8%, specificity 90.6%, PPV 81.2%, NPV 56.7%).


Composite prevalence in the landmarked cohort (n=1658): 393 events (23.7%).

