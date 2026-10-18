# Analysis pipeline — EEN after major abdominal surgery (MIMIC-IV v3.1)

Reproducible target-trial-emulation pipeline. Run in order; each stage reads the
previous stage's output. All scripts live here; raw data stays in `../mimic-iv/`.

## Stages

| File | What it does | Output |
|---|---|---|
| `01_build_dataset.py` | Builds the analysis-ready table in duckdb: cohort (first surgical ICU stay, major abdo surgery on/before ICU day, ICU LOS≥48h **and survival to 48h**), exposure (EEN/late/never via `category='Nutrition - Enteral'`), 0–24h covariates, outcomes (treated BSI, infection composite, leak/reoperation, in-hospital death). | `cohort.csv` (1658 rows) |
| `02_weighting.py` | Two co-primary comparisons × 4 outcomes × 3 methods (overlap weighting, stabilized/truncated IPTW, PSM caliper 0.2). Weighted RD + OR with GEE robust sandwich SE; SMD before/after; ESS. | `results.md`, `estimates.csv` |
| `03_tables.py` | Table 1 (baseline by EEN/late/never + SMD) and never-group 3-way dissection (died / therapeutic-NPO / oral recovery). | `table1.md`, `table1.csv` |
| `05_threshold_sensitivity.py` | 24/48/72h exposure-threshold + landmark sensitivity (reuses 02's estimator). | `threshold_sensitivity.md` |
| `06_sofa_covariates.py` | 2nd-pass severity covariates (0–24h): GCS/MAP/FiO2/PaO2/BMI → merged by `load_cohort`. | `sofa_covariates.csv` |
| `07_sensitivities.py` | Remaining prespecified sensitivities: same-day surgery (§8.3), feeding definition any/rate≥20/ONS (§8.2), ITT first-48h feeding order (§8.5), BSI no contaminant exclusion (§8.6), antibiotic course ≥3 and ≥5 days (§8.6b/c). | `sensitivities.md`, `sensitivity_extra.csv` |
| `08_competing_risk.py` | Landmark report (§8.4, 48h death/discharge) + death competing-risk (§8.9): Aalen-Johansen 28-day CIF and Fine-Gray subdistribution HR (OW-weighted; weighted Cox solved directly, validated vs statsmodels). | `competing_risk.md`, `tte.csv` |
| `10_reviewer_diagnostics.py` | Reviewer-driven diagnostics: PSM match-rate / caliper-sensitivity / discordant pairs (Comparison A), and upper-GI exclusion & stratification. | `psm_diagnostics.md`, `upper_gi_sensitivity.md` |
| `11_reviewer_figures.py` | Reviewer-driven figures: PS overlap (Fig 4), Love plot (Fig 5), threshold dose-response gradient (Fig 6), estimand schematic (Fig 7), plus supplement feeding-time / never-fed / composite-site figures. | `figures/fig{4..7}*.png`, `figures/supp*.png` |
| `13_causal_hardening.py` | Causal-hardening analyses: negative-control outcome (treated UTI), doubly-robust AIPW RD/RR/OR, and missing-data reporting + complete-case sensitivity. | `negative_control.md`, `missing_data.md` |
| `14_mimic3_replication.py` | Same-center/temporal replication in MIMIC-III v1.4 (D:\mimic3): rebuilds the cohort (no surgery-date filter; MV from CHARTEVENTS 720/223849; Elixhauser ICD-9), then OW for comparisons A/B × {infection composite, treated UTI}. | `mimic3_cohort.csv`, `mimic3_replication.md` |
| `15_eicu_replication.py` | Supportive multicenter (eICU-CRD v2.0, D:\eicu): APACHE "surgery for" cohort, intakeOutput enteral classifier, 48-h landmark, death/LOS/ventilation descriptive + OW death. **Not a validation** (microLab too sparse, no procedure table). | `eicu_cohort.csv`, `eicu_replication.md` |
| `16_replication_forest.py` | Replication forest plot: MIMIC-IV vs MIMIC-III, infection composite + treated-UTI negative control, crude + OW. | `figures/fig8_replication_forest.png` |

Supporting: `feeding_itemids.csv` = the 112 enteral-nutrition itemids
(`d_items.linksto='inputevents' AND category='Nutrition - Enteral'`), frozen for
the supplement.

## Key definitions

- **Exposure**: first tube-feed record with `rate≥10 mL/hr OR amount≥20 mL`.
  EEN = first feed ≤48h; late = >48h; never = no feed during ICU stay.
- **Time zero**: ICU `intime`. 48h landmark (`los≥2` days). Outcomes counted
  >48h and <28d.
- **Comparison A (timing)**: eventually-fed subset (`tf_any==1`), EEN vs late.
- **Comparison B (policy)**: full landmarked cohort, EEN vs no-EEN.
- **Infection composite** (primary): treated positive culture from blood /
  abdominal / respiratory / wound (excludes urine-only), with systemic antibiotic
  in [−1d, +2d]; contaminant organisms excluded.
- **Leak/reoperation** (key secondary safety): exploratory relaparotomy
  (`541` ICD-9 / `0WJG` ICD-10) 3–14 days after the index major abdominal op.
  Adhesiolysis `545` excluded (proxies SBO, not leak).
- **Covariates (0–24h fixed window)**: age, sex, emergency, site (upper/lower/HPB),
  stoma, exploratory index op, #major procedures, lactate/creatinine/WBC max +
  platelet/bilirubin (min/max), vasopressor, MV, diabetes, CKD, cirrhosis; **full
  SOFA set** (GCS, MAP, FiO2, PaO2) + BMI via `sofa_covariates.csv` (coverage
  GCS 99.5% / MAP 99.1% / FiO2 63.3% / PaO2 70.0% / BMI 67.0%, median-imputed).

## Headline results (full-SOFA covariates; final, post-landmark-fix)

- **Landmark fix (2026-10-17)**: the 48-h landmark now additionally requires
  hospital `deathtime > intime + 48h`; 5 patients with delayed ICU `outtime` but
  death ≤48h are excluded. Landmarked cohort 1663 → **1658** (EEN 192 / late 346 /
  never 1120). All numbers below are from the re-run pipeline.

- **Comparison A** (timing, n=538): infection composite — EEN protective and
  significant (OW OR 0.60, 95% CI 0.39–0.93; OW RR 0.73 [0.55–0.97]; OW p=0.023,
  below the Bonferroni α=0.025; crude 0.40; IPTW 0.68; PSM 0.33).
  Treated BSI null (OW 0.79, 0.31–1.99). In-hospital death null (OW 1.48, 0.87–2.53).
- **Comparison B** (policy, n=1658): infection composite null (OW OR 1.34, 0.93–1.95;
  OW RR 1.24; OW p=0.118; IPTW 1.76); in-hospital death OW 1.69 (1.08–2.65, RR 1.56,
  p=0.023), IPTW 2.32 — consistent with never-group confounding (healthy
  oral-recovery patients dilute the no-EEN arm), not causal harm.
- **PS-trimming sensitivity (PS∈[0.1,0.9], prespecified §8.10)**: B's "harm"
  signals vanish — after dropping 1154 extreme-PS patients (69.6%), infection OW
  1.34→1.01 (0.60–1.69) and death OW 1.69→1.25 (0.63–2.47). A's protection is
  preserved in direction (OW 0.64, 0.40–1.00; PSM 0.52 [0.29–0.95] significant).
  IPTW balance under full SOFA is poor (B main max|SMD| 0.149, trim 0.170),
  reinforcing OW (exact balance) as primary.
- **Threshold sensitivity (24/48/72h, landmark-linked, prespecified §8.1)**: A's
  protection is a gradient (infection OW OR 0.88 → 0.60 → 0.49; 48h & 72h significant)
  — not a 48h artifact. B's "harm" is maximal at 24h and vanishes by 72h (death OW
  2.54 → 1.69 → 1.17; infection 1.76 → 1.34 → 1.04) — the signature of never-group
  confounding. See `threshold_sensitivity.md`.
