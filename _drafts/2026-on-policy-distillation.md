# OPD 抗遗忘的证据边界：学生采样与师生分布匹配

<!-- domain: agentic-rl -->
<!-- edition_date: 2026-05-27 -->
<!-- revised_date: 2026-09-06 -->
<!-- revision_note: 将抗遗忘因果解释限定为待验证外推，区分策略KL与token交集，撤回97%重叠率的通用收敛阈值。 -->

`[tech report]` [DeepSeek-V4](#ref-deepseek-v4)（DeepSeek-AI，2026）把 post-training 写成两段：先通过 SFT 和 GRPO 独立培养 domain experts，再用 on-policy distillation 把不同 domain 的能力合并进单一模型。`[tech report]` [MiMo-V2-Flash](#ref-mimo)（小米 LLM-Core）用同样思路把多个 specialist 合并成单一 student，自报以 1/3 总参数对齐 Kimi-K2-Thinking。`[论文]` [SDAR](#ref-sdar)（美团 + 浙大，Lu et al. 2026）把 OPSD 接到 agent RL 上，去掉了推理时的 skill retrieval 依赖。

`[本文归纳]` 这些实践说明 OPD 已被用于能力合并，却没有单独回答它为什么能保留旧能力。本文比较两类证据：一组个人代码实验中，teacher 退化没有同样传给 student；另一组论文实验中，师生高概率 token 的匹配程度影响蒸馏效果。它们支持重视学生采样与师生兼容性，但尚不能证明 on-policy 数据是抗遗忘的唯一原因，或 teacher 质量可以忽略。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

## Minimal Code Editing 实验

`[个人实验]` 出处：[@nrehiew_](#ref-nrehiew2026) 在 X 长文里设计的个人实验任务「Minimal Code Editing」：给定 buggy function，目标是只修 bug，并尽量少改其他代码。他先训练两个 teacher：

| Teacher  | 任务表现 | 通用代码 benchmark (LiveCodeBench) |
|----------|----------|-------------------|
| SFT      | 学会     | 明显退化（catastrophic forgetting） |
| RL       | 学会     | 几乎不退化         |

然后用这两个 teacher 各自做 OPD，观察 student 的结果：

| 路径                   | 任务表现             | 通用代码 benchmark   |
|------------------------|----------------------|---------------------|
| SFT teacher → OPD student | 略超 RL teacher       | 几乎不退化           |
| RL teacher → OPD student  | 略超 RL teacher       | 几乎不退化           |

> 即使 SFT teacher 自己在通用代码上已经退化，从它蒸出来的 OPD student 仍然不退化。

`[本文归纳]` 这个对照说明，teacher 的通用能力退化并不必然按同样方式传给 student。作者将学生自身生成的训练轨迹视为重要解释；但上述对照并未独立消融所有变量，不能排除训练目标、更新幅度和任务配置的影响。

<a id="几何视角-on-policy-data-自带-kl-minimal-约束"></a>

## 学生采样与抗遗忘：已有观察及外推边界

`[论文]` [RL's Razor](#ref-shenfeld2025)（MIT Improbable AI，Shenfeld et al. 2025）给出几何机制：

> 在所有能够解决新任务的策略中，policy gradient 隐式偏向其中「和当前策略 KL 最近」的那一个。

该论文研究在线 RL 的隐式偏置，并在 LLM 与机器人 foundation model 设置中比较策略 KL 距离与遗忘。它为理解在线采样提供了理论参照，但不是对任意 OPD 更新的硬约束：不能由此推导每一步 OPD 都停留在固定 KL 邻域，或一定保留旧能力。

`[论文]` [Dong Nie 2026](#ref-nie2026)（独立研究者，arXiv:2605.22731）从 state distribution 的角度写了同一件事：

| 方法 | 训练 state 来源 |
|------|----------------|
| SFT  | 外部固定数据集 |
| RL   | 当前模型 induced |
| OPD  | 当前模型 induced（student 端） |

`[本文归纳]` OPD 在 student 自己访问的 prefix 上接受 teacher 监督，这与离线拟合 teacher 固定轨迹不同。它是否具有相同的抗遗忘机制，还需要直接测量 OPD 的策略变化与旧任务表现；RL 的结论不能替代这项验证。

<a id="token-视角-高概率交集承担学习"></a>

## 师生高概率 token 的交集提供了哪些学习信号

`[论文]` [Rethinking OPD](#ref-li2026)（清华 THUNLP，Li et al. 2026）报告：OPD 中主要承担学习的部分，是 student 高概率 token 与 teacher 高概率 token 的**交集**，这个集合上承载了 **97-99% 的概率质量**。词表绝大部分位置在 student 端就接近 0 概率，对 reverse-KL 的贡献趋零。具体实验在 R1-Distill-1.5B (student) + JustRL-1.5B / R1-Distill-7B (teacher) 这一组配置上得到：

| Teacher              | 整体强弱 | OPD 结果 |
|----------------------|----------|----------|
| JustRL-1.5B          | 中       | 提升明显 |
| R1-Distill-7B        | 强       | 失败     |

同一篇工作把 top-k token 拆成 overlap（和 teacher top-k 重合）和 non-overlap，单独做消融：

| 训练范围         | 效果              |
|------------------|-------------------|
| 只在 overlap     | 几乎等于完整 top-k OPD |
| 只在 non-overlap | 几乎无效          |

`[本文归纳]` 这里的 token 交集与上一节的策略 KL 不是同一个量。前者比较师生在特定 prefix 上的高概率 token，后者比较策略分布的变化；它们可能相关，但现有材料没有给出等价关系，也没有联合实验说明它们如何共同影响遗忘。

`[论文]` [Rethinking OPD](#ref-li2026) 的另一组实验：Qwen3-1.7B-Base 做 student，用 non-thinking teacher 和 GRPO 后的 thinking teacher 分别蒸馏，基准表现未必更强的 GRPO teacher 蒸馏效果反而更好，论文归因于它和 base student 的 thinking pattern 一致、初始 overlap 更高。

这给出一种 teacher 选型直觉：

> 在两个 teacher 中，基准表现稍弱但与 student thinking pattern 更兼容者，OPD 效果反而更好。

<a id="伪收敛的微观签名"></a>

## loss 下降但任务表现不升：检查师生分布失配

`[论文]` [Rethinking OPD](#ref-li2026) 的 failure mode 分析：per-token reverse-KL 持续下降，loss 数值收敛，downstream 却没有提升。机制是 reverse-KL 可以在很多形态下数值下降：student 将概率从一个错误的非 teacher token 移到另一个错误的非 teacher token 上，per-token loss 仍然下降，overlap 完全不变。student 始终在 teacher 的低概率区重新分配自己的高概率。

诊断时可以同时看下列指标。论文报告的 97–99% 是共享 token 集合承载的概率质量，不是 top-k 集合重叠率的通用验收阈值。

| 训练状态 | per-token reverse-KL | top-k overlap 占比 | downstream metric |
|----------|---------------------|---------------------|-------------------|
| 支持有效学习的现象 | 下降 | 师生高概率 token 逐步对齐 | 上升 |
| 伪收敛    | 下降                | 持平                | 无提升            |

`[本文归纳]` 仅 KL 下降不足以判断训练有效。如果 overlap 持平且下游指标不升，应检查师生分布失配，而不是宣布收敛。[Rethinking OPD](#ref-li2026) 在其失配配置中尝试先做短暂 off-policy 对齐、再恢复 OPD；这是一项具体修法，不是所有训练停滞的默认处置。

<a id="五个正交维度"></a>

## 比较采样、监督范围与 teacher 使用方式

`[本文归纳]` 下表帮助比较文中方案的设计选择。各项可能相互影响，并非已证明独立或穷尽所有方法的坐标系。

| 维度 | 含义 | 主要取值 |
|------|------|---------|
| K1   | student 访问什么训练状态 | 默认 student rollout / Uni-OPD data balancing |
| K2   | 每个 state 上给多少 token 的监督 | sampled-token / top-k / full-vocab |
| K3   | teacher 信号与额外信息 | teacher logits / OPSD self+answer / SDAR privileged context / ROPD rubric |
| K4   | 什么时候相信 teacher | 直接接受 / Uni-OPD margin calibration / SDAR sigmoid gate |
| K5   | OPD 在 pipeline 里的位置 | domain experts 后 consolidation / 与 RL 融合 / RL 的 gated 辅助 |

这五个维度的取值分别对应外部源中的具体设计。

**K1（state coverage）**。默认 student rollout 是 OPD 的标准设定。`[论文]` [Uni-OPD](#ref-hou2026)（浙大 + 腾讯 LLM Department，Hou et al. 2026）给出 data balancing，让 student 持续访问"既不全对也不全错"的 informative state，防止 dense token signal 浪费在饱和或全错的 state 上。`[论文]` [SDAR](#ref-sdar)（美团 + 浙大，Lu et al. 2026）走到另一端，给 teacher 端挂载 privileged retrieved skills，把 teacher 的高概率分布拉到 student 单凭自己无法到达的区域，再蒸馏回 student 权重。

**K2（signal density）**。三种粒度都是 reverse-KL 的不同估计：

| 取值 | 估计性质 | 工程代价 | 默认采用方 |
|------|---------|---------|----------|
| sampled-token | 单样本无偏估计，方差大 | 成本低 | `[论文]` [GKD](#ref-gkd)（Google DeepMind，Agarwal et al. 2023，ICLR 2024）方法学起源；`[工程博客]` [Thinking Machines Lab](#ref-tml-opd) 工程化导读；`[tech report]` 小米 [MiMo-V2-Flash](#ref-mimo) |
| top-k         | 截断到 teacher top-k 上的 reverse-KL | 中等 | `[论文]` [Revisiting OPD](#ref-fu2026)（CASIA SKL-MAIS + UCAS，Fu et al. 2026），自报在长 prefix 上 +19.8% 优于 sampled-token baseline |
| full-vocab    | 固定 prefix 下对全词表求和，不引入 token 子采样误差；仍有轨迹等训练随机性 | 成本高；报告采用 logits 量化、hidden-state cache 等工程优化 | `[tech report]` [DeepSeek-V4](#ref-deepseek-v4) |

**K3（signal source）**。经典 OPD 用 teacher logits（[GKD](#ref-gkd) 范式）。OPSD（On-Policy Self-Distillation）让 teacher 和 student 共享同一份权重，差别只在 teacher 多看了一份 ground-truth answer 作为 prompt 上下文。`[个人实验]` [@nrehiew_](#ref-nrehiew2026) 把 OPSD 的关键写成 teacher 与 student 之间的信息差：teacher 多拿一份答案上下文，参数量可以保持一致。`[论文]` [ROPD](#ref-fang2026)（中科大 + 腾讯，Fang et al. 2026）走得更远：teacher 只给文本答案，rubricator 生成 prompt-specific 的语义评判标准，verifier 用 rubric 给 rollout 打分作为 GRPO-style reward。论文自报 ~10× sample efficiency，黑盒 teacher 也支持。

**K4（signal acceptance）**。`[论文]` [Uni-OPD](#ref-hou2026) 的 outcome-guided margin calibration 显式恢复"正确轨迹的 OPD return > 错误轨迹"这个顺序约束。`[论文]` [SDAR](#ref-sdar) 用 sigmoid gate `g_t = σ(β · sg(Δ_t))` 按师生 log-prob gap 连续调节监督权重。有限的负 gap 仍有大于 0 的权重，因此这是软调权，不是“只接受正 gap”的硬门控。论文报告 privileged context 下 gap 多数为负；这个逐 token 概率比也不等于 top-k 集合重合，不能将两者视为同一个兼容性检测。

**K5（pipeline position）**。三种和 RL 共处的姿态：

| 取值 | 代表方案 | 设计动机 |
|------|---------|---------|
| domain experts 后 consolidation | `[tech report]` [DeepSeek-V4](#ref-deepseek-v4) on-policy distillation consolidation | 先用 SFT / GRPO 独立培养 domain experts，再用 OPD 把不同 domain 的能力合并进单一模型 |
| 与 RL 融合    | `[tech report]` [MiMo-V2-Flash](#ref-mimo) MOPD | dense token reverse-KL 和 sparse outcome reward 双轨叠加 |
| RL 的 gated 辅助 | `[论文]` [SDAR](#ref-sdar) | 主干仍是 GRPO，OPSD 的梯度贡献由 sigmoid 权重连续调节；自报 ALFWorld +9.4%、WebShop +10.2%、Search-QA +7.0% |

`[本文归纳]` 这些项目用于拆开比较，不构成通用分类定理。例如，给 teacher 增加信息会改变其分布，也可能改变 gate 的权重分布；不能假设这些改动的收益可以独立叠加。

## 开放问题

`[本文归纳]` 本文证据留下两个可直接验证的问题：

1. **什么训练状态值得多采样？** [Uni-OPD](#ref-hou2026) 用难度筛选既非全对也非全错的状态。这类状态是否也提供更有效的 teacher 信号，需要结合监督量与最终收益比较，不能由组内奖励有方差直接推出。
2. **策略变化能否预测遗忘？** 在同一组 OPD 对照里，同时测新任务收益、旧任务表现与策略 KL，再检验 token 匹配带来的增益是否伴随不同的遗忘代价。当前跨论文材料不能代替这项实验。

`[本文归纳]` 对已经有 verifier 或 rubric 资产的团队，[ROPD](#ref-fang2026) 给出的范式提供了一条额外路径：这些资产原本服务于 RL reward，原则上也可以充当 OPD 的 teacher 替代。**在这条路径下，白盒对话 teacher 的规模不再是必要条件。**

## Reference

<a id="ref-nrehiew2026"></a>
**[SFT, RL, and On-Policy Distillation Through a Distributional Lens]** [@nrehiew_](https://nrehiew.github.io/blog/sft_rl_opd) 个人 X 长文 / 博客长文，2026-05-10。本文 "Minimal Code Editing" 实验和 OPSD 信息差命题来自这里。`[个人实验 / X 长文]`

<a id="ref-deepseek-v4"></a>
**[DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence]** DeepSeek-AI，2026. [technical report](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro/blob/main/DeepSeek_V4.pdf)。本文用到它的两阶段 post-training：先通过 SFT 和 GRPO 独立培养 domain experts，再通过 on-policy distillation 做统一 consolidation。`[tech report]`

<a id="ref-mimo"></a>
**[MiMo-V2-Flash Technical Report]** Xiaomi LLM-Core，2026. [arXiv:2601.02780](https://arxiv.org/abs/2601.02780)。309B 总 / 15B active MoE；MOPD merging（per-token reverse-KL + verifier outcome reward 双轨）。`[tech report]`

<a id="ref-sdar"></a>
**[SDAR: Self-Distilled Agentic Reinforcement Learning]** Zhengxi Lu et al.，美团 + 浙江大学，2026. [arXiv:2605.15155](https://arxiv.org/abs/2605.15155)。OPSD as gated auxiliary on top of GRPO；privileged context + sigmoid gate。`[arxiv 论文]`

<a id="ref-shenfeld2025"></a>
**[RL's Razor: Why Online Reinforcement Learning Forgets Less]** Idan Shenfeld, Jyothish Pari, Pulkit Agrawal，MIT Improbable AI Lab，2025. [arXiv:2509.04259](https://arxiv.org/abs/2509.04259)。Anti-forgetting 的 KL-minimal 几何机制；在 LLM + robotic foundation model 两类 setting 上验证。`[arxiv 论文]`

<a id="ref-nie2026"></a>
**[Post-Training is About States, Not Tokens]** Dong Nie（独立研究者，ex-UNC），2026. [arXiv:2605.22731](https://arxiv.org/abs/2605.22731)。把 SFT / RL / OPD 重写为 state distribution 上的差异。`[arxiv 论文 / 独立研究者单人]`

<a id="ref-li2026"></a>
**[Rethinking On-Policy Distillation of Large Language Models: Phenomenology, Mechanism, and Recipe]** Yaxuan Li et al.（Ning Ding lab），清华大学 THUNLP，2026. [arXiv:2604.13016](https://arxiv.org/abs/2604.13016)。共享 token 集合承载 97–99% 概率质量；overlap / non-overlap 消融；thinking pattern 选型机制；伪收敛 failure mode 分析。`[arxiv 论文]`

<a id="ref-hou2026"></a>
**[Uni-OPD: Unifying On-Policy Distillation with a Dual-Perspective Recipe]** Wenjin Hou, Hehe Fan et al.，浙江大学 + 腾讯 LLM Department，2026. [arXiv:2605.03677](https://arxiv.org/abs/2605.03677)。Data balancing（K1）+ outcome-guided margin calibration（K4）。`[arxiv 论文]`

<a id="ref-gkd"></a>
**[On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes (GKD)]** Rishabh Agarwal, Nino Vieillard et al.，Google DeepMind，ICLR 2024（arXiv 2023-06）. [arXiv:2306.13649](https://arxiv.org/abs/2306.13649)。OPD 方法学起源；sampled-token reverse-KL 工程实现；students 超越 teacher 的 GSM8K observation。`[arxiv 论文 / 同行评审]`

<a id="ref-tml-opd"></a>
**[On-Policy Distillation]** Thinking Machines Lab 博客，2025 下半年。OPD 范式工程化导读，sampled-token 路径的 reference 实现。`[工程博客]`

<a id="ref-fu2026"></a>
**[Revisiting On-Policy Distillation: Empirical Failure Modes and Simple Fixes]** Yuqian Fu, Dongbin Zhao et al.，中国科学院自动化所（CASIA SKL-MAIS）+ 中国科学院大学 UCAS，2026. [arXiv:2603.25562](https://arxiv.org/abs/2603.25562)。sampled-token 在 long rollout 的 failure modes；teacher top-K local support matching；自报 +19.8%。`[arxiv 论文]`

<a id="ref-fang2026"></a>
**[Rubric-based On-Policy Distillation (ROPD)]** Junfeng Fang, Mao Zheng et al.，中国科学技术大学 USTC + 腾讯，2026. [arXiv:2605.07396](https://arxiv.org/abs/2605.07396)。Rubric-based teacher，黑盒 teacher 支持，自报 ~10× sample efficiency。`[arxiv 论文]`
