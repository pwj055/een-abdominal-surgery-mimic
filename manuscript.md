# Early versus Late Enteral Nutrition and Infectious Complications after Major Abdominal Surgery in the Intensive Care Unit: A Target Trial Emulation Using MIMIC-IV

*Draft manuscript — for journal submission. All numbers are drawn verbatim from `analysis/` (results.md, table1.md, sensitivities.md, competing_risk.md). Placeholder fields (authors, affiliations, funding, data-access statement wording) are marked `[ ]`.*

---

## Title page

**Title.** Early versus Late Enteral Nutrition and Infectious Complications after Major Abdominal Surgery in the Intensive Care Unit: A Target Trial Emulation Using MIMIC-IV

**Short running title.** Early enteral nutrition after abdominal surgery

**Authors.** [ ]

**Affiliations.** [ ]

**Corresponding author.** [ ]

**Word count.** [ ]

**Key words.** enteral nutrition; abdominal surgery; intensive care unit; infection; target trial emulation; overlap weighting

---

## Abstract

**Background.** The optimal timing of enteral nutrition (EN) after major abdominal surgery in the intensive care unit (ICU) is uncertain: early feeding may reduce infections but is often withheld for fear of anastomotic leak or ileus.

**Methods.** We emulated a target trial of early versus delayed EN using MIMIC-IV v3.1, among adults with major abdominal surgery and an ICU stay ≥48 h. Early EN (EEN) was a first tube feed within 48 h of ICU admission; patients fed later formed the late-EN group. We prespecified two co-primary comparisons: (A) EEN versus late EN among those ultimately fed (a timing effect conditional on the ultimately-fed stratum, not intention-to-treat; n=538) and (B) EEN versus no early EN in the full landmarked cohort (a policy effect; n=1658). The primary outcome was in-hospital treated infection, defined as a composite of non-urine positive cultures accompanied by systemic antibiotics, within 28 days. We used overlap weighting (primary), inverse-probability weighting, augmented inverse-probability weighting, and propensity-score matching.

**Results.** Among 1658 landmarked patients, 192 (11.6%) were EEN, 346 (20.9%) late EN, and 1120 (67.6%) never fed. In comparison A, infection occurred in 54/192 (28.1%) EEN and 171/346 (49.4%) late-EN patients; after overlap weighting EEN was associated with lower infection risk (odds ratio 0.60, 95% CI 0.39–0.93; risk ratio 0.73, 95% CI 0.55–0.97), replicated in MIMIC-III (OR 0.58, 95% CI 0.42–0.82; same-center, earlier era). In comparison B, infection risk was similar (weighted OR 1.34, 0.93–1.95). In-hospital mortality was not reduced; comparison A was null (OR 1.48, 0.87–2.53) and comparison B showed a higher weighted mortality estimate (OR 1.69, 1.08–2.65) interpreted as confounding rather than harm. A treated-urinary-infection negative-control outcome was null after adjustment in comparison A but reproduced the policy comparison's harm pattern, corroborating confounding. Comparison A was stable across threshold, feeding-definition, intention-to-treat, and competing-risk sensitivity analyses.

**Conclusions.** Among patients who ultimately received enteral nutrition, earlier initiation was associated with fewer antibiotic-treated infections — a conditional timing effect, not intention-to-treat, with robust direction but imprecise magnitude. The full-cohort harm signal is consistent with never-fed confounding and should not be interpreted causally.

---

## 1. Introduction

Nutritional support is a cornerstone of critical care, but the optimal timing of enteral nutrition (EN) after major abdominal surgery remains unsettled [1–3]. Early EN is advocated by major society guidelines [4–6], largely on the basis of trials conducted in medical and mixed ICUs; however, abdominal-surgery patients are frequently excluded from such trials or treated conservatively because of concern that early feeding precipitates anastomotic leak, ileus, or pneumonia from aspiration. As a result, current practice is highly variable, and observational studies of early EN in this population are prone to strong confounding by indication: patients selected for early feeding differ systematically from those in whom feeding is deferred.

Two distinct clinical questions are routinely conflated. The first is a *timing* question: among patients who will ultimately receive enteral nutrition, does starting within 48 hours rather than later reduce infectious complications? The second is a *policy* question: does a strategy of feeding all eligible patients early, compared with usual care (in which many patients are never fed by tube), improve outcomes? These questions target different populations and different causal estimands, and a single "early vs. late" comparison cannot answer both.

We used the Medical Information Mart for Intensive Care (MIMIC-IV) to emulate a target trial of early EN after major abdominal surgery, specifying two parallel, prespecified co-primary comparisons that separate the timing estimand from the policy estimand. We focused on a single primary endpoint — a composite of treated positive cultures — because infectious complications are the biologically plausible mechanism by which early feeding is thought to benefit surgical ICU patients, and because they are common enough to be estimable in this dataset. We used overlap weighting as the primary method, with inverse-probability weighting and propensity-score matching as triangulation, and an extensive prespecified sensitivity analysis program.

## 2. Methods

### 2.1 Study design and target-trial specification