- **Never group** is heterogeneous: died 11.3% / therapeutic NPO 18.8% / oral
  recovery 69.8%.
- **Balance**: OW achieves exact covariate balance (max |SMD| 0.000); IPTW max
  |SMD| 0.087 (A) / 0.149 (B) — the latter motivates the PS-trimming sensitivity.
- **Full-SOFA covariates** (GCS/MAP/FiO2/PaO2/BMI) are now the primary covariate set
  (§6). Adding them attenuated Comparison A infection OW from 0.53 (reduced core set)
  to 0.60 (0.39–0.93), still protective and significant — the expected attenuation once
  the late arm's greater severity is better captured. B's harm signals unchanged
  (infection OW 1.34, death OW 1.69). B's IPTW balance worsens with more covariates
  (trimmed max|SMD| 0.170), reinforcing OW as primary. See `protocol.md §12.3`.
- **Remaining sensitivities (§12.4, `07_sensitivities.py`)**: all confirm the
  primary finding. Comparison A infection composite OW is stable at 0.58–0.61
  across feeding definitions (any 0.61 / rate≥20 0.58 / ONS 0.60) and 0.64
  (0.44–0.93) under ITT (first-48h feeding order); same-day-surgery subgroup keeps
  the direction (0.70, 0.37–1.31) but loses significance on reduced n (EEN 111);
  contaminant handling is immaterial (0.60). B's "harm" is constant across every
  definition (infection 1.30–1.56, death 1.50–1.78) — a confounding signature, not
  causal. See `sensitivities.md`.
