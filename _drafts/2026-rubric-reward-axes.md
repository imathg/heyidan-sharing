# Rubric 奖励与步骤信用：两种细化训练信号的方法

<!-- domain: rubrics -->
<!-- edition_date: 2026-06-14 -->
<!-- revised_date: 2026-09-06 -->
<!-- revision_note: 区分按要求评分与按时间步骤分配信用，撤回“rubric条目就是credit单元”的等同表述。 -->

一个回答可能满足内容要求，却违反格式要求；一条最终失败的轨迹，也可能包含正确的中间步骤。前者需要按要求评分，后者需要给步骤分配信用。两者都能让训练信号更细，但评分对象不同，不能直接互换。

`[论文]` [Soft-RLVR](#ref-soft) 用原子要求 checklist 形成部分得分，在其指令遵循设置上 IFEval 提升至多 **11.1 分**；[VeriGate](#ref-verigate) 则在 GRPO 的组内轨迹全部取得 0 分时引入步骤监督。`[本文归纳]` 本文比较这两类方法的信号对象、来源、聚合和偏差，不把 rubric 条目等同于某个时间步骤的贡献，也不将跨论文对照当作统一数学证明。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<figure style="margin: 18px 0 24px;"><svg viewBox="0 0 760 300" width="100%" role="img" aria-label="按要求评分与按步骤分配信用的区别" style="border:1px solid #2a3441;border-radius:4px;background:#0a1018;"><defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#131922"/><stop offset="1" stop-color="#1a2230"/></linearGradient><style>.t{fill:#e6edf3;font:600 15px Charter,Georgia,serif}.s{fill:#8b97a4;font:12px Charter,Georgia,serif}.m{fill:#5fd0c8;font:12px "JetBrains Mono",monospace}.b{fill:url(#bg);stroke:#3aa89f;stroke-width:1.2;rx:8}</style></defs><text x="380" y="32" text-anchor="middle" class="t" font-size="17">按要求评分与按步骤分配信用</text><rect x="40" y="60" width="280" height="170" rx="8" class="b"/><text x="180" y="86" text-anchor="middle" class="t">judge 侧：rubric 构造</text><text x="180" y="110" text-anchor="middle" class="s">holistic 打分 → 拆成要求条目</text><rect x="70" y="128" width="220" height="26" rx="4" fill="#0a1018" stroke="#3aa89f" stroke-width="0.8"/><text x="180" y="146" text-anchor="middle" class="m">checklist item / criterion</text><text x="180" y="184" text-anchor="middle" class="s">Soft-RLVR · ELMES+ · MERIT</text><text x="180" y="206" text-anchor="middle" class="s">Dynamic Rubrics · Eval-Skill</text><rect x="440" y="60" width="280" height="170" rx="8" class="b"/><text x="580" y="86" text-anchor="middle" class="t">RL 侧：credit assignment</text><text x="580" y="110" text-anchor="middle" class="s">outcome reward → 拆到步骤</text><rect x="470" y="128" width="220" height="26" rx="4" fill="#0a1018" stroke="#3aa89f" stroke-width="0.8"/><text x="580" y="146" text-anchor="middle" class="m">step / prefix credit</text><text x="580" y="184" text-anchor="middle" class="s">VeriGate · PUM</text><text x="580" y="206" text-anchor="middle" class="s">Orch-RM (BT pair)</text><line x1="320" y1="145" x2="440" y2="145" stroke="#5fd0c8" stroke-width="1.4" stroke-dasharray="5 4"/><text x="380" y="138" text-anchor="middle" class="m">对象不同</text><text x="380" y="270" text-anchor="middle" class="s">要求条目与时间步骤并非一一对应；组合使用需要明确映射</text></svg></figure>

<a id="触发条件-可验证性是一道谱"></a>

## 回答只满足部分要求时，怎样给训练信号

`[论文]` 数学题的答案核对、代码的测试用例可以提供自动验证信号；但即使能判定最终成功与否，二值奖励也未必足以区分训练中的候选。多要求的指令、开放式写作和教学对话还可能只满足部分要求。[Soft-RLVR](#ref-soft)（Cohere Labs，Dash et al. 2026）将 prompt 转成原子要求的 checklist，逐项判断并给部分得分，让未完全合格的回答之间也能形成差异。

`[论文]` [VeriGate](#ref-verigate)（马里兰大学，Agrawal et al. 2026）处理另一种情况：GRPO 的组内优势依赖采样轨迹之间的得分差异，一组轨迹获得相同 outcome 分时，这部分优势归零。[其方法](https://arxiv.org/html/2605.30451v1#S3.SS1) 只在组内轨迹全部为 0 分时引入步骤监督，不包括全部为 1 分的组。`[本文归纳]` 这里的问题是组内缺少差异，不是“标量”这种表示本身有问题；按要求评分和按步骤监督，最终都可以汇总成标量奖励。

<a id="一个分解-两侧失败"></a>

## 按要求评分与按步骤分配信用，回答不同问题

`[本文归纳]` rubric 条目说明输出满足了哪项要求；步骤信用说明某个动作或前缀怎样影响后续回报。一项要求可能依赖多个步骤，一个步骤也可能同时影响多项要求。两者可以在同一训练中组合，但需要另行定义要求与步骤的对应关系；仅有逐项得分，不能恢复每一步的贡献。

`[论文]` [VeriGate](#ref-verigate) 在组内轨迹全部失败时启用过程监督，其他组保留 outcome reward；它累加 Process Reward Model 的后续步骤分，形成 future-cumulated reward，再转成 group-normalized token-level 优势。这里累加的是 PRM 预测分，不是后续真实执行结果。在 MATH 上训练 1.5B 和 7B 的 Qwen2.5-Instruct，并在六个推理基准上评测，平均准确率分别提升约 **20%** 和 **12%**，零梯度失败显著减少。`[论文]` [Soft-RLVR](#ref-soft) 则聚合 checklist 逐项分作为 RL reward。前者补的是步骤监督，后者补的是要求维度的部分得分。

> 细化要求有助于判断回答哪里不合格；细化时间步骤有助于定位过程贡献。是否组合，以及怎样组合，要由任务和可取得的证据决定。

## 切要求，还是切轨迹

`[本文归纳]` 首先区分切分对象。要求维度回答「这个回答好在哪几条」，时间维度回答「这条推理链从哪一步开始变好」。可以同时描述二者，但方法之间的联合效果仍需实验。

| 切分维度 | 子信号单位 | 代表方法 | 适用条件 |
|---|---|---|---|
| 要求空间 | checklist 条目 / criterion | Soft-RLVR、MERIT、Dynamic Rubrics | 要求能拆成可独立判定的原子条目 |
| 轨迹时间 | step / prefix | VeriGate、PUM | 任务有可监督的中间步骤（长 CoT、多跳搜索、多步 agent） |

`[论文]` [MERIT](#ref-merit)（华东师大，Yang et al. 2026）在审稿人匹配上切要求轴：把 criterion 级的专长匹配转成可扩展的适配度监督，RL 训一个 assessor 识别论文需要的专长维度，reward 由 paper-specific 专长 rubric 引导的 LLM judge 给出，4B 的 assessor 在适配度分类上超过更大的通用模型。`[论文]` [PUM](#ref-pum)（复旦，Zhou et al. 2026）切时间轴：给每个 prefix 一个 utility 分，在 Best-of-N、beam search 和 RL 上都能当 prefix 级监督，候选池越大、搜索预算越高、规则 reward 越稀疏时收益越明显。

## rubric 从哪来

`[本文归纳]` 第二个维度是 rubric 的出处：从人手编写，到每条 query 在线生成，再到离线演化为可复用 skill，或训练专门的 rubric 生成器。后两种方式更能摊薄单次推理成本并跨 query 复用，代价是更依赖一次性离线投入。

`[论文]` [Beyond Rubrics](#ref-evalskill)（浙大 + 小红书，Yue et al. 2026）直接比较了前两档：每条 query 在线生成 criteria 会带来推理开销，也容易产生僵硬或与任务不一致的指引；Eval-Skill 改为离线演化可复用的评判 skill，每个 domain 只用 100 个 case 演化两阶段，随后直接注入 judge context，在 RewardBench 2 上给 Qwen3-8B 带来 **+13.44%**、给 DeepSeek-V4-Flash 带来 **+18.51%**。`[论文]` [Dynamic Rubrics](#ref-wang2026) 采用生成器路线：先用免训练的方法在数据集和实例两个粒度自动生成 rubric，再用 meta-judge reward 迭代微调一个 rubric 生成器，微调后的 14B 生成器在 rubric 生成上超过更大的闭源模型。

<a id="把-item-分数锚在结果上"></a>

## 区分预测步骤分与实测结果增益

`[本文归纳]` 分数来自模型预测，还是来自后续执行测得的结果，会改变它能支持什么判断。两者都需要可靠性检查；不能仅凭“结果锚定”这个名称，就保证分数不会被操纵。

`[论文]` [PUM](#ref-pum) 用一组轻量 student 模型从指定 prefix 继续求解，以实测解题率增益定义 prefix utility。[VeriGate §3.2](https://arxiv.org/html/2605.30451v1#S3.SS2) 则累加后续 PRM 分数，让当前步骤的信用考虑预测的后续质量。前者测量求解结果，后者仍依赖 PRM；不能把 VeriGate 也当作真实结果锚定，再由两者共同推出抗 reward-hacking 的保证。

## 分解引入的新失败模式

`[本文归纳]` 细化或自动生成评分信号，还可能引入下面几类问题。

| 分解带来的好处 | 同时引入的失败模式 | 出处 |
|---|---|---|
| item 平均降低 verifier 噪声 | partial credit 奖励了不完整的回答 | Soft-RLVR |
| policy 自己当 verifier 省掉外部模型 | 自判过宽松导致 reward 通货膨胀，需显式 stabilization | Soft-SVeRL |
| 自动生成 rubric 去掉人工标注 | 评判标准和被评判模型同源，引入 self-preference 偏差 | ELMES+ |

`[论文]` [Soft-RLVR](#ref-soft) 形式化了这个 trade-off，并给出 checklist 验证何时比 holistic 验证更可靠的条件；它的自验证变体 Soft-SVeRL 让 policy 兼任 verifier，容易因过宽松的自判将分数单调推高，需要显式稳定化以维持训练稳定。`[论文]` [ELMES+](#ref-elmes)（华东师大，Liu et al. 2026）报告 LLM judge 的打分方差远低于人类，但带 judge-specific 偏差，典型是 self-preference；它的 SceneGen 模块让评判标准和测试数据共同演化，用分数分布反推过严、过松或区分度弱的 rubric。`[论文]` [Orch-RM](#ref-orchrm)（Rutgers + Salesforce，Tsang et al. 2026）用多 agent 执行的中间产物构造胜负对训练 Bradley-Terry reward model，自监督、无人工标注，token 效率提升至多 **10 倍**、MAS 测试时扩展准确率提升至多 **8%**，代价同样是标准由模型自生成。

<a id="五个维度"></a>

## 选择方法前，先确认信号对象、来源与可靠性

`[本文归纳]` 下表归纳八个方案的比较项目。它用于分辨方法差异，不证明这些项目相互独立或覆盖全部设计。

| 维度 | 取值范围 | 落点示例 |
|---|---|---|
| K1 切分维度 | 要求空间 ↔ 轨迹时间 | Soft-RLVR（要求）/ VeriGate（时间） |
| K2 rubric 出处 | 人手 → 在线 → 可复用 skill → 生成器 | Eval-Skill（可复用）/ Dynamic Rubrics（生成器） |
| K3 item grounding | LLM 主观判 ↔ outcome-grounded | MERIT（主观）/ PUM（结果锚定） |
| K4 聚合方式 | 平均 partial credit / gate / BT pair / token 优势 | Soft-RLVR / VeriGate / Orch-RM |
| K5 verifier 身份 | 外部独立 ↔ self-verify | Soft-RLVR（外部）/ Soft-SVeRL（自验） |

`[本文归纳]` 选择方法时先看能取得什么证据：任务要求能否逐项判断，有没有可监督的中间步骤，能否测量后续结果。再检查评分者的偏差和聚合方式。自验证带来的宽松打分、部分得分奖励不完整回答等问题，都不能靠增加条目数量自动消除。

## Reference

<a id="ref-soft"></a>
**[Soft-SVeRL: Self-Verified Reinforcement Learning with Soft Rewards]** Saurabh Dash, Pierre Clavier, John Dang, Matthias Galle, Marzieh Fadaee, Ahmet Üstün, Beyza Ermis，Cohere Labs，2026. [arXiv:2605.28561](https://arxiv.org/abs/2605.28561)。部分可验证任务的 checklist soft reward 与自验证 reward 通胀。`[arxiv 论文]`

<a id="ref-verigate"></a>
**[VeriGate: Verifier-Gated Step-Level Supervision for GRPO]** Aakriti Agrawal, Minghui Liu, Furong Huang，University of Maryland, College Park，2026. [arXiv:2605.30451](https://arxiv.org/abs/2605.30451)。outcome 退化时的 advantage 坍缩与 step-level future-cumulated 信用。`[arxiv 论文]`

<a id="ref-evalskill"></a>
**[Beyond Rubrics: Exploration-Guided Evaluation Skills for Reward Modeling]** Xing Yue, Linjuan Wu, Daoxin Zhang, Yongliang Shen, Weiming Lu，浙江大学 + 小红书，2026. [arXiv:2606.07040](https://arxiv.org/abs/2606.07040)。per-query rubric 生成与可复用 evaluation skill 的对比。`[arxiv 论文]`

<a id="ref-elmes"></a>
**[ELMES+: Automated Construction of Fine-Grained Evaluation Rubrics for LLMs in Long-Tail Educational Scenarios]** Tao Liu, Ye Lu, Ruohua Zhang, Siyu Song, Wentao Liu, Aimin Zhou, Hao Hao，华东师范大学（上海智能教育研究院），2026. [arXiv:2606.06546](https://arxiv.org/abs/2606.06546)。评判标准与测试数据共同演化、LLM judge 的 self-preference 偏差。`[arxiv 论文]`

<a id="ref-wang2026"></a>
**[Generating and Refining Dynamic Evaluation Rubrics for LLM-as-a-Judge]** Zijie Wang, Eduardo Blanco，University of Arizona，2026. [arXiv:2605.30568](https://arxiv.org/abs/2605.30568)。免训练自动生成 rubric 与 meta-judge 微调 rubric 生成器。`[arxiv 论文]`

<a id="ref-pum"></a>
**[From Correctness to Utility: Gain-Based Prefix Evaluation for LLM Reasoning]** Yuhang Zhou, Yixin Cao, Guangnan Ye，复旦大学，2026. [arXiv:2606.07190](https://arxiv.org/abs/2606.07190)。用 prefix gain（解题率提升）替代局部步骤正确性的 outcome-grounded 信用。`[arxiv 论文]`

<a id="ref-orchrm"></a>
**[Reward Modeling for Multi-Agent Orchestration]** King Yeung Tsang, Zihao Zhao, Vishal Venkataramani, Haizhou Shi, Zixuan Ke, Semih Yavuz, Shafiq Joty, Hao Wang，Rutgers University + Salesforce AI Research，2026. [arXiv:2606.13598](https://arxiv.org/abs/2606.13598)。用执行中间产物构造 Bradley-Terry 对的自监督 orchestration reward。`[arxiv 论文]`

<a id="ref-merit"></a>
**[MERIT: Matching Expertise via Rubric-Informed Training for Reviewer Assignment]** Zixuan Yang, Yibo Zhao, Weicong Liu, Xiang Li，华东师范大学，2026. [arXiv:2605.27865](https://arxiv.org/abs/2605.27865)。criterion 级专长匹配转成可扩展适配度监督。`[arxiv 论文]`
