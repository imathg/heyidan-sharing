# OPD 稳定域：teacher 监督信号的失真路径与修复

<!-- domain: agentic-rl -->

`[本文归纳]` 2026 年上半年，OPD（on-policy distillation）研究的焦点从「如何纳入 post-training pipeline」转向「何时失效」。半年内至少十篇论文分别报告了一种失效路径：prefix 变长后 teacher 失去判别力、teacher-student 分布差过大导致优化失败、异步训练下 rollout 变旧、聚合目标造成长度捷径。这些结果共同指向同一个图景：

> `[本文归纳]` OPD 的 token 级监督只在有限区域内可靠，区域的边界由 teacher 判别力的覆盖范围决定。prefix 变长、分布差拉大、rollout 变旧，是 student 状态离开这个区域的三种方式。各家修复方案的目标高度一致：将训练拉回这个区域，或在区域边缘修复监督信号本身。

下文称这个区域为**稳定域**。已发布的 [OPD 机制篇](../on-policy-distillation/) 从 token 级观测给出了这个稳定域的两个切面：有效梯度集中在 student/teacher 高概率 token 的交集上；交集不动而 KL 下降，就是伪收敛。2026 年的这批论文将这些切面扩展为完整的失效分类，并给出一组可操作的修复手段。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<figure class="diagram">
<svg width="100%" viewBox="0 0 820 620" xmlns="http://www.w3.org/2000/svg" role="img" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">
<defs><linearGradient id="panelGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#131922"/><stop offset="100%" stop-color="#1a2230"/></linearGradient><linearGradient id="nodeGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#131922"/><stop offset="100%" stop-color="#1a2230"/></linearGradient><linearGradient id="pseudoGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#10151d"/><stop offset="100%" stop-color="#151b25"/></linearGradient><marker id="arrowMuted" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#2a3441"/></marker><marker id="arrowCyan" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#5fd0c8"/></marker></defs>
<rect width="820" height="620" fill="#0d1117"/>
<text x="410" y="36" text-anchor="middle" fill="#e6edf3" font-size="24" font-weight="650">OPD 稳定域</text>
<text x="410" y="58" text-anchor="middle" fill="#8b97a4" font-size="13">teacher 仍能有效判别的 student 状态区域 · 三条离域路径与三类修复</text>
<rect x="60" y="80" width="210" height="85" rx="12" fill="url(#nodeGrad)" stroke="#2a3441"/>
<text x="78" y="108" fill="#e6edf3" font-size="14" font-weight="600">沿生成轴</text><text x="78" y="130" fill="#8b97a4" font-size="12.5">prefix 变长 → teacher 分布趋平</text><rect x="78" y="140" width="35" height="16" rx="8" fill="#202b37"/><text x="95.5" y="152" text-anchor="middle" fill="#8b97a4" font-size="11.5">SFD</text>
<rect x="305" y="80" width="210" height="85" rx="12" fill="url(#nodeGrad)" stroke="#2a3441"/>
<text x="323" y="108" fill="#e6edf3" font-size="14" font-weight="600">沿模型轴</text><text x="323" y="130" fill="#8b97a4" font-size="12.5">分布差过大 → 梯度不可靠</text><rect x="323" y="140" width="84" height="16" rx="8" fill="#202b37"/><text x="365" y="152" text-anchor="middle" fill="#8b97a4" font-size="11.5">TrOPD · TRB</text>
<rect x="550" y="80" width="210" height="85" rx="12" fill="url(#nodeGrad)" stroke="#2a3441"/>
<text x="568" y="108" fill="#e6edf3" font-size="14" font-weight="600">沿时间轴</text><text x="568" y="130" fill="#8b97a4" font-size="12.5">rollout 变旧 → 信号过期</text><rect x="568" y="140" width="65" height="16" rx="8" fill="#202b37"/><text x="600.5" y="152" text-anchor="middle" fill="#8b97a4" font-size="11.5">AsyncOPD</text>
<path d="M165 195 L165 165" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrowMuted)"/><text x="178" y="184" fill="#8b97a4" font-size="11.5">离域</text>
<path d="M410 195 L410 165" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrowMuted)"/><text x="423" y="184" fill="#8b97a4" font-size="11.5">离域</text>
<path d="M440 195 L440 181 L655 181 L655 165" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrowMuted)"/><text x="584" y="176" fill="#8b97a4" font-size="11.5">离域</text>
<rect x="60" y="195" width="380" height="135" rx="18" fill="url(#panelGrad)" stroke="#2a3441"/>
<text x="84" y="228" fill="#e6edf3" font-size="14" font-weight="650">稳定域</text><text x="84" y="258" fill="#8b97a4" font-size="12.5">token 级监督可靠</text><text x="84" y="282" fill="#8b97a4" font-size="12.5">有效梯度集中在 student/teacher 高概率交集</text>
<rect x="500" y="195" width="260" height="135" rx="18" fill="url(#panelGrad)" stroke="#2a3441"/>
<text x="522" y="220" fill="#e6edf3" font-size="14" font-weight="650">修复：三类信号调控</text>
<rect x="520" y="231" width="220" height="24" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="532" y="248" fill="#e6edf3" font-size="12.5">限域 · trust region/warmup</text>
<rect x="520" y="265" width="220" height="24" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="532" y="282" fill="#e6edf3" font-size="12.5">重加权 · drift gating</text>
<rect x="520" y="299" width="220" height="24" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="532" y="316" fill="#e6edf3" font-size="12.5">信号替换 · 重算或 delta/lookahead</text>
<path d="M500 282 L440 282" fill="none" stroke="#5fd0c8" stroke-width="1.5" stroke-dasharray="7 5" marker-end="url(#arrowCyan)"/><text x="470" y="270" text-anchor="middle" fill="#5fd0c8" font-size="11.5">回归域内</text>
<path d="M250 330 L250 385" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrowMuted)"/><text x="263" y="362" fill="#8b97a4" font-size="11.5">离域后的表现</text>
<rect x="60" y="385" width="700" height="60" rx="12" fill="url(#panelGrad)" stroke="#2a3441"/>
<text x="84" y="421" fill="#e6edf3" font-size="14" font-weight="650">行为签名</text>
<rect x="180" y="398" width="160" height="34" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="260" y="420" text-anchor="middle" fill="#e6edf3" font-size="12.5">长度捷径 · reward 上升</text>
<rect x="352" y="398" width="185" height="34" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="444.5" y="420" text-anchor="middle" fill="#e6edf3" font-size="12.5">后缀重复 · rollout 变长</text>
<rect x="549" y="398" width="185" height="34" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="641.5" y="420" text-anchor="middle" fill="#e6edf3" font-size="12.5">伪收敛 · KL 降</text>
<path d="M175 445 L175 505" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58"/><path d="M410 445 L410 505" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58"/><path d="M645 445 L645 505" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58"/>
<g opacity="0.78"><rect x="60" y="505" width="230" height="70" rx="12" fill="url(#pseudoGrad)" stroke="#2a3441"/><text x="78" y="533" fill="#e6edf3" font-size="14" font-weight="600" opacity="0.70">稳定域外 · context 内化</text><text x="78" y="555" fill="#8b97a4" font-size="12.5" opacity="0.70">context 重现时性能反而下降</text></g>
<g opacity="0.78"><rect x="295" y="505" width="230" height="70" rx="12" fill="url(#pseudoGrad)" stroke="#2a3441"/><text x="313" y="533" fill="#e6edf3" font-size="14" font-weight="600" opacity="0.70">稳定域外 · 置信度校准</text><text x="313" y="555" fill="#8b97a4" font-size="12.5" opacity="0.70">置信度位置依赖</text></g>
<g opacity="0.78"><rect x="530" y="505" width="230" height="70" rx="12" fill="url(#pseudoGrad)" stroke="#2a3441"/><text x="548" y="533" fill="#e6edf3" font-size="14" font-weight="600" opacity="0.70">补充视角 · 参数几何</text><text x="548" y="555" fill="#8b97a4" font-size="12.5" opacity="0.70">低维子空间锁定</text></g>
</svg>
</figure>

