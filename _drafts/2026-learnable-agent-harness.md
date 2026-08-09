# 可学习 Agent Harness：从固定工作流到运行时控制面
<!-- domain: claude-code-ecosystem -->

`[本文归纳]` Agent Harness 正在经历一次职责迁移。早期 Harness 主要回答“按什么步骤调用模型和工具”，新的研究开始让它回答五个运行时问题：当前什么状态有效，模型提出的动作何时生效，结果由什么证据确认，失败应修复哪一层，以及哪些运行经验可以更新下一版系统。

这里的**运行时控制面**，指模型外负责状态、动作生效与核验的执行层。模型可以提出计划、工具调用和状态更新；控制面决定这些 proposal 能否进入权威状态、能否产生外部副作用，以及执行结果如何回写。固定 workflow 是控制面的一种策略，控制面本身还可以由规则、训练策略或可演化程序实现。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../meta/#claim-tags)。

## 1. 从“怎么跑”到“什么算真的发生了”

`[个人实验]` [Harness Engineering for Self-Improvement](#ref-weng2026)（Lilian Weng 个人博客，Weng 2026）把 Harness 的范围扩展到 prompt 之外：它组织规划、工具与动作、上下文、持久化工件、评测、权限和状态。文章将优化对象依次列为 `prompt → structured context → workflow → harness code → optimizer code`。优化对象越往后，越接近模型外的完整执行程序。

`[本文归纳]` 这条演进可以画成一条状态机。输入先成为 observation，Harness 选出当前有效状态，模型基于它生成 proposal；控制面随后核验或补充证据，再决定 commit、fallback 或转交人工处理。执行结束后先生成 receipt，receipt 经过校验后才能更新状态。

| 阶段 | 输入 | Harness 的职责 | 常见失败 |
|---|---|---|---|
| Observe | 用户请求、工具结果、环境变化 | 保留来源、时间和对象身份 | 旧结果与新结果混在一起 |
| State | observation 与历史记录 | 选择当前有效版本，标出未决冲突 | 历史语法正确但已失效 |
| Propose | 模型计划或工具调用 | 解析成 typed action，不直接视为事实 | 「模型说完成」被当成完成 |
| Verify | proposal、policy、当前证据 | 检查约束，必要时发起低副作用 probe | 有权限却没有充分证据 |
| Commit | 已通过核验的 action | 释放外部副作用，记录精确目标 | 目标或参数绑定漂移 |
| Receipt | 环境返回的实际结果 | 校验、落账、局部 repair 或回滚 | 生成成功被误当成执行成功 |

`[本文归纳]` 工作流描述模型准备如何行动；生效合同规定哪一步改变了世界、谁能证明它发生过，以及失败后从哪个状态继续。长程任务真正需要持久化的是后者。

<figure class="diagram">
<svg width="100%" viewBox="0 0 820 620" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="harness-runtime-title harness-runtime-desc" font-family="-apple-system,'PingFang SC','Microsoft YaHei','Segoe UI',Roboto,Helvetica,Arial,sans-serif">
<title id="harness-runtime-title">Harness 运行时控制面</title>
<desc id="harness-runtime-desc">执行控制面内，权威状态、提案、核验与提交形成一次运行的生效合同；收据证据经两条互相独立的反馈回路，分别让运行时策略与候选程序学习演化。</desc>
<defs>
<marker id="ag" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#94a3b8"/></marker>
<marker id="ac" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#38bdf8"/></marker>
<marker id="aa" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#fbbf24"/></marker>
</defs>
<rect x="0" y="0" width="820" height="620" fill="#0b1220"/>
<text x="30" y="30" fill="#f1f5f9" font-size="22" font-weight="700">Harness 运行时控制面</text>
<text x="30" y="50" fill="#94a3b8" font-size="12.5">状态、提交和核验形成生效合同；策略与程序沿两条反馈回路学习</text>
<!-- executive / control plane boundary (state / admission / verification / commit) -->
<rect x="121" y="198" width="460" height="124" rx="10" fill="#0e1a30" stroke="#f59e0b" stroke-width="1.4" stroke-dasharray="1 5" opacity="0.92"/>
<text x="575" y="214" text-anchor="end" fill="#f59e0b" font-size="11" font-weight="700" letter-spacing="1.4">EXECUTIVE / CONTROL PLANE</text>
<!-- loop band labels -->
<text x="430" y="58" fill="#38bdf8" font-size="11" font-weight="700" letter-spacing="0.6">A · POLICY LOOP</text>
<text x="560" y="380" fill="#fbbf24" font-size="11" font-weight="700" letter-spacing="0.6">B · PROGRAM LOOP</text>
<!-- ===== connectors (under nodes) ===== -->
<!-- main one-run chain (solid, neutral) at y=278 -->
<line x1="120" y1="278" x2="131" y2="278" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#ag)"/>
<line x1="233" y1="278" x2="244" y2="278" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#ag)"/>
<line x1="346" y1="278" x2="357" y2="278" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#ag)"/>
<line x1="459" y1="278" x2="470" y2="278" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#ag)"/>
<line x1="572" y1="278" x2="583" y2="278" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#ag)"/>
<line x1="685" y1="278" x2="696" y2="278" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#ag)"/>
<line x1="296" y1="136" x2="296" y2="244" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#ag)"/>
<!-- Loop A policy (cyan dashed): receipt -> runtime policy -> model -->
<polyline points="749,246 749,64 122,64 122,78" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="6 4" marker-end="url(#ac)"/>
<line x1="228" y1="108" x2="239" y2="108" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="6 4" marker-end="url(#ac)"/>
<!-- Receipt -> 权威状态 (cyan dashed, cross-round evidence) -->
<polyline points="790,310 790,558 180,558 180,312" fill="none" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="6 4" marker-end="url(#ac)"/>
<text x="430" y="551" text-anchor="middle" fill="#7dd3fc" font-size="10.5">更新权威状态</text>
<!-- Loop B program (amber): receipt -> candidate -> gate -> promotion into plane -->
<line x1="720" y1="310" x2="720" y2="386" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="6 4" marker-end="url(#aa)"/>
<line x1="657" y1="444" x2="657" y2="468" stroke="#fbbf24" stroke-width="1.6" marker-end="url(#aa)"/>
<polyline points="560,498 530,498 530,316" fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="6 4" marker-end="url(#aa)"/>
<text x="524" y="362" text-anchor="end" fill="#fcd34d" font-size="10.5">晋升进入控制面</text>
<!-- ===== nodes ===== -->
<!-- Runtime Policy (cyan) -->
<rect x="30" y="78" width="198" height="60" rx="8" fill="#0f2532" stroke="#38bdf8" stroke-width="1.5"/>
<text x="42" y="99" fill="#e2e8f0" font-size="13" font-weight="600">Runtime Policy</text>
<text x="42" y="114" fill="#7dd3fc" font-size="10.5">read · update · consolidate</text>
<text x="42" y="129" fill="#7dd3fc" font-size="10.5">高频选择既有动作 · 下一轮直接生效</text>
<!-- Model (neutral) -->
<rect x="241" y="84" width="110" height="52" rx="8" fill="#131c2c" stroke="#94a3b8" stroke-width="1.5"/>
<text x="296" y="105" text-anchor="middle" fill="#e2e8f0" font-size="13" font-weight="600">Model</text>
<text x="296" y="122" text-anchor="middle" fill="#9fb3c8" font-size="10.5">计划与候选动作</text>
<!-- chain row -->
<rect x="20" y="246" width="100" height="64" rx="8" fill="#131c2c" stroke="#94a3b8" stroke-width="1.5"/>
<text x="70" y="272" text-anchor="middle" fill="#e2e8f0" font-size="12.5" font-weight="600">Observation</text>
<text x="70" y="292" text-anchor="middle" fill="#9fb3c8" font-size="10.5">来源 · 时间 · 身份</text>
<rect x="133" y="246" width="100" height="64" rx="8" fill="#0f2532" stroke="#38bdf8" stroke-width="1.5"/>
<text x="183" y="270" text-anchor="middle" fill="#e2e8f0" font-size="12.5" font-weight="600">权威状态</text>
<text x="183" y="287" text-anchor="middle" fill="#7dd3fc" font-size="10.5">current / unknown</text>
<text x="183" y="300" text-anchor="middle" fill="#7dd3fc" font-size="10.5">superseded</text>
<rect x="246" y="246" width="100" height="64" rx="8" fill="#131c2c" stroke="#c7d2e0" stroke-width="1.5"/>
<text x="296" y="272" text-anchor="middle" fill="#e2e8f0" font-size="12.5" font-weight="600">Proposal</text>
<text x="296" y="292" text-anchor="middle" fill="#9fb3c8" font-size="10.5">typed action</text>
<rect x="359" y="246" width="100" height="64" rx="8" fill="#241c10" stroke="#fbbf24" stroke-width="1.5"/>
<text x="409" y="270" text-anchor="middle" fill="#e2e8f0" font-size="12" font-weight="600">Verify / Probe</text>
<text x="409" y="287" text-anchor="middle" fill="#fcd34d" font-size="10.5">约束 · readback</text>
<text x="409" y="300" text-anchor="middle" fill="#fcd34d" font-size="10.5">低副作用探测</text>
<rect x="472" y="246" width="100" height="64" rx="8" fill="#241c10" stroke="#fbbf24" stroke-width="1.5"/>
<text x="522" y="272" text-anchor="middle" fill="#e2e8f0" font-size="12.5" font-weight="600">Commit</text>
<text x="522" y="292" text-anchor="middle" fill="#fcd34d" font-size="10.5">释放副作用</text>
<rect x="585" y="246" width="100" height="64" rx="8" fill="#131c2c" stroke="#94a3b8" stroke-width="1.5"/>
<text x="635" y="272" text-anchor="middle" fill="#e2e8f0" font-size="12" font-weight="600">Environment</text>
<text x="635" y="292" text-anchor="middle" fill="#9fb3c8" font-size="10.5">实际世界</text>
<rect x="690" y="246" width="118" height="64" rx="8" fill="#0f2532" stroke="#38bdf8" stroke-width="1.5"/>
<text x="749" y="263" text-anchor="middle" fill="#e2e8f0" font-size="11.5" font-weight="600">Receipt +</text>
<text x="749" y="277" text-anchor="middle" fill="#e2e8f0" font-size="11.5" font-weight="600">Failure Edge</text>
<text x="749" y="293" text-anchor="middle" fill="#7dd3fc" font-size="10.5">实际结果 · 修复 owner</text>
<text x="749" y="306" text-anchor="middle" fill="#7dd3fc" font-size="10.5">恢复入口</text>
<!-- Harness Candidate (amber) -->
<rect x="560" y="388" width="195" height="56" rx="8" fill="#241c10" stroke="#fbbf24" stroke-width="1.5"/>
<text x="657" y="408" text-anchor="middle" fill="#e2e8f0" font-size="12.5" font-weight="600">Harness Candidate</text>
<text x="657" y="424" text-anchor="middle" fill="#fcd34d" font-size="10.5">verifier · rule · builder</text>
<text x="657" y="437" text-anchor="middle" fill="#fcd34d" font-size="10.5">候选程序改变执行语义</text>
<!-- Behavioral Gate (amber) -->
<rect x="560" y="470" width="195" height="56" rx="8" fill="#241c10" stroke="#fbbf24" stroke-width="1.5"/>
<text x="657" y="490" text-anchor="middle" fill="#e2e8f0" font-size="12.5" font-weight="600">Behavioral Gate</text>
<text x="657" y="506" text-anchor="middle" fill="#fcd34d" font-size="10.5">frozen eval · replay</text>
<text x="657" y="519" text-anchor="middle" fill="#fcd34d" font-size="10.5">通过后晋升 · 失败 rollback</text>
<!-- footer -->
<text x="30" y="604" fill="#8194a8" font-size="10.5">反馈先成为可追溯证据；policy 直接学习选择，program 经过行为门后才改变控制面。</text>
</svg>
<figcaption>实线表示单次运行的生效链；虚线表示 receipt 回写权威状态、runtime policy 与候选 Harness program 的学习路径。</figcaption>
</figure>

## 2. 从终局失败定位修复位置

`[论文]` [Model or Harness?](#ref-raj2026)（Scale AI，Raj et al. 2026）将 41 类 Agent failure 定位到 interaction edge 上：模型与 context、memory、tool、local environment、external environment、owner、grader 或其他模型之间都可能产生故障。每条 failure 还带一个 `fault side`，标出修复应落在哪个组件。

`[论文]` 同一个“工具调用失败”可以有两条因果链。wrapper 吞掉错误时，模型从未看到真实 observation，修复 owner 在工具或 Harness；wrapper 已返回错误而模型仍继续声称成功时，修复 owner 在模型策略。论文让独立 reasoning agent 复现这些标签，表现最好的 judge 与人工标签的 Cohen's kappa 达到 **0.76**。这个数字表明 taxonomy 具有一定可复现性；复杂轨迹仍可能有多个共同成因。

`[论文]` [OneDayAgent](#ref-zheng2026)（浙江大学、蚂蚁集团等，Zheng et al. 2026）把开放请求拆成有界子任务，由 Harness 保留全局意图和 execution memory；所有子任务结束后，verifier 对原始请求、子任务结果与 attachments 做全局核验，再局部修补缺陷。在 AgentIF-OneDay 的 104 个任务上，GLM-5.2 backend 的 overall score 为 **0.821**，同一 Harness 还可运行于三个模型家族的五个 backend。

`[本文归纳]` 失败定位与局部 repair 共享一条因果链。定位回答“最早未恢复的错误发生在哪条交互边”；repair 回到那条边修 observation、state、policy 或 artifact。只看终局 success，会把模型错误、工具错误、环境错误和 grader 错误压成一个分数，也会诱导系统从头重跑已经做对的部分。

## 3. 状态权威与动作提交必须分开

`[论文]` [The LLM Proposes, the Executive Disposes](#ref-arjmandi2026)（独立研究者，Arjmandi 2026）把 LLM 限定为 typed proposal 的提交者。deterministic Executive 持有 belief；模型预先登记 prediction，代码再把它与 observation diff 匹配，只有匹配成立的 claim 才进入状态。长期目标由代码执行的 commitment store 保存，“done” 这段文本本身不构成事件。

`[论文]` 这套 instrument 将 binding drift 与 commitment drift 分开。三个种子的消融中，关闭 commitment mechanism 后 goal-abandonment 从 0.00 变为 **1.00**，binding error 仍为 0.00。作者也披露了关键边界：52 个 gated runs 在 ARC-AGI-3 上均未通过任何关卡。这项工作的贡献是让失败可测、让系统能在运行中判定自身无效，尚未证明系统更能完成任务。

`[论文]` [SafeCommit](#ref-akewar2026)（Florida International University，Akewar et al. 2026）处理更接近副作用释放的一层。它从 memory、observation、tool output、provenance 和 policy constraint 构造多个 plausible worlds。一个动作只有在所有保留 world 中都安全时才获得 certificate；证据不足时，控制器选择低副作用 probe、fallback 或转交人工处理。

`[本文归纳]` 权限与证据因此形成两道门。权限回答主体是否有权删除文件、发消息或修改远端对象；证据回答当前路径、收件人、对象版本和用户意图是否仍然有效。检索到的 memory 可能已过期，access control 仍会放行；SafeCommit 的 proof-of-concept 为这道缺口增加了 `commit / probe / fallback` 接口。

`[论文]` [When History Lies](#ref-wu2026)（腾讯微信团队，Wu et al. 2026）说明完整历史只记录发生过什么，当前状态需要单独判定。ContextPollute-Bench 保持最新请求、工具定义和 gold next action 不变，只向历史注入旧实体、旧参数或失败调用。Qwen3-1.7B 原本正确的决策中，有 **32.1%** 因污染而翻转。旧记录仍然语法合法、语义合理，问题在于它已经失去控制下一动作的资格。

`[论文]` 该工作在 Oracle State 条件下，让 teacher 对只看 polluted history 的 student 进行 on-policy distillation，Balanced Tool-Use Accuracy 达到 **87.0%**，高于 Gold-SFT 的 66.3%。训练目标由此多出一个维度：模型既要学会调用工具，也要学会判断哪份状态在当前回合有权约束调用。

## 4. 可学习的对象分成状态策略与 Harness 程序

`[论文]` [EvoHarness-RL](#ref-ning2026)（UIUC、Meta AI，Ning et al. 2026）把 Belief、Progress、Experience 三类外部状态合成 BPE 接口。SFT 先教模型 Harness action space，cost-aware GRPO 再优化何时 read、update 和 consolidate。在 Qwen3-8B、ALFWorld 设置中，论文报告 seen success **96.9%**、unseen success **86.6%**。

`[论文]` 这个实验的关键增量在于把外部状态使用转化为带成本的 policy action，并通过 memory store 的读写实现。训练后，模型把反复出现的 Harness 使用方式吸收到 policy 中，外部访问从固定、频繁的 scaffold 变为选择性调用。结论仍绑定 ALFWorld；真实工作流还包含权限、不可逆副作用和开放工具错误。

`[论文]` [EvolveNet](#ref-nie2026)（香港浸会大学、中国科学技术大学、香港科技大学，Nie et al. 2026）进一步把 Harness 程序本身设为学习对象：各数据本地部署从同一个 shared Harness 出发演化代码，随后只上传 scope-typed program delta 与行为证据。服务端组合候选修改，并在行为门通过后晋升下一版 Harness。

`[论文]` 程序演化需要语义合并，参数平均并不适用。两个本地有效的修改可能同时编辑同一控制路径，也可能分别加强和移除同一 verifier。EvolveNet 因此把共同 base、适用范围、行为变化和 adoption gate 一起交给 aggregator。论文在五类设置上报告改进，但每种 aggregation rule 只有一个 seed，且 data locality 本身不提供隐私保证。

`[本文归纳]` 这两类学习对象需要分开。runtime policy 学的是既有接口上的选择，例如何时读取状态、何时 probe、何时 consolidate；Harness evolution 学的是接口背后的程序，例如 verifier、repair rule 和 context builder。前者可以在线高频调整，后者会改变执行语义，更适合先作为候选版本接受回归验证，再受控晋升。

## 5. 五个旋钮描述了同一片设计空间

`[本文归纳]` 九个来源归纳出一组围绕模型外执行控制的五轴坐标，覆盖它如何形成、运行和更新；完整 Agent 架构还包含模型、环境与多 Agent 协议等其他维度。

| 旋钮 | 固定 Harness | 可学习 runtime policy | 可演化 Harness program |
|---|---|---|---|
| 状态 owner | transcript 或固定 store | BPE、Oracle-conditioned state | 新 schema 或 state operator 的候选版本 |
| 提交语义 | tool call 直接执行 | proposal 后 probe、certificate、commit | commit rule 代码经 gate 晋升 |
| 核验单位 | outcome score | action、observation diff、artifact | program delta 的行为回归 |
| 修复粒度 | 整轮重跑或固定分支 | targeted probe、局部 subtask repair | scope-typed patch 与 rollback |
| 学习对象 | prompt、workflow | read / update / consolidate / act policy | Harness code、aggregator rule |

`[本文归纳]` 五轴里最容易混读的是“状态 owner”和“学习对象”。把更多历史塞进 prompt 会增加可见信息量；能否作为 current 状态仍由外部版本、来源和有效性合同决定。policy 可以优化选择，权威状态则由经过 admission 的 observation 形成。

`[本文归纳]` “提交语义”决定系统风险。低副作用的搜索可以允许模型直接调用，再以超时和重试策略处理；删除、发送、支付、发布等动作需要更强的 proposal、readback、certificate 或人工 gate。同一个 Agent 可以按工具风险采用分级提交语义。

## 6. 先冻结运行合同，再训练 Harness

`[个人实验]` [从 Spec 驱动转向环境与验证驱动](#ref-wuzy2026)（吴佐衍个人技术文章，Wu 2026）把企业内部的构建、部署、测试、数据、日志、监控和发布链路视为 Agent 可调用环境。文章主张让 workflow 回到调度、权限、状态保存、审计和高风险检查，并把 spec 分成长期约束与可随反馈调整的实现假设。

`[本文归纳]` 这给可学习 Harness 划出一条实用边界。学习器可以寻找更好的步骤、状态读写和修复方式；以下合同应先稳定下来，否则每次“进步”都可能同时改写评测尺子：

1. **Observation 有来源和时间**。工具返回、用户更正和环境变化保留对象身份，能够区分 current、superseded 与 unknown。
2. **Proposal 不直接改权威状态**。模型输出先解析成候选动作或候选事实，外部系统决定 admission 与 commit。
3. **副作用有准确 receipt**。生成成功、传输成功和远端对象生效分别记账；结果不确定时不自动重发。
4. **Verifier 与任务目标绑定**。验证同时读取原始约束、实际 artifact 和环境结果，模型总结只作辅助。
5. **学习产物走版本晋升**。policy checkpoint、Harness patch 和 aggregator rule 都有 frozen evaluation、回归门和 rollback target。

`[本文归纳]` 这些合同为 Harness 学习提供可归因反馈。状态 owner 稳定后，模型才能知道一次失败来自错误 observation、错误 proposal、错误 commit 还是错误 verifier；成功定义稳定后，runtime policy 与 program delta 的收益才可比较。

## 7. 三个仍未闭合的问题

`[本文归纳]` 第一，谁验证 verifier。OneDayAgent 依赖交付级 judge，SafeCommit 依赖 plausible-world constructor，EvolveNet 依赖 behavioral gate。每个 gate 都把风险上移了一层。更完整的系统需要为 verifier 保留版本、覆盖范围、失败条件和独立 readback，让它成为可审计的判定组件。

`[本文归纳]` 第二，Harness policy 能否跨环境迁移。BPE 在 ALFWorld 中有明确语义，企业工作流里的 belief 可能是数据库快照、审批状态、文件树或对话承诺。统一 action protocol 是否能保留这些对象各自的有效性与权限边界，仍需要跨域实验。

`[本文归纳]` 第三，Harness 演化怎样控制语义漂移。程序 delta 能积累本地经验，也会改变 tool contract、error handling 与状态 schema。aggregate score 容易奖励投机修复。候选修改还需要 contract test、旧 case replay、scope review 和可恢复发布，才能把“会改 Harness”变成可维护能力。

`[本文归纳]` 可学习 Harness 的核心目标是给模型行动配上清晰的状态、证据和生效边界。模型负责提出更强的行动；运行时控制面记录行动依据、修复 owner 和恢复入口，并把执行结果变成下一次学习的可信反馈。

## Reference

<a id="ref-weng2026"></a>
**[Harness Engineering for Self-Improvement]** Lilian Weng，个人技术博客，2026. [Lil'Log](https://lilianweng.github.io/posts/2026-07-04-harness/)。用于界定 Harness 范围、优化对象上移和 Meta-Harness 研究版图。[个人实验 / 技术综述]

<a id="ref-raj2026"></a>
**[Model or Harness? An Interaction-Centric Taxonomy for Localizing Agent Failures]** Harsh Raj, Vipul Gupta, Anas Mahmoud, Razvan-Gabriel Dumitru, Darvin Yi, Aakash Sabharwal, Yunzhong He，Scale AI，2026. [arXiv:2607.28802](https://arxiv.org/abs/2607.28802)。用于 interaction edge、fault side 与修复 owner 归因。[arXiv 论文]

<a id="ref-zheng2026"></a>
**[OneDayAgent: Towards a Long-Horizon Harness for Autonomous Agents]** Jingsheng Zheng, Xinyuan Fang, Jintian Zhang, Zhengke Gui, Huajun Chen, Ningyu Zhang，Zhejiang University、Ant Group、Independent Researcher，2026. [arXiv:2608.05013](https://arxiv.org/abs/2608.05013)。用于长程任务拆分、execution memory、交付核验与局部 repair。[arXiv 论文 / ongoing work]

<a id="ref-arjmandi2026"></a>
**[The LLM Proposes, the Executive Disposes: A Self-Verifying Agent Instrument that Dissociates Commitment Drift from Binding Drift in Long-Horizon Agents]** Mohsen Arjmandi，Independent Researcher，2026. [arXiv:2608.04066](https://arxiv.org/abs/2608.04066)。用于 proposal / commitment 分离、deterministic Executive 和漂移测量边界。[arXiv 论文 / 独立研究者单人]

<a id="ref-akewar2026"></a>
**[SafeCommit: Certifying When Memory-Grounded Agents May Safely Act]** Mayur Akewar, Ravi Ranjan，Florida International University，2026. [arXiv:2608.04289](https://arxiv.org/abs/2608.04289)。用于 plausible-world certificate 与 commit / probe / fallback 接口。[arXiv 论文 / proof of concept]

<a id="ref-ning2026"></a>
**[EvoHarness-RL: Learning Self-Evolving Runtime Harness for Long-Horizon LLM Agents]** Xuying Ning, Dongqi Fu, Tianxin Wei, Hanqing Zeng, Yuanchen Bei, Bingxuan Li, Zihao Li, Qifan Wang, Xiang Shen, Yifan Wu, Jiayi Liu, Hong Li, Yinglong Xia, Xiangjun Fan, Hanghang Tong, Jingrui He，University of Illinois Urbana-Champaign、Meta AI，2026. [arXiv:2608.05446](https://arxiv.org/abs/2608.05446)。用于 BPE、Harness action policy 与 SFT+GRPO 结果。[arXiv 论文]

<a id="ref-wu2026"></a>
**[When History Lies: Evaluating and Improving Tool Use under Misleading Multi-Turn Histories]** Xiaoqing Wu, Xingyu Fan, Feifei Li, Wenhui Que，WeChat, Tencent Inc.，2026. [arXiv:2608.06057](https://arxiv.org/abs/2608.06057)。用于 history pollution、Oracle State 与可靠状态策略迁移。[arXiv 论文]

<a id="ref-nie2026"></a>
**[EvolveNet: Collaborative Harness Evolution for Agent Self-Improvement]** Jun Nie, Yonggang Zhang, Qianshu Cai, Yiu-ming Cheung, Xinmei Tian, Bo Han，Hong Kong Baptist University、University of Science and Technology of China、The Hong Kong University of Science and Technology，2026. [arXiv:2608.04968](https://arxiv.org/abs/2608.04968)。用于 scope-typed program delta、行为门与协同 Harness 演化。[arXiv 论文]

<a id="ref-wuzy2026"></a>
**[从 Spec 驱动转向环境与验证驱动：我对 AI Coding 的一点思考]** 吴佐衍，个人技术文章，2026. [微信公众号原文](https://mp.weixin.qq.com/s/EMUsGt6m1aNQ4T9yDtg7Jg)。用于环境与验证资产、workflow 职责及约束 / 假设边界。[个人实验 / 技术文章]
