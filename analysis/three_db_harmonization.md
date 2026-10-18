# Three-database harmonization (MIMIC-IV · MIMIC-III · eICU-CRD)

Purpose of the multi-database design: MIMIC-IV is the **primary** analysis;
MIMIC-III is a **same-center, earlier-era temporal replication** (same hospital
BIDMC, 2001–2012 vs 2008–2019 — NOT an external validation); eICU-CRD is
**supportive multicenter triangulation** of the feeding-exposure structure and of
the death/LOS endpoints only (its microLab table is too sparse to reproduce the
treated-culture infection composite, and it has no procedure-code table).

| Dimension | MIMIC-IV v3.1 (primary) | MIMIC-III v1.4 (temporal replication) | eICU-CRD v2.0 (supportive) |
|---|---|---|---|
| Centers / era | 1 (BIDMC), 2008–2019 | 1 (BIDMC), 2001–2012 | 208 US hospitals, 2014–2015 |
| Surgery identification | ICD-9/10 **procedure** codes (major abdominal, 42–54 + equivalents), with procedure date | ICD-9 **procedure** codes (no date → surgery-before-ICU filter dropped) | APACHE admission diagnosis **"surgery for …" labels** (proxy; no procedure table) |
| Time zero | ICU `intime` | ICU `intime` | ICU admission (offset 0) |
| 48-h landmark | ICU LOS ≥ 48 h **and** survival to 48 h | same | ICU stay ≥ 48 h (`unitdischargeoffset` ≥ 2880) |
| EN exposure | `inputevents` category "Nutrition – Enteral" (rate ≥ 10 or amount ≥ 20); first feed ≤ 48 h = EEN | same itemid logic (carevue + metavision) | `intakeOutput` tube/enteral cells (label classifier); first feed ≤ 48 h = EEN |
| Infection composite (primary) | treated positive culture (blood/abdo/resp/wound) + antibiotic [−1 d,+2 d], > 48 h & < 28 d | reproduced | **not reproducible** (microLab 145 KB) |
| Negative control (treated UTI) | reproduced | reproduced | not reproducible |
| Key covariates | age, sex, emergency, site, stoma, exploratory, #procedures, lactate/creat/WBC/plt/bili, vasopressor, MV, diabetes/CKD/cirrhosis, **full SOFA + BMI** | same + **chart-based SOFA** (GCS/MAP/FiO₂/PaO₂; BMI omitted) | **admission-level minimal set**: age, sex, elective, APACHE score, day-1 MV, diabetes, cirrhosis, immunosuppression |
| Ventilation | CHARTEVENTS mode | CHARTEVENTS 720/223849 | `apachePredVar.ventday1` / `actualventdays` |
| Primary estimate (A, infection, OW) | OR 0.60 (0.39–0.93) | OR 0.58 (0.42–0.82) | n/a |
| Negative control (A, UTI, OW) | OR 0.88 (0.49–1.60) — nulls | OR 0.67 (0.45–1.00) — only partially nulls | n/a |
| Death (A, OW) | OR 1.48 (0.87–2.53) | — | OR 0.88 (0.37–2.09) — null |
| Role | primary causal estimate | external-consistency check (time) | feeding-structure / death-LOS consistency (geography) |
| Main limitation | single center | overlapping years; no procedure date; BMI missing | proxy surgery; sparse microbiology; feeding under-ascertainment |

## Bias-direction note (per database)

- **MIMIC-III vs MIMIC-IV**: identical exposure/outcome definitions give nearly
  identical infection-composite estimates (0.58 vs 0.60) — strong evidence the
  primary finding is not an artifact of the ICD-10/meta era. The one asymmetry is
  the treated-UTI negative control, which nulls in IV but only partially in III
  (0.88 vs 0.67; CIs overlap) — residual confounding by general health status
  cannot be fully excluded, so we report this honestly rather than claiming clean
  specificity.
- **eICU**: feeding is documented only in a minority of stays (12% fed vs 32% in
  MIMIC-IV), so the eICU "never" group is under-ascertained and not comparable;
  only the **EEN-vs-late split among documented-fed patients** (62% EEN, 13 h vs
  95 h to first feed) is a valid cross-database check, and it reproduces MIMIC's
  structure. eICU death is null, consistent with MIMIC's null death endpoint.
