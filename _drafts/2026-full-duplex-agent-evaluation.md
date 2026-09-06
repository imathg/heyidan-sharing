# 全双工 Agent 评测：交互状态、时间边界与失败归因
<!-- domain: realtime-interactive-agent -->
<!-- edition_date: 2026-08-23 -->

`[本文归纳]` 把下文五类失效机制串进同一条时间线，可以构造一条合成错误链。服务端日志记下一段转写文本、一条完整生成、一次打断和一个成功终态。

`[本文归纳]` 沿用户侧时间线看，系统输入只保留转写，遗漏语气里的犹豫。回答播放到一半时，用户打断并追问前面两个选项里的第二个。系统按“整段回复都已共享”的假设理解指代，用户只能重复问题，日志中的任务终态仍记为成功。

`[本文归纳]` 两组记录都可能忠实于各自的观察面，提交时钟的错位却会导向不同归因。同一段内容在输入、生成、播放、打断和下一轮反应上各有生效时间，generation clock 记录生成进度，其余时钟分别记录内容何时进入对应状态。

`[本文归纳]` 这条错误链是基于五类来源机制构造的分析样例。责任可能落在四个不同位置：声音线索遗漏在模型输入之外；尚未播放的半句被写入共同上下文；打断重置了声学或对话状态；成功终态掩盖了中间的纠正轮次。评测的主问题是：在每个播放切点上，系统实际取得了什么输入、内容播放到哪里、打断后哪些状态延续、下一轮反应暴露了什么局部后果。四者对齐，失败才能归因到正确的接口和 owner。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

## 1. 全双工链路的状态与时钟

`[本文归纳]` 一次全双工交互至少包含九类关键事件与状态提交点。capture clock 记录原始音频进入系统；evidence 层记录转写、韵律、情绪与时序切点中实际进入模型输入的部分；generation clock 记录服务端逐 token 生成的进度，生成内容何时写入 dialogue state 需要另行记录；音频经排队与网络到达客户端后，playback clock 记录它越过播放边界的时刻；已生成或已入队、却在越过边界前被丢弃的内容记入 cancellation；用户在播放中途开口触发 interruption；打断之后还有 state inheritance，KV cache、声学状态与对话状态各自决定保留或重置；下一轮用户反应则提供局部后果。若日志只按 turn 聚合，这些事件会被压进同一个结果。

| 事件或状态提交点 | 记录的状态 |
|---|---|
| capture | 原始音频进入系统 |
| evidence | ASR 转写、韵律与情绪特征、时序切点实际进入模型输入 |
| generation | 服务端逐 token 生成；与 dialogue state 提交分开记录 |
| queue / network | 音频入队、传输，尚未到达客户端 |
| playback | 音频越过客户端播放边界 |
| cancellation | 已生成或已入队的内容在越过播放边界前被丢弃 |
| interruption | 用户在播放中途开口，触发取消与状态继承 |
| state inheritance | 打断后 KV、声学与对话状态各自保留或重置 |
| next turn | 用户下一轮反应作为局部后果出现 |

`[本文归纳]` 把下列三组状态压成等价关系，会产生来源中的反事实或对照实验能够检出的误判。其一，以 transcript 代表模型的全部输入，声音里的犹豫、强调与转折时机没有进入记录；其二，以 generated 代表用户已经听到，未播放内容被当作共同上下文参与后续推理；其三，以 terminal outcome 代表整轮互动的效果，有效澄清、局部错误与事后修复被压成同一个分数。三类错记都以较早出现的状态代替较晚生效的状态：生成快于播放时，系统状态已经走到第十句，用户侧的播放边界还停在第三句。

`[本文归纳]` 三个词在本文里严格区分。共同上下文指有资格被系统当作“用户可能已经听到”的内容集合，提交点是 playback boundary 而非 generation boundary。播放边界是工程代理：它证明音频可能抵达用户，不证明用户注意、理解或满意。终态任务结果只证明任务产物成立，不证明过程成本与体验。TTS 连续性与局部 reaction credit 分属另外两层，后文逐层展开。

## 2. 输入证据：模型实际取得了什么

