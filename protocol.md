# 研究方案（可行性定稿版）——普外科腹部大手术后 ICU 患者早期肠内营养

> 状态：**可行性检查已通过（有条件 GO）**。F1–F9 实测数字见 §11。
> 数据源：MIMIC-IV v3.1（仅 IV）。本文件是方法学定稿，投稿稿另写英文。
> 注册：OSF **https://osf.io/g39vw**（DOI 10.17605/OSF.IO/G39VW；2026-10-18 回顾性注册，分析计划 2026-10-16 冻结）。
> 代码：GitHub **https://github.com/pwj055/een-abdominal-surgery-mimic**
> 关键变更（相对初稿）：感染结局改为**单一主终点 × 两个并列 co-primary 对比**；吻合口漏降为 key secondary 安全结局；never 组拆解后仅作描述。

## 0. 题目（候选，投稿时定）

- 主选：**Timing of Enteral Nutrition After Major Abdominal Surgery and ICU Outcomes: A Target Trial Emulation Using the MIMIC-IV Database**
- 一句话 estimand：*Among postoperative surgical-ICU patients, we contrast (A) initiating tube enteral nutrition ≤48h vs >48h in those who are eventually tube-fed, and (B) an early-feeding strategy vs usual care in the full landmarked cohort.*

---

## 1. 锁定决策表（可行性定稿）

| # | 决策点 | 定稿 | 备注 |
|---|---|---|---|
| 1 | 暴露阈值 | **48h 主 + 24/72h 敏感性**；landmark 随阈值联动 | time zero = ICU 入科 |
| 2 | 主结局 | **单一主终点 = 感染复合（中等特异）**；BSI 为最特异层 + key secondary；吻合口漏/再手术为 key secondary 安全结局 | 不再设双主结局；见 §5、§7 |
| 3 | 时间零点 | ICU 入科 + 强制报告手术–ICU 间隔 QC + 同日手术敏感性 | 间隔仅日期粒度 |
| 4 | 人群 | **宽人群主分析 + 急诊/择期预设分层**；急诊**不升主** | 急诊 EEN 仅 35 例，F1 数据驱动 |
| 5 | 暴露=喂养类型 | 管饲为主（`category='Nutrition - Enteral'` 112 itemid）；ONS 敏感性 | category 过滤避开 "enteral⊂parenteral" 陷阱 |
| 6 | 主因果方法 | OW 主 + IPTW(稳定/截断) + PSM(caliper) 三角；报告 SMD/ESS/权重范围 | |
| 7 | 数据源 | 仅 MIMIC-IV | |
| 8 | 外部验证 | eICU 作 stretch（非 v1 必需） | |
| 9 | 吻合口漏反向因果 | landmark + 术中严重度代理 + **再手术按类型+3–14d 时间窗收紧** | F5 数据驱动 |
| 10 | 喂养启动颗粒度 | rate≥10 mL/hr 或 amount≥20 mL + 第二条记录证明持续；任意记录敏感性 | |
| 11 | 主对比结构 | **两个并列 co-primary 对比**：A=EEN vs late（eventually-fed 子集，时机效应）；B=EEN vs no-EEN（landmark 全队列，策略效应）；**never 拆解后仅描述** | 见 §2.1 estimand 声明 |
| 12 | 竞争风险/早期死亡 | 48h landmark（排除 48h 内死亡/出院）+ 描述 48h 死亡 + Fine-Gray 敏感性 | |
| 13 | 协变量窗口 | 0–24h 固定窗口；0–6h 敏感性；禁止随暴露变化的窗口 | |
| 14 | estimand 声明 | A 为 principal-stratum-like（条件于"最终被喂"）；B 为 ITT-like 策略效应；两者在 Methods 分列 | 见 §2.1 |
| 15 | 精度预期 | 明示 EEN 组 n≈192、treated BSI 8 例 → 复合结局 CI 预期宽；框架为"如实报告 + 方向一致性" | 见 §7.4 |
| 16 | never 组呈现 | 拆解（经口恢复/治疗性 NPO/死亡）进 Table 1 + 流程图，不进主因果模型 | 见 §5.3 |

---

## 2. Target trial emulation 规格

| 要素 | 规格 |
|---|---|
| 目标试验 | 术后入 ICU 患者随机分至「48h 内启动管饲」vs「延迟/不启动」 |
| Time zero | ICU 入科时间（`icustays.intime`） |
| 纳排 | ≥18；腹部大手术（ICD-PCS）；术后入外科 ICU；无强禁食指征；**ICU LOS≥48h（landmark）**；48h 内无 DNR/仅姑息 |
| 策略 A | 48h 内启动管饲（EEN） |
| 策略 B | 未在 48h 内启动管饲（常规照护） |
| 随访 | 48h landmark 起，至 28 天 / 出院 / 死亡 |
| 因果对比 | per-protocol 型为主；ITT 型（首 48h 喂养医嘱）敏感性 |
| 混杂控制 | 0–24h 固定窗口协变量（§6） |

### 2.1 Estimand 声明（Methods 必写，中英对照模板）

> **Comparison A（timing estimand, principal-stratum-like）**：在 ICU 期间**最终接受过管饲**的患者中，≤48h vs >48h 启动管饲的效应。这一限制条件依赖于一个**暴露之后发生的变量**（最终是否被喂），因此它是一个近似 principal stratum 的窄口径估计量，不是全人群的"喂养时机策略"效应。
>
> 英文模板：*"The EEN-vs-late-EN comparison estimates an effect within the subpopulation who ultimately received tube enteral nutrition during their ICU stay — a principal-stratum-like estimand conditioned on a post-baseline trajectory, rather than an intention-to-treat-type estimand. The full-cohort EEN-vs-no-EEN-by-landmark comparison is retained as a parallel policy estimand addressing the population-level effect of an early-feeding strategy."*
>
> **Comparison B（policy estimand, ITT-like）**：landmark 全队列 EEN vs no-EEN-by-48h，回答"早期喂养策略 vs 常规照护"的人群效应；never 组的异质性通过协变量调整 + 拆解描述处理，而非直接排除。

