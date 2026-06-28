# Rubric 当 reward：可验证答案缺席时，奖励信号往哪拆

<!-- domain: rubrics -->

`[论文]` RLVR 在数学和代码上好用，靠的是答案能自动判对错。一旦任务只满足部分要求、或根本没有单一参考答案，这个前提就没了。`[论文]` [Soft-RLVR](#ref-soft)（Cohere Labs，Dash et al. 2026）把每个 prompt 拆成一组原子要求的 checklist，逐项用 LLM verifier 打分再合成 soft reward，在指令遵循设置上 IFEval 提升至多 **11.1 分**。`[论文]` [VeriGate](#ref-verigate)（马里兰大学，Agrawal et al. 2026）从另一头切：GRPO 用 outcome reward 训练，当一组采样轨迹拿到相同 verifier 分时，group-relative advantage 坍缩到零，梯度消失。

`[本文归纳]` 2026 年上半年，一批互不引用的工作收敛到同一个动作：把一个标量 reward 摊成一组子信号，再聚合回去。**核心论点：rubric 构造（judge 侧把回答拆成要求条目）和 credit assignment（RL 侧把轨迹拆成 step 或 prefix）是同一个分解的两面，一个 rubric 条目就是一个 credit 单元**。这条线上的方案差异，落在五个正交旋钮上。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<figure style="margin: 18px 0 24px;"><svg viewBox="0 0 760 300" width="100%" role="img" aria-label="rubric reward decomposition two faces" style="border:1px solid #2a3441;border-radius:4px;background:#0a1018;"><defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#131922"/><stop offset="1" stop-color="#1a2230"/></linearGradient><style>.t{fill:#e6edf3;font:600 15px Charter,Georgia,serif}.s{fill:#8b97a4;font:12px Charter,Georgia,serif}.m{fill:#5fd0c8;font:12px "JetBrains Mono",monospace}.b{fill:url(#bg);stroke:#3aa89f;stroke-width:1.2;rx:8}</style></defs><text x="380" y="32" text-anchor="middle" class="t" font-size="17">一个标量 reward，两侧分解</text><rect x="40" y="60" width="280" height="170" rx="8" class="b"/><text x="180" y="86" text-anchor="middle" class="t">judge 侧：rubric 构造</text><text x="180" y="110" text-anchor="middle" class="s">holistic 打分 → 拆成要求条目</text><rect x="70" y="128" width="220" height="26" rx="4" fill="#0a1018" stroke="#3aa89f" stroke-width="0.8"/><text x="180" y="146" text-anchor="middle" class="m">checklist item / criterion</text><text x="180" y="184" text-anchor="middle" class="s">Soft-RLVR · ELMES+ · MERIT</text><text x="180" y="206" text-anchor="middle" class="s">Dynamic Rubrics · Eval-Skill</text><rect x="440" y="60" width="280" height="170" rx="8" class="b"/><text x="580" y="86" text-anchor="middle" class="t">RL 侧：credit assignment</text><text x="580" y="110" text-anchor="middle" class="s">outcome reward → 拆到步骤</text><rect x="470" y="128" width="220" height="26" rx="4" fill="#0a1018" stroke="#3aa89f" stroke-width="0.8"/><text x="580" y="146" text-anchor="middle" class="m">step / prefix credit</text><text x="580" y="184" text-anchor="middle" class="s">VeriGate · PUM</text><text x="580" y="206" text-anchor="middle" class="s">Orch-RM (BT pair)</text><line x1="320" y1="145" x2="440" y2="145" stroke="#5fd0c8" stroke-width="1.4" stroke-dasharray="5 4"/><text x="380" y="138" text-anchor="middle" class="m">item = credit</text><text x="380" y="270" text-anchor="middle" class="s">同一个稀疏 / 退化信号问题，分解是共同解</text></svg></figure>

## 触发条件：可验证性是一道谱

`[论文]` 数学和代码处在可验证性谱的一端，正确性能自动判定，reward 退化成 0/1 就够。多要求的指令、开放式写作、教学对话处在另一端，一个回答可能满足三条要求、违反第二条，没有哪个布尔函数能一次判完。[Soft-RLVR](#ref-soft)（Cohere Labs，Dash et al. 2026）把这种情况叫部分可验证（partially verifiable），处理办法是把 prompt 转成原子要求的 checklist，逐项判、给部分得分，把稀疏的全有全无监督换成稠密信号。

`[论文]` 同样的退化在 RL 侧表现为梯度消失。[VeriGate](#ref-verigate)（马里兰大学，Agrawal et al. 2026）指出，GRPO 的组内优势靠采样轨迹之间的差异提供梯度，当 verifier 给一组轨迹打出相同分数时，优势归零、训练停滞。`[本文归纳]` 两侧描述的是同一件事：标量信号在难判定的任务上要么太粗（judge 给不出区分度），要么太稀（RL 没有梯度）。把信号拆细是两侧共同的出路。

## 一个分解，两侧失败

`[本文归纳]` judge 侧和 RL 侧的修法在数学形式上重合。judge 侧把回答拆成要求条目逐条打分，RL 侧把轨迹拆成步骤逐步赋信用，两者都是先把一个标量摊成一组子分、再聚合成训练信号。一个 rubric 条目和一个 credit 单元是同一个对象在两侧的名字。

`[论文]` [VeriGate](#ref-verigate) 的三段设计把这层对应落到三步：verifier 能区分轨迹时让它做主，退化时才启用过程监督；把 Process Reward Model 的步骤分转成 future-cumulated reward，给出延续敏感的信用；再转成 group-normalized token-level 优势，恢复梯度。在 MATH 上训 1.5B 和 7B 的 Qwen2.5-Instruct、六个推理基准评测，平均准确率分别提升约 **20%** 和 **12%**，零梯度失败显著减少。`[论文]` [Soft-RLVR](#ref-soft) 走的是要求轴的对应版本：checklist 逐项分直接当 RL reward，judge 的分解和训练的分解是同一步。

> 把回答按要求拆（judge 侧）和把轨迹按时间拆（RL 侧），是同一个稀疏信号问题的两条解法。

## 切要求，还是切轨迹

`[本文归纳]` 第一个旋钮是切哪个维度。要求轴回答「这个回答好在哪几条」，时间轴回答「这条推理链从哪一步开始变好」。两轴独立，可同时取值。

| 切分维度 | 子信号单位 | 代表方法 | 适用条件 |
|---|---|---|---|
| 要求空间 | checklist 条目 / criterion | Soft-RLVR、MERIT、Dynamic Rubrics | 要求能拆成可独立判定的原子条目 |
| 轨迹时间 | step / prefix | VeriGate、PUM | 任务有可监督的中间步骤（长 CoT、多跳搜索、多步 agent） |

`[论文]` [MERIT](#ref-merit)（华东师大，Yang et al. 2026）在审稿人匹配上切要求轴：把 criterion 级的专长匹配转成可扩展的适配度监督，RL 训一个 assessor 识别论文需要的专长维度，reward 由 paper-specific 专长 rubric 引导的 LLM judge 给出，4B 的 assessor 在适配度分类上超过更大的通用模型。`[论文]` [PUM](#ref-pum)（复旦，Zhou et al. 2026）切时间轴：给每个 prefix 一个 utility 分，在 Best-of-N、beam search 和 RL 上都能当 prefix 级监督，候选池越大、搜索预算越高、规则 reward 越稀疏时收益越明显。

## rubric 从哪来

`[本文归纳]` 第二个旋钮是 rubric 的出处，从人手编写、到每条 query 在线生成、到离线演化成可复用 skill、到训练一个专门的 rubric 生成器，越往后端摊薄单次推理成本、越能跨 query 复用，代价是越依赖一次性离线投入。

`[论文]` [Beyond Rubrics](#ref-evalskill)（浙大 + 小红书，Yue et al. 2026）正面对比前两档：每条 query 在线生成 criteria 会带来推理开销，还容易产出僵硬或对不齐的指引；它的 Eval-Skill 改成离线演化出可复用的评判 skill，每个 domain 只用 100 个 case 演化两阶段，生成后直接注入 judge context，在 RewardBench 2 上给 Qwen3-8B 带来 **+13.44%**、给 DeepSeek-V4-Flash 带来 **+18.51%**。`[论文]` [Dynamic Rubrics](#ref-wang2026)（University of Arizona，Wang & Blanco 2026）走到生成器那一档：先用免训练的方法在数据集和实例两个粒度自动生成 rubric，再用 meta-judge reward 迭代微调一个 rubric 生成器，微调后的 14B 生成器在 rubric 生成上超过更大的闭源模型。

## 把 item 分数锚在结果上

`[本文归纳]` 第三个旋钮是每个子分锚在哪里。锚在 LLM 的主观判断（这一步看起来对不对）容易被 reward hacking，因为打分者和被打分者共享盲区；锚在下游结果（这一步是否真的提升解题率）把信号绑到可验证的终态上，更难被操纵。

`[论文]` [PUM](#ref-pum) 把 prefix 评估从局部步骤正确性改成 prefix gain，定义为用一组轻量 student 模型条件在该 prefix 上、测得的解题率提升量，是 outcome-grounded 的 prefix utility。`[论文]` [VeriGate](#ref-verigate) 把 PRM 步骤分转成 future-cumulated reward，称比直接优化聚合 PRM 分的方法更难被 reward hacking。`[本文归纳]` 两者指向同一条经验：主观步骤分提供密度，结果锚定提供抗操纵性，工程上需要在两者之间取位置。

## 分解引入的新失败模式

`[本文归纳]` 把稀疏信号拆稠密的同时，会引入两个新失败模式。

| 分解带来的好处 | 同时引入的失败模式 | 出处 |
|---|---|---|
| item 平均降低 verifier 噪声 | partial credit 奖励了不完整的回答 | Soft-RLVR |
| policy 自己当 verifier 省掉外部模型 | 自判过宽松导致 reward 通货膨胀，需显式 stabilization | Soft-SVeRL |
| 自动生成 rubric 去掉人工标注 | 评判标准和被评判模型同源，引入 self-preference 偏差 | ELMES+ |

`[论文]` [Soft-RLVR](#ref-soft) 自己形式化了这个 trade-off，并给出 checklist 验证何时比 holistic 验证更可靠的条件；它的自验证变体 Soft-SVeRL 让 policy 兼任 verifier，容易因过宽松的自判把分数单调推高，需要显式稳定化才不至于发散。`[论文]` [ELMES+](#ref-elmes)（华东师大，Liu et al. 2026）报告 LLM judge 的打分方差远低于人类，但带 judge-specific 偏差，典型是 self-preference；它的 SceneGen 模块让评判标准和测试数据共同演化，用分数分布反推过严、过松或区分度弱的 rubric。`[论文]` [Orch-RM](#ref-orchrm)（Rutgers + Salesforce，Tsang et al. 2026）用多 agent 执行的中间产物构造胜负对训 Bradley-Terry reward model，自监督、无人工标注，token 效率提升至多 **10 倍**、MAS 测试时扩展准确率提升至多 **8%**，代价同样是标准由模型自生成。

## 五个旋钮

`[本文归纳]` 把八个方案反向归纳，差异落在五维空间，任一方案对应一个位点。每个旋钮都来自变体集合的实际取值，逐个对回方案核对过。

| 旋钮 | 取值范围 | 落点示例 |
|---|---|---|
| K1 切分维度 | 要求空间 ↔ 轨迹时间 | Soft-RLVR（要求）/ VeriGate（时间） |
| K2 rubric 出处 | 人手 → 在线 → 可复用 skill → 生成器 | Eval-Skill（可复用）/ Dynamic Rubrics（生成器） |
| K3 item grounding | LLM 主观判 ↔ outcome-grounded | MERIT（主观）/ PUM（结果锚定） |
| K4 聚合方式 | 平均 partial credit / gate / BT pair / token 优势 | Soft-RLVR / VeriGate / Orch-RM |
| K5 verifier 身份 | 外部独立 ↔ self-verify | Soft-RLVR（外部）/ Soft-SVeRL（自验） |

`[本文归纳]` 五个旋钮彼此正交，挑任务时先定 K1（任务有没有可监督的中间步骤），再定 K3（有没有可测的下游结果决定能否结果锚定），K5 的自验证档要配 K4 的显式稳定化才安全。这组划分等更多方案进来再验证是否完备，出现切第三维或两轴塌成一轴就要修订。

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
