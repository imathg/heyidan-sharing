# 长程 agent 的上下文治理：记忆是一组带生命周期的对象

<!-- domain: agentic-rl -->

2026 年 6 月底到 7 月初，agent 论文出现一组密集信号。`[论文]` [Supersede](#ref-supersede)（Vrin，Patel 2026）将长期会话里的旧事实更新定义成可训练环境；`[论文]` [TraceRetain](#ref-traceretain)（Independent Researcher，Reddy 2026）显示 memory retention 在 noisy write 压力下才显现差异；`[论文]` [VISTA](#ref-vista)（CUHK + LIGHTSPEED，Xu et al. 2026）将 context 状态暴露成模型可见的 dashboard；`[论文]` [ECHO](#ref-echo)（北大 + 中科大 + 百度，Xie et al. 2026）在压缩后的 turn record 中保留 source index，用来回传训练 credit；`[论文]` [Self-GC](#ref-selfgc)（小红书，Hao et al. 2026）将 context 视为可 fold、mask、prune、recover 的对象集合；`[论文]` [AutoMem](#ref-automem)（Stanford，Wu et al. 2026）将 memory 管理视为可训练技能；`[论文]` [ContextNest](#ref-contextnest)（PromptOwl + Emory + IBM Research，Sulpovar et al. 2026）将 context governance 放到 retrieval 下层，负责版本、归属、完整性和审计。

这些工作分属不同层次，包括 benchmark、强化学习（RL）环境、系统层和知识库规范。`[本文归纳]` 它们共同指向一个转向：长程 agent 的上下文问题，已经从「如何将更多文本放入窗口」转向「哪些对象在什么时候可见、当前、可追溯、可训练」。摘要和向量库只覆盖其中一部分，记忆是一组带生命周期的对象。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<figure class="diagram">
<svg width="100%" viewBox="0 0 820 620" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="长程 agent 的上下文治理拓扑图：从历史文本和摘要转向带生命周期的上下文对象">
<defs>
<linearGradient id="panelGradAcmg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#131922"/><stop offset="1" stop-color="#1a2230"/></linearGradient>
<linearGradient id="nodeGradAcmg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#172130"/><stop offset="1" stop-color="#101823"/></linearGradient>
<linearGradient id="oldGradAcmg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#10151d"/><stop offset="1" stop-color="#151b25"/></linearGradient>
<filter id="shadowAcmg" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#05080d" flood-opacity="0.35"/></filter>
<marker id="arrowAcmg" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#5fd0c8"/></marker>
</defs>
<rect x="0" y="0" width="820" height="620" rx="18" fill="url(#panelGradAcmg)"/>
<text x="410" y="42" text-anchor="middle" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="24" font-weight="700" fill="#e6edf3">长程 agent 的上下文治理</text>
<text x="410" y="68" text-anchor="middle" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="13" fill="#8b97a4">从“把历史压短”转向“维护对象的可见性、当前性、源地址和审计轨迹”</text>
<g font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
<rect x="38" y="126" width="176" height="264" rx="18" fill="url(#oldGradAcmg)" stroke="#2a3441" opacity="0.9"/>
<text x="126" y="156" text-anchor="middle" font-size="15" font-weight="700" fill="#e6edf3">旧视角</text>
<rect x="62" y="184" width="128" height="42" rx="11" fill="#18212d" stroke="#384656"/>
<text x="126" y="210" text-anchor="middle" font-size="13" fill="#c9d3dc">历史文本</text>
<rect x="62" y="248" width="128" height="42" rx="11" fill="#18212d" stroke="#384656"/>
<text x="126" y="274" text-anchor="middle" font-size="13" fill="#c9d3dc">自动摘要</text>
<rect x="62" y="312" width="128" height="42" rx="11" fill="#18212d" stroke="#384656"/>
<text x="126" y="338" text-anchor="middle" font-size="13" fill="#c9d3dc">向量检索</text>
<text x="126" y="373" text-anchor="middle" font-size="11.5" fill="#8b97a4">只处理预算和相关性</text>
<path d="M222 258 C254 258 260 258 286 258" fill="none" stroke="#5fd0c8" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#arrowAcmg)"/>
<rect x="286" y="112" width="248" height="312" rx="18" fill="url(#nodeGradAcmg)" stroke="#5fd0c8" filter="url(#shadowAcmg)"/>
<text x="410" y="145" text-anchor="middle" font-size="16" font-weight="700" fill="#e6edf3">上下文对象的四个约束</text>
<rect x="314" y="178" width="86" height="74" rx="12" fill="#10222b" stroke="#5fd0c8"/>
<text x="357" y="204" text-anchor="middle" font-size="14" font-weight="700" fill="#5fd0c8">当前性</text>
<text x="357" y="225" text-anchor="middle" font-size="11.5" fill="#c9d3dc">旧事实</text>
<text x="357" y="240" text-anchor="middle" font-size="11.5" fill="#c9d3dc">失效出局</text>
<rect x="420" y="178" width="86" height="74" rx="12" fill="#10222b" stroke="#5fd0c8"/>
<text x="463" y="204" text-anchor="middle" font-size="14" font-weight="700" fill="#5fd0c8">选择性</text>
<text x="463" y="225" text-anchor="middle" font-size="11.5" fill="#c9d3dc">噪声写入</text>
<text x="463" y="240" text-anchor="middle" font-size="11.5" fill="#c9d3dc">过滤出局</text>
<rect x="314" y="278" width="86" height="74" rx="12" fill="#10222b" stroke="#5fd0c8"/>
<text x="357" y="304" text-anchor="middle" font-size="14" font-weight="700" fill="#5fd0c8">源地址</text>
<text x="357" y="325" text-anchor="middle" font-size="11.5" fill="#c9d3dc">压缩后</text>
<text x="357" y="340" text-anchor="middle" font-size="11.5" fill="#c9d3dc">仍可回查</text>
<rect x="420" y="278" width="86" height="74" rx="12" fill="#10222b" stroke="#5fd0c8"/>
<text x="463" y="304" text-anchor="middle" font-size="14" font-weight="700" fill="#5fd0c8">审计</text>
<text x="463" y="325" text-anchor="middle" font-size="11.5" fill="#c9d3dc">版本与可见性</text>
<text x="463" y="340" text-anchor="middle" font-size="11.5" fill="#c9d3dc">能重构</text>
<text x="410" y="389" text-anchor="middle" font-size="12.5" fill="#8b97a4">记忆 = 带生命周期的对象集合；摘要属于其中一种视图</text>
<path d="M534 258 C566 258 572 258 598 258" fill="none" stroke="#5fd0c8" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#arrowAcmg)"/>
<rect x="598" y="126" width="184" height="264" rx="18" fill="url(#nodeGradAcmg)" stroke="#2a3441"/>
<text x="690" y="156" text-anchor="middle" font-size="15" font-weight="700" fill="#e6edf3">三层架构</text>
<rect x="622" y="184" width="136" height="42" rx="11" fill="#142231" stroke="#5fd0c8"/>
<text x="690" y="210" text-anchor="middle" font-size="13" fill="#e6edf3">object store</text>
<rect x="622" y="248" width="136" height="42" rx="11" fill="#142231" stroke="#5fd0c8"/>
<text x="690" y="274" text-anchor="middle" font-size="13" fill="#e6edf3">policy layer</text>
<rect x="622" y="312" width="136" height="42" rx="11" fill="#142231" stroke="#5fd0c8"/>
<text x="690" y="338" text-anchor="middle" font-size="13" fill="#e6edf3">learning / audit</text>
<text x="690" y="373" text-anchor="middle" font-size="11.5" fill="#8b97a4">保存对象、选择可见性、回传证据</text>
<rect x="62" y="456" width="150" height="76" rx="12" fill="#111a24" stroke="#2a3441"/>
<text x="137" y="482" text-anchor="middle" font-size="13.5" font-weight="700" fill="#e6edf3">系统策略</text>
<text x="137" y="505" text-anchor="middle" font-size="11.5" fill="#8b97a4">ContextForge</text>
<text x="137" y="520" text-anchor="middle" font-size="11.5" fill="#8b97a4">TraceRetain</text>
<rect x="244" y="456" width="150" height="76" rx="12" fill="#111a24" stroke="#2a3441"/>
<text x="319" y="482" text-anchor="middle" font-size="13.5" font-weight="700" fill="#e6edf3">模型可见界面</text>
<text x="319" y="505" text-anchor="middle" font-size="11.5" fill="#8b97a4">VISTA dashboard</text>
<text x="319" y="520" text-anchor="middle" font-size="11.5" fill="#8b97a4">typed blocks</text>
<rect x="426" y="456" width="150" height="76" rx="12" fill="#111a24" stroke="#2a3441"/>
<text x="501" y="482" text-anchor="middle" font-size="13.5" font-weight="700" fill="#e6edf3">planner + harness</text>
<text x="501" y="505" text-anchor="middle" font-size="11.5" fill="#8b97a4">Self-GC</text>
<text x="501" y="520" text-anchor="middle" font-size="11.5" fill="#8b97a4">ContextNest</text>
<rect x="608" y="456" width="150" height="76" rx="12" fill="#111a24" stroke="#2a3441"/>
<text x="683" y="482" text-anchor="middle" font-size="13.5" font-weight="700" fill="#e6edf3">可训练 policy</text>
<text x="683" y="505" text-anchor="middle" font-size="11.5" fill="#8b97a4">Supersede</text>
<text x="683" y="520" text-anchor="middle" font-size="11.5" fill="#8b97a4">AutoMem / ECHO</text>
<path d="M137 456 V416 H357" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" opacity="0.65"/>
<path d="M319 456 V424 H410" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" opacity="0.65"/>
<path d="M501 456 V424 H410" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" opacity="0.65"/>
<path d="M683 456 V416 H463" fill="none" stroke="#8b97a4" stroke-width="1.05" stroke-dasharray="1 7" opacity="0.65"/>
<text x="410" y="575" text-anchor="middle" font-size="12.5" fill="#8b97a4">核心判断：长窗口降低压力，治理层决定哪些对象有资格影响下一步行动</text>
</g>
</svg>
</figure>

## 从容量预算，到当前事实

`[论文]` [ContextForge](#ref-contextforge) 从最直接的方向切入：大语言模型（LLM）是无状态系统，每次调用都靠 context window 接收外部知识。ContextForge 将窗口视为固定预算的执行工作区，每轮显式加载、使用、释放上下文，在 12 轮和 15 轮评测中保持相近准确率，同时减少 token 和延迟。

`[论文]` [Context Rot](#ref-contextrot)（上海交大 + 复旦 + SII + GAIR，Xia et al. 2026）把问题推进到退化层面。长搜索任务里，context 变长后，模型常见退化表现为直接放弃，或提前给出不确定答案。论文系统比较七种 context management 方法，并加上 rot-aware rejection sampling，说明“长”本身会改变模型的决策状态。

`[论文]` [Supersede](#ref-supersede) 进一步进入事实更新问题。长期会话里事实会更新，用户搬家，价格变动，计划修订。正确回答依赖当前值，旧值需要退出可见集合。把 full context 换成 bounded self-maintained memory 后，前沿模型在 LongMemEval knowledge-update 子集上从 92% 掉到 77%。作者继续加大记忆空间，准确率没有恢复；对话长度扩大 24 倍后，准确率从 68% 掉到 28%。这说明主因是维护当前事实的能力，压缩比例解释不了这组下降。论文随后用 GRPO（Group Relative Policy Optimization）把当前事实选择定义为训练信号。

`[本文归纳]` 这三篇合起来，把长程上下文问题分成三层：

| 层 | 问题 | 代表信号 |
|---|---|---|
| 预算层 | 窗口有限，历史会越积越多 | ContextForge 用固定预算工作区复用上下文 |
| 退化层 | 累积上下文会让模型给出不确定或过早答案 | Context Rot 测到 give-up 和 premature answer |
| 当前性层 | 多个事实版本共存时，模型要判断哪个生效 | Supersede 将 stale-vs-current 定义为训练目标 |

`[本文归纳]` 第一层工程直觉是扩窗口或做摘要。这一做法只能处理预算层。进入退化层和当前性层后，系统要维护对象状态：哪条信息已过期、哪条仍可用、哪个版本在某次回答时对 agent 可见。

## 四个约束：当前、选择、地址、审计

`[本文归纳]` 这些论文反复出现四个约束。相比「记忆容量」，它们更接近长程 agent 的核心指标。

第一是当前性。`[论文]` [Supersede](#ref-supersede) 把当前事实和旧事实分开，奖励 agent 使用当前值，惩罚 stale value。`[论文]` [ContextNest](#ref-contextnest) 在知识库层也处理同一件事：retrieval 负责相关性，governance 先决定哪些 artifact 是 approved、current、attributable、integrity-verified。二者都说明，相关性高的旧事实仍然可能是错误输入。

第二是选择性。`[论文]` [TraceRetain](#ref-traceretain) 在 clean ALFWorld 设置中发现，不同 retention 策略差异落在 Wilson 95% 置信区间内；加入 75% synthetic distractor 后，无界 memory 和 FIFO-K50 的 Precision@5 明显下降，TraceRetain-CEM 基本保持不变。关键机制是 unbounded memory 的平均 embedding similarity 最高，但 precision 最低，失败 distractor 离 query 也很近。选择性要同时纳入 success、redundancy、specificity、downstream utility；相似度是多项输入中的一项。

第三是源地址。`[论文]` [ECHO](#ref-echo) 把问题落到 source address 上：历史 turn 被删掉或压成 summary 后，原始 turn 一旦失去 source address，outcome-based RL 的 credit 回传路径就会断掉，成功答案也难以回到支撑它的证据。ECHO 把每个完成的环境 turn 压成 compact memory record，再用 selected source index 把正向 credit 路由回 evidence 和 selection action。`[论文]` [Self-GC](#ref-selfgc) 从系统角度给出同样约束：summary 能保留叙事状态，但会掩盖 exact evidence、locator 和 editable artifact。

第四是审计。`[论文]` [ContextNest](#ref-contextnest) 的关键目标是重构 agent 当时看到的知识版本。它用 typed Markdown、metadata、deterministic selector、hash-chained version history、graph checkpoint、MCP（Model Context Protocol）source node、audit trace，让组织能重建某次输出由哪些知识版本支撑。在 stale-version attack 里，governed selection 以更高 pass rate 和约三分之一 token cost 优于 BM25 sparse retrieval。

| 约束 | 失败时的表现 | 对应方法 |
|---|---|---|
| 当前性 | 旧事实看起来相关，回答却用错版本 | Supersede、ContextNest |
| 选择性 | 失败轨迹或噪声写入被高相似度召回 | TraceRetain |
| 源地址 | 摘要保留结论，训练和审计找不到证据来源 | ECHO、Self-GC |
| 审计 | 系统回答后无法复原知识版本和可见性 | ContextNest |

## 谁来管理上下文

`[本文归纳]` 这些工作还呈现一条产品分歧：上下文管理由谁负责。不同答案对应不同产品形态。

`[论文]` [ContextForge](#ref-contextforge) 和 `[论文]` [TraceRetain](#ref-traceretain) 落在系统侧。前者用检索和合成管线复用上下文，后者用一组可解释特征给 memory entry 打分。模型使用结果，但管理策略主要由外部系统提供。

`[论文]` [VISTA](#ref-vista) 位于中间路线。它的入口是把 runtime 状态暴露给模型：typed block、token usage、recency、access history、recoverable payload。论文称前沿模型对自身上下文“proprioceptively blind”，意思是模型从 prompt 本身看不到每块上下文的大小、年龄和使用历史。VISTA 在 LOCA-Bench 上把 Gemini-3-Flash 从 22.7 提到 50.7%，并且 ablation 显示 dashboard 的作用超过 archive 和 recovery tool 本身。这说明模型可能已有 keep/drop 能力，缺的是可读的状态变量。

`[论文]` [Self-GC](#ref-selfgc) 把决策拆成 side-channel planner 和 harness enforcement。planner 提议 fold、mask、prune；harness 负责 recoverable sidecar、safe commit boundary、cache-aware commit。Self-GC 在 33-session Hard Set 上剪掉 43.95% prefix token，同时 84.85% future continuation 保持可用；生产 split 中白天平均 input token 降 10% 到 15%。

`[论文]` [AutoMem](#ref-automem) 属于训练路线。它把 file-system operation 提升为一等 memory action，让模型决定写什么、何时取、如何组织。AutoMem 有两层循环：强模型审阅完整 trajectory 并改 memory scaffold，agent 自己的高质量 memory decision 再变成训练信号。训练目标聚焦 memory，task-action behavior 保持原样，在 Crafter、MiniHack、NetHack 上带来约 2x 到 4x 的提升。

`[本文归纳]` 四种路线可以放进一张表：

| 管理者 | 方法 | 优点 | 代价 |
|---|---|---|---|
| 外部系统 | ContextForge、TraceRetain | 可控、成本低、易部署 | 难知道未来依赖，策略可能僵硬 |
| 模型可见界面 | VISTA | 无需训练即可调用模型的 latent 能力 | 依赖 dashboard 设计和模型读表能力 |
| planner + harness | Self-GC | 管理对象化，可恢复，可设安全边界 | 运行时更复杂 |
| 可训练 memory policy | Supersede、AutoMem、ECHO | 能把 memory 决策变成学习目标 | 需要环境、轨迹和奖励定义 |

这些路线也能对应到很多 agent infra 产品形态。一个自动摘要功能属于外部系统；一个让模型看到上下文预算和 block 状态的面板属于 VISTA 路线；一个带 sidecar、checkpoint、artifact selector 的 agent harness 属于 Self-GC 和 ContextNest 路线；一个把写 memory 当动作训练的系统属于 AutoMem 路线。

## 压缩以后还要能学习

`[论文]` [ECHO](#ref-echo) 把这个话题连接到 RL 训练。context management 已经让长程 rollout 可行：截断、summary、compact memory state 都在减少 token。同时，这些方法会引入两个副作用。细粒度 evidence 更难复用；原始 turn 失去 source address 后，outcome reward 也失去可回传路径。

ECHO 的做法是把每个 environment turn 压成 memory record，重建 bounded policy context 时从这些 record 里选择，同时保留 selected source indices。这样成功结果的正向 credit 可以回到证据和选择动作。BrowseComp-Plus 上，ECHO 达到 43.4% held-out accuracy，高于 GRPO 的 28.9% 和 rolling-summary baseline SUPO 的 36.1%。

`[本文归纳]` 这种思路将 context management 和 credit assignment 连接起来：压缩会改变训练信号追溯证据的路径。一个 summary 可能让模型答对当前问题，却让训练系统无法确定该奖励哪段证据选择。source-addressable memory record 牺牲一些压缩率上限，换来可训练性和可审计性。

这也是 `[论文]` [Self-GC](#ref-selfgc) 强调 recoverable sidecar 的原因。fold、mask、prune 可以降低 active token；sidecar 保证被移出 active context 的对象仍可恢复。对 agent 来说，隐藏对象时仍保留定位和恢复路径；删除对象会切断 evidence path。

## 记忆有模态，也会改变推理

`[论文]` [DMV-Bench](#ref-dmvbench)（Dartmouth College，Tang et al. 2026）把记忆对象扩展到文本以外。DMV-Bench 让 agent 在多轮购物任务中见到带 incidental cue 的产品图片，稍后要找回对应商品 URL。文字 caption baseline 无法充分保留视觉 cue；DualMem 维护 visual 和 verbal 两条 code，在 Gemini 2.5 Flash 与 Qwen2.5-VL-7B 上都优于 caption baseline 和三种 multimodal memory system。

`[论文]` [DRIFTLENS](#ref-driftlens)（Amazon，Fang et al. 2026）给出另一类风险：记忆会改变推理轨迹。个性化系统会把用户属性、偏好和历史上下文注入后续 prompt。DRIFTLENS 比较无记忆轨迹和注入 user-attribute memory 后的轨迹，发现四个 LLM 在 10 类用户属性上都出现 medium-to-large reasoning drift；最终回答仍然流畅合理，漂移发生在价值权衡和推理步骤里。GRPO 和 DPO（Direct Preference Optimization）都能降低漂移，效果依赖模型和 reward 设计。

`[本文归纳]` 这两篇将 memory 从单一 buffer 扩展为多对象系统。视觉 cue、事实版本、用户属性、tool evidence、file locator 是不同对象。每种对象有自己的保真要求：视觉对象要保留感知细节，事实对象要保留当前性，个性化对象要控制推理漂移，tool evidence 要保留 source address。将它们全压成一段自然语言摘要，会让不同约束互相覆盖。

## 一张设计表

`[本文归纳]` 这些方法可以归入四个设计维度。它们彼此可组合，每个系统都需在这些维度上取值。

| 维度 | 取值 | 代表工作 |
|---|---|---|
| 管理对象 | transcript turn、fact value、memory entry、visual cue、user attribute、artifact version、skill layer | ECHO、Supersede、TraceRetain、DMV-Bench、DRIFTLENS、ContextNest、AgenticSTS |
| 决策者 | heuristic、retrieval pipeline、model-visible dashboard、side-channel planner、trainable memory policy、governance selector | TraceRetain、ContextForge、VISTA、Self-GC、AutoMem、ContextNest |
| 保留保证 | 当前性、抗噪选择、source address、bounded visibility、模态保真、reasoning stability、audit reconstruction | Supersede、TraceRetain、ECHO、AgenticSTS、DMV-Bench、DRIFTLENS、ContextNest |
| 反馈环 | inference reuse、diagnostic benchmark、RL reward、trajectory review、audit trace | ContextForge、Context Rot、Supersede、AutoMem、ContextNest |

`[论文]` [AgenticSTS](#ref-agenticsts)（Alaya Lab + 上海交大 + 上海创智学院 + 南开 + 中科大，Cheng et al. 2026）在这张表中更像一个评测方法学样例。它将 memory 定义成「未来每个 decision 被允许看到什么」的 contract。每一步都从 typed retrieval 组装新 user message，跨决策原始 transcript 留在 prompt 之外。这样 prompt 长度有界，memory/skill layer 能单独 ablate。论文在 Slay the Spire 2 中给出 298 条完成轨迹、condition tag、frozen snapshot、prompt record 和分析脚本。

`[本文归纳]` 这类 testbed 的价值主要来自实验变量化的 memory interface，小样本胜率属于附带读数。未来 agent memory 论文若只报告「加 memory 提升多少」，而缺少对象可见性、层级 ablation 和版本复原说明，证据密度会偏低。

## 对 agent 产品的含义

`[本文归纳]` 如果将这些结论用于 coding agent、research agent 或个人知识库 agent，最直接的产品判断是：自动摘要适合做 token 预算工具，长期记忆仍需要显式治理层。自动摘要可以降低 token；当前性、选择性、源地址和审计需由治理层单独承担。

对应到架构上，可以分成三层：

| 层 | 负责什么 | 对应约束 |
|---|---|---|
| object store | 保存 turn、tool span、file、fact、artifact version、user attribute | 源地址、审计 |
| policy layer | 决定当前 step 看哪些对象，哪些 fold、mask、prune、retrieve | 当前性、选择性 |
| learning/audit layer | 记录选择动作与结果，回传 credit，支持复盘 | 可训练、可追溯 |

`[本文归纳]` 这三层可以与「长上下文模型」并行。长窗口减少了管理压力，但不会自动判断事实版本、噪声写入、视觉 cue 或个性化漂移。长窗口提供更大的内存空间，context governance 则提供类似操作系统和文件系统的管理能力。缺少后者时，容量增加会同时带来更多旧事实、更多 distractor 和更多不可审计状态。

> **结论：长程 agent 的记忆系统负责维护可见性、当前性、源地址和审计约束。摘要只解决 token 预算；治理层决定哪些对象在下一步有资格影响行动。**

## Reference

<a id="ref-contextforge"></a>
**[Context Recycling for Long-Horizon LLM Inference]** Derek Thomas，Independent Researcher，2026. [arXiv:2606.26105](https://arxiv.org/abs/2606.26105)。本文用到它的固定预算 context workspace 与 context recycling 设定，作为预算层起点。`[arxiv 论文 / 独立研究者]`

<a id="ref-supersede"></a>
**[Supersede: Diagnosing and Training the Memory-Update Gap in LLM Agents]** Vedant Patel，Vrin，2026. [arXiv:2606.27472](https://arxiv.org/abs/2606.27472)。本文用到它的 supersession gap、LongMemEval knowledge-update 结果、conversation length 而非 compression ratio 的失败机制，以及 GRPO 训练当前事实选择的环境。`[arxiv 论文]`

<a id="ref-dmvbench"></a>
**[DMV-Bench: Diagnosing Long-Horizon Multimodal Agents' Visual Memory with Incidental Cue Injection]** Yujin Tang, Chenming Shang, Ruize Xu, Nikhil Singh，Dartmouth College，2026. [arXiv:2606.27499](https://arxiv.org/abs/2606.27499)。本文用到它的 visual memory benchmark 与 DualMem 结果，说明 text summary 对视觉 cue 保真的覆盖不足。`[arxiv 论文]`

<a id="ref-traceretain"></a>
**[Selective Memory Retention for Long-Horizon LLM Agents]** Pranath Reddy，Independent Researcher, Huntsville, Alabama，2026. [arXiv:2606.29178](https://arxiv.org/abs/2606.29178)。本文用到它在 clean ALFWorld 与 noisy-write stress 下的对照，以及 high-similarity failed distractor 的 memory pollution 机制。`[arxiv 论文 / 独立研究者]`

<a id="ref-vista"></a>
**[LLM Agents Are Latent Context Managers: Eliciting Self-Managed Context via a Proprioceptive Dashboard]** Binyan Xu, Haitao Li, Kehuan Zhang，The Chinese University of Hong Kong + LIGHTSPEED，2026. [arXiv:2606.30005](https://arxiv.org/abs/2606.30005)。本文用到它的 proprioceptive dashboard、typed block 状态、LOCA-Bench 提升和 dashboard ablation。`[arxiv 论文]`

<a id="ref-contextrot"></a>
**[Diagnosing and Mitigating Context Rot in Long-horizon Search]** Shijie Xia, Yikun Wang, Zhen Huang, Pengfei Liu，Shanghai Jiao Tong University + Fudan University + Shanghai Innovation Institute + Generative AI Research Lab，2026. [arXiv:2606.29718](https://arxiv.org/abs/2606.29718)。本文用到它对 context rot 的定义、give-up / premature uncertain answer 现象、七类 context management 策略比较。`[arxiv 论文]`

<a id="ref-echo"></a>
**[ECHO: Prune to act, trace to learn with selective turn memory in agentic RL]** Zijun Xie, Binbin Zheng, Enlei Gong, Jihua Liu, Yuyang You, Lingfeng Liu, Jiayao Tang, Guanqun Zhao, Aoqi Hu, Zeyu Chen，Peking University + University of Science and Technology of China + Baidu Inc.，2026. [arXiv:2606.31650](https://arxiv.org/abs/2606.31650)。本文用到它的 source-indexed reconstruction、credit routing 和 BrowseComp-Plus 结果。`[arxiv 论文]`

<a id="ref-selfgc"></a>
**[Self-GC: Self-Governing Context for Long-Horizon LLM Agents]** Xubin Hao, Hongjin Meng, Xin Yin, Jiawei Zhu, Chenpeng Cao，Xiaohongshu，2026. [arXiv:2607.00692](https://arxiv.org/abs/2607.00692)。本文用到它把 context 当 indexed object lifecycle 管理、sidecar recovery、Hard Set 与 production token reduction 结果。`[arxiv 论文]`

<a id="ref-automem"></a>
**[AutoMem: Automated Learning of Memory as a Cognitive Skill]** Shengguang Wu, Hao Zhu, Yuhui Zhang, Xiaohan Wang, Serena Yeung-Levy，Stanford University，2026. [arXiv:2607.01224](https://arxiv.org/abs/2607.01224)。本文用到它把 file-system memory operation 当成一等 action、memory scaffold optimization、memory proficiency training 和 2x 到 4x 长程游戏结果。`[arxiv 论文]`

<a id="ref-agenticsts"></a>
**[AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents]** Xiangchen Cheng, Yunwei Jiang, Jianwen Sun, Zizhen Li, Chuanhao Li, Xiangcheng Cao, Yihao Liu, Fanrui Zhang, Li Jin, Kaipeng Zhang，Alaya Lab + Shanghai Jiao Tong University + Shanghai Innovation Institute + Nankai University + University of Science and Technology of China，2026. [arXiv:2607.02255](https://arxiv.org/abs/2607.02255)。本文用到它把 memory 定义成 bounded visibility contract，并用 typed retrieval、frozen snapshots、prompt records 支持 ablation。`[arxiv 论文]`

<a id="ref-driftlens"></a>
**[DRIFTLENS: Measuring Memory-Induced Reasoning Drift in Personalized Language Models]** Xi Fang, Weijie Xu, Yingqiang Ge, Yuhui Xu, Stephanie Eckman, Chandan K. Reddy，Amazon，2026. [arXiv:2607.02374](https://arxiv.org/abs/2607.02374)。本文用到它的 memory-induced reasoning drift 度量，以及个性化属性对推理轨迹的影响。`[arxiv 论文]`

<a id="ref-contextnest"></a>
**[ContextNest: Verifiable Context Governance for Autonomous AI Agents]** Misha Sulpovar, Benn R. Konsynski, Qaish Kanchwala, Gabe Goodhart，PromptOwl, LLC + Goizueta Business School, Emory University + Independent + IBM Research，2026. [arXiv:2607.02116](https://arxiv.org/abs/2607.02116)。本文用到它的 context governance 层、typed documents、deterministic selector、hash-chained version history、MCP source node 和 stale-version attack 结果。`[arxiv 论文]`