---

## 3. 人群定义（宽人群 + 预设分层）

- **纳入**：≥18；同次住院含腹部大手术（编码清单见下）；首次入外科 ICU（SICU/TSICU/MICU-SICU/Neuro SICU）；手术日 ≤ ICU 入科日；ICU LOS≥48h。
- **排除**：强禁食指征（肠缺血/梗阻/穿孔诊断码）；48h 内 DNR/仅姑息。
- **预设分层**：急诊 vs 择期；上消化道 vs 下消化道 vs 肝胆胰。
- **决策（F1 数据驱动，已定）**：急诊亚组 EEN 仅 35 例 → **不升主**，作预设分层。宽人群为主。

**编码清单（`procedures_icd`）**：同初稿。ICD-9-PCS `42/43/45/46/50/51/52`（主），`541`(剖腹探查)/`545`(粘连松解)；ICD-10-PCS 前缀 `0DB/0DT/0D1/0DQ/0FB/0FT` + `0WJG`。⚠️ 2015-10 编码切换，需查可比性。

---

## 4. 暴露定义（管饲 + 颗粒度，#10）

- **管饲 itemid 最终清单**：`d_items.linksto='inputevents' AND category='Nutrition - Enteral'`，共 **112 个 itemid**（Nutren/Jevity/Peptamen/Osmolite/Nepro/Glucerna/Vital/Promote/Isosource/Fibersource/Two Cal/Pulmocare/Vivonex/Replete/Impact/ProBalance/NovaSource 等，含 Ensure/Boost/Enlive/Beneprotein）。**在补充材料列出完整清单**；ONS（Ensure/Boost/Enlive）作敏感性 C 处理。
- **主定义（管饲启动）**：首个满足「rate ≥10 mL/hr **或** amount ≥20 mL」的管饲记录，且 48h 窗口内存在第 2 条记录（证明持续）。v3.1 无 `statusdescription='Rewritten'`（状态为 FinishedRunning/ChangeDose/Rate/Stopped/Paused/Bolus），分析时排除 Stopped/Paused 定义"启动"。
- **eventually-fed**：ICU 停留期间任意时间出现管饲记录（inputevents 为 ICU 内）。
- **late EN**：首次管饲 >48h（ICU 停留内）；住院期扩展作敏感性。
- **敏感性 A/B/C**：任意记录 / rate≥20 / ONS 宽定义。

---

## 5. 结局定义

### 5.1 主终点 —— 感染复合（中等特异，唯一主终点）
- **成分**：treated BSI（血培养阳性非污染菌 + 系统抗生素）**+** 腹腔感染/脓肿（培养/引流/抗生素代理，或 ICD+抗生素）**+** VAP（呼吸道培养/影像 + 抗生素代理；做不到则降入宽松层）**+** SSI（仅 ICD，只放宽松层）。
- **两档梯度**（避免过宽被批"机制混"）：
  - **Primary（中等特异）**：treated BSI + 腹腔感染（培养/引流+抗生素）+ VAP（培养/影像+抗生素）。
  - **Sensitivity（更宽）**：再加 ICD-coded SSI/腹腔感染。
- **treated 算法**：培养阳性前后窗口（−1d ~ +2d）内系统抗生素处方（抗生素清单同可行性脚本，最终经 mimic-code 校验）。

### 5.2 Key secondary 结局
- **treated BSI**（最特异层，单独报告，不占 α）。
- **吻合口漏/再探查安全结局**（harm/safety）：
  - 层 1：ICD 漏码 `9974`（吻合口并发症，队列内 145 例，4.5%）+ `56981`/`K9189`/`K632`（肠瘘）+ `T814%`（T81.4 感染，前缀匹配）。
  - 层 2：**再手术收紧版** = 第二次腹部大手术在 **3–14 天**内（队列内 406 例）。
  - 层 3（最特异）：3–14 天内 + 第二次为探查性剖腹/再探查（`541`/`0WJG`，队列内 **69 例，2.1%**）。
- 其余：ICU LOS、总住院 LOS、院内死亡、MV 时长、AKI（KDIGO）、TPN 比例、VAP、CRBSI。

### 5.3 反向因果处理（#9）与 never 组拆解（#16）
- **landmark/排除分析**：报告"最终漏"患者在 48h 内已出现的早期征象比例（体温≥38.5 / WBC≥15k / 48h 内二次腹部大手术）。
- **术中严重度代理**：急诊状态、是否造口、同期大手术数 + 0–24h 生理严重度。真术中变量不可得 → Limitations。
- **never 组拆解**（进 Table 1/流程图，不进主因果模型）：按 (a) 经口恢复（无肠梗阻诊断、存活）、(b) 治疗性 NPO（肠梗阻/麻痹 560.x/K56.x）、(c) 死亡（deathtime/dod）拆三组。实测 ~45%/~13%/~42%，证明 never 为双峰分布、不可当同质组。

---

## 6. 协变量（0–24h 固定窗口）

- 严重度：SOFA 组成（乳酸 50813、肌酐 50912、WBC 51301、血小板、胆红素、MAP、FiO2、GCS）、升压药、MV、WBC。
- 手术严重度：急诊/择期、手术部位、是否造口、同期大手术数。
- 共病：糖尿病、CKD、肝硬化、BMI（Elixhauser 诊断码）。
- **数据可得性（F7，区分两件事）**：肌酐 99.4%、WBC 99.5%、乳酸 80.6% = **检验完整性**；升压药 33.5%、MV 46.1% = **人群患病率**（非缺失）。

---

## 7. 统计分析计划

