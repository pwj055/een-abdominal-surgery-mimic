# RECORD Statement — Checklist of items (extension for studies using routinely-collected health data)

Complements the STROBE checklist (same item numbering); RECORD-only items are suffixed `.x`.

| Item | RECORD checklist item | Reported |
|---|---|---|
| 1.1 | Methods used to assess the extent to which the study population was representative of the target population | §2.3, §3.1 (all eligible surgical-ICU stays in MIMIC-IV v3.1 at a single center); §4 Limitations (single-center generalizability). |
| 1.2 | Methods used to assess the extent to which the data were complete | §2.6 (per-covariate missingness ≤1.1% to 37.5%), Supplement Table S9. |
| 1.3 | If linkages were performed, describe the methods and any validation | Not applicable beyond native MIMIC-IV relational tables (linked by `subject_id`/`hadm_id`/`stay_id`); §2.2. |
| 6.1 | List the codes and algorithms used to classify exposures, outcomes, confounders, and effect modifiers | §2.4 (feeding itemids in `Nutrition - Enteral` category, Table S2), §2.5 (culture-site mapping, antibiotic list, contaminant list), §2.6 (ICD-9-PCS/ICD-10-PCS procedure codes, Table S7). |
| 6.2 | List the codes used to classify inclusion/exclusion criteria | §2.3 (major-abdominal-procedure ICD-9-PCS/ICD-10-PCS list, Table S7). |
| 6.3 | Describe any validation of the codes/algorithms against an external or gold standard | §4 Limitations (culture-based endpoint not chart-validated; treated-infection is a proxy; leak/reoperation ICD coding is non-specific and mitigated by exploratory-relaparotomy window). |
| 7.1 | Describe methods of data linkage across databases | §2.2 (native MIMIC-IV relational schema; no external linkage). |
| 12.1 | Describe the extent to which the investigators had access to the raw data | §2.2, Declarations (MIMIC-IV via credentialed PhysioNet DUA). |
| 12.2 | Provide information on access to the population and statistical code | Declarations (code available from the corresponding author on request; PhysioNet for data). |
| 13.1 | Describe the cleaning of the data, including any changes made | §2.3–2.5 and the analysis pipeline (analysis/README.md): landmark requires survival to 48 h; contaminants excluded; urine excluded from the primary composite; exploratory relaparotomy excluding adhesiolysis. |
| 19.1 | Discuss the generalizability of the results to other populations | §4 Limitations (single US tertiary center; upper-GI/jejunostomy feeding practice; external eICU replication not yet available). |
| 22.1 | Provide sources of funding and the role of funders | Declarations. |
