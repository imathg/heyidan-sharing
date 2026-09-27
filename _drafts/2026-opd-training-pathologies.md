# OPD 失效诊断：学生离域、教师偏差与旧轨迹

<!-- domain: agentic-rl -->
<!-- edition_date: 2026-07-19 -->
<!-- revised_date: 2026-09-27 -->
<!-- revision_note: 补入 OPSD 原论文、teacher 自身偏移与实验控制证据，修正仅用 student 状态解释失效的边界。 -->

`[本文归纳]` OPD（on-policy distillation）的 loss 来自 teacher 和 student 的 token 分布差。这个差并不天然等于“student 缺少的能力”。一类失效来自 student 状态：prefix 太长、师生分布太远、rollout 过旧，都会让 teacher 的纠偏信号变弱或过期。另一类失效来自 teacher：privileged information 在补充正确答案的同时，也可能改变响应长度、置信度和 thinking mode，标准 OPD 会把这些行为偏移一起学走。

> `[本文归纳]` 判断 OPD 信号前要分开问两件事：teacher 在当前 student state 上还能不能可靠判别；teacher 相对 student 的差分，是能力差，还是 teacher 自己的行为变化。前者靠状态、staleness 和 support 诊断，后者要靠干预、对消或校准识别。KL 下降回答不了这两个问题。

下文仍用“稳定域”概括 teacher 能可靠判别的 student 状态，但把它收窄为第一层诊断，而不是所有 OPD 病理的统一解释。它只是本文组织材料的比喻，不是已有统一指标或证明的数学区域。[OPD 机制篇](../on-policy-distillation/) 讨论高概率 token 交集和伪收敛；本文继续对照状态离域、teacher 偏差、训练时序与实验控制。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<figure class="diagram">
<svg width="100%" viewBox="0 0 820 650" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="opd-diagram-title opd-diagram-desc" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">
<title id="opd-diagram-title">OPD 监督可靠性的两层诊断</title><desc id="opd-diagram-desc">上层展示生成、模型与时间三条 student 状态离域路径；下层展示 teacher 行为偏移、context 内化、置信度校准与参数几何等稳定域无法解释的问题。</desc>
<defs><linearGradient id="panelGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#131922"/><stop offset="100%" stop-color="#1a2230"/></linearGradient><linearGradient id="nodeGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#131922"/><stop offset="100%" stop-color="#1a2230"/></linearGradient><linearGradient id="pseudoGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#10151d"/><stop offset="100%" stop-color="#151b25"/></linearGradient><marker id="arrowMuted" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#2a3441"/></marker><marker id="arrowCyan" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#5fd0c8"/></marker></defs>
<rect width="820" height="650" fill="#0d1117"/>
<text x="410" y="36" text-anchor="middle" fill="#e6edf3" font-size="24" font-weight="650">OPD 监督可靠性的两层诊断</text>
<text x="410" y="58" text-anchor="middle" fill="#8b97a4" font-size="13">先查 student state 是否离域，再查 teacher 差分是否就是要学的能力</text>
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
<rect x="520" y="299" width="220" height="24" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="532" y="316" fill="#e6edf3" font-size="12.5">信号替换 · 重算 / delta / 对消</text>
<path d="M500 282 L440 282" fill="none" stroke="#5fd0c8" stroke-width="1.5" stroke-dasharray="7 5" marker-end="url(#arrowCyan)"/><text x="470" y="270" text-anchor="middle" fill="#5fd0c8" font-size="11.5">回归域内</text>
<path d="M250 330 L250 385" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrowMuted)"/><text x="263" y="362" fill="#8b97a4" font-size="11.5">离域后的表现</text>
<rect x="60" y="385" width="700" height="60" rx="12" fill="url(#panelGrad)" stroke="#2a3441"/>
<text x="84" y="421" fill="#e6edf3" font-size="14" font-weight="650">行为签名</text>
<rect x="180" y="398" width="160" height="34" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="260" y="420" text-anchor="middle" fill="#e6edf3" font-size="12.5">长度捷径 · reward 上升</text>
<rect x="352" y="398" width="185" height="34" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="444.5" y="420" text-anchor="middle" fill="#e6edf3" font-size="12.5">后缀重复 · rollout 变长</text>
<rect x="549" y="398" width="185" height="34" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="641.5" y="420" text-anchor="middle" fill="#e6edf3" font-size="12.5">伪收敛 · KL 降</text>
<path d="M150 445 L150 505" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58"/><path d="M325 445 L325 505" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58"/><path d="M500 445 L500 505" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58"/><path d="M675 445 L675 505" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58"/>
<g opacity="0.82"><rect x="60" y="505" width="165" height="92" rx="12" fill="url(#pseudoGrad)" stroke="#2a3441"/><text x="75" y="532" fill="#e6edf3" font-size="13" font-weight="600">teacher / style 偏移</text><text x="75" y="554" fill="#8b97a4" font-size="11.5">正确性与表达、长度</text><text x="75" y="572" fill="#8b97a4" font-size="11.5">置信度混在同一差分</text></g>
<g opacity="0.78"><rect x="235" y="505" width="165" height="92" rx="12" fill="url(#pseudoGrad)" stroke="#2a3441"/><text x="250" y="532" fill="#e6edf3" font-size="13" font-weight="600">context 内化</text><text x="250" y="554" fill="#8b97a4" font-size="11.5">context 重现时</text><text x="250" y="572" fill="#8b97a4" font-size="11.5">性能反而下降</text></g>
<g opacity="0.78"><rect x="410" y="505" width="165" height="92" rx="12" fill="url(#pseudoGrad)" stroke="#2a3441"/><text x="425" y="532" fill="#e6edf3" font-size="13" font-weight="600">置信度校准</text><text x="425" y="554" fill="#8b97a4" font-size="11.5">生成前后可靠性</text><text x="425" y="572" fill="#8b97a4" font-size="11.5">随位置变化</text></g>
<g opacity="0.78"><rect x="585" y="505" width="175" height="92" rx="12" fill="url(#pseudoGrad)" stroke="#2a3441"/><text x="600" y="532" fill="#e6edf3" font-size="13" font-weight="600">参数空间视角</text><text x="600" y="554" fill="#8b97a4" font-size="11.5">off-principal update</text><text x="600" y="572" fill="#8b97a4" font-size="11.5">与低维子空间锁定</text></g>
</svg>
</figure>