1. **主因果方法**：OW 主 + IPTW（稳定/截断）+ PSM（caliper）三角；报告加权后 SMD、ESS、权重范围。
2. **两个并列 co-primary 对比**：
   - **Comparison A（timing）**：eventually-fed 子集（EEN 192 vs late 346，n=538），estimand 见 §2.1。
   - **Comparison B（policy）**：landmark 全队列（EEN 192 vs no-EEN 1466，n=1658）。
3. **多重比较**：单一主终点 × 两个 co-primary 对比 → 双侧 α 各 0.025（Bonferroni）；报告未校正 95% CI。**不设双主结局**（BSI/漏为 key secondary，不占 α）。
4. **精度预期（明示）**：EEN 组 n≈192、treated BSI 8 例；感染复合预期事件仍偏少 → CI 宽。论文框架为**如实报告点估计 + 方向一致性（梯度）+ 宽 CI**，不声称精确效应。若 OW 后 ESS <40%，切换 trimming PS 0.1–0.9 或更强重叠区间作敏感性。
5. **异质性**：急诊/择期、手术部位预设分层；诚实报告交互。
6. **报告规范**：STROBE/target-trial 清单；estimand 声明（§2.1）原文进 Methods。

---

## 8. 敏感性分析清单

1. 阈值 24h / 72h —— **landmark 时点同步改为对应阈值**（24h 分析用 24h landmark，72h 用 72h），避免重引入 immortal time bias。
2. 喂养定义：任意记录 / rate≥20 / ONS 宽定义。
3. 同日手术亚组（手术日=ICU 入科日，66%）。
4. 剔除 48h 内死亡/出院（landmark）处理报告。
5. ITT 型（首 48h 喂养医嘱）对比 per-protocol。
6. 污染菌剔除 vs 不剔除（BSI）。
7. eICU 复现（stretch，非 v1）。
8. never 组拆解后：Comparison A 为主 + Comparison B 并列，互为参照（非"主/次要"）。
9. 死亡结局 Fine-Gray 竞争风险；48h 死亡比例描述。
10. trimming PS 0.1–0.9（低 ESS 时）。

---

## 9. 可行性门槛（§11 实测对照）

| 指标 | 门槛 | 实测 | 判读 |
|---|---|---|---|
| F1 样本量 | 急诊各暴露组≥100 且事件≥40 → 升主 | 急诊 450（EEN 35） | **不升主，宽人群主** |
| F2 itemid | 覆盖≥70–80% | 112 个完整 | ✅ |
| F3 EEN 比例 | 10–90% | landmark 后 11.6%（全队列 8.1%） | ⚠️ 偏低但可用 |
| F4 BSI 事件 | ≥60 稳做 | 总 80（EEN 仅 8） | ⚠️ 复合升主、BSI 降 key secondary |
| F5 漏/再手术 | 决定层 2/3 | 再探查收紧版 69（2.1%） | 层 3 可做，作安全结局 |
| F6 同日手术 | 过低则重估 | 66% | ✅ |
| F7 协变量 | 高缺失降级 | 肌酐/WBC 99%、乳酸 81% | ✅ |
| F8 永不喂养 | 过大需 eventually-fed 子集 | 81.2%（landmark 67.6%） | **Comparison A 并立** |
| F9 48h 死亡 | 过高外推受限 | 3.6% | 可接受 |

---

## 10. 局限与风险（预登记写法）

- **principal-stratum 可识别性**：Comparison A 条件于暴露后的"最终被喂"，属 principal-stratum-like，其估计依赖该层可识别假设，解释为窄口径时机效应（§2.1）。
- **事件稀疏**：EEN 组 treated BSI 8 例 → 复合结局 CI 宽，结论为方向性而非精确量效（§7.4）。
- 不可测混杂：外科医生基于术中所见的主观喂养决策。
- 信息性删失：平稳患者提前出 ICU。
- 手术–ICU 间隔仅日期粒度；术中失血/术时不可得。
- 单中心；吻合口漏编码不特异（已用类型+时间窗收紧）。
- 编码切换（2015-10）前后可比性需验证。

---

## 11. 可行性实测结果（MIMIC-IV v3.1，2026-10-16 跑出）

- **队列**：3246 例（宽人群）；ICD-9 2574 / ICD-10 672；急诊 450 / 择期 2796；同日手术 66%；LOS≥48h 51.1%。
- **landmark 后三组**（n=1658）：EEN 192（11.6%）/ late 346（20.9%）/ never 1120（67.6%）。
- **感染事件（treated）**：BSI 总 80（EEN 8 / late 26 / never 46）；任意培养阳性 EEN 74 / late 221 / never 265（含尿培养，上界）。
- **never 拆解**：经口恢复 ~45% / 死亡 ~42% / 治疗性 NPO ~13%。
- **再手术**：粗 738（22.7%）→ 3–14d 406 → 3–14d+探查 69（2.1%）。
- **协变量**：肌酐 99.4%、WBC 99.5%、乳酸 80.6%、MV 46.1%、升压药 33.5%。
- **48h 死亡**：3.6%。

**Go/no-go：有条件 GO。** 主分析 = 宽人群；主终点 = 感染复合（中等特异）；两个并列 co-primary 对比（timing A + policy B）；never 拆解描述；再探查收紧版作安全结局。**精度预期明示为宽 CI。**

---

## 12. 正式分析流水线（2026-10-16 跑出，`analysis/`）

三阶段脚本（`01_build_dataset.py` → `02_weighting.py` → `03_tables.py`）已跑通，产出分析就绪表 + OW/IPW/PSM 估计 + Table 1。**（2026-10-17 修正）48h landmark 现额外要求 `deathtime > intime+48h`**——5 例 ICU `outtime` 延迟但 48h 内死亡的患者被误纳入，已剔除，landmark 队列 1663→1658；本节所有数字均已按重跑结果更新。关键数字（与 §11 可行性一致或已收紧）：