- **Strict-treated sensitivity (§8.6b/c, antibiotic course ≥3 and ≥5 days)**:
  requiring a minimum 3-day course attenuates Comparison A from OW 0.60 to 0.75
  (0.46–1.20), and a ≥5-day course gives 0.66 (0.38–1.16) — both preserve the
  protective direction with overlapping CIs (no monotonic attenuation); B is
  unchanged (1.36 / 1.29). RR and RD are reported alongside OR because ORs are not
  collapsible; PSM (conditional, 126/192 matched pairs) is demoted to Table S4/S5.
  See `results.md` and `sensitivities.md`.
- **Upper-GI exclusion & stratification (`10_reviewer_diagnostics.py`)**: the
  protective association is **not** an artifact of the upper-GI/jejunostomy channel.
  Excluding upper-GI surgery leaves Comparison A essentially unchanged in direction
  (OW 0.63, 0.36–1.10; n drops 538→351) and stratification is homogeneous (upper-GI
  0.58 vs non-upper-GI 0.63). Upper-GI surgery remains the largest measured
  covariate imbalance (SMD 0.807 vs late, 1.020 vs no-EEN). See
  `upper_gi_sensitivity.md`.
- **PSM diagnostics (`10_reviewer_diagnostics.py`)**: Comparison A PSM matches only
  126/192 (65.6%) of the EEN arm (34% dropped for lack of a caliper-matched control)
  and is driven by 54 discordant pairs (b=13/c=41), so its larger apparent effect
  (OR 0.33 vs marginal 0.60) reflects the conditional estimand + non-collapsibility,
  not greater precision; it is stable across calipers 0.05–0.3 (0.39/0.33/0.33/0.36).
  See `psm_diagnostics.md`.
- **Landmark report + competing risk (§12.5, `08_competing_risk.py`)**: wide cohort
  3246 → died ≤48h 117 (3.6%), ICU-discharged ≤48h 1471 (45.3%), landmarked 1658
  (51.1%). Death competing-risk (discharge = competing, 28-day) is consistent with
  the main analysis: Comparison A 28-day death CIF 13.5% vs 14.5%, Fine-Gray SHR
  1.33 (0.61–2.90) — null; Comparison B 13.5% vs 10.8%, SHR 1.62 (0.81–3.24) —
  harm signal, still consistent with never-group confounding. Only 38/223 deaths
  occur after 28 days. See `competing_risk.md`.
