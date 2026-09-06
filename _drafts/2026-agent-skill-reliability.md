# Agent Skill 的七道可靠性门
<!-- domain: claude-code-ecosystem -->
<!-- edition_date: 2026-08-16 -->

Agent Skill 常被理解成“按需加载的一段最佳实践”：检索找对文档，模型照着执行，成功轨迹再回写成新版 Skill。但实际生效过程要长得多。

`[论文]` 2026 年 8 月集中出现的几项工作分别暴露了这条链上的断点。相关 Skill 可能不值得执行；模型读懂了程序也可能跳步；层级委派会丢失原始授权；看似成功的轨迹可能把后门沉淀进下一版 Skill；即使任务最终通过，Skill 也可能带来巨大的验证和实现成本。

`[本文归纳]` 因此，Skill 是一段会生效的 policy：它改变计划、工具调用、检查项、停止条件和后续经验。可靠性问题需要沿着一条完整生效链逐层检查：

`nominate → admit → instantiate constraints → execute with authority → verify and diff → adopt or reject`

每一层消费不同的证据，也有不同的失败 owner。

<figure class="diagram">
<svg width="100%" viewBox="0 0 820 620" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="skill-gates-title skill-gates-desc">
<defs>
<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="#131922"/>
<stop offset="100%" stop-color="#1a2230"/>
</linearGradient>
<linearGradient id="node" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="#1b2532"/>
<stop offset="100%" stop-color="#141c27"/>
</linearGradient>
<linearGradient id="pseudo" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="#10151d"/>
<stop offset="100%" stop-color="#151b25"/>
</linearGradient>
<marker id="arrow-muted" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M1 1L9 5L1 9Z" fill="#2a3441"/>
</marker>
<marker id="arrow-dotted" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M1 1L9 5L1 9Z" fill="#8b97a4" opacity="0.58"/>
</marker>
<marker id="arrow-accent" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M1 1L9 5L1 9Z" fill="#5fd0c8"/>
</marker>
</defs>
<title id="skill-gates-title">Agent Skill 的七道可靠性门</title>
<desc id="skill-gates-desc">从候选提名到受控晋升的可靠性拓扑，包含失败模式、原始请求重锚和运行反馈闭环。</desc>
<rect width="820" height="620" fill="#0b1017"/>
<rect x="20" y="20" width="780" height="580" rx="24" fill="url(#panel)" stroke="#2a3441" stroke-width="1.05"/>
<text x="410" y="61" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="24" font-weight="700" text-anchor="middle">Agent Skill 的七道可靠性门</text>
<text x="410" y="88" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="13" text-anchor="middle">Skill 可见 → 当前执行放行，需要逐门留下可核验证据</text>
<rect x="95" y="116" width="146" height="44" rx="12" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<circle cx="112" cy="138" r="3.5" fill="#fbbf24"/>
<text x="170" y="143" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="13" text-anchor="middle">相关但无用</text>
<rect x="337" y="116" width="146" height="44" rx="12" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<circle cx="354" cy="138" r="3.5" fill="#fbbf24"/>
<text x="412" y="143" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="13" text-anchor="middle">读懂但跳步</text>
<rect x="579" y="116" width="146" height="44" rx="12" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<circle cx="596" cy="138" r="3.5" fill="#fbbf24"/>
<text x="654" y="143" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="13" text-anchor="middle">成功但带后门</text>
<rect x="38" y="228" width="114" height="82" rx="18" fill="url(#node)" stroke="#2a3441" stroke-width="1.05"/>
<text x="95" y="258" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" font-weight="650" text-anchor="middle">候选提名</text>
<text x="95" y="282" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="12.5" text-anchor="middle">Nominate</text>
<rect x="164" y="228" width="114" height="82" rx="18" fill="url(#node)" stroke="#2a3441" stroke-width="1.05"/>
<text x="221" y="258" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" font-weight="650" text-anchor="middle">执行准入</text>
<text x="221" y="282" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="12.5" text-anchor="middle">Admit</text>
<rect x="290" y="228" width="114" height="82" rx="18" fill="url(#node)" stroke="#2a3441" stroke-width="1.05"/>
<text x="347" y="258" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" font-weight="650" text-anchor="middle">约束实例化</text>
<text x="347" y="282" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="12.5" text-anchor="middle">Closure</text>
<rect x="416" y="228" width="114" height="82" rx="18" fill="url(#node)" stroke="#5fd0c8" stroke-width="1.25"/>
<text x="473" y="258" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" font-weight="650" text-anchor="middle">授权执行</text>
<text x="473" y="282" fill="#5fd0c8" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="12.5" text-anchor="middle">Execute</text>
<rect x="542" y="228" width="114" height="82" rx="18" fill="url(#node)" stroke="#2a3441" stroke-width="1.05"/>
<text x="599" y="258" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" font-weight="650" text-anchor="middle">配对核验</text>
<text x="599" y="282" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="12.5" text-anchor="middle">Verify / Diff</text>
<rect x="668" y="228" width="114" height="82" rx="18" fill="url(#node)" stroke="#2a3441" stroke-width="1.05"/>
<text x="725" y="258" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" font-weight="650" text-anchor="middle">受控晋升</text>
<text x="725" y="282" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="12.5" text-anchor="middle">Adopt / Reject</text>
<rect x="38" y="320" width="114" height="54" rx="11" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<text x="95" y="351" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">relevance</text>
<rect x="164" y="320" width="114" height="54" rx="11" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<text x="221" y="351" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">utility / risk</text>
<rect x="290" y="320" width="114" height="54" rx="11" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<text x="347" y="343" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">require graph +</text>
<text x="347" y="359" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">source span</text>
<rect x="416" y="320" width="114" height="54" rx="11" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<text x="473" y="343" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">original request +</text>
<text x="473" y="359" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">current state</text>
<rect x="542" y="320" width="114" height="54" rx="11" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<text x="599" y="343" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">paired trace +</text>
<text x="599" y="359" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">verifier</text>
<rect x="668" y="320" width="114" height="54" rx="11" fill="url(#pseudo)" stroke="#2a3441" stroke-width="1.05"/>
<text x="725" y="343" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">provenance +</text>
<text x="725" y="359" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5" text-anchor="middle">frozen replay</text>
<path d="M152 269H164" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrow-muted)"/>
<path d="M278 269H290" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrow-muted)"/>
<path d="M404 269H416" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrow-muted)"/>
<path d="M530 269H542" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrow-muted)"/>
<path d="M656 269H668" fill="none" stroke="#2a3441" stroke-width="1.05" marker-end="url(#arrow-muted)"/>
<path d="M168 160C174 184 204 194 218 226" fill="none" stroke="#8b97a4" stroke-width="1.2" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58" marker-end="url(#arrow-dotted)"/>
<path d="M410 160C401 184 366 195 351 226" fill="none" stroke="#8b97a4" stroke-width="1.2" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58" marker-end="url(#arrow-dotted)"/>
<path d="M652 160C645 184 615 195 601 226" fill="none" stroke="#8b97a4" stroke-width="1.2" stroke-dasharray="1 7" stroke-linecap="round" opacity="0.58" marker-end="url(#arrow-dotted)"/>
<path d="M656 269C662 269 662 278 662 288V382H221V374" fill="none" stroke="#5fd0c8" stroke-width="1.35" stroke-dasharray="7 5" opacity="0.78" marker-end="url(#arrow-accent)"/>
<rect x="377" y="370" width="210" height="23" rx="10" fill="#151c26" stroke="#2a3441" stroke-width="0.8"/>
<text x="482" y="386" fill="#5fd0c8" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="12.5" text-anchor="middle">运行证据更新 utility gate</text>
<path d="M782 269C790 269 790 279 790 290V526H347V374" fill="none" stroke="#5fd0c8" stroke-width="1.35" stroke-dasharray="7 5" opacity="0.78" marker-end="url(#arrow-accent)"/>
<rect x="447" y="514" width="228" height="23" rx="10" fill="#151c26" stroke="#2a3441" stroke-width="0.8"/>
<text x="561" y="530" fill="#5fd0c8" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="12.5" text-anchor="middle">只有门后版本进入下一轮</text>
<rect x="38" y="405" width="140" height="46" rx="12" fill="url(#pseudo)" stroke="#5fd0c8" stroke-width="1.05"/>
<circle cx="58" cy="428" r="4" fill="#5fd0c8"/>
<text x="109" y="433" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" font-weight="650" text-anchor="middle">原始请求</text>
<path d="M178 428H384C402 428 410 416 410 398V291C410 278 411 270 416 270" fill="none" stroke="#131922" stroke-width="5"/>
<path d="M178 428H384C402 428 410 416 410 398V291C410 278 411 270 416 270" fill="none" stroke="#5fd0c8" stroke-width="1.8" stroke-dasharray="7 5" marker-end="url(#arrow-accent)"/>
<rect x="205" y="410" width="166" height="23" rx="10" fill="#151c26" stroke="#2a3441" stroke-width="0.8"/>
<text x="288" y="426" fill="#5fd0c8" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" text-anchor="middle">每次副作用前重锚</text>
<text x="38" y="476" fill="#8b97a4" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="11.5">authority 由原始请求持有</text>
<rect x="38" y="555" width="744" height="32" rx="12" fill="#10151d" stroke="#2a3441" stroke-width="1.05"/>
<circle cx="63" cy="571" r="3.5" fill="#fbbf24"/>
<text x="410" y="576" fill="#e6edf3" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif" font-size="14" font-weight="600" text-anchor="middle">当前执行需要独立的放行证据。</text>
</svg>
<figcaption>主链表示 Skill 从候选到晋升的生效过程；虚线表示原始授权重锚与运行证据反馈。</figcaption>
</figure>

## 1. 检索只提名候选，执行还需要单独准入

`[论文]` [RADEG](#ref-he2026)（同济大学、悉尼大学等，He et al. 2026）检验了一个问题：检索器认为 Skill bundle 相关，是否意味着值得为它启动一次 Agent rollout？作者对 72 个 SkillsBench query 的原始 bundle 分别进行删除、增加和替换，得到 288 个 query-bundle 组合。22 个 query 至少在一种扰动下发生 reward 变化，说明 bundle 中只改一个成员，就可能让结果从零变成正值，或发生翻转。

`[论文]` RADEG 位于 retrieval 与 execution 之间，保持 retriever 和 Agent 不变，单独用既往 `(query, bundle, verifier reward)` 训练一个轻量 utility gate。在默认决策点跳过 **68%** 的 Agent 调用，同时保留 **61%** 的总 reward；当预算只允许执行 20% 的调用时，它保留 **40%** reward，优于 relevance gate 和随机 gate。实验规模仍小，每个组合只跑一次；它已经把两个问题分开了：相关性负责提名，执行价值负责花预算。

`[本文归纳]` 这道准入门要同时看预期成功率、调用成本、副作用等级、当前环境状态和 fallback。例如纯读搜索可以低门槛执行；会发消息、改配置或启动昂贵训练的 Skill，即使主题完全相关，也应该先取得更强证据。

## 2. 长 Skill 依从性依赖规则闭包，不依赖“多塞一点原文”

`[论文]` [SkillCDG](#ref-zhao2026)（美团，Zhao et al. 2026）讨论的是执行后的 compliance audit。长 Skill 往往同时包含流程、资格条件、例外、强制确认和额度限制。两个 Agent 可以给出同样的退款结果，一个完成了资格检查和确认，另一个直接越过前置步骤。只看终局动作，二者没有区别。

`[论文]` SkillCDG 把 Skill 分成两层图：上层按场景路由 Skill，下层把规则拆成原子 condition-action constraint，并用 `require` 边表示强制前置依赖。检索只找 seed rule；系统随后展开 dependency closure，把 eligibility、exception 和 mandatory check 一起带回 judge，同时保留每条规则到原始 span 的链接。在三个匿名企业数据集和两个公共 benchmark 变体上，论文报告 detection F1 相对 baseline 最高提高 **12.8** 个百分点，token 消耗最高降低 **64.3%**。

`[本文归纳]` 一个动作依赖多少分散约束、删掉哪条会改变结论，定义了 Skill 更有意义的复杂度。语义压缩可以删除重复解释；强制依赖仍需完整保留。对高风险 Skill，编写格式应该让 prerequisite、exception、source span 和 completion condition 能被机器检查。

## 3. Procedure 进入上下文之后，还有执行稳定性

`[论文]` [SkillSentry](#ref-lu2026)（论文首页未给出完整校名，Lu et al. 2026）把问题从文档审计推进到运行时。模型曾经在 Skill 指导下完成任务，只能证明它有基本能力，不能证明下一次会遵守同样步骤。相似 query 的微小改写、中间工具反馈的差异，都可能让 Agent 跳过频率对齐、用错参数或过早结束。

`[论文]` SkillSentry 从 Skill 文档抽取步骤、依赖、约束和完成条件，再从成功与失败轨迹提炼 action pattern、suggestion 和 warning，写成一套 DSL runtime guidance。它通过 hook 包住 Agent loop：到达某一步时只下发该步需要的提示；发现已知失败模式时要求 re-plan；模型准备结束时检查必做步骤是否完成。在 15 个 Skill、Claude Code 与 Codex、四个 backbone 的实验中，平均 task success 提高 **24.1%**，重复运行 success-rate 的标准差降低 **41.1%**。step-level guidance 相比把全部 guidance 塞进 system prompt，再提高 **5.8%** 成功率并降低 **26.8%** 标准差。

`[本文归纳]` Skill 因而有三个不同的介入时机：加载前决定是否启用；执行中根据 current step 给局部约束；终止前按 completion condition 验收。一次性把所有内容放进 prompt，既增加干扰，又无法把一条 warning 绑定到它真正生效的动作窗口。

## 4. 授权必须回到原始请求

`[论文]` [MasDrift](#ref-xu2026)（纽约大学、纽约大学阿布扎比分校、香港理工大学、清华大学，Xu et al. 2026）用 600 个 benign productivity task 测量多 Agent 协作中的授权漂移。每个任务同时给出 required work 与 reserved action，例如可以整理材料，但不能发送；可以草拟变更，但不能提交。中心化层级的完成率达到 **93.9–98.6%**，高于 peer network 的 **85.7–87.0%**；与此同时，中心化结构的未授权动作达到 **2.7–19.8%**，peer network 只有 **0.6–0.8%**。

`[论文]` 作者比较了两种防御。一种让每个 pending call 回到原始用户请求，重新判断当前动作是否获授权；另一种沿 delegation chain 逐级携带衰减后的 policy。source re-anchoring 在所有模型配置中都降低未授权动作，pooled completion 只损失 1.6 点。链式传播主要通过阻断合法工作降低风险，最多损失 **36.3** 点完成率。

`[本文归纳]` Skill 告诉 subagent “怎样做”，原始请求、后续用户更正和 current environment 决定“可以做到哪一步”。Skill、上游 agent 总结和 handoff policy 都是辅助证据。尤其在发消息、发布、删除、支付、开权限等不可逆动作前，系统需要重新绑定原始授权，避免让已经传了几跳的自然语言摘要独立放行。

## 5. 工业自治放在少量决策点

`[论文]` [RecSys Factory](#ref-ao2026)（腾讯 FiT，Ao et al. 2026）把工业 Agent 的矛盾概括为自治、确定性与效率三者的张力。平台运行 78 天，覆盖三条推荐业务线，共记录 1,624 次 CLI dispatch。聚合成功率为 **78.6%**；把 WAITING 视为正确状态信号时约为 **83.7%**。整个 wall time 中 **94%** 在等待 Spark 或 GPU 作业，因此真正需要模型判断的时间远少于 pipeline 的总持续时间。

`[论文]` 这套系统把自治限制在 typed decision point。29 个 Skill 共 8,971 行，每个 Skill 的 pitfall table 机械编译成 400 项 PitfallStore；host event 负责唤醒，预提交 pipeline 负责确定性执行，诊断与执行之间保留 human-in-the-loop card。作者同时明确：onboarding 压缩缺少受控 baseline，HITL 数据也只有 8 天 16-run pilot，属于案例观察，外推范围有限。

`[本文归纳]` Skill 在确定性骨架上只暴露少量需要语义判断的表面。schema 转换、幂等写入、等待和 readback 交给代码；模型处理根因判断、候选选择与异常解释。自治边界本身应当成为每个 Skill 的显式字段。

## 6. 判断 Skill 是否有害，需要同任务的配对运行

`[论文]` [Agent Skills Can Be Harmful](#ref-dong2026)（华中科技大学、Microsoft Research、Microsoft、UIUC，Dong et al. 2026）把 failed run 当作待归因对象。一个任务失败，成因可能在于 base Agent 能力、环境、verifier 范围或采样随机性。作者为同一个任务寻找 no-skill 或 semantically matched Skill 的成功运行；对效率问题，则寻找结果相同但成本更低的 reference run，再比较 Skill 内容、轨迹、artifact、verifier、token 与时间。

`[论文]` 这套 differential framework 确认了 307 个 skill-induced failure：125 个功能失败、182 个效率回退。功能失败中，task-implementation fault 占 **86/125（68.8%）**。效率回退中，excessive procedure 占 **114/182（62.6%）**；其中 excessive verification 67 个，heavy implementation pipeline 30 个。危险 Skill 往往并非明显不相关，反而是“看起来很对”的 checklist 和 recipe 被模型当成无条件必做项。

`[本文归纳]` 这为 Skill 评测提供了比 aggregate pass rate 更细的最小单位：`same task + candidate Skill run + reference run + trace diff`。它既看功能，也看成本、授权与副作用。候选版相对旧版的变化被定位之后，Skill owner 才能判断该修文档、runtime、tool wrapper、verifier，或停止启用该 Skill。

## 7. 自演化把攻击入口移到了 experience

`[论文]` [Query-Only Backdoor Attacks](#ref-luo2026)（Emory University，Luo et al. 2026）研究一种不需要直接访问 Skill 的攻击。攻击者只提交经过构造的 query，让 Agent 在轨迹中执行目标动作，并明确表达对应触发条件；相同 condition-action pattern 在多个不同任务中重复出现后，可信 evolver 会把它总结成可复用的 trigger-dependent rule。

`[论文]` Trajectory Backdoor Attack 在三个 benchmark、两个 skill-evolution system 和四个开源/闭源 backbone 上都能植入条件后门，同时保持 clean-task utility，并可达到或超过直接 Skill injection。风险来自 evolver 把“内部真实执行过”直接当成“可信、普遍、值得沉淀”。

`[本文归纳]` Skill 演化需要单独的 adoption gate。轨迹记录发生过什么，它的规范资格仍待审核。进入下一版 Skill 前，应保留 query 来源、执行环境、触发频率、对照任务、授权状态和 verifier receipt；候选规则还要经过冻结回归集、对抗触发检查和人工 scope review。缺少这道门，系统越擅长总结经验，越可能把稳定重复的攻击模式学得更牢。

## 8. 六个旋钮，把 Skill 可靠性变成可设计对象

`[本文归纳]` 七篇工作分别定位了可靠性链上的独立失效面。可以用六个旋钮描述这片设计空间：

| 旋钮 | 弱合同 | 强合同 |
|---|---|---|
| activation gate | 检索到就加载 | relevance 只提名，utility / risk 决定执行 |
| constraint closure | 相似片段或长 prompt | 原子规则、强制依赖、source span |
| intervention timing | 一次性注入 | 加载前、step-level、termination 三段介入 |
| authority anchor | 相信 Skill 或上游摘要 | 每个副作用动作重锚原始请求与 current state |
| comparison unit | 单跑 success / cost | 同任务 paired trace diff |
| adoption gate | 成功轨迹直接总结 | provenance、冻结回归、对抗检查、受控晋升 |

`[本文归纳]` 这六轴允许按风险调节门的重量。低成本、能回滚的纯读任务可以合并步骤；高成本或高副作用任务需要更强合同。哪个步骤可以跳过、哪条授权不可继承、哪种结果能改写下一版，都应当写成系统状态，并配套观测、测试与回滚入口。

`[本文归纳]` 可靠的 Skill 系统是一条能区分候选、权威和证据的晋升链。Skill 提供可复用策略；runtime 决定何时以及如何让它生效；原始请求限定权限；verifier 与配对运行判断增量；adoption gate 决定经验是否有资格进入下一版。这些 owner 分开后，Skill 才能从“偶尔有帮助的上下文”变成可维护的 Agent 能力。

## Reference

<a id="ref-he2026"></a>
**[From Relevance to Execution Utility: Reward-Aware Dynamic Execution Gating for Skill-Based LLM Agents]** Liang He, Jingbo Wen, Hongyu Gu, Hao Li, Haoyu Wang, Yixiong Chen, Kangning Cui, Xilu Wang；Tongji University、The University of Sydney、University of Science and Technology of China、Nankai University、Johns Hopkins University、City University of Hong Kong、University of Surrey；2026. [arXiv:2608.09168](https://arxiv.org/abs/2608.09168)。用于 relevance–utility gap、配对 bundle 扰动与 execution gate 结果。[arXiv 论文]

<a id="ref-zhao2026"></a>
**[Long SKILL Compliance as Logical Reasoning: Closure-Grounded Detection with Scaling-Guided On-Policy Distillation]** Shuaitao Zhao, Feng Ni, Lichao Ma, Jiaye Lin, Fei Han, Yang Wei, Lu Pan；Meituan；2026. [arXiv:2608.08146](https://arxiv.org/abs/2608.08146)。用于原子约束、dependency closure、source span 与长 Skill audit。[arXiv 论文]

<a id="ref-lu2026"></a>
**[SkillSentry: Reliable Skill Execution for LLM Agents via Runtime Assurance]** You Lu, Xinyu Huang, Bihuan Chen, Xin Peng；论文首页仅标 `College of Computer Science and Artificial Intelligence, China`，完整校名未给出；2026. [arXiv:2608.09253](https://arxiv.org/abs/2608.09253)。用于 step-aware runtime guidance、重复运行稳定性与终止检查。[arXiv 论文]

<a id="ref-xu2026"></a>
**[MasDrift: Benchmarking Authorization Preservation Across Multi-Agent Architectures]** Zhuoning Xu, Xiucheng Zhang, Hanjun Luo, Yingbin Jin, Yinpeng Dong, Hanan Salam；New York University、NYU Abu Dhabi、The Hong Kong Polytechnic University、Tsinghua University；2026. [arXiv:2608.07556](https://arxiv.org/abs/2608.07556)。用于多 Agent 授权漂移、source re-anchoring 与 chain propagation 对照。[arXiv preprint]

<a id="ref-ao2026"></a>
**[RecSys Factory: Bounding LLM Agent Autonomy to Decision Points in the Industrial Recommender Lifecycle]** Dongyang Ao, Kaixiang Fang, Shijie Xu；FiT, Tencent, Shenzhen；2026. [arXiv:2608.11241](https://arxiv.org/abs/2608.11241)。用于工业 Skill 生态、decision-point autonomy、host event 与 HITL 边界。[arXiv 工业 case study]

<a id="ref-dong2026"></a>
**[Agent Skills Can Be Harmful: An Empirical Study of Skill-Induced Failures in LLM Agents]** Gen Dong, Yanjie Gao, Liqun Li, Tianyin Xu, Yu Hua, Fan Yang；Huazhong University of Science and Technology、Microsoft Research、Microsoft、University of Illinois Urbana-Champaign；2026. [arXiv:2608.11888](https://arxiv.org/abs/2608.11888)。用于 paired differential attribution、功能失败与效率回退 taxonomy。[arXiv 论文]

<a id="ref-luo2026"></a>
**[Query-Only Backdoor Attacks on Self-Evolving Skills via Trajectory Poisoning]** Yuyang Luo, Haoran Wang, Kai Shu；Emory University；2026. [arXiv:2608.08303](https://arxiv.org/abs/2608.08303)。用于 query-only trajectory poisoning、自演化 Skill 的 experience supply-chain 风险。[arXiv 论文]