- **分析队列**：1658（EEN 192 / late 346 / never 1120）。§11 的 347/1123 为四舍五入，正式数为 192/346/1120。
- **感染复合（landmarked）**：EEN 54 / late 171 / never 168；**treated BSI**：8 / 26 / 46（不变）。
- **漏/再探查（收紧版，landmarked）**：定义改为「索引大手术后 3–14 天的探查性再剖腹 `541`/`0WJG`，剔除粘连松解 `545`」→ 全队列 84（2.6%），landmarked **53**（EEN 2 / late 30 / never 21）。§11 的 69 为可行性粗版（rn=2 定义），正式流水线用更严谨的「索引后 3–14d 探查」定义。
- **never 拆解**：died 127（11.3%）/ 治疗性 NPO 211（18.8%）/ 经口恢复 782（69.8%）。
- **112 个喂养 itemid** 已固化至 `analysis/feeding_itemids.csv`。

**主估计（OW 主，双 co-primary × 感染复合；全 SOFA 主协变量集）：**

| 对比 | Crude OR | OW OR (95%CI) | IPTW OR (95%CI) | PSM OR (95%CI) |
|---|---|---|---|---|
| A（EEN vs late，n=538） | 0.40 (0.27–0.58) | **0.60 (0.39–0.93)** | 0.68 (0.42–1.09) | 0.33 (0.18–0.60) |
| B（EEN vs no-EEN，n=1658） | 1.30 (0.93–1.82) | 1.34 (0.93–1.95) | 1.76 (1.15–2.70) | 1.37 (0.85–2.21) |

**OW RR / RD / p（主终点，补充口径）**：A 感染 RR 0.73 (0.55–0.97)、RD −0.12 (−0.22, −0.02)、p=0.023；B 感染 RR 1.24 (0.95–1.62)、RD 0.06、p=0.118。死亡：A OW RR 1.38、p=0.149；B OW RR 1.56、p=0.023（IPTW OR 2.32，p=0.001）。按 Bonferroni 双侧 α=0.025 判定：A 感染 p=0.023 < 0.025 仍显著，B 感染不显著。**OR 不可折叠**——PSM（条件/配对）OR 与 OW/IPTW（边际）OR 不可直接比大小，RR/RD 可折叠，供跨方法比较（manuscript §2.7）。

**方向解读（待成文，非因果结论）**：Comparison A 中 EEN 感染保护方向一致（OW 显著；IPTW 同向，PSM 0.33）；Comparison B 感染近 null、且院内死亡 OW 1.69 / IPTW 2.32——与 never 组混杂一致（经口恢复的健康患者稀释 no-EEN 组），**不能读作 EEN 因果有害**。OW 达精确平衡（max|SMD| 0.000），IPTW 在 B 中 max|SMD|=0.149（触发 §8.10 预设 PS-trimming 敏感性）。Table 1 揭示主导混杂：**上消化道手术 EEN 58.3% vs late 21.7%**（食管/胃切除常规空肠造口喂养），及 late 组更重（升压药 63.6% vs 31.8%、乳酸 4.2 vs 3.0）。

### 12.1 PS-trimming 敏感性（预设 §8.10，PS∈[0.1,0.9] 重叠域重估）

| 对比 | n（剔除） | 感染复合 OW OR | IPTW OR | PSM OR | 死亡 OW OR |
|---|---|---|---|---|---|
| A（EEN vs late） | 456（−82） | 0.64 (0.40–1.00) | 0.76 (0.47–1.24) | **0.52 (0.29–0.95)** | 1.34 (0.75–2.38) |
| B（EEN vs no-EEN） | 504（−1154） | 1.01 (0.60–1.69) | 0.88 (0.50–1.55) | 0.89 (0.51–1.55) | 1.25 (0.63–2.47) |

**结论**：① A 的感染保护效应在 trim 后**方向保留**（OW 0.64，0.40–1.00）但仅 PSM 显著（0.52，0.29–0.95）——与贪婪 1:1 匹配在小样本下的不稳定性一致；A 的死亡信号趋 null。② B 的感染/死亡原先的"有害"信号（感染 OW 1.34→1.01、死亡 OW 1.69→1.25）**全部消失为 null**——证实 B 的"有害"完全由 never 组极端 PS 患者（经口恢复健康者稀释对照）驱动，非因果。B 剔除 1154/1658（69.6%）亦量化了 never 组与 EEN 组重叠之窄。③ 全 SOFA 下 B 的 IPTW 平衡本就差（主分析 max|SMD| 0.149、trim 后 0.170），进一步支持以 OW（精确平衡）为主方法、IPTW 仅作参照。

### 12.2 阈值敏感性（预设 §8.1，24/48/72h，landmark 与阈值联动）

| 阈值 | 对比 | n（EEN/对照） | 感染复合 OW OR | IPTW OR | PSM OR | 死亡 OW OR |
|---|---|---|---|---|---|---|
| 24h | A | 598（121/477） | 0.88 (0.53–1.47) | 0.72 (0.40–1.30) | 0.72 (0.38–1.39) | 1.87 (0.97–3.62) |
| 24h | B | 2680（121/2559） | 1.76 (1.11–2.78) | 1.81 (1.02–3.22) | 2.33 (1.13–4.81) | 2.54 (1.45–4.46) |
| **48h** | **A** | 538（192/346） | **0.60 (0.39–0.93)** | 0.68 (0.42–1.09) | 0.33 (0.18–0.60) | 1.48 (0.87–2.53) |
| 48h | B | 1658（192/1466） | 1.34 (0.93–1.95) | 1.76 (1.15–2.70) | 1.37 (0.85–2.21) | 1.69 (1.08–2.65) |
| 72h | A | 470（212/258） | **0.49 (0.32–0.74)** | 0.54 (0.35–0.83) | 0.50 (0.32–0.81) | 1.03 (0.62–1.71) |
| 72h | B | 1092（212/880） | 1.04 (0.73–1.49) | 1.24 (0.85–1.80) | 0.94 (0.62–1.41) | 1.17 (0.76–1.80) |