## 先查 student 是否离开 teacher 的有效区域

`[本文归纳]` student-state 失稳可以按离开稳定域的方式分成三条路径。它们仍是有效诊断，但只回答 teacher 在当前状态上能否提供可靠信号：

| 失真路径 | 触发条件 | 机制 | 代表论文 |
|---|---|---|---|
| 沿生成轴 | prefix 变长 | teacher next-token 分布趋平，纠偏项衰减 | SFD（中科院软件所 + 小红书） |
| 沿模型轴 | teacher-student 分布差大 | reverse-KL 估计器给出不可靠梯度 | TrOPD（三星北京研究院） |
| 沿时间轴 | rollout 变旧（异步训练） | reverse-KL 信号基于过期的 student 分布计算 | AsyncOPD（FuriosaAI） |

`[论文]` [SFD 论文](#ref-liu2026)（中科院软件所 + 小红书，Liu et al. 2026）将沿生成轴的失真命名为 Supervision Fidelity Decay：student 自生成的 prefix 越长，teacher 的 next-token 分布置信度越低、判别力越弱，reverse-KL 里依赖 teacher 的纠偏信号随之衰减，student 的漂移会沿推理链逐步累积。这解释了为什么长生成任务上失真最重：他们的修复（用下一步的 teacher 置信度评估 top-K 候选 token，按组归一化后作为奖励）在 39k token 的 AIME-26 上取得 **+4.92** 的最大增益，六个数学与代码 benchmark 平均 +2.57。

`[论文]` [TrOPD](#ref-xing2026)（三星北京研究院，Xing et al. 2026）描述了沿模型轴的失真：teacher 和 student 分布差过大时，由 teacher 对 student 生成 token 的监督导出的 policy gradient 会变得不可靠，直至优化失败。修复是只在 teacher 监督可靠的区域做 OPD，外围区域改用梯度裁剪、掩码或 forward-KL。`[个人实验]` 工程侧也有相同判断：[@nrehiew_](#ref-nrehiew2026) 在 X 的推文中认为 teacher 应选同族模型，否则分布距离过大。`[论文]` [TRB](#ref-plyusov2026)（T-Tech，Plyusov et al. 2026）处理的是同一路径在训练早期的特例：student 起点弱，rollout 质量差，teacher 监督集中在低质量 prefix 上。修复是 warmup 阶段在以 student 为中心的 KL 信赖域内，选择与 teacher 最接近的行为策略来生成 rollout，KL 预算退火到零后回到纯 on-policy。

`[论文]` 沿时间轴的失真来自异步训练系统：rollout 生成和 learner 更新解耦后，训练数据来自过期的 student 分布。[AsyncOPD](#ref-kang2026)（FuriosaAI，Kang et al. 2026）的系统性结论是 KL 方向决定脆弱性：teacher 加权的 forward KL 对 stale rollout 稳健，student 加权的 reverse KL 对 stale rollout 脆弱。将异步 RL 的稳定化手段用于 OPD，收效有限；更有效的是 OPD 专用的替代方案：在 learner 更新时，用当前 student 重算 reverse-KL 信号。配合多样本 Monte Carlo 压低方差，异步管线将吞吐提高 **1.6 到 3.8 倍**，精度与同步训练相当。

`[论文]` [Prompt Breadth and Rollout Refresh Interact](#ref-hu2026) 把“数据更广”和“状态更新”放进同一个 3×3 对照：固定 14,080 条 trajectory 与 110 次 optimizer update，只改变 prompt 数量和生成响应所用的 policy snapshot。冻结初始 policy 的响应时，扩大 prompt breadth 让平均准确率从 21.16% 降到 19.05%；每次 update 都刷新响应时，则从 23.61% 升到 25.57%。论文报告的交互为 **4.07 个点**，95% paired interval 为 [2.00, 6.28]。因此，prompt 多样性不能脱离 rollout freshness 单独解释；“数据更广”不等于 student 实际访问了更多新的 on-policy state。

## 再查 teacher 差分是否就是要学的能力

student 没有离域，也不代表 teacher-student discrepancy 可以原样学习。`[论文]` [OPSD 原论文](#ref-opsd2026) 的设置正好给出基线：student 与 teacher 从同一模型出发，student 只看问题并生成轨迹、持续更新；teacher 多看已验证参考答案，固定在初始策略，对同一 student prefix 给出全词表分布。这不是训练中始终共享参数的“同一个模型”，而是同一起点、不同条件、随后参数分离的两种策略。

`[论文]` 原论文自己的控制已经暴露出 teacher 差分并不中性：少量 style token 的巨大 divergence 会压过数学 token 信号，因此使用 pointwise clipping；在其 Qwen3-1.7B AIME25 消融里，forward KL 优于 reverse KL 与 JSD；Qwen3-4B 对照中，full-vocabulary distillation 优于 sampled-token，而把 rollout 从 1,024 延长到 4,096 token 没有稳定增益。固定 teacher、裁剪异常位置和覆盖全词表都能稳定或强化信号，但这些操作仍不能证明剩余差分全是能力。

`[论文]` [On Repulsive and Attractive Teachers](#ref-baumann2026) 进一步用 attractive 与 repulsive self-distillation 分开观察 privileged teacher 的作用：向正确答案条件 teacher 靠近时，模型更短、更自信，也减少探索；远离 privileged teacher 时，响应变长，可能切入 latent thinking mode，最终不稳定。把正确答案条件 teacher 的 attraction 与错误答案条件 teacher 的 repulsion 结合后，两类 teacher 共有的行为偏移在论文设置里大体对消，剩下的 token 信号更接近正确性差分。

`[论文]` [Cal-OPD](#ref-he2026) 用正负 privileged intervention 估计 teacher 自身的 deviation region，只保留超出这一区域的 teacher-student discrepancy。数学推理实验中，留下的信号约占原 discrepancy 的 **52%–65%**，在论文所报模型规模上仍优于标准 OPD 与比较变体。这个比例不是通用配方；更重要的结论是，teacher 自己的 likelihood shift 必须和 capability gap 分开估计。

`[本文归纳]` 这会改变故障归因。看到长度缩短、置信度上升或 thinking mode 消失时，不能只在 student 侧找 length exploitation；也要检查这些变化是否已经存在于 privileged teacher。前一类问题通过限制 state、刷新 rollout 或重加权修；后一类问题需要对消或校准 teacher-side deviation。

## 行为签名：训练曲线与真实能力脱钩

`[本文归纳]` student-state 失真与 teacher-side behavior shift 都会让训练指标和真实能力脱钩。至少要区分五种签名：

| 签名 | 表象 | 实际发生的事 | 检测量 |
|---|---|---|---|
| 长度捷径 | reward 上升 | student 用截断或冗余填充套取聚合目标的奖励 | 长度分布 vs 任务正确率 |
| 后缀重复 | rollout 变长 | 恢复预算花在低信息量的重复后缀上 | teacher 确认的重复后缀占比 |
| 伪收敛 | KL 下降 | 高概率 token 交集不动，能力无迁移 | top-K overlap（见[机制篇](../on-policy-distillation/)） |
| style-token 主导 | loss 被少量位置支配 | privileged teacher 的表达差异压过数学 token 信号 | token 类型切片的 divergence 与 clipping 前后收益 |
| teacher 行为偏移 | 响应更短、更自信，或反向变长 | privileged intervention 改了生成行为，不只补充正确性 | 正负 intervention 的共享变化与对消后信号 |

`[论文]` 长度捷径由 [Demystifying OPD](#ref-ruiwang2026)（港中文 + 腾讯 AI Lab，Rui Wang et al. 2026）系统刻画。这篇论文先界定 OPD 的作用：它是探索催化剂（exploration catalyst），通过密集的 token 级引导将 student 引向正确推理路径，并不扩展能力上限；prompt 多样性比单题采样数更重要。明确这一定位后，两个病理就有了统一解释：师生失配（Student-Teacher Mismatch）指引导信号与任务正确性错位（沿模型轴失真的行为面）；长度套取（Length Exploitation）指聚合 token 目标造成的长度依赖捷径，student 探索的是退化的长度模式，偏离推理策略。他们的结论不再以 teacher 规模为重心：**调控后的信号质量，而非 teacher 大小，决定 OPD 成败**。

`[论文]` 后缀重复来自压缩恢复场景。[ShortOPD](#ref-zhang2026)（字节跳动 + 中科院软件所，Zhang et al. 2026）观察到结构化剪枝后的模型 greedy pass@1 几乎归零，pass@k 却大幅可恢复，说明压缩降低了有用生成结果的概率，这些结果仍对应分布中的低概率区域，重复采样就能找回；可恢复区域的主要失效模式是后缀重复，长 rollout 会将早期用于恢复性能的 rollout 预算耗在这些低信息后缀上。修复是检测 teacher 确认的重复后缀，将重复开始前的存活 prefix 作为有效长度，按由短到长的训练日程（short-to-long）分配 rollout 预算：把分数恢复到未恢复值的约 **9 倍**，以四分之一训练时间（8.5 小时 vs 35.9 小时）达到与固定 8192-token 方案相当的性能。

<a id="修复方案收敛为三类信号调控"></a>

## 修复方法：限制训练区域、重加权或重算监督

`[本文归纳]` 2026 年各篇提出的修复动作，可以按调控对象索引为三类：在哪里训练（限域）、给各位置的信号多大权重（重加权）、用什么量做监督（信号替换）。这是定位工程动作的目录，不是三个互相独立的因果轴。

| 类别 | 做法 | 代表方案 |
|---|---|---|
| 限域 | 只在信号可靠的区域训练 | TrOPD 信赖域、TRB warmup、异常值掩码（outlier masking） |
| 重加权 | 按可靠性缩放各位置的损失 | OPSD pointwise clipping、按块漂移门控（blockwise drift gating）、优势裁剪（advantage clipping）、对数压缩（log-scale compression） |
| 信号替换或重算 | 换一个更可靠的监督量 | learner 时重算（AsyncOPD）、delta signal（OPD²）、contrastive / calibrated teacher discrepancy |

`[论文]` 重加权类里有一个直接来自 student 自身漂移的控制信号。[Blockwise Policy-Drift Gating](#ref-zheng2026)（独立研究者 Zheng & Jiang 2026）在 rollout 复用场景下，用行为 student 与当前 student 在采样 token 路径上的 log-prob 偏移（按 64-token 块聚合、去梯度、均值归一）重加权各位置损失，不改动 teacher 目标，也不改动 rollout 策略，四个数学 benchmark 的 mean pass@8 从 0.4978 提到 **0.5160**。信号完全来自 student 侧，说明是否离开稳定域可仅用 student 自己的信息检测。

`[论文]` 信号替换类的代表方案之一是 [OPD²](#ref-heo2026)（NAVER AI Lab，Heo et al. 2026）：不再直接模仿 teacher 输出分布，改用 delta signal，即 teacher 与其推理调优前的 base model 之间的分布差。这个信号只保留推理调优带来的分布变化，剔除了 teacher 分布里与推理能力无关的部分，在数学、科学、代码 benchmark 上稳定超过常规 OPD。

方法比较本身也可能制造假结论。`[论文]` [A Shared Learning Rate Is Not a Neutral Control](#ref-zhu2026) 在 GSM8K、Qwen2.5-1.5B student / 7B teacher、LoRA 的八档学习率上发现：dense supervision 只摆动 1.8 个点，而 selective arms 摆动 5.4–17.7 个点；相邻学习率就能翻转部分 selector 的显著性判断。这个 rate dependence 没在 MATH-500 的 LoRA 设置复现，所以它不是“选择性监督一定无效”的结论。更稳妥的验收是报告 arm × learning-rate matrix，而不是给所有 selector 共用一个 rate 后比较单列结果。

`[论文]` 工程侧的实现碎片化也表明可调控的维度很多：[EasyOPD](#ref-sun2026)（中科大 + 腾讯，Sun et al. 2026）指出现有 OPD 实现「在监督形式、tokenizer 兼容性、teacher 访问方式、监督粒度上差异巨大，难以复现和扩展」，作者据此基于 verl 构建了统一框架。

## 稳定域之外：内化与校准仍是独立问题

`[本文归纳]` 除了 teacher-side deviation，还有两类问题不能被 student-state 稳定域吸收，根源在蒸馏目标的使用方式。

`[论文]` 第一类涉及 context 内化。OPD 可以把 system prompt、task hint 这类只在训练时提供的 privileged context 内化进 student，推理时不再需要。[When Context Returns](#ref-xunwang2026)（清华 IIIS，Xun Wang et al. 2026）报告了一个反直觉现象：在许多设置中，将原 context 再次提供给蒸馏后的 student，性能反而下降，连原本在没有 context 时也能做对的样例都受损。他们提出上下文可移除性（context removability）作为稳健内化的必要条件：context 重新出现时 student 行为保持稳定。修复方案是一个一致性正则（以无 context 输出为固定参照，并用 forward KL 惩罚相对该输出的偏离），在 12 种配置中的 **11 种**里减轻了这种损害；表示层分析显示，内化成功的 student 的隐藏状态（hidden state）与 context 是否在场几乎无关。

`[论文]` 第二类涉及置信度。[三阶段校准分析](#ref-shuhaoli2026)（宁波东方理工 + 港理工，Shuhao Li et al. 2026）比较 SFT、RL、OPD 三种后训练方法如何改变置信度：OPD 产生的推理前置信度（pre-reasoning）对后续决策最有帮助，但其置信度在生成后段可能出现反向校准（置信度越高，答案反而越可能错）；只在可靠的相对位置区间使用置信度（PosConf），能将 OPD 早停在较紧的 token 预算下的收益提升至 **4.3 个点**。用 OPD student 的置信度做早停或聚合时，必须将 token 位置一并作为条件考虑。

## 参数空间视角：OPD 有自己的更新几何

`[论文]` [几何分析](#ref-shen2026)（HKUST，Shen et al. 2026）从参数空间为稳定域图景补充了一个视角：OPD 涉及的权重更新少于 SFT，更能避开主方向，受到的优化约束也弱于 RLVR（reinforcement learning with verifiable rewards）；累计更新会迅速进入一个低维窄通道（子空间锁定，subspace locking）。将训练约束在早期形成的子空间内，能够保住 OPD 性能，却不能保持 SFT 性能。稀疏化更新 token、将 rollout 偏向 off-policy 都不改变这种秩的演化（rank dynamics），混入 RLVR 目标才会改变。结论是 OPD 在参数空间里有独立的更新几何，与 SFT 和 RLVR 都不同。原文尚未建立这组诊断与行为层病理之间的因果联系，这仍是一个开放问题。

## 边界与未决问题

`[本文归纳]` 三点边界。其一，稳定域目前没有统一可测指标：teacher confidence、KL 信赖域、staleness 与 drift gate 只是不同 proxy；OPSD 的 style-token divergence 和新增 teacher-side deviation 也说明单个 state-distance 指标不可能覆盖全部失效。其二，修复与实验旋钮不能假设正交：prompt breadth 与 rollout refresh 已出现受控交互，selector 与 learning rate 也会耦合；但这些结果仍来自特定 reasoning setup，尚不能给出统一的最优联调方案。其三，量化数字来自不同模型、benchmark 与训练预算，横向只能比较机制方向，不能把单篇增益直接排成方法榜单。

## Reference

<a id="ref-opsd2026"></a>
**[Self-Distilled Reasoner: On-Policy Self-Distillation for Large Language Models]** Siyan Zhao, Zhihui Xie, Mengchen Liu, Jing Huang, Guan Pang, Feiyu Chen, Aditya Grover，2026. [arXiv:2601.18734v3](https://arxiv.org/abs/2601.18734)。用于支撑：同起点双条件策略、固定初始 teacher、student rollout 上的全词表监督，以及 KL 方向、pointwise clipping、监督粒度与 rollout 长度的稳定化证据。结果限于论文的 OpenThoughts、Qwen3 Instruct 与 LoRA 设置。`[arxiv 论文]`

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

<a id="ref-baumann2026"></a>
**[On Repulsive and Attractive Teachers: Separating Correctness from Behavior in Self-Distillation]** Anton Baumann, Akmal Ashirmatov, Leo Schmidt-Traub, Frederike Lübeck, Jonas Hübotter, Thomas Kleine Buening, Andreas Krause，2026. [arXiv:2609.21561](https://arxiv.org/abs/2609.21561)。用于支撑：privileged teacher 的正确性与行为偏移会混在同一蒸馏差分中。`[arxiv 论文]`

<a id="ref-he2026"></a>
**[Calibrating Teacher--Student Discrepancy for On-Policy Distillation]** Qiangqiang He, Jin Li, MingCai Chen，2026. [arXiv:2609.21619](https://arxiv.org/abs/2609.21619)。用于支撑：teacher self-deviation region、52%–65% 信号保留与校准结果。`[arxiv 论文]`

<a id="ref-zhu2026"></a>
**[A Shared Learning Rate Is Not a Neutral Control in Selective On-Policy Distillation]** Chencheng Zhu，2026. [arXiv:2609.22109](https://arxiv.org/abs/2609.22109)。用于支撑：selector-rate entanglement 与 arm × rate 对照要求。`[arxiv 论文 / 单作者预印本]`

<a id="ref-hu2026"></a>
**[Prompt Breadth and Rollout Refresh Interact in On-Policy Distillation]** Lingxiang Hu, Tianle Xia, Ming Xu, Yiding Sun, Linfang Shang，2026. [arXiv:2609.25048](https://arxiv.org/abs/2609.25048)。用于支撑：固定轨迹与更新预算下 prompt breadth × rollout refresh 的 3×3 交互。`[arxiv 论文]`
