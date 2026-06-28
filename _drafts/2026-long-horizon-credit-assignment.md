# 长程 credit assignment：奖励信号该在轨迹的哪一层附着

<!-- domain: agentic-rl -->

2026 年 6 月，七个互不隶属的团队动的是同一件事：GRPO 给长程 agent 分配 credit 的方式。`[论文]` [HSD](#ref-hsd)（George Washington University，Li et al. 2026）把 token 级 credit 定位到失败与成功路径的分叉处；`[论文]` [SCPO](#ref-scpo)（香港科技大学广州，Xu et al. 2026）从同组成功 sibling 恢复 step 级 credit；`[论文]` [HiMPO](#ref-himpo)（中国联通，Yan et al. 2026）只给 memory 写入动作单独的 credit 通道；`[论文]` [VIMPO](#ref-vimpo)（UC Berkeley，Kang et al. 2026）从 KL 最优性条件解析地读出 per-step value；`[论文]` [Progress Advantage](#ref-progress-advantage)（威斯康星大学麦迪逊分校，Oh et al. 2026）用训练策略与参考策略的对数概率比当 step 信号；`[论文]` [BiPACE](#ref-bipace)（芝加哥大学 + 斯坦福 + 美团等，Wang et al. 2026）按行为相似度聚类 step、给每类动作配反事实基线；`[论文]` [多步 tool-use RL 失稳分析](#ref-tooluse-collapse)（中科院自动化所，Hao et al. 2026）诊断这套训练为什么会失稳、外部监督怎么救它。

这七篇调的是同一组旋钮，针对的是同一个失败模式。

> **核心论点：GRPO 把一条轨迹的成败压成一个数，均匀盖到轨迹里每个 token。长程、稀疏奖励下，这个数分不清「失败轨迹上的好步」和「成功轨迹上的坏步」。七个配方都在做同一件事，在不训练 critic 的前提下给每个 step 估一个反事实基线，分歧只在「反事实从哪里取」。**

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<svg viewBox="0 0 780 500" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GRPO 把轨迹级 advantage 均匀盖到每个 token；七个方法按附着粒度（横轴）和反事实参照系（颜色）分布">
  <defs>
    <linearGradient id="lhbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#131922"/>
      <stop offset="1" stop-color="#1a2230"/>
    </linearGradient>
    <marker id="lharrow" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto">
      <path d="M0 0 L8 4 L0 8 Z" fill="#5b6a76"/>
    </marker>
  </defs>
  <rect x="0" y="0" width="780" height="500" rx="14" fill="url(#lhbg)"/>
  <text x="390" y="36" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="18.5" font-weight="600" fill="#e8eef2">长程 credit assignment：七个配方补的是同一个洞</text>
  <text x="390" y="59" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="12.5" fill="#8a96a0">失败模式 → 缺的 per-step 反事实基线 → 三种取法（颜色） × 附着粒度（横轴）</text>
  <g font-family="-apple-system,Segoe UI,sans-serif">
    <rect x="36" y="80" width="206" height="36" rx="8" fill="#222d36" stroke="#3a4550"/>
    <text x="139" y="98" text-anchor="middle" font-size="11.5" font-weight="600" fill="#c2ccd4">GRPO：轨迹级 advantage</text>
    <text x="139" y="111" text-anchor="middle" font-size="11" fill="#8a96a0">一条轨迹压成一个数</text>
    <line x1="242" y1="98" x2="286" y2="98" stroke="#5b6a76" stroke-width="1.6" marker-end="url(#lharrow)"/>
    <circle cx="306" cy="98" r="6" fill="#4a5560"/>
    <circle cx="332" cy="98" r="6" fill="#4a5560"/>
    <circle cx="358" cy="98" r="6" fill="#4a5560"/>
    <circle cx="384" cy="98" r="6" fill="#4a5560"/>
    <circle cx="410" cy="98" r="6" fill="#4a5560"/>
    <text x="440" y="102" text-anchor="start" font-size="11.5" fill="#f0a868">每个 token 同值，分不清好步与坏步（秩退化）</text>
  </g>
  <line x1="36" y1="134" x2="744" y2="134" stroke="#2a343d" stroke-width="1"/>
  <line x1="110" y1="392" x2="110" y2="158" stroke="#27313a" stroke-width="1" stroke-dasharray="3 4"/>
  <line x1="320" y1="392" x2="320" y2="158" stroke="#27313a" stroke-width="1" stroke-dasharray="3 4"/>
  <line x1="500" y1="392" x2="500" y2="158" stroke="#27313a" stroke-width="1" stroke-dasharray="3 4"/>
  <line x1="648" y1="392" x2="648" y2="158" stroke="#27313a" stroke-width="1" stroke-dasharray="3 4"/>
  <g font-family="-apple-system,Segoe UI,sans-serif">
    <rect x="42" y="222" width="136" height="42" rx="8" fill="#1c2630" stroke="#4d5a64" stroke-dasharray="4 3"/>
    <text x="110" y="241" text-anchor="middle" font-size="12" font-weight="600" fill="#8a96a0">GRPO 基线</text>
    <text x="110" y="256" text-anchor="middle" font-size="10" fill="#6b7785">一个数盖整条</text>
    <rect x="252" y="166" width="136" height="42" rx="8" fill="#1c2630" stroke="#5fd0c8"/>
    <text x="320" y="185" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5fd0c8">SCPO</text>
    <text x="320" y="200" text-anchor="middle" font-size="10" fill="#8a96a0">成功 sibling 语义一致</text>
    <rect x="252" y="218" width="136" height="42" rx="8" fill="#1c2630" stroke="#a89af0"/>
    <text x="320" y="237" text-anchor="middle" font-size="12.5" font-weight="600" fill="#a89af0">BiPACE</text>
    <text x="320" y="252" text-anchor="middle" font-size="10" fill="#8a96a0">行为聚类 + 动作反事实</text>
    <rect x="252" y="270" width="136" height="42" rx="8" fill="#1c2630" stroke="#f0a868"/>
    <text x="320" y="289" text-anchor="middle" font-size="12.5" font-weight="600" fill="#f0a868">Progress Advantage</text>
    <text x="320" y="304" text-anchor="middle" font-size="10" fill="#8a96a0">训练/参考策略对数比</text>
    <rect x="432" y="166" width="136" height="42" rx="8" fill="#1c2630" stroke="#5fd0c8"/>
    <text x="500" y="185" text-anchor="middle" font-size="12.5" font-weight="600" fill="#5fd0c8">HSD</text>
    <text x="500" y="200" text-anchor="middle" font-size="10" fill="#8a96a0">成功 peer 分叉处定位</text>
    <rect x="432" y="218" width="136" height="42" rx="8" fill="#1c2630" stroke="#f0a868"/>
    <text x="500" y="237" text-anchor="middle" font-size="12.5" font-weight="600" fill="#f0a868">VIMPO</text>
    <text x="500" y="252" text-anchor="middle" font-size="10" fill="#8a96a0">策略隐含 value，终止锚定</text>
    <rect x="580" y="166" width="136" height="42" rx="8" fill="#1c2630" stroke="#a89af0"/>
    <text x="648" y="185" text-anchor="middle" font-size="12.5" font-weight="600" fill="#a89af0">HiMPO</text>
    <text x="648" y="200" text-anchor="middle" font-size="10" fill="#8a96a0">仅 memory token 单独通道</text>
  </g>
  <line x1="56" y1="392" x2="724" y2="392" stroke="#3a4550" stroke-width="2" marker-end="url(#lharrow)"/>
  <g font-family="-apple-system,Segoe UI,sans-serif">
    <circle cx="110" cy="392" r="5" fill="#5b6a76"/>
    <circle cx="320" cy="392" r="5" fill="#5fd0c8"/>
    <circle cx="500" cy="392" r="5" fill="#5fd0c8"/>
    <circle cx="648" cy="392" r="5" fill="#5fd0c8"/>
    <text x="110" y="413" text-anchor="middle" font-size="11.5" fill="#c2ccd4">轨迹</text>
    <text x="320" y="413" text-anchor="middle" font-size="11.5" fill="#c2ccd4">step</text>
    <text x="500" y="413" text-anchor="middle" font-size="11.5" fill="#c2ccd4">token</text>
    <text x="648" y="413" text-anchor="middle" font-size="11.5" fill="#c2ccd4">动作子集</text>
    <text x="732" y="396" text-anchor="start" font-size="10.5" fill="#6b7785">附着粒度（粗→细）</text>
  </g>
  <g font-family="-apple-system,Segoe UI,sans-serif" font-size="11">
    <rect x="36" y="440" width="13" height="13" rx="3" fill="#5fd0c8"/>
    <text x="55" y="451" fill="#c2ccd4">成功轨迹参照（别的轨迹同处怎么做对）</text>
    <rect x="400" y="440" width="13" height="13" rx="3" fill="#f0a868"/>
    <text x="419" y="451" fill="#c2ccd4">当前策略参照（相对起点进步多少）</text>
    <rect x="36" y="464" width="13" height="13" rx="3" fill="#a89af0"/>
    <text x="55" y="475" fill="#c2ccd4">同类动作/状态参照（结构等价处本该如何）</text>
    <rect x="400" y="464" width="13" height="13" rx="3" fill="#e57373"/>
    <text x="419" y="475" fill="#c2ccd4">成本另一端：内生信号失效时需外部监督（tool-use 失稳分析）</text>
  </g>
</svg>

## 失败模式：一个数盖整条轨迹

group-based RL（GRPO 是代表）的做法是采一组 rollout，用每条的终局成败算一个轨迹级 advantage，并把这个 advantage 原样发给该轨迹里的每一个 token。单步任务里这没问题，一次问答就是一个 step，终局即 step。长程 agent 不一样：一条轨迹是几十步工具调用、几十轮对话，奖励只在最后才给。一个数盖整条轨迹，等于声明这条轨迹里所有 step 一样好或一样坏。

`[论文]` [SCPO](#ref-scpo) 把这个问题说得最干脆：一个 step 的 credit 绑死在它所在 rollout 的终局上，于是语义近乎相同的两个中间步，因为各自轨迹最终一个成功一个失败，拿到符号相反的 credit。`[论文]` [HiMPO](#ref-himpo) 指出长程 agent 里的具体后果：一次有用的 memory 写入会因为下游工具失败、噪声观测被连坐惩罚，模型于是学会丢掉有用证据。`[论文]` [VIMPO](#ref-vimpo) 从算法侧点出根本原因，group-relative 方法回避了 critic，代价是只能给出轨迹级 advantage，对每个 token 取同一个值。

这三种描述是同一件事的三个切面。轨迹级 advantage 是一种秩退化的 credit，它在「这一步本身贡献多少」这个维度上没有分辨率。轨迹越长、奖励越稀疏，退化越严重。`[论文]` [多步 tool-use RL 失稳分析](#ref-tooluse-collapse) 报告了退化的终点，在多步工具调用上只靠 RL 常常训练不稳定，或几乎拿不到增益。

| 论文 | 同一失败模式的不同说法 |
|---|---|
| `[论文]` SCPO | 语义近乎相同的中间步，因终局成败拿到符号相反的 credit |
| `[论文]` HiMPO | memory 写入被下游工具失败连坐，归因失真，模型丢掉有用证据 |
| `[论文]` VIMPO | group-relative 免 critic，代价是只有轨迹级 advantage，每个 token 同值 |
| `[论文]` tool-use 失稳分析 | 多步工具调用上只靠 RL 常导致训练不稳定，或拿不到增益 |

## 缺的那个对象：critic 本会给的 per-step 基线

actor-critic 方法本来有一个部件专门解这个问题。critic 估「从这一步往后的期望回报」，于是每个 step 都有自己的基线，advantage 是当前回报减去这个基线。问题是 critic 自己要训练，而且训练起来不稳定。GRPO 把 critic 砍掉换来简单，砍掉的同时也丢了 per-step 基线。

`[本文归纳]` 七篇里有六篇明确强调自己 critic-free、value-free 或 annotation-free。这六种方法估的是同一个被砍掉的对象：critic 本该提供的 per-step 反事实基线。区别只在一点，不训 critic 的话，这个基线的代理从哪里取。三种取法：

`[本文归纳]` **取自同组的成功轨迹。** `[论文]` [HSD](#ref-hsd) 不拿标准答案作 teacher 的条件，改用当前训练组里成功的 peer rollout，让信号集中在失败路径与成功路径分叉的 token。`[论文]` [SCPO](#ref-scpo) 同源，但落在 step 层：给定一个中间步，到成功 sibling 里找它语义对应的那一步，看它在成功路径里出不出现。这一派的反事实是「别的轨迹在同一处怎么做对的」。

`[本文归纳]` **取自当前策略自身。** `[论文]` [VIMPO](#ref-vimpo) 从 KL 正则 RL 的最优性条件导出策略隐含的 value，自回归生成下这个 value 写成策略与参考策略的对数比，由「轨迹末端没有未来奖励」这个终止条件锚定，于是不训 critic 也拿到一个 value 损失。`[论文]` [Progress Advantage](#ref-progress-advantage) 用训练策略与参考策略的对数概率比直接当 advantage，并论证它恢复了最优 advantage 函数。这一派的反事实是「当前策略相对它的起点进步了多少」，信号本就在训练管线里。

`[本文归纳]` **取自同类的动作或状态。** `[论文]` [BiPACE](#ref-bipace) 按行为相似度把 step 聚类，给每一类动作配一个 action-specific 基线，一个 step 的 credit 与「同类动作在别处表现如何」对齐。`[论文]` [HiMPO](#ref-himpo) 对 memory 写入估 local utility，比较「同一写入前状态下，旧 memory 与更新后 memory 各能恢复多少任务相关信息」。这一派的反事实是「结构上等价的动作或状态本该是什么样」。

| 反事实参照系 | 方法 | 取的是 |
|---|---|---|
| 同组成功轨迹 | HSD、SCPO | 别的轨迹在同一处怎么做对的 |
| 当前策略自身 | VIMPO、Progress Advantage | 当前策略相对起点进步了多少 |
| 同类动作或状态 | BiPACE、HiMPO | 结构上等价的动作或状态本该是什么样 |

这三派回答的是同一个问题的不同侧面，原则上可以叠加，比如同组成功 sibling 定位粗位置，action-cluster 基线在该位置上细化。

## 四个旋钮

`[本文归纳]` 七个方案的差异落在四个维度的取值组合上，各自是这四维空间里的一个位点。

| 旋钮 | 取值范围 | 各方法落点 |
|---|---|---|
| 附着粒度 | 轨迹 / token / step / 动作子集 | 轨迹（GRPO 基线）；token（HSD、VIMPO）；step（SCPO、BiPACE、Progress Advantage）；动作子集（HiMPO 只管 memory token） |
| 反事实参照系 | 成功轨迹 / 当前策略 / 同类动作 | 见上一节三派 |
| 额外部件成本 | 零成本到外部监督 | 管线副产物零成本（Progress Advantage）；解析 value 无新增部件（VIMPO）；critic-free 但加一道塑形或聚类（HSD、SCPO、BiPACE、HiMPO）；需要外部监督注入（tool-use 失稳分析） |
| 时序方向 | 回溯 / 前瞻 | 回溯，用已实现的终局或成功 sibling（HSD、SCPO、HiMPO）；前瞻，估未来期望（VIMPO、Progress Advantage） |

附着粒度是最直接的一条轴。从轨迹往下走到 token，credit 的分辨率越来越高，但定位越来越难。`[论文]` [HSD](#ref-hsd) 在 token 层用分叉点解决定位，它在简答任务（AIME）上增益更大，说明分叉点集中时定位最划算；长链推理里分叉分散，这条收益下降。`[论文]` [HiMPO](#ref-himpo) 走了另一个极端，不追求全轨迹细粒度，只把一类最容易被连坐的动作（memory 写入）单独拎出来走一条去纠缠的通道，其余 token 仍走轨迹级。这是一种以约束换稳健的取法，只解一类动作，但解得干净。

时序方向这条轴和反事实参照系有关联。用同组成功轨迹当参照的方法本就是回溯的，因为「成功」是已实现的事实。用当前策略当参照的方法偏前瞻，估的是期望。两条轴在已知的七个样本里没完全分开，正交性要更多方案才能判定。

## 成本那一端：什么时候免不了外部监督

前六篇的共同主张是省掉 critic。`[论文]` [多步 tool-use RL 失稳分析](#ref-tooluse-collapse) 站在成本谱的另一端，它的结论是有些情况下省不掉外部信号。这篇先诊断多步 tool-use RL 为什么会失稳，再考察哪些监督信号能稳住训练，包括 off-policy 监督和 hint-based 引导。

`[本文归纳]` 把它和前六篇对照，得到一条边界：内生的反事实基线（从成功轨迹、当前策略或同类动作里挖出来的信号）在奖励虽稀疏但同组里存在成功路径时够用；当一组 rollout 全错、没有成功 sibling 可对照，或动作空间稀疏到聚不出可靠的同类，内生信号本身就失效了，这时候得从外部灌入 off-policy 数据或 hint。成本最低的 Progress Advantage 是零成本管线副产物，成本最高的这一端要专门准备外部监督数据，四个旋钮里「额外部件成本」这一轴的两端就是这两篇。

## 与单步 RLVR、与蒸馏的边界

`[本文归纳]` 这条线和单步 RLVR 的目标函数变体（GRPO 的裁剪、归一化、优势估计那些轴）落在不同层。目标函数变体改的是单步上损失怎么算，这条线改的是 credit 沿一条长轨迹怎么附着。在单步任务上两者重合，因为终局就是唯一的 step；任务越长，本文这条轴越独立。

`[本文归纳]` 它和 on-policy 蒸馏也有结构上的呼应。蒸馏那条线的核心是「用 teacher 信号在 student 自己的状态分布里做选择性强化」，本文这条线的核心是「在 student 自己的轨迹里做选择性 credit 分配」。HSD 把蒸馏的形式（teacher 以成功 peer 为条件）直接搬来做 credit 定位，是两条线交汇的一个具体点。一个开放问题是这两套旋钮能不能收进同一个更大的框架，都看成「在 student 自分布里，按某个反事实参照做选择性加权」。

> **一句话收束：长程 agent 的 credit assignment 问题，是 GRPO 砍掉 critic 后留下的洞。2026 年 6 月这一批方法都在补这个洞，补法的差异可以收进四个旋钮，最关键的一个是反事实基线从哪里取。**

## Reference

<a id="ref-hsd"></a>
**[Localizing Credit at the Divergence: Path-Conditioned Self-Distillation for LLM Reasoning]** Yu Li, Shu Hong, Tian Lan，George Washington University（Dept. of Electrical and Computer Engineering），2026. [arXiv:2606.15576](https://arxiv.org/abs/2606.15576)。本文用到它的 token 级 credit 定位在失败与成功路径分叉处、teacher 以同组成功 peer rollout 为条件。`[arxiv 论文]`

<a id="ref-himpo"></a>
**[HiMPO: Hindsight-Informed Memory Policy Optimization for Less-Entangled Credit in Long-Horizon Agents]** Jiangze Yan, Yi Shen, Wenjing Zhang, Jieyun Huang, Zhaoxiang Liu, Ning Wang, Kai Wang, Shiguo Lian，China Unicom（Unicom Data Intelligence / Data Science & AI Research Institute），2026. [arXiv:2606.16285](https://arxiv.org/abs/2606.16285)。本文用到它的 memory-write credit 去纠缠、advantage 只施加在 memory token、hindsight relevance 作 bounded filter。`[arxiv 论文]`

<a id="ref-vimpo"></a>
**[VIMPO: Value-Implicit Policy Optimization for LLMs]** Zhewei Kang, Aosong Feng, Sergey Levine, Dawn Song, Xuandong Zhao，UC Berkeley（Aosong Feng 在 Yale），2026. [arXiv:2606.20008](https://arxiv.org/abs/2606.20008)。本文用到它从 KL 正则 RL 最优性条件导出 policy-implied value、终止条件锚定、把奖励吸收与策略改进分开。`[arxiv 论文]`

<a id="ref-scpo"></a>
**[Semantic Consistency Policy Optimization for Reinforcement Learning of LLM Agents]** Peng Xu, Sijia Chen, Junzhuo Li, Xuming Hu，The Hong Kong University of Science and Technology (Guangzhou)，2026. [arXiv:2606.25852](https://arxiv.org/abs/2606.25852)。本文用到它 value-free 从同组成功 sibling 恢复 step 级 credit、ALFWorld 93.7±4.1% / WebShop 74.8±2.0%（1.5B）。`[arxiv 论文]`

<a id="ref-progress-advantage"></a>
**[Neglected Free Lunch from Post-training: Progress Advantage for LLM Agents]** Changdae Oh, Wendi Li, Seongheon Park, Samuel Yeh, Tanwi Mallick, Sharon Li，University of Wisconsin–Madison（Tanwi Mallick 在 Argonne National Laboratory），2026. [arXiv:2606.26080](https://arxiv.org/abs/2606.26080)。本文用到它用训练策略与参考策略的对数概率比当 step 信号、恢复最优 advantage、annotation-free 管线副产物。`[arxiv 论文]`

<a id="ref-bipace"></a>
**[BiPACE: Bisimulation-Guided Policy Optimization with Action Counterfactual Estimation for LLM Agents]** Hanyang Wang, Weijieying Ren, Yuxiang Zhang, Ding Cao, Zhizhao Zeng, Ke Zeng, Tianxiang Zhao，University of Chicago / Stanford University / HKUST (Guangzhou) / USTC / Meituan，2026. [arXiv:2606.25556](https://arxiv.org/abs/2606.25556)。本文用到它按行为相似度聚类 step（bisimulation）、给每类动作配 action-specific 反事实基线。`[arxiv 论文]`

<a id="ref-tooluse-collapse"></a>
**[Why Multi-Step Tool-Use Reinforcement Learning Collapses and How Supervisory Signals Fix It]** Yupu Hao, Zhuoran Jin, Huanxuan Liao, Kang Liu, Jun Zhao，中科院自动化所（认知与决策智能重点实验室）+ 中国科学院大学人工智能学院，2026. [arXiv:2606.26027](https://arxiv.org/abs/2606.26027)。本文用作成本谱另一端的对照：多步 tool-use RL 失稳诊断、off-policy 与 hint-based 外部监督稳住训练。`[arxiv 论文]`