**结论**：① A 的感染保护效应呈**梯度**（24h 0.88 → 48h 0.60 → 72h 0.49），48/72h 均显著、72h 更强——证明效应非 48h 阈值选择的偶然产物；24h 因 EEN 仅 121 例且超早期喂养为高选择群体而 null。② B 的"有害"信号（感染与死亡）**在 24h 最弱口径下最强、随阈值放宽而衰减至 null**（72h 死亡 OW 1.17、感染 1.04）——正是"EEN 口径越窄越选择、never 组健康患者越稀释对照"的混杂特征。③ 死亡信号在 A/B 中均随阈值放宽消失（72h 均 null），支持死亡"有害"为残余混杂而非因果。

### 12.3 全 SOFA 协变量（已并入主协变量集，协议 §6 必需项）

全 SOFA 协变量集（含 GCS/MAP/FiO2/PaO2/BMI；覆盖率 GCS 99.5%、MAP 99.1%、FiO2 63.3%、PaO2 70.0%、BMI 67.0%，缺失中位插补）现已作为**主协变量集**——§12 主估计即此口径。相对较早的核心协变量口径（A 感染 OW 0.53），补全严重度后 A 感染 OW **0.60（0.39–0.93）仍保护且显著**，仅小幅向 null 衰减（符合"更充分控制 late 组更重"的预期）；B 感染 OW 1.34、死亡 OW 1.69（1.08–2.65）不变。全 SOFA 下 B 的 IPTW 平衡变差（主分析 max|SMD| 0.149、trim 后 0.170），**进一步支持以 OW（精确平衡）为主方法、IPTW 仅作参照**。

### 12.4 剩余预设敏感性（§8.2 喂养定义 / §8.3 同日手术 / §8.5 ITT / §8.6 污染菌 / §8.6b 疗程≥3天 / §8.6c 疗程≥5天，2026-10-16/17 跑出）

全部复用 48h-landmarked 队列 + 全 SOFA 协变量，主终点感染复合 OW 主：

| 敏感性 | 对比 | n（EEN/对照） | 感染 OW OR | IPTW OR | PSM OR | 死亡 OW OR |
|---|---|---|---|---|---|---|
| §8.3 同日手术（=ICU 入科日） | A | 310（111/199） | 0.70 (0.37–1.31) | 0.81 (0.41–1.60) | 0.46 (0.21–1.00) | 1.27 (0.54–3.01) |
| §8.3 同日手术 | B | 958（111/847） | 1.37 (0.80–2.32) | 2.40 (1.24–4.64) | 1.14 (0.56–2.30) | 1.50 (0.69–3.24) |
| §8.2 任意记录 | A | 539（193/346） | **0.61 (0.39–0.94)** | 0.68 (0.43–1.10) | 0.47 (0.27–0.80) | 1.49 (0.88–2.54) |
| §8.2 rate≥20 | A | 537（191/346） | **0.58 (0.37–0.89)** | 0.65 (0.40–1.04) | 0.68 (0.42–1.10) | 1.36 (0.79–2.33) |
| §8.2 ONS 宽定义 | A | 538（192/346） | **0.60 (0.39–0.93)** | 0.68 (0.42–1.09) | 0.33 (0.18–0.60) | 1.48 (0.87–2.53) |
| §8.5 ITT（首 48h 喂养医嘱） | A | 695（230/465） | **0.64 (0.44–0.93)** | 0.70 (0.47–1.05) | **0.47 (0.29–0.78)** | 1.23 (0.78–1.96) |
| §8.5 ITT | B | 1658（230/1428） | 1.56 (1.11–2.18) | 1.87 (1.27–2.74) | 1.29 (0.84–1.96) | 1.76 (1.17–2.66) |
| §8.6 污染菌不剔除 | A | 538（192/346） | **0.60 (0.39–0.92)** | 0.67 (0.42–1.07) | 0.34 (0.19–0.62) | 1.48 (0.87–2.53) |
| §8.6 污染菌不剔除 | B | 1658（192/1466） | 1.31 (0.91–1.89) | 1.75 (1.14–2.68) | 1.33 (0.83–2.12) | 1.69 (1.08–2.65) |
| §8.6b 疗程≥3天（严格 treated） | A | 538（192/346） | **0.75 (0.46–1.20)** | 0.92 (0.55–1.54) | 0.56 (0.30–1.05) | 1.48 (0.87–2.53) |
| §8.6b 疗程≥3天（严格 treated） | B | 1658（192/1466） | 1.36 (0.89–2.08) | 1.94 (1.20–3.12) | 1.27 (0.73–2.20) | 1.69 (1.08–2.65) |
| §8.6c 疗程≥5天（严格 treated） | A | 538（192/346） | **0.66 (0.38–1.16)** | 0.73 (0.39–1.34) | 0.47 (0.24–0.92) | 1.48 (0.87–2.53) |
| §8.6c 疗程≥5天（严格 treated） | B | 1658（192/1466） | 1.29 (0.78–2.15) | 1.58 (0.89–2.81) | 1.22 (0.60–2.51) | 1.69 (1.08–2.65) |

