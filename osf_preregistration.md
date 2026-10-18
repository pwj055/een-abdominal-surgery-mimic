# OSF 预注册文本（可直接粘贴）

> 说明（给作者，不要贴进 OSF）：
> - 这是按 OSF「OSF Preregistration」表单字段填好的英文正文，逐条复制即可。
> - **时间诚实性**：OSF 会在你点击 register 的那一刻打时间戳（今天是 2026-10-18，晚于分析完成）。所以这是「注册版 protocol」（registered protocol），**不是**「前瞻性预注册」。论文里写「registered at OSF [链接]（注册于 2026-10-18）」即可，不要写「prospectively preregistered」。可补充一句「分析计划本身在拟合前已冻结（protocol.md 定稿于 2026-10-16）」——这是事实，因为 protocol 是先锁再跑的。
> - 可选：把 `protocol.md` 一并上传到该项目，作为完整 protocol 的载体。

---

## Study Information

**Title.** Early versus late enteral nutrition after major abdominal surgery in the intensive care unit: a target-trial emulation using MIMIC-IV (with same-center temporal replication in MIMIC-III and supportive multicenter triangulation in eICU-CRD).

**Authors.** [填写]

**Research questions.** Among adults admitted to the ICU after major abdominal surgery who survive to 48 hours and remain in the ICU for at least 48 hours, (A) does initiation of enteral nutrition within 48 hours of ICU admission (early enteral nutrition, EEN), compared with later initiation among patients who are eventually fed, reduce the 28-day incidence of antibiotic-treated infection; and (B) does EEN, compared with no early enteral nutrition in the full landmarked cohort, affect treated infection and in-hospital mortality?

**Hypotheses.** (A) EEN is associated with a lower incidence of antibiotic-treated infection than late enteral nutrition (directional, protective). (B) In the full-cohort policy comparison, no infection benefit is expected and any apparent mortality increase is attributed to confounding by the heterogeneous never-fed subgroup (patients who recover and resume oral intake vs those who die or require therapeutic nil-per-os) rather than to a causal effect.

## Sampling Plan

**Existing data.** Retrospective secondary analysis of three de-identified critical-care databases accessed under credentialed PhysioNet data-use agreements: MIMIC-IV v3.1 (primary analysis, Beth Israel Deaconess Medical Center, 2008–2019), MIMIC-III v1.4 (same-center temporal replication, 2001–2012), and eICU-CRD v2.0 (supportive multicenter triangulation, 208 US hospitals, 2014–2015). No data were collected for this study.

**Study population.** First ICU stay of adult patients with a major abdominal procedure (esophageal, gastric, small-/large-intestinal, hepatobiliary, or pancreatic resection or reconstruction) recorded on or before the ICU admission day. We require ICU length of stay ≥ 48 hours and survival to 48 hours (the 48-hour landmark) to define the feeding window without immortal-time bias. We exclude patients with a prior surgical-ICU stay and patients who died within 48 hours of ICU admission.

**Sample size.** All eligible patients are used (no a priori power calculation; this is an observational study of an existing database). The landmarked MIMIC-IV cohort is n = 1658 (EEN 192, late EN 346, never fed 1120).

## Variables

**Exposure.** First enteral-nutrition record (input-events items in the `Nutrition - Enteral` category, 112 frozen item IDs) with infusion rate ≥ 10 mL/h or volume ≥ 20 mL. EEN = first feed ≤ 48 h from ICU admission; late EN = first feed > 48 h; never fed = no feed during the ICU stay.

**Primary outcome.** Antibiotic-treated infection composite within 28 days and after 48 h: a positive culture from blood, abdominal, respiratory, or wound sites with a systemic antibiotic started in [−1 day, +2 days]; urine-only cultures, contaminant organisms, and cultures before 48 h are excluded.

**Negative-control outcome.** Antibiotic-treated urinary-tract infection (same definition restricted to urine cultures).

**Key secondary outcomes.** Treated bloodstream infection; anastomotic leak/reoperation (exploratory relaparotomy 3–14 days after the index operation, excluding adhesiolysis); in-hospital death.

**Covariates (0–24 h after ICU admission, fixed window).** Age, sex, emergency status, surgical site (upper / lower / hepatobiliary / other), stoma creation, exploratory laparotomy at index, number of major procedures; maximum lactate, creatinine, white-cell count, bilirubin; minimum platelet, Glasgow Coma Scale, mean arterial pressure; maximum FiO₂; minimum PaO₂; body-mass index; vasopressor receipt; mechanical ventilation; diabetes, chronic kidney disease, cirrhosis.

## Design Plan

**Study type.** Observational, retrospective target-trial emulation. Time zero = ICU admission; follow-up from the 48-hour landmark to 28 days (outcomes left-truncated at 48 h).

**Two co-primary comparisons.** (A) EEN vs late EN among eventually-fed patients (a principal-stratum / timing estimand, n = 538); (B) EEN vs no early EN in the full landmarked cohort (a policy estimand, n = 1658).

## Analysis Plan

**Statistical models.** Propensity score for EEN estimated by logistic regression on the full covariate set. Primary estimator = overlap weighting (treated weight 1−PS, control weight PS). Triangulation with stabilized and 1st/99th-percentile-truncated inverse-probability-of-treatment weighting, 1:1 propensity-score matching (caliper 0.2 SD of the logit PS), and doubly-robust augmented inverse-probability weighting. Treatment effects estimated with generalized estimating equations (independence working correlation, robust sandwich standard errors): odds ratios (weighted binomial-logit), risk ratios (weighted modified-Poisson log-link), and risk differences (weighted Gaussian-identity). Balance reported as weighted standardized mean differences and effective sample size.

**Inference criteria.** Two-sided Wald p-values; the two co-primary comparisons are judged against a Bonferroni-corrected α = 0.025. Point and 95% confidence-interval E-values are reported for the primary comparison-A estimate.

**Missing data.** Continuous covariates median-imputed with a missingness indicator for lactate; a complete-case sensitivity is reported for transparency.

**Sensitivity analyses (prespecified).** Feeding threshold at 24 and 72 h with the landmark synchronized; alternative feeding definitions (any record; rate ≥ 20 mL/h; oral-nutrition-supplement-inclusive); same-day-surgery subgroup; intention-to-treat exposure using the first-48-h feeding order; treated bloodstream infection with and without contaminant exclusion; stricter treated-infection definitions requiring ≥ 3- and ≥ 5-day antibiotic courses; overlap trimming to PS ∈ [0.1, 0.9]; death modeled with discharge as a competing risk (Fine–Gray); a treated-urinary-tract-infection negative control.

**Replication (external-consistency checks).** Same-center temporal replication in MIMIC-III (identical exposure/outcome definitions); supportive multicenter triangulation of the feeding-exposure structure and death/length-of-stay in eICU-CRD (its microbiology table is too sparse to reproduce the primary endpoint, and it has no procedure table).

## Other

Any deviations from this plan will be reported explicitly in the manuscript and flagged as exploratory.