- **Figures (`09_figures.py`, `11_reviewer_figures.py`)**: `09` renders Fig 1 flow,
  Fig 2 forest (now including strict-treated ≥3/≥5-day rows), Fig 3 death CIF; `11`
  renders the reviewer-requested Fig 4 PS overlap, Fig 5 Love plot, Fig 6 threshold
  dose-response gradient, Fig 7 estimand schematic, plus supplement Fig S1
  (feeding-time distribution), S2 (never-fed dissection), S3 (composite site
  decomposition — respiratory dominates, EEN 41/54 events; blood count 8 = treated
  BSI 8), S4 (infection CIF: EEN 28.1% / late 49.4% / never 15.0%, matching the
  crude composite proportions). Both scripts were regenerated after correcting
  stale pre-landmark-fix numbers in Fig 1/2 (landmarked 1663→1658, EEN 193→192,
  never 1124→1120, never-died 467→127; threshold 0.86/0.45→0.88/0.49).
- **Negative control + AIPW + missing data (`13_causal_hardening.py`, 2026-10-18)**: the
  treated-urinary-tract-infection negative control (same definition as the primary
  composite but urine-only) passes the falsification check — in comparison A its crude
  protective association (OR 0.56) is fully attenuated on adjustment (OW 0.88, AIPW 0.80)
  while the infection composite stays protective (OW 0.60), and in comparison B it
  reproduces the primary outcome's "harm" pattern (IPTW/AIPW ≈1.80/1.81), corroborating
  that B's harm is never-fed confounding. Doubly-robust AIPW preserves the direction of
  the comparison-A protective estimate (RR 0.83, 0.63–1.09) with a wider CI that crosses
  1, underscoring the imprecision of the estimate. Missingness is ≤1.1% for age/procs/
  creatinine/WBC/platelets/GCS/MAP, 19–38% for bilirubin/BMI/FiO2/lactate/PaO2; the
  complete-case sensitivity is severely underpowered (A n=170, 14 EEN events). See
  `negative_control.md` and `missing_data.md`.
- **MIMIC-III replication (`14_mimic3_replication.py`, 2026-10-18)**: same-center, earlier-era
  (BIDMC 2001–2012) temporal sensitivity, NOT external validation. Comparison A replicates the
  primary direction almost exactly — infection composite OW OR 0.58 (0.42–0.82, p=0.002) vs
  MIMIC-IV 0.60 (0.39–0.93); cohort 3590→2498 landmarked (EEN 272/late 406/never 1820). Honest
  caveat: the treated-UTI negative control attenuates only incompletely in MIMIC-III (OW 0.67,
  0.45–1.00, p=0.048) even with the full chart-based SOFA set (GCS/MAP/FiO2/PaO2, coverage 78–99%),
  unlike MIMIC-IV (0.88); the CIs overlap, so not a formal contradiction, but specificity does not
  cleanly replicate across eras and residual confounding cannot be fully excluded. See
  `mimic3_replication.md` and `figures/fig8_replication_forest.png`.
- **eICU supportive (`15_eicu_replication.py`, 2026-10-18)**: NOT a validation. Cohort
  4578 → 2128 landmarked (EEN 159 / late 97 / never 1872). Among documented-fed patients the
  EEN/late structure reproduces MIMIC (62% EEN; first feed 13 h vs 95 h), but the absolute
  feeding rate is far lower (12% fed vs MIMIC-IV 32%) — intakeOutput under-ascertainment, so
  the eICU "never" group is not comparable. In-hospital death is null (A OW 0.88 [0.37–2.09],
  B OW 0.82 [0.46–1.45]), consistent with MIMIC's null death endpoint; the infection composite
  cannot be reproduced (microLab 145 KB). Cross-database harmonization is in
  `three_db_harmonization.md`.

## Re-run

```
python analysis/01_build_dataset.py   # ~minutes (scans labevents/inputevents)
python analysis/02_weighting.py
python analysis/03_tables.py
```

Requires: `duckdb`, `pandas`, `numpy`, `statsmodels`.