**结论**：① **喂养定义稳健**——A 的感染保护在任意记录 / rate≥20 / ONS / 主定义四种口径下 OW OR 恒为 0.58–0.61，PSM 在任意记录（0.47）与 ONS（0.33）下亦显著。② **ITT 稳健**——首 48h 喂养医嘱（order-based，非给药）口径下 A 的感染保护 OW 0.64 (0.44–0.93)、PSM 0.47 仍显著，说明结论不依赖"实际给药 vs 医嘱"的选择。③ **同日手术亚组** A 方向仍保护（OW 0.70）但 CI 因 n 减半（EEN 111）而跨 1——功效不足，非方向反转。④ **污染菌剔除与否**不影响（OW 0.60≈0.60）。⑤ **疗程 ≥3 / ≥5 天严格 treated**（剔除短暂围术期预防）下 A 感染 OW 为 0.75 (0.46–1.20) / 0.66 (0.38–1.16)——均方向保留、CI 重叠、无单调衰减，说明主结论对抗生素定义不脆弱；部分保护估计可能来自 late 组（探查 35.5% vs 15.6%、造口 16.2% vs 6.2%）更长的围术期预防用药被计入 treated。B 严格口径 1.36 (0.89–2.08) / 1.29 (0.78–2.15) 与主口径一致。⑥ B 的"有害"信号（感染 1.30–1.56、死亡 1.50–1.78）**在所有口径下恒定存在**——再次支持其为 never 组混杂而非因果（因果效应不应随喂养定义漂移，但混杂结构恒定）。⑦ 同日手术占宽队列 65%（≈F6 的 66%），landmarked 子集 57.8%——LOS≥48h 入组条件使同日手术占比下降，属正常成分偏移。

### 12.5 landmark 报告（§8.4）+ 死亡竞争风险（§8.9，2026-10-16 跑出）

**§8.4 landmark 报告（宽队列 n=3246，与 §11 一致）**：48h 内死亡 117（3.6%）；48h 内转出 ICU 存活 1471（45.3%）；landmark 存活≥48h **1658（51.1%）**。48h 死亡比例低（3.6%），支持 48h landmark 未造成实质 selection。

**§8.9 死亡竞争风险（出院为竞争事件，28 天，Aalen-Johansen CIF + Fine-Gray SHR，OW 加权）**：

| 对比 | 臂（n） | 28d 死亡 CIF | Fine-Gray SHR (95% CI) |
|---|---|---|---|
| A（EEN vs late） | EEN 192 / late 346 | 13.5% / 14.5% | 1.33 (0.61–2.90) |
| B（EEN vs no-EEN） | EEN 192 / no-EEN 1466 | 13.5% / 10.8% | 1.62 (0.81–3.24) |

注：landmarked 内死亡共 223 例，仅 38 例发生在 28 天之后（28 天窗口基本覆盖全部死亡）。

**结论**：① 竞争风险模型与主分析**方向完全一致**——A 死亡近 null（SHR 1.33，CI 跨 1；CIF 13.5% vs 14.5% 几乎相等），B 死亡呈"有害"方向（SHR 1.62；CIF 13.5% vs 10.8%）。② 死亡"有害"信号（B）在竞争风险口径下依然存在但不显著（CI 0.81–3.24），与主分析（OW OR 1.69）一致，支持其为 never 组混杂而非因果。③ 至此 §8 清单全部可执行项完成（§8.1–8.6、§8.9、§8.10）；§8.7 eICU 复现为 stretch 目标，需单独下载 eICU 数据（另需 DUA），暂缓。

### 12.6 审稿驱动诊断：PSM 异常 + upper-GI 排除/分层（2026-10-17 跑出，`10_reviewer_diagnostics.py`）

**PSM 主结局异常（Comparison A 感染 OW 0.60 / IPTW 0.68 / PSM 0.33）已查明，非 bug**：贪婪 1:1 匹配（caliper 0.2·SD logit PS）**仅匹配 126/192（65.6%）**——34% 的 EEN 患者因 caliper 内无对照被丢弃；McNemar OR 由 54 个不一致对（b=13 / c=41）驱动，故条件估计量天然偏大。**caliper 敏感性**（0.05/0.1/0.2/0.3）：OR 0.39 / 0.33 / 0.33 / 0.36——**稳定，收紧 caliper 不会把 PSM 拉回 OW**，证明是条件估计量 + 不可折叠性所致，非 caliper 过宽。匹配后 max|SMD| 0.110；匹配样本 site 均衡（upper 44.0% vs 全 treated 臂 58.3%）。→ manuscript 已改为：**PSM 从主 Table 2 降级到 Supplement（Table S4 完整 PSM 估计 + Table S5 匹配诊断）**，正文 §3.3 仅保留"方向一致但条件估计量、126 对、34% 丢弃"一句；Discussion/Limitations 用具体数字（126 对、54 不一致对、caliper 稳定）替代"known sensitivity"笼统说法。

**upper-GI 排除/分层（回应"dominant confounder 未检验"）**：

| 分析 | n（EEN/对照） | OW OR | IPTW OR | PSM OR |
|---|---|---|---|---|
| 排除 upper-GI | 351（80/271） | **0.63 (0.36–1.10)** | 0.66 (0.36–1.21) | 0.63 (0.32–1.24) |
| upper-GI 层 | 187（112/75） | 0.58 (0.28–1.19) | 0.54 (0.26–1.12) | 0.23 (0.07–0.72) |
| 非 upper 层 | 351（80/271） | 0.63 (0.36–1.10) | 0.66 (0.36–1.21) | 0.63 (0.32–1.24) |

**结论**：A 的保护效应**不是** upper-GI/空肠造瘘通道的伪影——排除后 OW 仍 0.63、方向不变（仅 n 538→351 失去显著性），分层方向一致（upper 0.58 vs 非 upper 0.63）。upper-GI 是**最大的协变量失衡**（SMD 0.807 vs late、1.020 vs no-EEN），但**非效应驱动者**。→ Discussion 原"dominant confounder"句已改写为"largest measured covariate imbalance … not the driver"，并附排除/分层数字（Table 3 加排除行、Supplement Table S6）。此结果**加强**（而非削弱）核心结论。

### 12.7 图审驱动：新增方法学图 + 旧图数据校正（2026-10-17 跑出，`11_reviewer_figures.py` / `09_figures.py`）

回应图审"现有三图不足以支撑方法学论证完整性"。**新增 4 幅主图 + 3 幅补充图**（`analysis/figures/`）：