## 信号失真的三条路径

`[本文归纳]` 失稳的触发条件可以按 student 状态离开稳定域的方式分成三条路径，每条路径均有独立论文描述其机制，并提出修复方案：

| 失真路径 | 触发条件 | 机制 | 代表论文 |
|---|---|---|---|
| 沿生成轴 | prefix 变长 | teacher next-token 分布趋平，纠偏项衰减 | SFD（中科院软件所 + 小红书） |
| 沿模型轴 | teacher-student 分布差大 | reverse-KL 估计器给出不可靠梯度 | TrOPD（三星北京研究院） |
| 沿时间轴 | rollout 变旧（异步训练） | reverse-KL 信号基于过期的 student 分布计算 | AsyncOPD（FuriosaAI） |

`[论文]` [SFD 论文](#ref-liu2026)（中科院软件所 + 小红书，Liu et al. 2026）将沿生成轴的失真命名为 Supervision Fidelity Decay：student 自生成的 prefix 越长，teacher 的 next-token 分布置信度越低、判别力越弱，reverse-KL 里依赖 teacher 的纠偏信号随之衰减，student 的漂移会沿推理链逐步累积。这解释了为什么长生成任务上失真最重：他们的修复（用下一步的 teacher 置信度评估 top-K 候选 token，按组归一化后作为奖励）在 39k token 的 AIME-26 上取得 **+4.92** 的最大增益，六个数学与代码 benchmark 平均 +2.57。

`[论文]` [TrOPD](#ref-xing2026)（三星北京研究院，Xing et al. 2026）描述了沿模型轴的失真：teacher 和 student 分布差过大时，由 teacher 对 student 生成 token 的监督导出的 policy gradient 会变得不可靠，直至优化失败。修复是只在 teacher 监督可靠的区域做 OPD，外围区域改用梯度裁剪、掩码或 forward-KL。`[个人实验]` 工程侧也有相同判断：[@nrehiew_](#ref-nrehiew2026) 在 X 的推文中认为 teacher 应选同族模型，否则分布距离过大。`[论文]` [TRB](#ref-plyusov2026)（T-Tech，Plyusov et al. 2026）处理的是同一路径在训练早期的特例：student 起点弱，rollout 质量差，teacher 监督集中在低质量 prefix 上。修复是 warmup 阶段在以 student 为中心的 KL 信赖域内，选择与 teacher 最接近的行为策略来生成 rollout，KL 预算退火到零后回到纯 on-policy。

`[论文]` 沿时间轴的失真来自异步训练系统：rollout 生成和 learner 更新解耦后，训练数据来自过期的 student 分布。[AsyncOPD](#ref-kang2026)（FuriosaAI，Kang et al. 2026）的系统性结论是 KL 方向决定脆弱性：teacher 加权的 forward KL 对 stale rollout 稳健，student 加权的 reverse KL 对 stale rollout 脆弱。将异步 RL 的稳定化手段用于 OPD，收效有限；更有效的是 OPD 专用的替代方案：在 learner 更新时，用当前 student 重算 reverse-KL 信号。配合多样本 Monte Carlo 压低方差，异步管线将吞吐提高 **1.6 到 3.8 倍**，精度与同步训练相当。

## 行为签名：训练曲线与真实能力脱钩

`[本文归纳]` 三条失真路径反映在训练曲线上，都表现为指标发生变化，能力却保持不变。行为签名有三个，检测量各不相同：

| 签名 | 表象 | 实际发生的事 | 检测量 |
|---|---|---|---|
| 长度捷径 | reward 上升 | student 用截断或冗余填充套取聚合目标的奖励 | 长度分布 vs 任务正确率 |
| 后缀重复 | rollout 变长 | 恢复预算花在低信息量的重复后缀上 | teacher 确认的重复后缀占比 |
| 伪收敛 | KL 下降 | 高概率 token 交集不动，能力无迁移 | top-K overlap（见[机制篇](../on-policy-distillation/)） |

`[论文]` 长度捷径由 [Demystifying OPD](#ref-ruiwang2026)（港中文 + 腾讯 AI Lab，Rui Wang et al. 2026）系统刻画。这篇论文先界定 OPD 的作用：它是探索催化剂（exploration catalyst），通过密集的 token 级引导将 student 引向正确推理路径，并不扩展能力上限；prompt 多样性比单题采样数更重要。明确这一定位后，两个病理就有了统一解释：师生失配（Student-Teacher Mismatch）指引导信号与任务正确性错位（沿模型轴失真的行为面）；长度套取（Length Exploitation）指聚合 token 目标造成的长度依赖捷径，student 探索的是退化的长度模式，偏离推理策略。他们的结论不再以 teacher 规模为重心：**调控后的信号质量，而非 teacher 大小，决定 OPD 成败**。

`[论文]` 后缀重复来自压缩恢复场景。[ShortOPD](#ref-zhang2026)（字节跳动 + 中科院软件所，Zhang et al. 2026）观察到结构化剪枝后的模型 greedy pass@1 几乎归零，pass@k 却大幅可恢复，说明压缩降低了有用生成结果的概率，这些结果仍对应分布中的低概率区域，重复采样就能找回；可恢复区域的主要失效模式是后缀重复，长 rollout 会将早期用于恢复性能的 rollout 预算耗在这些低信息后缀上。修复是检测 teacher 确认的重复后缀，将重复开始前的存活 prefix 作为有效长度，按由短到长的训练日程（short-to-long）分配 rollout 预算：把分数恢复到未恢复值的约 **9 倍**，以四分之一训练时间（8.5 小时 vs 35.9 小时）达到与固定 8192-token 方案相当的性能。

## 修复方案收敛为三类信号调控

`[本文归纳]` 2026 年各篇提出的修复方案，可以按调控对象划为三类。每类回答一个问题：在哪里训练（限域）、给各位置的信号多大权重（重加权）、用什么量做监督（信号替换）。

| 类别 | 做法 | 代表方案 |
|---|---|---|
| 限域 | 只在信号可靠的区域训练 | TrOPD 信赖域、TRB warmup、异常值掩码（outlier masking） |
| 重加权 | 按可靠性缩放各位置的损失 | 按块漂移门控（blockwise drift gating）、优势裁剪（advantage clipping）、对数压缩（log-scale compression） |
| 信号替换或重算 | 换一个更可靠的监督量 | learner 时重算（AsyncOPD）、delta signal（OPD²）、lookahead group reward（SFD） |

`[论文]` 重加权类里有一个直接来自 student 自身漂移的控制信号。[Blockwise Policy-Drift Gating](#ref-zheng2026)（独立研究者 Zheng & Jiang 2026）在 rollout 复用场景下，用行为 student 与当前 student 在采样 token 路径上的 log-prob 偏移（按 64-token 块聚合、去梯度、均值归一）重加权各位置损失，不改动 teacher 目标，也不改动 rollout 策略，四个数学 benchmark 的 mean pass@8 从 0.4978 提到 **0.5160**。信号完全来自 student 侧，说明是否离开稳定域可仅用 student 自己的信息检测。

`[论文]` 信号替换类的代表方案之一是 [OPD²](#ref-heo2026)（NAVER AI Lab，Heo et al. 2026）：不再直接模仿 teacher 输出分布，改用 delta signal，即 teacher 与其推理调优前的 base model 之间的分布差。这个信号只保留推理调优带来的分布变化，剔除了 teacher 分布里与推理能力无关的部分，在数学、科学、代码 benchmark 上稳定超过常规 OPD。

`[论文]` 工程侧的实现碎片化也表明可调控的维度很多：[EasyOPD](#ref-sun2026)（中科大 + 腾讯，Sun et al. 2026）指出现有 OPD 实现「在监督形式、tokenizer 兼容性、teacher 访问方式、监督粒度上差异巨大，难以复现和扩展」，作者据此基于 verl 构建了统一框架。

## 稳定域之外：内化与校准的两类病理

`[本文归纳]` 有两类病理落在稳定域框架之外，根源在蒸馏目标本身而非监督信号质量。

`[论文]` 第一类涉及 context 内化。OPD 可以把 system prompt、task hint 这类只在训练时提供的 privileged context 内化进 student，推理时不再需要。[When Context Returns](#ref-xunwang2026)（清华 IIIS，Xun Wang et al. 2026）报告了一个反直觉现象：在许多设置中，将原 context 再次提供给蒸馏后的 student，性能反而下降，连原本在没有 context 时也能做对的样例都受损。他们提出上下文可移除性（context removability）作为稳健内化的必要条件：context 重新出现时 student 行为保持稳定。修复方案是一个一致性正则（以无 context 输出为固定参照，并用 forward KL 惩罚相对该输出的偏离），在 12 种配置中的 **11 种**里减轻了这种损害；表示层分析显示，内化成功的 student 的隐藏状态（hidden state）与 context 是否在场几乎无关。

`[论文]` 第二类涉及置信度。[三阶段校准分析](#ref-shuhaoli2026)（宁波东方理工 + 港理工，Shuhao Li et al. 2026）比较 SFT、RL、OPD 三种后训练方法如何改变置信度：OPD 产生的推理前置信度（pre-reasoning）对后续决策最有帮助，但其置信度在生成后段可能出现反向校准（置信度越高，答案反而越可能错）；只在可靠的相对位置区间使用置信度（PosConf），能将 OPD 早停在较紧的 token 预算下的收益提升至 **4.3 个点**。用 OPD student 的置信度做早停或聚合时，必须将 token 位置一并作为条件考虑。

## 参数空间视角：OPD 有自己的更新几何

`[论文]` [几何分析](#ref-shen2026)（HKUST，Shen et al. 2026）从参数空间为稳定域图景补充了一个视角：OPD 涉及的权重更新少于 SFT，更能避开主方向，受到的优化约束也弱于 RLVR（reinforcement learning with verifiable rewards）；累计更新会迅速进入一个低维窄通道（子空间锁定，subspace locking）。将训练约束在早期形成的子空间内，能够保住 OPD 性能，却不能保持 SFT 性能。稀疏化更新 token、将 rollout 偏向 off-policy 都不改变这种秩的演化（rank dynamics），混入 RLVR 目标才会改变。结论是 OPD 在参数空间里有独立的更新几何，与 SFT 和 RLVR 都不同。原文尚未建立这组诊断与行为层病理之间的因果联系，这仍是一个开放问题。

## 边界与未决问题

`[本文归纳]` 三点边界。其一，稳定域目前还没有统一、可测的指标：各家用的 proxy 各不相同（teacher confidence、KL 信赖域、staleness 步数、drift gate），尚无对照实验说明哪一量适合作为统一度量。其二，三类修复之间的组合效应尚无人测量：限域、重加权、信号替换在同一训练里叠加后是否仍然相互独立，现有论文只分别测量各自的方案。其三，量化数字来自不同 setup（模型规模、benchmark、训练预算各异），横向比较只能在方向一致的粒度上进行，具体数值要结合各论文的实验条件解读。

## Reference

<a id="ref-liu2026"></a>
**[Your Teacher Can't Help You Here: Combating Supervision Fidelity Decay in On-Policy Distillation]** Yanjiang Liu, Jie Lou, Xinyan Guan, Yuqiu Ji, Hongyu Lin, Ben He, Xianpei Han, Le Sun, Xing Yu, Yaojie Lu，中国科学院软件研究所中文信息处理实验室 + 中国科学院大学 + 小红书，2026. [arXiv:2605.30833](https://arxiv.org/abs/2605.30833)。用于支撑：SFD 命名与长生成增益数据。`[arxiv 论文]`

<a id="ref-plyusov2026"></a>
**[Trust-Region Behavior Blending for On-Policy Distillation]** Daniil Plyusov, Alexey Gorbatovski, Alexey Malakhov, Nikita Balagansky, Boris Shaposhnikov, Daria Korotyshova, Daniil Gavrilov，T-Tech，2026. [arXiv:2605.31159](https://arxiv.org/abs/2605.31159)。用于支撑：早期弱 rollout 的病理与信赖域 warmup 方案。`[arxiv 论文]`

<a id="ref-xing2026"></a>
**[Trust Region On-Policy Distillation]** Xingrun Xing, Haoqing Wang, Boyan Gao, Ziheng Li, Yehui Tang，三星北京研究院 + 牛津大学 + 北京大学，2026. [arXiv:2606.01249](https://arxiv.org/abs/2606.01249)。用于支撑：分布差失稳机制与可靠域限定方案。`[arxiv 论文]`

<a id="ref-shen2026"></a>
**[On the Geometry of On-Policy Distillation]** Zhennan Shen, Yanshu Li, Qingyu Yin, Chak Tou Leong, Zhilin Wang, Yanxu Chen, Rongduo Han, Sunbowen Lee, Yi R. Fung，香港科技大学等，2026. [arXiv:2606.07082](https://arxiv.org/abs/2606.07082)。用于支撑：偏离主方向的区域（off-principal regime）与子空间锁定（subspace locking）的诊断。`[arxiv 论文]`

<a id="ref-zheng2026"></a>
**[Blockwise Policy-Drift Gating for On-Policy Distillation]** Liwen Zheng, Haiyun Jiang，独立研究者，2026. [arXiv:2606.24084](https://arxiv.org/abs/2606.24084)。用于支撑：student 侧 drift 门控与 pass@8 数据。`[arxiv 论文 / 独立研究者]`

<a id="ref-kang2026"></a>
**[AsyncOPD: How Stale Can On-Policy Distillation Be?]** Wonjun Kang, Kevin Galim, Seunghyuk Oh, Minjun Kang, Sanghyun Park, Donghoon Kim, Minjae Lee, Minseo Kim, Rishabh Tiwari, Yuchen Zeng, Hyung Il Koo, Kangwook Lee，FuriosaAI + Ajou University + UC Berkeley + Microsoft Research + KRAFTON，2026. [arXiv:2606.24143](https://arxiv.org/abs/2606.24143)。用于支撑：KL 方向脆弱性结论与 learner 更新时重算方案。`[arxiv 论文]`

<a id="ref-xunwang2026"></a>
**[When Context Returns: Toward Robust Internalization in On-Policy Distillation]** Xun Wang, Ruishuo Chen, Zhuoran Li, Yu Chen, Longbo Huang，清华大学交叉信息研究院，2026. [arXiv:2606.11627](https://arxiv.org/abs/2606.11627)。用于支撑：context-induced degradation 现象与一致性正则结果。`[arxiv 论文]`

<a id="ref-ruiwang2026"></a>
**[Demystifying On-Policy Distillation: Roles, Pathologies, and Regulations]** Rui Wang, Hongru Wang, Yi Chen, Boyang Xue, Tianqing Fang, Wenhao Yu, Kam-Fai Wong，香港中文大学 + 腾讯 AI Lab，2026. [arXiv:2607.13399](https://arxiv.org/abs/2607.13399)。用于支撑：探索催化剂定位、两个病理现象的命名与信号调控方案。`[arxiv 论文]`

<a id="ref-shuhaoli2026"></a>
**[Post-Training Shifts Confidence: A Three-Stage Analysis of How SFT, RL, and OPD Shape Pre-, Intra-, and Post-CoT Calibration]** Shuhao Li, Guodong Du, Anhao Zhao, Wanyu Lin, Tianyu Yuan, Xiaoyu Shen，宁波东方理工大学 + 香港理工大学，2026. [arXiv:2607.13753](https://arxiv.org/abs/2607.13753)。用于支撑：OPD 置信度位置依赖结论与 PosConf 数据。`[arxiv 论文]`

<a id="ref-heo2026"></a>
**[On-Policy Delta Distillation]** Byeongho Heo, Jaehui Hwang, Sangdoo Yun, Dongyoon Han，NAVER AI Lab，2026. [arXiv:2607.15161](https://arxiv.org/abs/2607.15161)。用于支撑：作为信号替换类代表的 delta signal 设计。`[arxiv 论文]`

<a id="ref-sun2026"></a>
**[EasyOPD: An Easy-to-use On-Policy Distillation Framework for Large Language Models]** Jie Sun, Mao Zheng, Mingyang Song, Qiyong Zhong, Gengsheng Li, Zhepei Hong, Chang Wu, Pengfei Liu, Junfeng Fang, Xiang Wang，中国科学技术大学 + 腾讯 LLM 部门 + 上海创智学院 + 新加坡国立大学，2026. [arXiv:2607.11012](https://arxiv.org/abs/2607.11012)。用于支撑：OPD 实现碎片化。`[arxiv 论文]`

<a id="ref-zhang2026"></a>
**[ShortOPD: Recovering Pruned LLMs with Short-to-Long On-Policy Distillation]** Qingyu Zhang, Qianhao Yuan, Hongyu Lin, Yaojie Lu, Xianpei Han, Le Sun, Xiang Li, Ming Xu, Jiarui Li, Xiuying Zhao，字节跳动 + 中国科学院软件研究所 + 中国科学院大学，2026. [arXiv:2607.13124](https://arxiv.org/abs/2607.13124)。用于支撑：后缀重复这一失效签名与恢复效率数据。`[arxiv 论文]`

<a id="ref-nrehiew2026"></a>
**[@nrehiew_ 关于 OPD teacher 选择的 X 推文]** [原推](https://x.com/nrehiew_/status/2072318210788245649)，2026-07。观点：teacher 应选同族模型，否则分布距离过大。`[个人实验 / X 推文]`
