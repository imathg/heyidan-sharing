# OPD：on-policy 数据是抗遗忘的真正承担者

<!-- domain: agentic-rl -->
<!-- edition_date: 2026-05-27 -->

`[tech report]` [DeepSeek-V4](#ref-deepseek-v4)（DeepSeek-AI，2026）把 post-training 写成两段：先通过 SFT 和 GRPO 独立培养 domain experts，再用 on-policy distillation 把不同 domain 的能力合并进单一模型。`[tech report]` [MiMo-V2-Flash](#ref-mimo)（小米 LLM-Core）用同样思路把多个 specialist 合并成单一 student，自报以 1/3 总参数对齐 Kimi-K2-Thinking。`[论文]` [SDAR](#ref-sdar)（美团 + 浙大，Lu et al. 2026）把 OPSD 接到 agent RL 上，去掉了推理时的 skill retrieval 依赖。

`[本文归纳]` 近期实践已将 OPD 从「另一种 post-training 选项」变为前沿模型能力整合的常用组件。**本文的核心论点：OPD 的抗遗忘能力主要由 student 自己生成的 on-policy data 承担；teacher 的 token-level 监督负责在这些 state 上提供 credit assignment**。teacher 可以替换、可以退化、甚至可以是 student 自己；失去 on-policy data 后，整条机制会退化为带噪声的 SFT。

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

teacher 的能力表现（一个退化、一个保留）和 student 的能力表现（均未退化，且都超过 RL teacher）出现错配。可解释的变量只剩一个：student 的 rollout 由 student 自己产生。

## 几何视角：on-policy data 自带 KL-minimal 约束

`[论文]` [RL's Razor](#ref-shenfeld2025)（MIT Improbable AI，Shenfeld et al. 2025）给出几何机制：

> 在所有能够解决新任务的策略中，policy gradient 隐式偏向其中「和当前策略 KL 最近」的那一个。

SFT 将模型拉向一个外部固定分布，这个分布可以离起点任意远；RL 则将模型推向「距离当前策略最近的能解题策略」。抗遗忘来自 on-policy sampling 自带的几何性质：每一步 update 的目标都被限制在距离当前策略最近的解集合里。该论文在 LLM 和机器人 foundation model 两类设置上验证了 KL distance 与 forgetting magnitude 的相关性。

`[论文]` [Dong Nie 2026](#ref-nie2026)（独立研究者，arXiv:2605.22731）从 state distribution 的角度写了同一件事：

| 方法 | 训练 state 来源 |
|------|----------------|
| SFT  | 外部固定数据集 |
| RL   | 当前模型 induced |
| OPD  | 当前模型 induced（student 端） |

`[本文归纳]` OPD 的抗遗忘沿用了这条几何约束。teacher 提供 token-level credit assignment，student 训练时访问的 prefix（state distribution）由 student 自己产生。teacher 退化主要落在 teacher 自己 rollout 的分布上；student 训练时访问的是 student-induced prefix。

## Token 视角：高概率交集承担学习

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

`[本文归纳]` 这是同一个机制的两层投影。宏观层面，update 被限制在 student 当前分布的 KL 邻域（[RL's Razor](#ref-shenfeld2025)）；微观层面，有效梯度集中在 student/teacher 高概率 token 的 overlap 上（[Rethinking OPD](#ref-li2026)）。「student 当前分布」在 token level 就是 student 在自己访问的 state 上倾向产出的 high-probability token；「和 teacher 一致的部分」是这些 token 中也属于 teacher 高概率的子集。

`[论文]` [Rethinking OPD](#ref-li2026) 的另一组实验：Qwen3-1.7B-Base 做 student，用 non-thinking teacher 和 GRPO 后的 thinking teacher 分别蒸馏，基准表现未必更强的 GRPO teacher 蒸馏效果反而更好，论文归因于它和 base student 的 thinking pattern 一致、初始 overlap 更高。

这给出一种 teacher 选型直觉：

> 在两个 teacher 中，基准表现稍弱但与 student thinking pattern 更兼容者，OPD 效果反而更好。

## 伪收敛的微观签名

`[论文]` [Rethinking OPD](#ref-li2026) 的 failure mode 分析：per-token reverse-KL 持续下降，loss 数值收敛，downstream 却没有提升。机制是 reverse-KL 可以在很多形态下数值下降：student 将概率从一个错误的非 teacher token 移到另一个错误的非 teacher token 上，per-token loss 仍然下降，overlap 完全不变。student 始终在 teacher 的低概率区重新分配自己的高概率。

监控诊断表（沿用 [Rethinking OPD](#ref-li2026) 的 R1-Distill 配置阈值）：

| 训练状态 | per-token reverse-KL | top-k overlap 占比 | downstream metric |
|----------|---------------------|---------------------|-------------------|
| 有效收敛  | 下降                | 单调上升至 ≥97%     | 上升              |
| 伪收敛    | 下降                | 持平                | 无提升            |

实操结论：**将 student top-token 与 teacher top-token 的重叠率作为核心监控指标，仅 KL 下降不足以判定训练有效。** overlap 持平、KL 下降、downstream 无提升同时出现时，可判定训练进入伪收敛区。补救方式是先做一轮短暂的 off-policy distillation 以对齐 prior，再恢复 OPD。该 failure mode 在 thinking pattern mismatch 的 teacher-student 组合上高频出现。

## 五个正交维度

`[本文归纳]` 将 sampled-token、top-k、full-vocab、OPSD、ROPD、SDAR、Uni-OPD、MOPD 等 10+ 个 2026 方案归入 5 个维度的不同取值组合。

| 维度 | 含义 | 主要取值 |
|------|------|---------|
| K1   | student 探索什么 state | 默认 student rollout / Uni-OPD data balancing / SDAR privileged context |
| K2   | 每个 state 上给多少 token 的监督 | sampled-token / top-k / full-vocab |
| K3   | teacher 信号的源 | teacher logits / OPSD self+answer / ROPD rubric |
| K4   | 什么时候相信 teacher | 直接接受 / Uni-OPD margin calibration / SDAR sigmoid gate |
| K5   | OPD 在 pipeline 里的位置 | domain experts 后 consolidation / 与 RL 融合 / RL 的 gated 辅助 |

这五个维度的取值分别对应外部源中的具体设计。

**K1（state coverage）**。默认 student rollout 是 OPD 的标准设定。`[论文]` [Uni-OPD](#ref-hou2026)（浙大 + 腾讯 LLM Department，Hou et al. 2026）给出 data balancing，让 student 持续访问"既不全对也不全错"的 informative state，防止 dense token signal 浪费在饱和或全错的 state 上。`[论文]` [SDAR](#ref-sdar)（美团 + 浙大，Lu et al. 2026）走到另一端，给 teacher 端挂载 privileged retrieved skills，把 teacher 的高概率分布拉到 student 单凭自己无法到达的区域，再蒸馏回 student 权重。

**K2（signal density）**。三种粒度都是 reverse-KL 的不同估计：

| 取值 | 估计性质 | 工程代价 | 默认采用方 |
|------|---------|---------|----------|
| sampled-token | 单样本无偏估计，方差大 | 成本低 | `[论文]` [GKD](#ref-gkd)（Google DeepMind，Agarwal et al. 2023，ICLR 2024）方法学起源；`[工程博客]` [Thinking Machines Lab](#ref-tml-opd) 工程化导读；`[tech report]` 小米 [MiMo-V2-Flash](#ref-mimo) |
| top-k         | 截断到 teacher top-k 上的 reverse-KL | 中等 | `[论文]` [Revisiting OPD](#ref-fu2026)（CASIA SKL-MAIS + UCAS，Fu et al. 2026），自报在长 prefix 上 +19.8% 优于 sampled-token baseline |
| full-vocab    | 零方差、零偏差 | 成本高：teacher logits 需 FP4 量化 + hidden state cache 才能容纳 10+ specialist | `[tech report]` [DeepSeek-V4](#ref-deepseek-v4) |

**K3（signal source）**。经典 OPD 用 teacher logits（[GKD](#ref-gkd) 范式）。OPSD（On-Policy Self-Distillation）让 teacher 和 student 共享同一份权重，差别只在 teacher 多看了一份 ground-truth answer 作为 prompt 上下文。`[个人实验]` [@nrehiew_](#ref-nrehiew2026) 把 OPSD 的关键写成 teacher 与 student 之间的信息差：teacher 多拿一份答案上下文，参数量可以保持一致。`[论文]` [ROPD](#ref-fang2026)（中科大 + 腾讯，Fang et al. 2026）走得更远：teacher 只给文本答案，rubricator 生成 prompt-specific 的语义评判标准，verifier 用 rubric 给 rollout 打分作为 GRPO-style reward。论文自报 ~10× sample efficiency，黑盒 teacher 也支持。

**K4（signal acceptance）**。`[论文]` [Uni-OPD](#ref-hou2026) 的 outcome-guided margin calibration 显式恢复"正确轨迹的 OPD return > 错误轨迹"这个顺序约束。`[论文]` [SDAR](#ref-sdar) 的 sigmoid gate `g_t = σ(β · sg(Δ_t))` 更细：teacher 与 student log-prob gap 为正时放大、为负时压制。论文报告带 privileged context 的 teacher 在 student 实际采到的 token 上 gap **多数情况为负**；privileged context 把 teacher 分布拉偏到了 student 无法自主到达的区域，只接受正 gap 等于做 overlap 对齐检测。

**K5（pipeline position）**。三种和 RL 共处的姿态：

| 取值 | 代表方案 | 设计动机 |
|------|---------|---------|
| domain experts 后 consolidation | `[tech report]` [DeepSeek-V4](#ref-deepseek-v4) on-policy distillation consolidation | 先用 SFT / GRPO 独立培养 domain experts，再用 OPD 把不同 domain 的能力合并进单一模型 |
| 与 RL 融合    | `[tech report]` [MiMo-V2-Flash](#ref-mimo) MOPD | dense token reverse-KL 和 sparse outcome reward 双轨叠加 |
| RL 的 gated 辅助 | `[论文]` [SDAR](#ref-sdar) | 主干仍是 GRPO，OPSD 仅在 gate 通过时贡献梯度；自报 ALFWorld +9.4%、WebShop +10.2%、Search-QA +7.0% |

`[本文归纳]` 五个维度彼此正交，任何一个 2026 工业方案都对应五维空间里的一个具体位点。相比将它们视为 10+ 个独立技术，将其理解为 5 维参数空间里的 10+ 个位点更清楚。

## 开放问题

`[本文归纳]` 理想 post-training 算法的设计目标是：**兼具 distillation 的密度、RL 的无偏性，同时保持 on-policy 的几何性质**。同时满足这三条的算法目前仍是 open problem。outcome reward 过于稀疏，PRM 训练不稳定，logit distillation 有 bias，因此需要 clipping。

围绕这个目标，两个延伸方向：

1. **informative state 的结构化定义**。[Uni-OPD](#ref-hou2026) 用难度做代理（不全对也不全错），是经验启发式；RL 框架里它对应 group advantage variance > 0；OPD 框架里应该有一个更准的描述。这两个写法对应同一个量吗？
2. **KL-tradeoff Pareto frontier 的可操作化**。把每种 post-training 方法画在 "capability gain vs KL move" 平面上目前是 conceptual layer。实际可采集的训练 metric 到该平面的映射、对应的离线评估流程，都是 open。

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
**[Rethinking On-Policy Distillation of Large Language Models: Phenomenology, Mechanism, and Recipe]** Yaxuan Li et al.（Ning Ding lab），清华大学 THUNLP，2026. [arXiv:2604.13016](https://arxiv.org/abs/2604.13016)。97-99% overlap window；overlap / non-overlap 消融；thinking pattern 选型机制；伪收敛 failure mode 分析。`[arxiv 论文]`

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