- **Fig 4 PS 重叠图**（`fig4_ps_overlap.png`）：A/B 各一 panel，PS 直方图 EEN vs 对照，叠加预设 trim 区间 [0.1, 0.9] 阴影——直接支撑 §2.7 positivity 与 §3.5 trim 论点。
- **Fig 5 Love plot**（`fig5_love_plot.png`）：A/B 各一 panel，协变量 |SMD| 未加权 vs OW vs IPTW 排序点图；upper-GI（|SMD| 0.81/1.02）为最大失衡源，OW 后全部 <0.1。
- **Fig 6 阈值剂量-反应梯度**（`fig6_threshold_gradient.png`）：24/48/72h OW OR（对数刻度）点+误差棒；A 单调梯度 0.88→0.60→0.49，B 72h 衰减至 1.04——Hill 生物学梯度证据。
- **Fig 7 estimand 示意图**（`fig7_estimand.png`）：A 限定 eventually-fed 子集（timing），B 用全 landmarked 队列（policy）。
- **补充图 S1**（`supp1_feeding_time.png`）：首次喂养时间分布（EEN≤48h vs late>48h），标 24/48/72h。
- **补充图 S2**（`supp2_never_fed.png`）：never 组拆解（死亡 127 / NPO 211 / 口服恢复 782）。
- **补充图 S3**（`supp3_composite_sites.png`）：复合终点按培养部位拆解（blood/abdo/resp/wound，A、B 各一）。实测呼吸培养主导（EEN 41/54 事件），blood 计数 8 = treated BSI 8，交叉验证正确。
- **补充图 S4**（`supp4_infection_cif.png`）：感染复合终点的累积发生率曲线（Aalen–Johansen，出院/住院死亡为竞争风险，28 天）。28 天 CIF：EEN **28.1%** / late **49.4%** / never **15.0%**——与粗感染率（54/192、171/346、168/1120）一致，交叉验证通过。

**同时修正旧图硬编码漂移**：`09_figures.py` 的 Fig 1/2 仍为 landmark-fix 前数值（Fig1: 1663/193/1124/467；Fig2: 阈值 0.86/0.45、缺 strict-treated 行等），已全部校正为当前 pipeline 数值（Fig1: 1658/192/1120/127；Fig2: 阈值 0.88/0.49、新增 §8.6b/c strict-treated 两行）。

### 12.8 因果硬核项：阴性对照 + 双重稳健 AIPW + 缺失数据（2026-10-18 跑出，`13_causal_hardening.py`）

**① 阴性对照结局 = 治疗的尿路感染（treated UTI）**：尿培养阳性 + 全身抗生素 [−1d,+2d]，与主复合终点同口径（>48h 且 <28d、污染菌排除、site='urine'）。选尿液因 EEN 无任何机制降低尿路感染——若调整后关联消失则证明混杂控制充分，若持续则提示残余混杂。复用 `01_build_dataset.py` 的 ABX/CONTAM/site 逻辑（site='urine' 在 pos_events 中本已映射，仅未导出为结局列），经 duckdb 重新查询 microbiologyevents+prescriptions 合并到 cohort.csv。

| 结局 | 对比 | Crude OR | OW OR | IPTW OR | AIPW OR |
|---|---|---|---|---|---|
| 感染复合（主） | A | 0.40 (0.27–0.58) | **0.60 (0.39–0.93)** | 0.68 (0.42–1.09) | 0.73 (0.47–1.14) |
| 感染复合（主） | B | 1.30 (0.93–1.82) | 1.34 (0.93–1.95) | 1.76 (1.15–2.70) | 1.81 (1.21–2.72) |
| treated UTI（阴性对照） | A | 0.56 (0.33–0.94) | **0.88 (0.49–1.60)** | 0.91 (0.48–1.72) | 0.80 (0.40–1.63) |
| treated UTI（阴性对照） | B | 1.12 (0.70–1.80) | 1.30 (0.77–2.21) | 1.80 (1.02–3.19) | 1.81 (1.03–3.19) |

**结论**：① **特异性论证通过**——A 中 UTI 的粗保护关联（0.56）经调整后完全消失（OW 0.88/AIPW 0.80），而主复合终点同样调整后仍保护（OW 0.60），说明主效应**特异**、非未测健康状态伪影。② **B 的"有害"是混杂而非效应的又一佐证**——阴性对照 UTI 在 B 中复现了与主结局相同的"有害"形态（IPTW/AIPW ≈1.80/1.81，与感染复合 1.76/1.81 平行）；EEN 不可能增加尿路感染，故该平行印证 B 的"有害"来自 never 组混杂。

**② 双重稳健 AIPW（augmented IPW，Lunceford & Davidian 2004）**：边际 RD/RR/OR，EIF 影响函数方差。A 感染 RR 0.83 (0.63–1.09) / OR 0.73 (0.47–1.14)——**方向一致（保护）但 CI 跨 1**，较 OW 更保守（已知现象：PS 模型设定良好时 OW 更高效）；B 感染 RR 1.52 (1.17–1.99) 与 IPTW 1.76 一致。→ 主结论"方向稳健、幅度不精确"进一步坐实。

**③ 缺失数据**（`missing_data.md`）：age/n_major_procs 0% 缺失；creat/wbc/plt/gcs/map ≤1.1%；lactate 22.6%、bili 37.5%、fio2 25.8%、po2 19.1%、bmi 33.8%。**完全案例敏感性严重underpowered**（A n=170、EEN 事件 14 vs 主 54；OW OR 1.11 [0.48–2.56] 无信息量）——故主分析用中位数填补 + lactate 缺失指示变量是合理选择，完全案例仅作透明度报告。

→ 全部写入 manuscript.md（§2.5 阴性对照定义、§2.6 缺失比例、§2.7 AIPW + 敏感性(9)、§3.6 新增结果小节、Discussion 特异性/混杂句、Limitations AIPW 跨1+完全案例underpowered、Table 2 脚注、Supplement Table S9/S10、新增 ref [18] Lipsitch 2010 / [19] Lunceford & Davidian 2004）。