`[论文]` [Counterfactual Audits](#ref-miller2026)（Boston University，Miller et al. 2026）从音频 judge 的输入查起。一个模型可以接收完整音频，却仍然只依赖 transcript 或候选回答的表面风格。作者固定文本，只改变 affect、prosody 或情绪转折发生的时机：有效 judge 必须跟随声音线索，无法靠字面猜中。

`[论文]` 论文把评测分成两种。native one-context judgment 直接给一段音频做真实判定；contrastive recoverability 把差异显式摆在一起，只检验模型能否恢复那条线索。实验发现，contrastive success 经常高估 native judge 的可靠性；相近的 aggregate accuracy 背后，也可能是完全不同的 perception 失败与 response-mapping 失败。

`[本文归纳]` 输入侧的第一处错记发生在转写完成之后：文本看起来完整，声音里的犹豫、强调和转折时机却没有进入记录。输入侧至少要保存原始音频、ASR 转写、韵律与情绪特征、时序切点，以及评测模型实际拿到的输入；再用固定文本、只改一类声音线索的反事实实验，分清“模型没有听出差异”和“听出后没有做出合适反应”。这项工作审计的是音频 judge，支持的是对评测输入做行为审计；用户满意度仍需其他证据。

## 3. 播放边界：共同上下文的提交点

`[论文]` [PACE](#ref-wang2026)（Alibaba Group，Wang et al. 2026）给时间线上的第二处错记命了名：Generative Context Mis-anchoring。服务端生成快于客户端播放时，模型已经把回复后半段写入 dialogue state，用户却还没听到。此时用户打断或使用指代，系统会基于一段从未成为共同上下文的内容继续推理。

`[论文]` PACE 的修法是把 client playback boundary 设为 model-facing context 的提交点：打断后保留已播放内容，并从后续上下文排除未播放内容。在 108 个 GCM-Bench case 上，Referent Anchoring Accuracy 从 cancellation-only baseline 的 **25.0%** 提高到 **96.3%**；在 200 个 Full-Duplex-Bench v1 interruption 样本上，interruption response quality 保持不变。两组结果表明，这项上下文修复保留了原有的打断响应质量。

`[本文归纳]` 播放侧的状态因此至少有四种：`generated → queued → played` 是主路径，`cancelled` 是音频越过播放边界前的分支。只有真正播放的内容才有资格进入“用户可能听到”的共同上下文。PACE 的实现覆盖 browser voice assistant 的 audio-only projection，并使用 black-box speech model；playback clock 仍是工程代理，用户是否注意和理解每个 token 需要另行验证。

## 4. 打断之后：上下文、生成状态与声学状态分别继承

`[论文]` 打断同时暴露三层连续性问题。第一层是对话上下文，由播放边界处理；第二层是合成侧的生成状态。[VoiceChat-TTS](#ref-casanova2026)（NVIDIA，Casanova et al. 2026）针对的正是这一层：常规 TTS 按完整 utterance 生成，barge-in 会把合成状态整个切断；端到端 duplex 模型又常把 ASR、打断控制和高保真合成绑在同一个优化问题里。它直接消费 LLM 的 text-token stream，用 control token 处理 mid-utterance interruption，没有文本时输出 silence，打断后保留 KV cache。识别、打断控制与合成因此可以分开验收。

`[论文]` 第三层是跨 segment 的声学状态。[X2Streaming-TTS](#ref-wen2026)（X Square Robot，Wen et al. 2026）处理另一类断裂。等待整句文本再合成属于 pseudo-streaming；严格 token-level synthesis 又要同时面对未知前缀、segment 边界断裂，以及无限流只能保留有界 context 的冲突。它用 causal commitment 把歧义表达暂时保持为 provisional，再用 speech-state inheritance 跨 segment 携带完整 Code2Wav state 和选定 Talker state。论文报告严格 token-level 合成在大多数主客观指标上优于所测 pseudo-streaming 模型，单请求 median TTFT 为 **15.8 ms**，128 并发时为 **260.8 ms**。

`[本文归纳]` 两篇论文合起来给出“打断成功”的三个独立结果：输出及时停止、已共享的 dialogue context 得到保留、下一段声音延续原有 speaker identity 与韵律状态。三者共用一个 interruption pass rate 时，context owner、TTS owner 与 control-policy owner 会互相替代。continuation receipt 应该分项覆盖 KV、acoustic state、played span 和下一段首帧延迟。TTFT 与 boundary continuity 的证据停在 TTS 层，任务成功和用户偏好需要更高层的实验继续验证。

## 5. 下一轮反应：局部 credit 的对齐单位

`[论文]` 结果侧的错记来自 terminal reward。[FACA](#ref-zhao2026)（Fudan University、Ant International，Zhao et al. 2026）指出，terminal reward 会把有效澄清、局部错误和后续修复压成同一个结果，无法定位哪一段互动改变了用户的下一轮行为。它把下一轮 reaction 对齐到前一个 user-to-user segment，构造 locally normalized reaction advantage，再与 verified terminal outcome advantage 合并。

`[论文]` 在 simulator、可见对话、初始化、rollout 与优化配置都匹配的对照实验中，FACA 相对 outcome-only Interactive GRPO 把九领域平均提高 **5.91 个百分点（8B）** 和 **10.22 个百分点（14B）**。收益主要集中在 Telecom；在 8B 上随机化 reaction polarity 会消除该领域增益。这个消融把收益指向了 reaction 提供的方向信息。

`[本文归纳]` 把这类 reaction 信号接入全双工评测时，可以把最小对齐单位定义为“上一段实际播放内容 → 下一轮用户反应”：接受、自然续说、主动补充、重复问题、纠正、打断和退出，携带不同方向的局部证据。它带噪，也受用户个体差异影响；实验又在 simulator 上完成。务实做法是把它与任务结果合并，保留为带噪的局部证据；明确偏好仍需真实用户侧验证。

## 6. 场景终态：三条独立的评测轴

`[论文]` 局部证据之上还有场景级终态。[DuplexWorld](#ref-bhosale2026)（Centific、University of Maryland，Bhosale et al. 2026）把 voice agent 放进 banking、insurance、travel、healthcare、logistics 与 pathfinding 六个领域，覆盖 11 类对话、156 个 scenario 和 **350+ 小时**交互，同时保留 agentic、conversational 与 speech-naturalness 三条轴。

`[论文]` 最佳系统的 Pass@1 为 **0.490**，turn-taking 为 **0.653**，DNSMOS 为 **3.378**。三条轴都留有明显缺口，且失败模式不同。一个声音自然但任务没完成的系统，与一个任务完成但频繁抢话的系统，经过平均后可能落成同一种“中等体验”。benchmark 的 world 与 scenario 有自己的分布，这些数值只描述该测试集；三轴差异则说明总分会隐藏不同的失败形态。

`[论文]` [Multi-turn Conversational AI survey](#ref-ahmed2026)（Qatar Computing Research Institute，Ahmed et al. 2026）把 text、AudioLLM、multimodal / omni-modal 与 tool agent 放在同一版图，指出模态能力的增长快于 session 内持续 coherence、persistent memory、跨轮 grounding、full-duplex interaction 与 robust evaluation 的闭合。

`[本文归纳]` 这篇 survey 提供的是研究版图边界：模态扩展与评测合同仍是两项独立工程，分轴与分层需要显式维护；它不承担独立实验结果。

## 7. 三本账：分层评测与反事实归因

`[本文归纳]` 输入、播放、连续性与反应四处时钟错记，共同反推出一次失败的最小记账结构。输入侧冻结系统实际取得的线索，播放侧冻结用户可能听到的位置，反应侧冻结下一轮暴露的局部后果。在每个播放切点同时保留这三类状态，一次交互的后果才能追溯到正确的责任模块。三类状态分别记入 evidence ledger、playback ledger 和 reaction ledger；场景级的总分掩盖是另一类问题，由分轴与 score decomposition 处理，不进账本。

<figure class="diagram">
<svg width="100%" viewBox="0 0 820 620" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="ledger-title ledger-desc">
<title id="ledger-title">全双工 Agent 评测的三本账</title>
<desc id="ledger-desc">证据账本记录模型实际取得的输入，播放账本记录生成内容是否越过播放边界，反应账本把用户下一轮反应对齐到已播放内容。</desc>
<defs>
<linearGradient id="panelGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#131922"/><stop offset="1" stop-color="#1a2230"/></linearGradient>
<linearGradient id="nodeGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#131922"/><stop offset="1" stop-color="#1a2230"/></linearGradient>
<linearGradient id="pseudoGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#10151d" stop-opacity=".78"/><stop offset="1" stop-color="#151b25" stop-opacity=".7"/></linearGradient>
<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="5" stdDeviation="7" flood-color="#05080d" flood-opacity=".36"/></filter>
<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#5fd0c8"/></marker>
<style>.t{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif}.main{fill:#e6edf3}.sub{fill:#8b97a4}.mint{fill:#5fd0c8}.panel{fill:url(#panelGrad);stroke:#2a3441;stroke-width:1.05}.node{fill:url(#nodeGrad);stroke:#3a4655;stroke-width:1}.pseudo{fill:url(#pseudoGrad);stroke:#8b97a4;stroke-width:1;stroke-dasharray:1 7}.edge{fill:none;stroke:#5fd0c8;stroke-width:1.35;marker-end:url(#arrow)}.soft{fill:none;stroke:#2a3441;stroke-width:1.05}.dash{fill:none;stroke:#5fd0c8;stroke-width:1.2;stroke-dasharray:7 5}</style>
</defs>
<rect x="10" y="10" width="800" height="600" rx="22" fill="#0d1219" stroke="#2a3441"/>
<text class="t main" x="36" y="50" font-size="24" font-weight="700">全双工 Agent 评测，要对齐三本账</text>
<text class="t sub" x="36" y="75" font-size="13">每本账回答一个不同问题；越过边界的 receipt 才能进入下一层。</text>
<rect class="panel" x="30" y="98" width="760" height="126" rx="18" filter="url(#shadow)"/>
<text class="t mint" x="50" y="126" font-size="14" font-weight="700">1 · EVIDENCE LEDGER</text>
<text class="t sub" x="224" y="126" font-size="12.5">模型实际拿到了什么</text>
<rect class="node" x="50" y="146" width="132" height="52" rx="11"/>
<text class="t main" x="116" y="168" text-anchor="middle" font-size="14">原始音频</text>
<text class="t sub" x="116" y="187" text-anchor="middle" font-size="11.5">capture clock</text>
<rect class="node" x="228" y="146" width="132" height="52" rx="11"/>
<text class="t main" x="294" y="168" text-anchor="middle" font-size="14">ASR 转写</text>
<text class="t sub" x="294" y="187" text-anchor="middle" font-size="11.5">语义</text>
<rect class="node" x="406" y="146" width="142" height="52" rx="11"/>
<text class="t main" x="477" y="168" text-anchor="middle" font-size="14">韵律 · 情绪</text>
<text class="t sub" x="477" y="187" text-anchor="middle" font-size="11.5">timing cut</text>
<rect class="node" x="594" y="140" width="170" height="64" rx="12" stroke="#5fd0c8"/>
<text class="t main" x="679" y="166" text-anchor="middle" font-size="14">输入 receipt</text>
<text class="t sub" x="679" y="187" text-anchor="middle" font-size="11.5">评测模型实际取得的输入</text>
<path class="edge" d="M182 172 H218"/><path class="edge" d="M360 172 H396"/><path class="edge" d="M548 172 H584"/>
<rect class="panel" x="30" y="242" width="760" height="154" rx="18" filter="url(#shadow)"/>
<text class="t mint" x="50" y="270" font-size="14" font-weight="700">2 · PLAYBACK LEDGER</text>
<text class="t sub" x="232" y="270" font-size="12.5">用户可能听到了哪里</text>
<rect class="node" x="50" y="290" width="116" height="48" rx="11"/>
<text class="t main" x="108" y="320" text-anchor="middle" font-size="14">generated</text>
<rect class="node" x="214" y="290" width="116" height="48" rx="11"/>
<text class="t main" x="272" y="320" text-anchor="middle" font-size="14">queued</text>
<rect class="node" x="378" y="290" width="116" height="48" rx="11"/>
<text class="t main" x="436" y="320" text-anchor="middle" font-size="14">played</text>
<path class="edge" d="M166 314 H204"/><path class="edge" d="M330 314 H368"/>
<path class="dash" d="M532 278 V370"/>
<text class="t mint" x="544" y="301" font-size="11.5">playback boundary</text>
<text class="t sub" x="544" y="320" font-size="11.5">共享上下文提交点</text>
<rect class="node" x="610" y="334" width="154" height="40" rx="10" stroke="#5fd0c8"/>
<text class="t main" x="687" y="359" text-anchor="middle" font-size="14">played-span receipt</text>
<path class="edge" d="M494 314 H522 V354 H600"/>
<rect class="pseudo" x="214" y="350" width="116" height="32" rx="10"/>
<text class="t sub" x="272" y="371" text-anchor="middle" font-size="12.5">cancelled</text>
<path class="soft" d="M272 338 V350"/>
<text class="t sub" x="342" y="371" font-size="11.5">播放前分支，不写入共享上下文</text>
<rect class="panel" x="30" y="414" width="760" height="130" rx="18" filter="url(#shadow)"/>
<text class="t mint" x="50" y="442" font-size="14" font-weight="700">3 · REACTION LEDGER</text>
<text class="t sub" x="230" y="442" font-size="12.5">下一轮暴露了什么局部后果</text>
<rect class="node" x="50" y="465" width="160" height="48" rx="11"/>
<text class="t main" x="130" y="486" text-anchor="middle" font-size="14">上一段 played span</text>
<text class="t sub" x="130" y="504" text-anchor="middle" font-size="11.5">对齐单位</text>
<path class="edge" d="M210 489 H256"/>
<rect class="node" x="266" y="465" width="104" height="48" rx="11"/>
<text class="t main" x="318" y="494" text-anchor="middle" font-size="14">接受</text>
<rect class="node" x="384" y="465" width="104" height="48" rx="11"/>
<text class="t main" x="436" y="494" text-anchor="middle" font-size="14">澄清</text>
<rect class="node" x="502" y="465" width="104" height="48" rx="11"/>
<text class="t main" x="554" y="494" text-anchor="middle" font-size="14">纠正</text>
<rect class="node" x="620" y="465" width="144" height="48" rx="11" stroke="#5fd0c8"/>
<text class="t main" x="692" y="486" text-anchor="middle" font-size="14">局部结果 receipt</text>
<text class="t sub" x="692" y="504" text-anchor="middle" font-size="11.5">含打断与退出</text>
<path class="soft" d="M370 489 H384 M488 489 H502 M606 489 H620"/>
<path class="dash" d="M679 204 V232 M687 374 V404"/>
<rect x="132" y="566" width="556" height="34" rx="17" fill="#101a20" stroke="#5fd0c8" stroke-width="1.1"/>
<text class="t main" x="410" y="588" text-anchor="middle" font-size="14">输入证据 + 实际播放 + 后续反应 → 可定位、可复现的失败 owner</text>
</svg>
<figcaption>三本账分别保留模型取得的证据、真正播放的内容和用户后续反应；跨层对齐后，失败才有明确 owner。</figcaption>
</figure>

`[本文归纳]` 三本账要能诊断，离不开反事实。全双工链路耦合很强，端到端 A/B 会让多个变量同时变化；更有诊断力的做法是固定上一层、只改当前边界：

| 反事实 | 固定什么 | 只改变什么 | 能定位的失败 |
|---|---|---|---|
| 音频证据 | transcript、任务、回答候选 | affect / prosody / timing | perception 与 response mapping |
| 播放切点 | 用户输入、生成内容、模型 | played / unplayed boundary | context mis-anchoring |
| 状态继承 | 文本流、speaker、打断点 | reset / inherit KV 与 speech state | 声学连续性与恢复延迟 |
| 下一轮反馈 | 轨迹、terminal outcome | reaction polarity 或对齐位置 | 局部 credit 是否来自用户反应 |
| 场景分轴 | scenario 与系统版本 | metric aggregation | 总分是否掩盖独立失败 |

`[本文归纳]` 这五组实验对应六个可调旋钮：evidence channel、commit clock、continuation state、credit horizon、score decomposition 和 counterfactual unit。它们把评测单位从“同一段音频算一个 case”扩展为连续状态机：每个 playback cut 都有输入证据、已生效内容、保留状态和后续反应。

`[本文归纳]` 落到指标上，可以先分层、再决定是否汇总：

| 层 | 核心问题 | 最小 receipt | 典型指标 |
|---|---|---|---|
| Evidence | 系统实际取得了什么线索 | input projection + counterfactual id | cue sensitivity、native/contrastive gap |
| Playback | 用户可能听到哪里 | played span + cancellation boundary | referent anchoring、late/cancelled span |
| Continuation | 打断或切段后保留什么 | KV / acoustic / dialogue state hash | boundary continuity、TTFT、speaker identity |
| Reaction | 下一轮暴露什么局部后果 | prior played span + reaction | correction、repeat、accept、segment advantage |
| Scenario | 完整任务是否成立 | task artifact + session trace | Pass@1、turn-taking、naturalness、safety |

`[本文归纳]` 任一层通过，只证明状态在该接口保持连续。音频 judge 用到韵律之后，播放内容仍要单独核验；TTS 跨段连续之后，任务结果仍要单独核验；任务成功之后，多轮纠正成本仍要单独核验。七个来源在这条链上各居一层，也各有不能越过的边界：

| 来源 | 支持的层 | 不能支持 |
|---|---|---|
| Counterfactual Audits | 输入证据的行为审计 | 完整系统判定、用户满意度 |
| PACE | 播放边界作为上下文提交点 | 用户实际注意或理解已播内容 |
| VoiceChat-TTS | 打断后生成状态（KV）继承 | 任务成功、用户偏好 |
| X2Streaming-TTS | 跨 segment 声学状态继承与 TTS 层延迟 | 互动层面的任务成功 |
| FACA | 下一轮反应的局部 credit | 真实语音用户的偏好强度 |
| DuplexWorld | 场景级三轴终态 | 任一线上产品的线上质量 |
| Multi-turn survey | 研究版图与评测维度边界 | 独立性能结论 |

## 8. 工程代理、用户证据与因果缺口

`[本文归纳]` 六个容易混用的评测对象需要分开计数：

| 评测对象 | 当前证据支持 | 仍需补充的证据 |
|---|---|---|
| 播放边界 | 音频可能抵达用户 | 用户是否注意与理解 |
| 共同上下文 | 系统侧共享假设的截止点 | 用户是否记住已播内容 |
| TTS 连续性 | 声学状态跨打断与切段延续 | 对话策略是否正确 |
| 局部 reaction credit | 前一个 user-to-user segment 的训练信号 | 与实际播放内容的因果关系、明确偏好 |
| 终态任务结果 | 任务产物成立 | 过程成本与纠正轮次 |
| 真实用户体验 | 注意、理解与满意 | 现有七个来源缺少直接测量 |

`[本文归纳]` 证据链还在两个地方断掉。其一，reaction 会混入人格、任务难度、环境噪声和用户策略：礼貌性继续、系统错误导致的打断和用户目标的自然变化携带完全不同的方向信息，使用前必须分开计数；而 FACA 的实验在 simulator 上完成，方向信息能否迁移到真实语音用户仍待验证。其二，七个来源之间留有一段因果空白：VoiceChat-TTS 与 X2Streaming-TTS 证明了可保留的生成状态与声学状态，PACE 证明了播放边界对上下文一致性的作用，DuplexWorld 与 FACA 在更长 horizon 上观察任务与下一轮后果；哪类低层 continuity 改善能稳定转成更少的纠正、更高的任务成功或更自然的话轮，仍缺统一的端到端消融。分层验收能保留这段因果缺口，汇总分数会把它重新压平。

`[本文归纳]` 近期更实用的完成标准因此是让三本账能回放、能对齐、能做单层反事实。系统取得了什么输入、哪些内容越过了播放边界、下一轮暴露了什么反应，三条证据链闭合之后，“体验不好”才会变成一处能定位、能复现的失败；而从“能定位的失败”到“被证明的体验提升”，还隔着一层现有来源都没有跨过的用户证据。

## Reference

<a id="ref-miller2026"></a>
**[Do Audio Language Models Use Paralinguistic Evidence? Counterfactual Audits for Response Evaluation]** Kevin Miller, Arjun Chandra, Venkatesh Saligrama；Boston University；2026. [arXiv:2608.06718](https://arxiv.org/abs/2608.06718)。用于固定 transcript 的副语言反事实、native 与 contrastive judge 诊断。[arXiv 论文]

<a id="ref-wang2026"></a>
**[PACE: A Playback-Aligned Context Engine for LLM-Based Full-Duplex Voice Dialogue]** Shibo Wang, Zicheng Zhang, Libo Wang, Junfeng Ma；Alibaba Group；2026. [arXiv:2608.07631](https://arxiv.org/abs/2608.07631)。用于 playback-aligned context、GCM-Bench 与打断后的 referent anchoring。[arXiv 论文]

<a id="ref-bhosale2026"></a>
**[DuplexWorld: Can voice agents help you get through the day?]** Aryan Vijay Bhosale, Harshit Rajgarhia, Akhil Pothanapalli, Asif Shaik, Abhishek Mukherji, Dinesh Manocha；Centific Global Solutions Inc.、University of Maryland；2026. [arXiv:2608.10716](https://arxiv.org/abs/2608.10716)。用于现实场景的 agentic、conversational 与 speech-naturalness 分轴评测。[arXiv 论文]

<a id="ref-casanova2026"></a>
**[VoiceChat-TTS: A Low-Latency Continuous Speech Synthesis Model for Interactive Agents]** Edresson Casanova, Jaehyeon Kim, Mariana Graterol Fuenmayor, Shehzeen Hussain, Viacheslav Klimkov, Valentin Mendelev, Mikyas Desta, Paarth Neekhara, Piotr Zelasko, Chen Chen, Elena Rastorgueva, Ke Hu, Ankita Pasad, Xuesong Yang, Aya Alja'fari, Rajarshi Roy, Rohan Badlani, Jason Roche, Jason Li, Zhehuai Chen；NVIDIA Corporation；2026. [arXiv:2608.13831](https://arxiv.org/abs/2608.13831)。用于连续 text-token TTS、control-token interruption 与 KV continuation。[arXiv 论文]

<a id="ref-zhao2026"></a>
**[Towards Better Agents for Multi-Turn User Interaction: The Next User Turn Is More Than Context]** Yiwen Zhao, Zhihao Wen, Yuchen Mao, Mingxuan Jiang, Yihao Hu, Pan Wang, Xin Zhang, Wei Wu；Fudan University、Ant International, Ant Group；2026. [arXiv:2608.17499](https://arxiv.org/abs/2608.17499)。用于 next-turn reaction、FACA 局部 credit 与 polarity 消融。[arXiv 论文]

<a id="ref-ahmed2026"></a>
**[Multi-turn Conversational AI from Text to Multimodal Interaction: Data, Models, Evaluation, and Open Challenges]** Syeda Faiza Ahmed, Zien Sheikh Ali, Hunzalah Hassan Bhatti, Firoj Alam, Shammur Absar Chowdhury；Qatar Computing Research Institute, Qatar；2026. [arXiv:2608.17605](https://arxiv.org/abs/2608.17605)。用于多轮、跨模态与 full-duplex evaluation 的研究版图和边界。[arXiv survey]

<a id="ref-wen2026"></a>
**[X2Streaming-TTS: Causal Token-Level Text-to-Speech from Streaming Text with Speech-State Inheritance]** Rime Wen, Zehan Liu, Shawn Qin, Lights Shi, Roy Gan, Hao Wang, Qian Wang；X Square Robot；2026. [arXiv:2608.18661](https://arxiv.org/abs/2608.18661)。用于 causal commitment、speech-state inheritance 与严格 token-level TTS 延迟结果。[arXiv 论文]