We used the target-trial-emulation framework [7] to make explicit the causal question, and we declared the estimand before analysis. The protocol, including all outcome definitions, covariate sets, and sensitivity analyses, was finalized before model fitting (Supplement). The protocol and analysis plan are registered at OSF (https://osf.io/g39vw; DOI 10.17605/OSF.IO/G39VW). Because MIMIC-IV has been publicly available for several years, true prospective preregistration (prior to any investigator exposure to the data) is not feasible; the OSF entry represents a time-stamped analysis plan finalized before outcome modeling, following recommended practice for secondary-database studies. Table S1 maps each component of the target trial to its emulation. This study is reported in accordance with the STROBE statement for cohort studies and its RECORD extension for studies using routinely collected health data (Additional Files 1 and 2).

| Target-trial component | Emulation |
|---|---|
| Eligibility | Adults with major abdominal surgery admitted to a surgical ICU, with ICU length of stay ≥48 h |
| Treatment strategies | (1) start tube EN within 48 h of ICU admission; (2) defer tube EN beyond 48 h |
| Time zero | ICU admission |
| Assignment | Randomization | Emulated by adjustment for baseline covariates (overlap weighting) |
| Follow-up | From the 48-h landmark to 28 days after ICU admission, hospital discharge, or death (whichever occurred first); outcomes were left-truncated at 48 h |
| Primary outcome | In-hospital treated infection composite after the 48-h landmark and within 28 days of ICU admission |
| Causal contrasts | (A) timing effect among the eventually-fed; (B) policy effect of an early-feeding strategy |

We prespecified two co-primary comparisons. **Comparison A (timing)** restricted to patients who received tube EN at any time during their ICU stay and compared EEN (first feed ≤48 h) with late EN (first feed >48 h). Because "eventually fed" is a post-baseline trajectory, this contrast is a principal-stratum (survivor-average-causal-effect) estimand [8] rather than intention-to-treat: it estimates the effect of early versus late feeding *within the subpopulation who are ultimately fed*. **Comparison B (policy)** compared EEN with no-EEN-by-48-h in the full landmarked cohort, a policy (intention-to-treat-like) estimand. The never-fed group was characterized descriptively but was not treated as a homogeneous comparator.

We used a 48-h landmark design to avoid immortal-time (guarantee-time) bias [9] and to align time zero across the compared strategies; the landmark excludes patients who died or were discharged before 48 h (reported transparently in Figure 1). Clone–censor–weight approaches are a more general alternative suited to dynamic or time-varying feeding decisions, and we note them as a direction for methodological follow-up work [10]; as a pragmatic check within the landmark design, a sensitivity deferring the outcome window start to 72 h is reported in the Supplement (Table S13).

### 2.2 Data source

MIMIC-IV v3.1 [11] is a single-center database of de-identified electronic health records for patients admitted to Beth Israel Deaconess Medical Center, Boston, USA. Use was approved under the PhysioNet data-use agreement (certificate number [ ]). Analyses were performed with Python (duckdb, pandas, statsmodels).

### 2.3 Cohort

We identified first surgical-ICU stays (SICU, Trauma SICU, MICU/SICU, Neuro SICU) with a major abdominal procedure (ICD-9-PCS / ICD-10-PCS codes for esophageal, gastric, intestinal, hepatobiliary, or pancreatic resection or reconstruction; Supplement) dated on or before the ICU admission day. We required ICU length of stay ≥48 h to define the 48-h feeding window without immortal-time bias, and we additionally required survival to 48 h (patients whose hospital death time preceded the landmark were excluded). We excluded patients with a prior surgical-ICU stay. The never-fed subgroup was described in three mutually exclusive categories — in-hospital death (death time recorded in the indexed hospital admission), therapeutic nil-per-os with ileus/obstruction (ICD-9 `560` / ICD-10 `K56`), and presumptive oral recovery (the remainder).

### 2.4 Exposure

Enteral feeding was identified from the input-events table using the 112 items in the `Nutrition - Enteral` category (frozen item list in the Supplement; this category — not keyword matching — avoids misclassifying parenteral-nutrition items). The primary definition of feeding initiation was the first record with infusion rate ≥10 mL/h or volume ≥20 mL. EEN was defined as first feed ≤48 h from ICU admission; late EN as first feed >48 h; never-fed as no feed during the ICU stay.

### 2.5 Outcomes

The **primary outcome** was in-hospital treated infection within 28 days of ICU admission, defined as a composite of positive cultures associated with systemic antibiotic treatment (a proxy for clinically treated infection) occurring after the 48-h landmark (events in the first 48 h were excluded to avoid reverse causation): a positive blood, abdominal (peritoneal/ascites/bile/abscess/drain), respiratory (sputum/tracheal/BAL), or wound/swab culture, with a systemic antibiotic prescribed in the window −1 day to +2 days around the culture. Urine cultures and culture-negative results were excluded, as were likely contaminants (coagulase-negative staphylococci, *Corynebacterium*, *Micrococcus*, *Bacillus*, viridans streptococci, diphtheroids). Because the composite is a proxy for clinically treated infection, we checked its face validity by cross-tabulating it against ICD-coded infection/sepsis diagnoses recorded during the admission (Supplement Table S15). **Key secondary outcomes** were treated bloodstream infection (the blood-culture component alone, the most specific layer), anastomotic leak/reoperation (an exploratory relaparotomy — ICD-9-PCS 54.1 (stored without a decimal as `541`) / ICD-10-PCS `0WJG…` — 3–14 days after the index procedure, excluding adhesiolysis 54.5 (stored as `545`) as a proxy for bowel obstruction rather than leak), and in-hospital death (assessed through hospital discharge). We additionally report ICU and hospital length of stay. The primary infection outcome was capped at 28 days because cultures are only observable during hospitalization; death was assessed through hospital discharge, but only 38 of the 223 landmarked deaths (17%) occurred beyond 28 days, and 28-day mortality was additionally examined in the competing-risk sensitivity. As a negative-control (falsification) outcome [12], we additionally defined treated urinary-tract infection — a positive urine culture with a systemic antibiotic in the same [−1 d, +2 d] window, under the same >48-h/<28-d and contaminant-exclusion rules as the primary composite. Urine was chosen because early enteral feeding has no plausible mechanism by which it should reduce urinary infection; an association that attenuates to the null on adjustment would support the adequacy of confounding control, whereas a persisting association would signal residual confounding.

### 2.6 Covariates

Covariates were measured in the fixed 0–24 h window after ICU admission to avoid post-exposure adjustment. They comprised demographics (age, sex), admission and surgery characteristics (emergency status, surgical site [upper/lower/hepatobiliary/other], stoma creation, exploratory laparotomy at index, number of major procedures), physiology and organ function (maximum lactate, creatinine, white-cell count, bilirubin; minimum platelet, Glasgow Coma Scale, mean arterial pressure; maximum FiO₂; minimum PaO₂), vasopressor receipt, mechanical ventilation, and comorbidities (diabetes, chronic kidney disease, cirrhosis). Body-mass index (from recorded height and weight, a fixed characteristic not tied to the 0–24-h window) was included separately. Continuous covariates were median-imputed with a missingness indicator for lactate. Because several laboratories had substantial missingness, single median imputation (rather than complete-case analysis) was used primarily to preserve cohort size and avoid selection; a sensitivity additionally assigning a missingness indicator to every variable with >10% missingness is reported alongside the complete-case results (Supplement Table S9). As a further robustness check, the five covariates with >10% missingness (bilirubin, body-mass index, FiO₂, lactate, PaO₂) were multiply imputed by chained equations (m=25 imputations, 15 iterations, linear 'norm' models, with the exposure and outcome included in the imputation model) and estimates pooled across imputations by Rubin's rules (Supplement Table S14). Missingness was ≤1.1% for age, number of procedures, creatinine, white-cell count, platelets, Glasgow Coma Scale, and mean arterial pressure, but appreciable for bilirubin (37.5%), body-mass index (33.8%), FiO₂ (25.8%), lactate (22.6%), and PaO₂ (19.1%); a complete-case sensitivity was therefore limited by attrition and is reported for transparency (Supplement Table S9).

### 2.7 Statistical analysis

Baseline characteristics were summarized by feeding group, with standardized mean differences (SMD). For each co-primary comparison we fit a propensity-score (PS) model [13] for EEN using the full covariate set. The **primary estimator was overlap weighting** [14] (treated weight 1−PS, control weight PS), which targets the overlap population (the region of greatest clinical equipoise), where covariate balance is expected to be excellent; balance was verified with weighted standardized mean differences; stabilized and 1st/99th-percentile-truncated inverse-probability-of-treatment weighting [15] and 1:1 propensity-score matching (caliper of 0.2 SD of the logit propensity score, the standard shown to remove most measured confounding [16]) served as triangulation. As a doubly-robust check, we additionally estimated marginal risk differences and risk ratios with augmented inverse-probability weighting [17], which combines the propensity-score and outcome models and is consistent if either is correctly specified. Treatment effects were estimated with generalized estimating equations (independence working correlation, robust sandwich standard errors): odds ratios from a weighted binomial-logit model, risk ratios from a weighted modified-Poisson (log-link) model [18], and risk differences from a weighted Gaussian-identity model. Because the primary outcome was common, odds ratios may overstate relative effects, so risk ratios and risk differences are reported alongside them. We report weighted SMD and effective sample size for each method, and assessed the positivity assumption by inspecting the propensity-score overlap (Figure 4) and effective sample size (Supplement).

Because we specified a single primary endpoint across two co-primary comparisons, statistical significance was assessed at a Bonferroni-corrected two-sided α = 0.025 per comparison; 95% confidence intervals are reported throughout for descriptive comparability across methods, with two-sided Wald p-values reported for the primary estimates. Odds ratios are not collapsible, so the propensity-score-matched (conditional) odds ratios are not directly comparable in magnitude to the overlap-weighted and inverse-probability-weighted (marginal) odds ratios; the risk ratio and risk difference, which are collapsible, provide the method-to-method comparability. All analyses were performed in the 48-h landmarked cohort.

**Sensitivity analyses** (prespecified): (1) feeding threshold at 24 and 72 h with the landmark synchronized to the threshold; (2) alternative feeding definitions (any record; rate ≥20 mL/h; ONS-inclusive); (3) same-day-surgery subgroup; (4) intention-to-treat exposure using the first-48-h feeding order (rather than administered feed); (5) treated-bloodstream-infection with and without contaminant exclusion; (6) stricter treated-infection definitions requiring minimum antibiotic courses of 3 and 5 days, to exclude brief perioperative prophylaxis; (7) overlap trimming to PS ∈ [0.1, 0.9]; (8) death modeled with discharge as a competing risk (Fine–Gray subdistribution hazard) [19]; (9) a treated-urinary-tract-infection negative-control outcome [12]; (10) a same-center replication in an earlier era using MIMIC-III; (11) a supportive multicenter (eICU-CRD) triangulation of the feeding-exposure structure and death/length-of-stay; (12) a post-48-h reverse-causation sensitivity that defers the infection outcome window start from 48 h to 72 h while keeping the 48-h landmarked cohort; (13) a missingness-indicator sensitivity that adds an indicator for every covariate with >10% missingness; and (14) a multiple-imputation sensitivity (chained equations, m=25) for the covariates with >10% missingness, pooled by Rubin's rules. Analyses (1)–(9) were prespecified in the original OSF protocol; the MIMIC-III replication (10) and the eICU-CRD triangulation (11) were added as a protocol amendment (recorded in the OSF version history) in response to the need for temporal and multicenter robustness checks, and the reverse-causation (12), missingness-indicator (13), and multiple-imputation (14) sensitivities were added as post hoc analyses after protocol finalization (recorded in the OSF version history). The 48-h landmark was justified by reporting death/discharge within 48 h.

## 3. Results

### 3.1 Cohort

Of 3246 eligible patients, 1658 (51.1%) survived and remained in the ICU at 48 h and formed the landmarked cohort (Figure 1). Within 48 h, 117 (3.6%) died and 1471 (45.3%) were discharged from the ICU alive. Among the landmarked cohort, 192 (11.6%) were EEN, 346 (20.9%) late EN, and 1120 (67.6%) never fed.

The never-fed group was markedly heterogeneous (Supplement): 127 (11.3%) died during hospitalization, 211 (18.8%) had ileus/obstruction (therapeutic NPO), and 782 (69.8%) were classified as presumptive oral recovery.

### 3.2 Baseline characteristics

Table 1 shows baseline characteristics. In comparison A, late-EN patients were more severely ill than EEN patients — vasopressors 63.6% vs 31.8%, maximum lactate 4.2 vs 3.0 mmol/L, exploratory laparotomy 35.5% vs 15.6% — whereas EEN patients more often had upper-GI surgery (58.3% vs 21.7%), consistent with routine early jejunostomy feeding after esophageal/gastric resection. This pattern motivated the propensity-score adjustment.

### 3.3 Primary outcome

**Comparison A (EEN vs late EN).** The treated-infection composite occurred in 54/192 (28.1%) EEN and 171/346 (49.4%) late-EN patients (crude OR 0.40, 95% CI 0.27–0.58). After overlap weighting the association attenuated but remained protective (OR 0.60, 95% CI 0.39–0.93, p=0.023; RR 0.73, 0.55–0.97; risk difference −0.12, −0.22 to −0.02, corresponding to a number needed to treat of approximately 8 [range 5–50], derived from the risk-difference confidence interval and interpreted cautiously given its width); IPTW (OR 0.68, 0.42–1.09) was consistent, and PSM — a conditional estimate restricted to 126 matched pairs (65.6% of the EEN arm, 34% dropped for lack of a caliper-matched control) — was directionally consistent but larger in magnitude (OR 0.33, 0.18–0.60; Tables S4, S5). Overlap weighting achieved near-perfect measured covariate balance in comparison A (max |weighted SMD| <0.01; overlap-population effective sample size 154 treated / 222 control) and comparison B (max |weighted SMD| <0.01; effective sample size 181 / 640), versus raw max |SMD| of 0.81 and 1.02 dominated by upper-GI surgery (Figure 4, Figure 5).

**Comparison B (EEN vs no-EEN).** Infection risk was similar: 54/192 (28.1%) vs 339/1466 (23.1%); overlap-weighted OR 1.34 (0.93–1.95, p=0.118; RR 1.24, 0.95–1.62), IPTW 1.76 (1.15–2.70).

As a face-validity check of the primary endpoint, the composite was cross-tabulated against ICD-coded infection diagnoses recorded during the admission. Against ICD-coded any-site infection the composite showed high specificity (90.6%) and positive predictive value (81.2%) with modest sensitivity (36.8%); against ICD-coded sepsis/bacteremia, concordance was modest (67.3% agreement; Cohen's κ = 0.215). The modest sensitivity is expected because the composite intentionally restricts to culture-confirmed, antibiotic-treated infection — favoring specificity, the property that most limits outcome misclassification, over sensitivity. ICD-coded diagnoses are not a reference standard, so these metrics describe concordance rather than diagnostic accuracy (Supplement Table S15).

### 3.4 Secondary outcomes

**Treated bloodstream infection.** Events were sparse in the EEN arm (8/192, 4.2%): comparison A overlap-weighted OR 0.79 (0.31–1.99); comparison B OR 0.81 (0.36–1.80). Estimates were imprecise.

**Leak/reoperation.** Exploratory relaparotomy within 3–14 days occurred in 2/192 (1.0%) EEN and 30/346 (8.7%) late-EN patients (comparison A). After adjustment the association was imprecise (OR 0.29, 0.06–1.35) but did not suggest harm from early feeding.

**In-hospital death.** In comparison A, death was 32/192 (16.7%) vs 64/346 (18.5%); overlap-weighted OR 1.48 (0.87–2.53, p=0.149). In comparison B, death was 32/192 (16.7%) vs 191/1466 (13.0%); overlap-weighted OR 1.69 (1.08–2.65, p=0.023; RR 1.56, 1.07–2.28), IPTW 2.32 (1.41–3.82, p=0.001).

### 3.5 Sensitivity analyses

The primary finding in comparison A was stable across all prespecified sensitivity analyses (Table 3). The overlap-weighted infection OR was 0.58–0.61 across four feeding definitions, 0.64 (0.44–0.93) under the intention-to-treat (first-48-h feeding-order) definition, and 0.60 (0.39–0.92) without contaminant exclusion. Requiring a minimum 3-day antibiotic course (to exclude brief perioperative prophylaxis) attenuated the comparison-A estimate to 0.75 (0.46–1.20), and a ≥5-day course gave 0.66 (0.38–1.16); both preserved the protective direction with overlapping confidence intervals. Across thresholds the effect formed a monotonic gradient (24 h: 0.88; 48 h: 0.60; 72 h: 0.49; Figure 6). The same-day-surgery subgroup retained the direction (OR 0.70, 0.37–1.31) but lost precision (EEN n=111). Death modeled with discharge as a competing risk gave a Fine–Gray subdistribution hazard ratio of 1.33 (0.61–2.90) in comparison A and 1.62 (0.81–3.24) in comparison B, consistent with the primary analysis. Excluding upper-GI surgery — the largest measured covariate imbalance (SMD 0.807) — left the association intact in direction but underpowered (OW 0.63, 0.36–1.10), and stratification showed a homogeneous direction (upper-GI 0.58, 0.28–1.19 vs non-upper-GI 0.63, 0.36–1.10), indicating the effect was not an artifact of the routine-jejunostomy channel. Propensity-score matching was stable across calipers (0.05–0.3 SD of the logit PS: OR 0.39/0.33/0.33/0.36), confirming that its larger magnitude reflects the conditional estimand rather than caliper choice.

The "harm" signals in comparison B were attenuated by overlap trimming to PS ∈ [0.1, 0.9] (infection OR 1.01, 0.60–1.69; death OR 1.25, 0.63–2.47), whereas the protective estimate in comparison A was preserved (infection OR 0.64, 0.40–1.00; the PS-overlap region is shown in Figure 4).

As a quantitative assessment of unmeasured confounding, the E-value for the comparison-A infection estimate (risk ratio 0.73) was 2.08 for the point estimate and 1.21 for the confidence limit closest to the null [20]: a moderately strong unmeasured confounder (associated with both feeding timing and infection by a risk ratio of ≈2.1) would be required to fully explain away the point estimate, whereas a weaker confounder (≈1.2) could move the confidence interval to include the null — consistent with a real but imprecise protective effect.

As further robustness checks, a post-48-h reverse-causation sensitivity deferring the infection outcome window start from 48 h to 72 h (keeping the 48-h landmarked cohort) attenuated comparison A (overlap-weighted OR 0.67, 0.43–1.04, p=0.072; AIPW 0.81, 0.52–1.25) but preserved the protective direction, arguing against the association being a pure artifact of infections arising in the 48–72-h window that also determined the feeding decision; comparison B remained null under overlap weighting (OR 1.29, 0.88–1.89). A missingness-indicator sensitivity adding an indicator for every covariate with >10% missingness left comparison A essentially unchanged (overlap-weighted OR 0.63, 0.41–0.98) and comparison B still null (OR 1.41, 0.97–2.05). A multiple-imputation sensitivity (chained equations, m=25, pooled by Rubin's rules) gave an overlap-weighted OR of 0.59 (0.38–0.92) for comparison A and 1.34 (0.91–1.95) for comparison B, preserving the protective direction in A and the null in B.

### 3.6 Doubly-robust estimation and negative control

Augmented inverse-probability weighting (AIPW) — consistent if either the propensity-score or the outcome model is correct — gave directionally consistent estimates: comparison-A infection risk ratio 0.83 (0.63–1.09; OR 0.73, 0.47–1.14) versus overlap-weighted 0.73 (RR) / 0.60 (OR), and comparison-B risk ratio 1.52 (1.17–1.99; OR 1.81, 1.21–2.72). The treated-urinary-tract-infection negative control behaved as expected under adequate confounding control. In comparison A, the crude association of early feeding with the negative-control outcome (OR 0.56, 0.33–0.94) was fully attenuated by adjustment (overlap-weighted OR 0.88, 0.49–1.60; AIPW 0.80, 0.40–1.63), whereas the primary infection composite retained its protective association after the same adjustment — evidence that the primary finding is specific rather than an artifact of unmeasured health status. In comparison B, the negative-control outcome reproduced the primary outcome's "harm" pattern (IPTW OR 1.80, 1.02–3.19; AIPW 1.81, 1.03–3.19, mirroring the infection composite's 1.76 / 1.81); because early feeding cannot plausibly increase urinary infection, this parallel is further evidence that comparison B's apparent harm reflects never-fed confounding rather than a causal effect (Supplement Table S10). Although early EN has no direct biological pathway to prevent urinary infection, a treated urinary infection could still be indirectly influenced by recovery-related processes (e.g., urinary-catheter duration); it therefore serves as a falsification test for broad health-status confounding rather than a definitive placebo outcome.

### 3.7 Replication in an earlier era (MIMIC-III)

To test whether the comparison-A association generalizes beyond the MIMIC-IV era, we re-ran the same exposure and outcome definitions in MIMIC-III v1.4 [21] (same hospital, 2001–2012, with partial calendar-time overlap with MIMIC-IV's 2008–2019 but independently de-identified and non-linkable to MIMIC-IV admissions) — a same-center temporal replication rather than an independent external validation. Because MIMIC-III stores procedures without a date, the surgery-before-ICU filter and the leak/reoperation outcome were dropped, prescriptions are date-granular, and body-mass index was omitted (no omr table); the full chart-based SOFA physiology (Glasgow Coma Scale, mean arterial pressure, FiO₂, PaO₂; coverage 78–99%) plus mechanical ventilation, vasopressors, lactate, organ-function laboratories and Elixhauser comorbidity were included. Of 3590 eligible first surgical-ICU stays, 2498 were landmarked (EEN 272, late 406, never 1820). Comparison A replicated the primary direction: overlap-weighted infection OR 0.58 (0.42–0.82, p=0.002), against 0.60 (0.39–0.93) in MIMIC-IV. The treated-urinary-tract-infection negative control, however, attenuated only incompletely in MIMIC-III (overlap-weighted OR 0.67, 0.45–1.00, p=0.048) in contrast to MIMIC-IV (0.88, 0.49–1.60); the confidence intervals overlap, so this is not a formal contradiction, but it means the specificity evidence does not cleanly replicate across eras and residual confounding by general health status cannot be fully excluded (Supplement Table S11).

### 3.8 Supportive multicenter triangulation (eICU-CRD)

To probe whether the feeding-exposure *structure* — rather than the infection estimate itself — holds beyond a single center, we additionally examined eICU-CRD v2.0 [22] (208 US hospitals, 2014–2015). This analysis is supportive rather than validating: eICU's microbiology table is too sparse to reproduce the antibiotic-treated-culture composite, and it has no procedure table, so major abdominal surgery was identified by the APACHE admission diagnosis ("surgery for …" gastrointestinal categories) and enteral feeding from the intake–output flowsheet using a label classifier (tube/enteral/gastric/jejunal cells, excluding oral, parenteral, flush, and residual). Of 4578 eligible first-ICU-stay patients, 2128 were landmarked (EEN 159, late 97, never 1872). Among documented-fed patients the EEN/late structure reproduced MIMIC (62% EEN; median time to first feed 13 h vs 95 h), but the absolute feeding rate was far lower (12% vs 32% in MIMIC-IV), consistent with under-ascertainment of enteral intake in the flowsheet, so the eICU "never" group is not comparable. In-hospital death was null in both comparisons (overlap-weighted OR 0.88, 0.37–2.09, and 0.82, 0.46–1.45), consistent with MIMIC's null death endpoint. A three-database harmonization table (Table S12) and a replication forest plot (Figure 8) summarize the cross-database concordance.

## 4. Discussion

In this target-trial emulation of early versus late enteral nutrition after major abdominal surgery, earlier feeding among patients who were ultimately fed was associated with a lower risk of antibiotic-treated infection (overlap-weighted OR 0.60, 95% CI 0.39–0.93; RR 0.73), an association that was stable across threshold, definition, intention-to-treat, and competing-risk sensitivity analyses and directionally consistent across four estimation methods, including the doubly-robust augmented-IPW estimator (RR 0.83, 0.63–1.09). The direction was reproduced in an earlier era at the same center (MIMIC-III overlap-weighted OR 0.58, 0.42–0.82; partial calendar-time overlap, but independently de-identified and non-linkable to MIMIC-IV), supporting that the finding is not an artifact of a single data vintage. A supportive multicenter eICU-CRD analysis reproduced the feeding-exposure structure among documented-fed patients but could not reproduce the infection endpoint; death was null there as in MIMIC. Because the late-EN group had more contaminated/open-bowel procedures (exploratory laparotomy, stoma) that are associated with extended perioperative antibiotic prophylaxis, we tested a stricter definition requiring a minimum 3-day antibiotic course; this attenuated the comparison-A association (OR 0.75, 0.46–1.20) but did not reverse its direction, indicating that part of the protective estimate may reflect differential short-course antibiotic use rather than a large true treatment effect. By contrast, the full-cohort policy comparison showed no infection benefit and an apparent increase in mortality, which we interpret as confounding rather than harm: the never-fed subgroup is heterogeneous, containing both patients who recover quickly and resume oral intake and patients who die or require therapeutic NPO, and the "harm" signal was abolished by restricting the analysis to the region of covariate overlap. A negative-control outcome (treated urinary-tract infection, which early feeding cannot plausibly affect) reinforced both readings: in comparison A it was null after adjustment while the infection composite remained protective, and in comparison B it reproduced the same harm pattern as the primary outcome — corroborating that the policy comparison's apparent harm is confounding rather than effect.

Comparison A must be read precisely: it is not an intention-to-treat contrast but a principal-stratum (survivor-average-causal-effect) estimand that conditions on the post-baseline event of ultimately receiving enteral nutrition [8]. This conditioning can in principle induce selection bias, because a patient must survive long enough to be classified as late-EN, which would tend to make the late-EN arm appear healthier and thereby attenuate — not inflate — any early-feeding benefit. That the adjusted comparison still favors early feeding therefore argues against the protective association being a pure artifact of this selection. We retained comparison A alongside the policy estimand (comparison B) because the timing question — should a patient who will be fed be fed early? — is the question clinicians actually face, and it is precisely the question that a single policy comparison cannot isolate. Formal bounds for the survivor-average causal effect (e.g., Lee bounds [23] or Zhang–Rubin bounds [24]) would require reformulating the eventually-fed stratum under a baseline strategy-assignment framework — a substantial extension beyond the present landmark design — so we instead argue qualitatively that the direction of selection bias from conditioning on eventual feeding would, if anything, bias comparison A toward the null, and note formal bounds and a clone–censor–weight reformulation as priorities for methodological follow-up work.

The separation of the two estimands is the central methodological point of this study. A single "early versus late" comparison that ignores the never-fed majority conflates the timing effect with the population effect and can produce a spurious reversal of direction. Upper-GI surgery was the largest measured covariate imbalance (SMD 0.807 vs the late-EN arm, 1.020 vs the no-EEN arm), reflecting routine early jejunostomy feeding after esophageal/gastric resection; however, it was not the driver of the protective association, since excluding upper-GI surgery left the estimate essentially unchanged in direction (OW 0.63, 0.36–1.10) and stratification showed a homogeneous effect across upper-GI (0.58, 0.28–1.19) and non-upper-GI (0.63, 0.36–1.10) strata, both underpowered after the split.

**Limitations.** Single center; sparse events in the EEN arm (8 treated bloodstream infections) so the primary estimate is imprecise and should be read as a direction of effect; principal-stratum-like comparison A conditions on a post-baseline trajectory and is not intention-to-treat; intraoperative severity and the surgeon's subjective feeding decision are unmeasured (an E-value of 2.08 for the point estimate and 1.21 for the confidence-interval limit indicates that moderate-to-weak unmeasured confounding could explain or move the association); the surgery-to-ICU interval is date-granular; some 0–24-h covariates may have been recorded after EN initiation in the earliest-fed patients (a fixed window was used to avoid differential measurement windows across groups); ICD coding of anastomotic leak is non-specific (mitigated by requiring exploratory relaparotomy in a 3–14-day window); for the leak/reoperation outcome, early signs of anastomotic complication arising before the 48-h landmark could have led both to deferred feeding and to subsequent reoperation — a reverse-causation pathway not addressed by the landmark, which was applied only to the primary infection outcome (a sensitivity deferring the outcome window start to 72 h preserved but attenuated the protective association, OW OR 0.67, so a contribution of reverse causation to early-window events cannot be fully excluded); and eICU-CRD, though now available, cannot reproduce the primary endpoint (sparse microbiology and no procedure codes) and served only as supportive triangulation of the feeding structure and death; the MIMIC-III replication is same-center with overlapping years, and there its treated-urinary-tract-infection negative control attenuated only incompletely (OR 0.67, 0.45–1.00) even with the full SOFA severity set — so the specificity evidence does not cleanly generalize across eras and residual confounding cannot be fully excluded. Propensity-score matching was a conditional estimate restricted to 126 matched pairs (65.6% of the EEN arm; 34% dropped for lack of a caliper-matched control) and driven by 54 discordant pairs, so its larger apparent effect (infection OR 0.33 vs the marginal 0.60) reflects non-collapsibility and the conditional estimand rather than a more precise estimate; it was stable across calipers (0.05–0.3). The primary endpoint, a proxy for treated infection defined by antibiotic association, may include a minority of brief perioperative prophylaxis; a sensitivity requiring a ≥3-day antibiotic course attenuated but preserved the direction of the comparison-A association. The doubly-robust AIPW estimate for comparison A preserved the protective direction but was wider and crossed the null (RR 0.83, 0.63–1.09), underscoring the imprecision of the underlying estimate; the complete-case sensitivity was severely underpowered (n=170, 14 EEN events) and is reported only for transparency, which is why median imputation with a missingness indicator was used as the primary approach. The primary endpoint also relies on culture data and is therefore not reproducible in datasets without microbiology tables. The endpoint's concordance with ICD-coded infection was only modest (κ = 0.215), indicating that the composite and administrative diagnoses capture partly different events, so differential outcome misclassification cannot be excluded. We also could not measure culture-sampling intensity; if early-fed patients were cultured more frequently, this would tend to increase detected infections in the EEN arm (bias toward harm), making the observed protective association less likely to be explained by surveillance alone.

**Conclusions.** Earlier enteral nutrition after major abdominal surgery was associated with fewer antibiotic-treated infections among patients who were ultimately fed, with a consistent direction but imprecise magnitude. These findings support the safety and potential benefit of early enteral feeding in selected surgical ICU patients and argue for explicit estimand separation in future observational studies of feeding timing.

## Key messages

- Among surgical ICU patients who ultimately received enteral nutrition, earlier initiation (≤48 h) was associated with fewer antibiotic-treated infections, with a consistent direction across multiple causal-inference methods, temporal replication in MIMIC-III, and supportive multicenter triangulation in eICU-CRD.
- A naive "early vs. late" comparison that ignores the large never-fed subgroup can produce a spuriously reversed ("harmful") association — explicit separation of timing and policy estimands is essential in observational feeding-timing research.
- These findings support early enteral feeding in appropriately selected post-abdominal-surgery ICU patients, but should not be extrapolated to a universal early-feeding mandate.

---

## Tables

### Table 1. Baseline characteristics by feeding group (landmarked cohort, n=1658)

| Characteristic | EEN (n=192) | Late EN (n=346) | Never (n=1120) | SMD (EEN vs late) | SMD (EEN vs no-EEN) |
|---|---|---|---|---|---|
| Age, y, mean (SD) | 63.2 (14.0) | 62.4 (16.6) | 63.4 (16.5) | 0.052 | −0.001 |
| Major procedures, mean (SD) | 2.1 (1.3) | 2.2 (1.6) | 1.7 (1.2) | −0.100 | 0.193 |
| Lactate max, mmol/L, mean (SD) | 3.0 (2.7) | 4.2 (2.8) | 3.2 (2.6) | −0.440 | −0.187 |
| Creatinine max, mg/dL, mean (SD) | 1.4 (1.2) | 1.6 (1.2) | 1.5 (1.4) | −0.190 | −0.124 |
| WBC max, K/µL, mean (SD) | 14.0 (8.6) | 15.1 (8.5) | 15.0 (10.0) | −0.133 | −0.109 |
| Platelet min, K/µL, mean (SD) | 191.1 (116.5) | 167.2 (110.1) | 191.9 (122.0) | 0.211 | 0.042 |
| Bilirubin max, mg/dL, mean (SD) | 6.0 (12.0) | 4.8 (8.4) | 3.6 (5.4) | 0.113 | 0.217 |
| Female, n (%) | 65 (33.9) | 150 (43.4) | 523 (46.7) | −0.196 | −0.248 |
| Emergency admission, n (%) | 34 (17.7) | 64 (18.5) | 148 (13.2) | −0.020 | 0.088 |
| Stoma, n (%) | 12 (6.2) | 56 (16.2) | 80 (7.1) | −0.319 | −0.113 |
| Exploratory laparotomy (index), n (%) | 30 (15.6) | 123 (35.5) | 265 (23.7) | −0.469 | −0.268 |
| Vasopressor 0–24 h, n (%) | 61 (31.8) | 220 (63.6) | 444 (39.6) | −0.672 | −0.281 |
| Mechanical ventilation 0–24 h, n (%) | 108 (56.2) | 255 (73.7) | 514 (45.9) | −0.372 | 0.076 |
| Diabetes, n (%) | 52 (27.1) | 83 (24.0) | 302 (27.0) | 0.071 | 0.019 |
| CKD, n (%) | 30 (15.6) | 50 (14.5) | 187 (16.7) | 0.033 | −0.015 |
| Cirrhosis, n (%) | 16 (8.3) | 47 (13.6) | 145 (12.9) | −0.169 | −0.154 |
| Site — hepatobiliary, n (%) | 44 (22.9) | 140 (40.5) | 469 (41.9) | −0.384 | −0.407 |
| Site — upper GI, n (%) | 112 (58.3) | 75 (21.7) | 139 (12.4) | 0.807 | 1.020 |
| Site — lower GI, n (%) | 24 (12.5) | 102 (29.5) | 425 (37.9) | −0.426 | −0.569 |
| Site — other, n (%) | 12 (6.2) | 29 (8.4) | 87 (7.8) | −0.082 | −0.065 |

### Table 2. Primary and key secondary outcomes (overlap weighting primary)

| Outcome | Comparison | Events (EEN / control) | OW OR (95% CI) | OW RR (95% CI) | OW RD (95% CI) | OW p | IPTW OR (95% CI) | AIPW OR (95% CI) |
|---|---|---|---|---|---|---|---|---|
| Infection composite (primary) | A | 54/192 / 171/346 | **0.60 (0.39–0.93)** | 0.73 (0.55–0.97) | −0.12 (−0.22 to −0.02) | 0.023* | 0.68 (0.42–1.09) | 0.73 (0.47–1.14) |
| Infection composite (primary) | B | 54/192 / 339/1466 | 1.34 (0.93–1.95) | 1.24 (0.95–1.62) | 0.06 (−0.02 to 0.13) | 0.118 | 1.76 (1.15–2.70) | 1.81 (1.21–2.72) |
| Treated bloodstream infection | A | 8/192 / 26/346 | 0.79 (0.31–1.99) | 0.80 (0.33–1.92) | −0.01 (−0.06 to 0.03) | 0.617 | 0.92 (0.32–2.61) | — |
| Treated bloodstream infection | B | 8/192 / 72/1466 | 0.81 (0.36–1.80) | 0.82 (0.38–1.76) | −0.01 (−0.04 to 0.02) | 0.604 | 1.02 (0.39–2.66) | — |
| Leak/reoperation | A | 2/192 / 30/346 | 0.29 (0.06–1.35) | 0.30 (0.07–1.36) | −0.03 (−0.06 to −0.00) | 0.116 | 0.18 (0.04–0.90) | — |
| Leak/reoperation | B | 2/192 / 51/1466 | 0.44 (0.10–1.90) | 0.44 (0.10–1.89) | −0.02 (−0.04 to 0.01) | 0.268 | 0.34 (0.07–1.54) | — |
| In-hospital death | A | 32/192 / 64/346 | 1.48 (0.87–2.53) | 1.38 (0.89–2.15) | 0.06 (−0.02 to 0.13) | 0.149 | 1.75 (0.98–3.12) | — |
| In-hospital death | B | 32/192 / 191/1466 | 1.69 (1.08–2.65) | 1.56 (1.07–2.28) | 0.07 (0.00 to 0.13) | 0.023 | 2.32 (1.41–3.82) | — |
| Negative control (treated urinary infection) | A | 22/192 / 65/346 | 0.88 (0.49–1.60) | 0.90 (0.54–1.49) | −0.02 (−0.09 to 0.06) | 0.685 | 0.91 (0.48–1.72) | 0.80 (0.40–1.63) |
| Negative control (treated urinary infection) | B | 22/192 / 152/1466 | 1.30 (0.77–2.21) | 1.26 (0.80–2.01) | 0.03 (−0.03 to 0.08) | 0.324 | 1.80 (1.02–3.19) | 1.81 (1.03–3.19) |

Comparison A = EEN vs late EN (eventually-fed, n=538); Comparison B = EEN vs no-EEN (full landmarked cohort, n=1658). OW = overlap weighting; RR = risk ratio; RD = risk difference; IPTW = inverse-probability-of-treatment weighting; AIPW = augmented inverse-probability weighting (doubly robust). p values are two-sided Wald p-values from the overlap-weighted logistic model; *p < 0.025, the Bonferroni-corrected threshold for the two co-primary comparisons. Propensity-score-matched (conditional) estimates and matching diagnostics are reported in Tables S4 and S5; doubly-robust augmented-IPW estimates are reported in §3.6 and Supplement Table S10. AIPW was estimated for the primary infection composite and the negative-control outcome; secondary outcomes are reported under overlap weighting, IPTW, and PSM (Table S4). The treated-urinary-infection rows are a negative-control (falsification) outcome, not a clinical endpoint.

### Table 3. Sensitivity analyses for the primary outcome (overlap-weighted OR, infection composite)

| Sensitivity | A (EEN vs late) | B (EEN vs no-EEN) |
|---|---|---|
| Main (48 h) | 0.60 (0.39–0.93) | 1.34 (0.93–1.95) |
| Threshold 24 h | 0.88 (0.53–1.47) | 1.76 (1.11–2.78) |
| Threshold 72 h | 0.49 (0.32–0.74) | 1.04 (0.73–1.49) |
| Feeding definition: any record | 0.61 (0.39–0.94) | 1.38 (0.96–2.00) |
| Feeding definition: rate ≥20 | 0.58 (0.37–0.89) | 1.30 (0.89–1.89) |
| Feeding definition: ONS-inclusive | 0.60 (0.39–0.93) | 1.34 (0.93–1.95) |
| ITT (first-48-h feeding order) | 0.64 (0.44–0.93) | 1.56 (1.11–2.18) |
| Same-day surgery subgroup | 0.70 (0.37–1.31) | 1.37 (0.80–2.32) |
| No contaminant exclusion | 0.60 (0.39–0.92) | 1.31 (0.91–1.89) |
| Antibiotic course ≥3 days | 0.75 (0.46–1.20) | 1.36 (0.89–2.08) |
| Antibiotic course ≥5 days | 0.66 (0.38–1.16) | 1.29 (0.78–2.15) |
| Excluding upper-GI surgery | 0.63 (0.36–1.10) | — |
| PS-trim 0.1–0.9 | 0.64 (0.40–1.00) | 1.01 (0.60–1.69) |
| Outcome window 72 h (reverse causation) | 0.67 (0.43–1.04) | 1.29 (0.88–1.89) |
| Missingness indicators (>10% missing) | 0.63 (0.41–0.98) | 1.41 (0.97–2.05) |

---

## Figures

- **Figure 1. Study flow diagram.** 3246 eligible → 1658 landmarked (EEN 192 / late 346 / never 1120), with 48-h death/discharge counts and the never-fed 3-way dissection. — [analysis/figures/fig1_flow.png](analysis/figures/fig1_flow.png)
- **Figure 2. Forest plot of the primary outcome.** Overlap-weighted ORs (with 95% CI) for the infection composite across comparisons A and B and all sensitivity analyses (including strict-treated ≥3- and ≥5-day antibiotic courses), demonstrating the stability of the comparison-A estimate and the attenuation of comparison B on trimming. — [analysis/figures/fig2_forest.png](analysis/figures/fig2_forest.png)
- **Figure 3. Cumulative incidence of death by feeding group.** Aalen–Johansen estimator [25] with discharge as the competing risk, truncated at 28 days, shown for all three feeding groups (EEN / late EN / never fed); presented to explain the mechanism behind the comparison-B signal, not as a causal-effect estimate. — [analysis/figures/fig3_cif.png](analysis/figures/fig3_cif.png)
- **Figure 4. Propensity-score overlap.** Distribution of the estimated propensity score in the EEN versus control arms for comparisons A and B, with the prespecified PS-trim region [0.1, 0.9] shaded; supports the positivity assessment and the trimming sensitivity. — [analysis/figures/fig4_ps_overlap.png](analysis/figures/fig4_ps_overlap.png)
- **Figure 5. Covariate balance (Love plot).** Absolute standardized mean differences before (unweighted) and after overlap weighting and IPTW for each covariate; upper-GI surgery is the largest raw imbalance (|SMD| 0.81 in A, 1.02 in B) and all |SMD| fall below 0.1 after overlap weighting. — [analysis/figures/fig5_love_plot.png](analysis/figures/fig5_love_plot.png)
- **Figure 6. Dose–response gradient across feeding-time thresholds.** Overlap-weighted ORs (95% CI) for the infection composite at 24/48/72-h EEN thresholds, on a log scale; the monotonic gradient in comparison A (0.88 → 0.60 → 0.49) is consistent with a biological gradient, while comparison B attenuates toward the null by 72 h. — [analysis/figures/fig6_threshold_gradient.png](analysis/figures/fig6_threshold_gradient.png)
- **Figure 7. Estimand schematic.** Comparison A restricts to the eventually-fed subset (EEN vs late EN, timing effect), whereas comparison B uses the full landmarked cohort (EEN vs no-EEN, policy effect). — [analysis/figures/fig7_estimand.png](analysis/figures/fig7_estimand.png)

---

## Supplement (to be assembled from `analysis/`)

- **Table S1.** Full target-trial emulation specification.
- **Table S2.** The 112 enteral-nutrition itemids.
- **Table S3.** Covariate balance before/after weighting (SMD table for each comparison, including comparison B).
- **Table S4.** Complete estimates for all outcomes × methods × sensitivity analyses (`estimates.csv`).
- **Table S5.** Propensity-score-matching diagnostics (`analysis/psm_diagnostics.md`).
- **Table S6.** Upper-GI exclusion and stratification (`analysis/upper_gi_sensitivity.md`).
- **Table S7.** Full ICD-9-CM / ICD-10-PCS procedure-code list for major abdominal surgery and leak/reoperation.
- **Table S8.** Never-fed dissection algorithm (died / ileus-obstruction ICD-9 560.x or ICD-10 K56.x / presumptive oral recovery = neither).
- **Table S9.** Per-covariate missingness and complete-case sensitivity (`analysis/missing_data.md`).
- **Table S10.** Doubly-robust AIPW estimates and treated-urinary-tract-infection negative control (`analysis/negative_control.md`).
- **Table S11.** MIMIC-III replication (same-center, earlier era): cohort flow, outcome tallies, and comparison A/B estimates (`analysis/mimic3_replication.md`).
- **Table S12.** Three-database harmonization (MIMIC-IV / MIMIC-III / eICU-CRD) with bias-direction notes (`analysis/three_db_harmonization.md`).
- **Table S13.** Post hoc sensitivity analyses: post-48-h (72-h) reverse-causation sensitivity and missingness-indicator sensitivity (`analysis/reviewer_sensitivity.md`).
- **Table S14.** Multiple-imputation (MICE, m=25) sensitivity: pooled OW / IPTW / AIPW estimates (`analysis/mice_sensitivity.md`).
- **Table S15.** Primary-endpoint concordance check against ICD-coded infection/sepsis diagnoses (`analysis/outcome_validation.md`).
- **Figure 8.** Replication forest plot: infection composite and treated-urinary-tract-infection negative control, crude and overlap-weighted, MIMIC-IV vs MIMIC-III (`analysis/figures/fig8_replication_forest.png`).
- **Figure S1.** First-feeding-time distribution among eventually-fed patients (EEN ≤48 h vs late >48 h), with 24/48/72-h thresholds marked. — [analysis/figures/supp1_feeding_time.png](analysis/figures/supp1_feeding_time.png)
- **Figure S2.** Never-fed group dissection (died / therapeutic NPO / presumptive oral recovery). — [analysis/figures/supp2_never_fed.png](analysis/figures/supp2_never_fed.png)
- **Figure S3.** Infection-composite components by culture site (blood / abdominal / respiratory / wound) for comparisons A and B. — [analysis/figures/supp3_composite_sites.png](analysis/figures/supp3_composite_sites.png)
- **Figure S4.** Cumulative incidence of the treated-infection composite by feeding group (Aalen–Johansen [25], with in-hospital death and discharge as competing risks, truncated at 28 days). — [analysis/figures/supp4_infection_cif.png](analysis/figures/supp4_infection_cif.png)
- **Additional File 1.** STROBE checklist for cohort studies (`STROBE_checklist.md`).
- **Additional File 2.** RECORD checklist (STROBE extension for routinely-collected health data) (`RECORD_checklist.md`).

---

## Declarations

**Ethics approval and consent to participate.** This study used publicly available, de-identified data (MIMIC-IV, MIMIC-III, eICU-CRD). Individual informed consent was waived by the Institutional Review Boards of Beth Israel Deaconess Medical Center and the Massachusetts Institute of Technology (for the MIMIC databases) and of Philips Healthcare / the Massachusetts Institute of Technology (for eICU-CRD); these databases received institutional ethics approval for secondary research use under certified data-use agreements with PhysioNet (certificate number [ ]).

**Consent for publication.** Not applicable.

**Availability of data and materials.** The MIMIC-IV, MIMIC-III, and eICU-CRD datasets are available from PhysioNet (https://physionet.org/content/mimiciv/, https://physionet.org/content/mimiciii/, https://physionet.org/content/eicu-crd/) subject to credentialed data-use agreements; analysis code is publicly available at https://github.com/pwj055/een-abdominal-surgery-mimic and archived at Zenodo (https://doi.org/10.5281/zenodo.23446232). The study protocol and analysis plan are registered at OSF (https://osf.io/g39vw, DOI 10.17605/OSF.IO/G39VW).

**Competing interests.** [ ]

**Funding.** [ ]

**Authors' contributions.** [ ]

**Acknowledgements.** Not applicable.

---

## References

1. Lewis SJ, Egger M, Sylvester PA, Thomas S. Early enteral feeding versus "nil by mouth" after gastrointestinal surgery: systematic review and meta-analysis of controlled trials. *BMJ*. 2001;323(7316):773–776.
2. Andersen HK, Lewis SJ, Thomas S. Early enteral nutrition within 24h of colorectal surgery versus later commencement of feeding for postoperative complications. *Cochrane Database Syst Rev*. 2006;(4):CD004080.
3. Doig GS, Heighes PT, Simpson F, Sweetman EA, Davies AR. Early enteral nutrition, provided within 24 h of injury or intensive care unit admission, significantly reduces mortality in critically ill patients: a meta-analysis of randomised controlled trials. *Intensive Care Med*. 2009;35(12):2018–2027.
4. Singer P, Blaser AR, Berger MM, et al. ESPEN guideline on clinical nutrition in the intensive care unit. *Clin Nutr*. 2019;38(1):48–79.
5. McClave SA, Taylor BE, Martindale RG, et al. Guidelines for the Provision and Assessment of Nutrition Support Therapy in the Adult Critically Ill Patient: Society of Critical Care Medicine (SCCM) and American Society for Parenteral and Enteral Nutrition (A.S.P.E.N.). *JPEN J Parenter Enteral Nutr*. 2016;40(2):159–211.
6. Reintam Blaser A, Starkopf J, Alhazzani W, et al. Early enteral nutrition in critically ill patients: ESICM clinical practice guidelines. *Intensive Care Med*. 2017;43(3):380–398.
7. Hernán MA, Robins JM. Using Big Data to Emulate a Target Trial When a Randomized Trial Is Not Available. *Am J Epidemiol*. 2016;183(8):758–764.
8. Frangakis CE, Rubin DB. Principal stratification in causal inference. *Biometrics*. 2002;58(1):21–29.
9. Giobbie-Hurder A, Gelber RD, Regan MM. Challenges of guarantee-time bias. *J Clin Oncol*. 2013;31(23):2963–2969.
10. Maringe C, Benitez Majano S, Exarchakou A, et al. Reflection on modern methods: trial emulation in the presence of immortal-time bias. Assessing the benefit of major surgery for elderly lung cancer patients using observational data. *Int J Epidemiol*. 2020;49(5):1719–1729.
11. Johnson AEW, Bulgarelli L, Shen L, et al. MIMIC-IV, a freely accessible electronic health record dataset. *Sci Data*. 2023;10(1):1.
12. Lipsitch M, Tchetgen Tchetgen E, Cohen T. Negative controls: a tool for detecting confounding and bias in observational studies. *Epidemiology*. 2010;21(3):383–388.
13. Rosenbaum PR, Rubin DB. The central role of the propensity score in observational studies for causal effects. *Biometrika*. 1983;70(1):41–55.
14. Li F, Morgan KL, Zaslavsky AM. Balancing covariates via propensity score weighting. *J Am Stat Assoc*. 2018;113(521):390–400.
15. Cole SR, Hernán MA. Constructing inverse probability weights for marginal structural models. *Am J Epidemiol*. 2008;168(6):656–664.
16. Austin PC. Optimal caliper widths for propensity-score matching when estimating differences in means and differences in proportions in observational studies. *Pharm Stat*. 2011;10(2):150–161.
17. Lunceford JK, Davidian M. Stratification and weighting via the propensity score in estimation of causal treatment effects: a comparative study. *Stat Med*. 2004;23(19):2937–2960.
18. Zou G. A modified Poisson regression approach to prospective studies with binary data. *Am J Epidemiol*. 2004;159(7):702–706.
19. Fine JP, Gray RJ. A proportional hazards model for the subdistribution of a competing risk. *J Am Stat Assoc*. 1999;94(446):496–509.
20. VanderWeele TJ, Ding P. Sensitivity analysis in observational research: introducing the E-value. *Ann Intern Med*. 2017;167(4):268–274.
21. Johnson AEW, Pollard TJ, Shen L, et al. MIMIC-III, a freely accessible critical care database. *Sci Data*. 2016;3:160035.
22. Pollard TJ, Johnson AEW, Raffa JD, Celi LA, Mark RG, Badawi O. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. *Sci Data*. 2018;5:180178.
23. Lee DS. Training, wages, and sample selection: estimating sharp bounds on treatment effects. *Rev Econ Stud*. 2009;76(3):1071–1102.
24. Zhang JL, Rubin DB. Estimation of causal effects via principal stratification when some outcomes are truncated by "death". *J Educ Behav Stat*. 2003;28(4):353–368.
25. Aalen OO, Johansen S. An empirical transition matrix for non-homogeneous Markov chains based on censored observations. *Scand J Stat*. 1978;5(3):141–150.

---

*End of draft.*