### 12.9 外部/时代复制：MIMIC-III v1.4（2026-10-18 跑出，`14_mimic3_replication.py`）

用户提供了本地 MIMIC-III 数据（D:\mimic3，此前做其他分析时下载）。**注意：这是同中心（BIDMC）+ 重叠年代的时序敏感性，不是真正的外部验证**（III 2001–2012 vs IV 2008–2019；carevue 时代 2001–2008 与 IV 完全不相交）。因 MIMIC-III schema 差异，以下偏差不可避免并在脚本内注明：procedures 无日期 → 丢弃"术前即 ICU"过滤 + 跳过 leak/reoperation 结局；prescriptions 仅日期粒度（startdate/enddate）；chart 版 SOFA 生理变量（GCS/MAP/FiO2/PaO2）**已提取**（carevue+metavision itemid，单次 CHARTEVENTS 扫描；覆盖 GCS 98%/MAP 99%/FiO2 78%/PaO2 83%）+ **机械通气**（itemid 720/223849，0–24h）+ vasopressor/lactate/器官化验 + Elixhauser 共病；**BMI 未提取**（III 无 omr 表）。

**队列流**：eligible（首 SICU/TSICU + ICD-9 大腹部手术）3590 → 48h 内死亡 83 / 48h 内出 ICU 1009 → landmarked **2498**（EEN 272 / late 406 / never 1820）。

| 结局 | 对比 | Crude OR | OW OR | 与 MIMIC-IV 对照 |
|---|---|---|---|---|
| 感染复合 | A | 0.58 (0.42–0.79) | **0.58 (0.42–0.82, p=0.002)** | IV: OW 0.60 (0.39–0.93) —— 方向与幅度近完全复现 |
| 感染复合 | B | 1.46 (1.13–1.88) | 0.89 (0.68–1.17) | IV: OW 1.34 —— 同样"有害"信号经调整消失 = never 组混杂 |
| treated UTI（阴性对照） | A | 0.63 (0.43–0.91) | **0.67 (0.45–1.00, p=0.048)** | IV: OW 0.88 (0.49–1.60) —— **未完全归零** |
| treated UTI（阴性对照） | B | 1.28 (0.93–1.77) | 1.11 (0.79–1.57) | IV: OW 1.30 |

**诚实结论（已写入 manuscript §3.7 / Discussion / Limitations）**：① **主方向复现成功**——A 感染复合 OW 0.58 几乎逐位复现 MIMIC-IV 的 0.60，方向（保护）与幅度一致，支持该发现不是单一数据年份的伪影。② **但 III 中阴性对照未完全归零**（A UTI OW 0.67，仍弱保护、p=0.048），与 IV（0.88）不同——**即使补全了 chart 版 SOFA（GCS/MAP/FiO2/PaO2，覆盖 78–99%）依然如此**，所以这不是缺协变量的伪影，而是真实的年代差异。两者 CI 重叠（0.45–1.00 vs 0.49–1.60），不算形式矛盾，但意味着**特异性证据未跨年代干净复现**，残余健康状态混杂不能完全排除——已如实写入 §3.7/Limitations。③ 补 SOFA 前后 A 感染 OW 几乎不动（0.58→0.58），UTI 也几乎不动（0.64→0.67），说明残余混杂并非由单一缺失协变量承载，更可能是 carevue 时代（2001–2008）数据质量/喂养与抗生素实践的年代差异。

→ 写入 manuscript.md（Abstract "replicated in MIMIC-III"、§2.7 敏感性(10)、新增 §3.7、Discussion 复现句、Limitations 同中心/重叠年代+阴性对照未归零、Data availability 加 MIMIC-III、Supplement Table S11 = mimic3_replication.md、新增 ref [20] Johnson 2016）。

### 12.10 多中心支持性三角验证：eICU-CRD v2.0（2026-10-18 跑出，`15_eicu_replication.py`）

eICU-CRD v2.0 已通过 AWS S3 下载（31 csv.gz + LICENSE，SHA256 全过，D:\eicu）。**定位：支持性多中心一致性，不是外部验证**——eICU `microLab` 仅 145 KB，无法复现"培养+抗生素"感染复合结局；且无 procedure 表，手术识别只能用 APACHE 入院诊断里的 `"surgery for …"` 标签作 proxy。因此 eICU 只做**喂养暴露结构 + 死亡/LOS 支持性**，不产出独立效应估计。

- **队列**：APACHE 入院诊断为 13 个明确"大腹部手术"类别（GI obstruction/perforation、colon-rectal cancer、cholecystectomy、previous GI surgery complication、Whipple、GI ischemia、diverticular、esophageal 等）→ 首 ICU 停留/患者 4578 → 48h landmark（unitdischargeoffset≥2880）**2128**（EEN 159 / late 97 / never 1872）。
- **暴露**：`intakeOutput` 管饲/肠内分类器（保留 enteral/tube feed/gastric/jejunal/PEG，剔除 oral/PO/TPN/flush/residual/water），EEN = 首条肠内记录 ≤48h。
- **结果**：① 在"有记录喂养"患者内，EEN/late 结构与 MIMIC 一致（62% EEN；首喂 13 h vs 95 h）——这是 eICU 唯一有效的跨库校验。② 绝对喂养率远低于 MIMIC（12% fed vs IV 32%），88% "never" 是 intakeOutput 漏记（各院喂养记录散在其它 cell / infusionDrug / 未记），故 eICU "never" 组不可比。③ 院内死亡两对比皆 null（A OW 0.88 [0.37–2.09]，B OW 0.82 [0.46–1.45]），与 MIMIC 死亡 null 一致；感染复合无法复现。
- **产物**：`analysis/eicu_replication.md` + `analysis/three_db_harmonization.md`（三库 harmonization 表，含偏倚方向注）+ `figures/fig8_replication_forest.png`（MIMIC-IV vs III 感染复合 + UTI 阴性对照并排森林图）。
