# Agent 执行经验：复用粒度与部署条件
<!-- domain: agentic-rl -->
<!-- edition_date: 2026-09-06 -->

一个 Agent 刚把难题做成，最自然的动作是“总结成 Skill，下次复用”。这句话听起来是一个动作，拆开却是三个问题：这次成功究竟归功于计划、执行，还是现场状态；应该留下整条轨迹、可换参数的操作，还是更抽象的程序；这份总结又凭什么有资格影响下一次运行。

不拆开处理，经验库多半滑向两个极端。一个总纲越写越像“先理解需求、谨慎调用工具、完成后验证”；逐任务保存则会留下大量路径、ID、页面位置和当时的偶然决策。前者没有可执行结构，后者离开原任务就失效。

`[本文归纳]` 真正需要复用的并不是“更多记忆”，而是任务之间仍然成立的那一层程序。它有时是一模一样的动作，有时只是可替换参数的模板；只有一组任务共享解题骨架、而现场绑定会变化时，程序族才是合适的中间层。全新任务则不该被旧经验强行解释。

## 任务关系决定复用粒度

经验写回的第一个决策不是存储格式，而是当前任务与历史任务的关系。关系不同，值得留下的单位就不同：

| 当前任务与历史任务的关系 | 值得留下的单位 | 当前任务怎么用 | 不应保留什么 |
|---|---|---|---|
| 同一个请求再次出现 | 已验证的执行结果或精确 replay | 先校验前置状态，再直接复用 | 无意义的重复推理 |
| 结构相同，输入参数变化 | 参数化操作 / deterministic template | 替换显式变量后执行 | 原实例的 ID、时间和对象绑定 |
| 任务相关，共享解题骨架 | 程序族 prior | 用 prior 规划，再生成本地 detail | 把局部绑定冒充通用步骤 |
| 没有已证实的共同结构 | 原始证据与失败边界 | 重新规划，事后再判断能否归类 | 为了命中旧 Skill 而强行套用 |

这四档不是分类学练习：来源中能找到对应的实现或边界，但它们没有在同一个 benchmark 上被统一比较。

中间一档——任务不相同，但共享一段稳定的解题骨架——最直接的对照来自 `[论文]` [SkillGLoW](#ref-yan2026)（NUS，Yan et al. 2026）。它把两个常见极端放进同一条异构长程任务流：单一 global document 逐渐收敛成通用纪律，flat per-task pool 不断膨胀，条目仍绑定生成它的 instance。SkillGLoW 把 related tasks 按 shared solving procedure 聚成 family，将局部 Skill 去实例化成 prior，再为当前任务重新生成路径、对象和参数等局部细节。四个 benchmark、三个模型的 12 个 continual run 全部取得正增益，hard score 相对 no-skill 平均提升 17.2，library 比 per-task pool 小 3.6 倍，未见过的 ALFWorld 任务从 73.9% 提升到 83.9%。但作者也明确限制了结论：实验复用的是反复出现的 task category，不是真实 domain change；跨模型继承尚未验证，多数主表单元格还是 provider-default 的单次运行。

其中三类关系被 `[论文]` [TRIAGE](#ref-wei2026)（China Telecom Cloud，Wei 2026）做成了明确路由：相同请求走 Direct Reuse；结构相同但参数变化时走 deterministic Skill Substitution；新请求才完整运行 ReAct，并从高频轨迹中继续抽取参数化 Skill。1,007 条安全监控查询报告 token 减少 62.3%，ToolBench 的 15 个 domain、345 条查询报告平均减少 76.3%。这组结果适合证明“分级路由能工作”，却不适合外推一般工作负载的命中率：主数据本来就由 15 个 SQL 模板和重复日报查询构成，论文也说明它不是为严格统计结论设计的数据集。

程序甚至不必永远以文本库的形态留在部署环境。`[论文]` [SPACE](#ref-yang2026)（Rutgers、Toronto、HK PolyU、Amazon、Microsoft，Yang et al. 2026）从成功轨迹中诱导 composite skill 和 subskill，用它们的边界监督 Agent 何时一次输出一组 primitive actions；训练完成后，policy 直接生成 action chunk，部署时不再读取 Skill library。ALFWorld 和 ScienceWorld 上，成功率相对各自 strongest baseline 提升 7.0%–31.3%，LLM decision rounds 最多减少 78.9%。这里得到验证的是程序层级作为训练期边界，而不是“所有程序都应该进入一份长期文本记忆”。

`[论文]` [APEx](#ref-ding2026)（USTC、ByteDance、CAS，Ding et al. 2026）保留了另一种双层结构：instance-level trajectory memory 提供具体经历，category-level procedural skill 为 Planner 的在线适配提供 prior。七个 benchmark 的平均结果比论文中最强 memory baseline 高 3.0 points；移除 Distiller、Planner、Executor 的 GRPO，分别下降 2.3、1.8、8.4 points。它的 backbone 较小，在线 reward 依赖多个 LLM judge，三阶段顺序训练也没有与 joint training 完整比较——这些限制意味着，双层经验是可行结构，而不是已经确定的唯一结构。

`[本文归纳]` 把这些证据放回表里，结论恰好是中间层的条件性：“程序族”不是一种普遍优于 Skill 文件或轨迹库的新格式，它只回答一种特定关系——任务不相同，但共享一段稳定的解题骨架。关系更近，复用单位应该更具体；关系更远，就该只留证据、重新规划。

## 经验写回前的责任归因

选对了抽象层级，还只解决了一半问题。同一条失败轨迹里，计划可能是对的，工具执行却错了；也可能执行完全忠实，只是计划本身遗漏了约束。直接把终局 outcome 总结进同一个库，会让错误修复写到错误的位置。

`[论文]` [CHIME](#ref-ye2026)（Xiamen University、Zhejiang University、Alibaba，Ye et al. 2026）把 plan memory 与 execution memory 分开：先把结果归因到 plan、execution、both 或 neither，再只更新对应 bank。四个 benchmark、两个 backbone 上，eval average 比最强 baseline 高 2.96% 和 3.68%；合并两库的 ablation 平均下降 3.60%，去掉 attribution gate 下降 2.44%。不过归因和 memory quality 都包含 LLM 判断，sequential stream 也只用三种顺序测试。它支持的是“先归因、再记忆”，不是 plan / execution 必然构成所有系统的唯一分法。

`[论文]` [Recuris](#ref-yu2026)（NUS、Princeton、Stanford、Oxford，Yu et al. 2026）把 owner 再向前推进了一步：Working Memory 只提交经过工具结果支持的当前进展，再据此选择 Experiential Memory；执行 trace 将失败归到具体 memory component，固定 Meta-Agent 只修改被归因的部分，候选还要通过 source task 和 held-out development set。37 个完成的 model-benchmark pair 中有 35 个提升；作为对照，完整 Skill library 常驻 prompt 多用 3,111 token、少 18 个得分点，每次成功成本高 46%。但它为每个 benchmark 单建 memory，并由一个 deployment model 的失败塑形，仍不能证明同一 memory 能跨真实 domain 或跨任意模型继承。

`[本文归纳]` 所以 owner 不只是“哪一个文件”。它可以是当前 working state、planning、execution、retrieval，也可以是训练 policy。先找到发生变化的环节，才能判断一次经历该修改哪个消费面；否则，成功会把偶然路径固化，失败会把正确计划污染。

## 经验的归因、收敛与部署验证

`[本文归纳]` 把七项工作放在一起，经验写回可以拆成三道相互独立的门：

1. **归因门**：这次结果属于哪个 owner 或 stage？没有归因，先保留 trace，不改长期策略。
2. **收敛门**：跨任务仍然成立的变量是什么？保留 instance、抽参数、归成程序族，还是只留下反例边界。
3. **生效门**：候选在真实执行中是否带来收益，并且没有破坏已部署能力？内容看起来正确，不等于已经值得部署。

<figure class="diagram">
<svg width="100%" viewBox="0 0 920 520" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="psc-title psc-desc">
<title id="psc-title">从执行证据到可部署经验的三道门</title>
<desc id="psc-desc">执行证据先经过归因，再按任务关系选择精确复用、参数化、程序族或重新规划，最后经过真实执行验收后才进入部署。</desc>
<defs>
<linearGradient id="psc-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#101722"/><stop offset="100%" stop-color="#182334"/></linearGradient>
<linearGradient id="psc-node" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#213149"/><stop offset="100%" stop-color="#172337"/></linearGradient>
<marker id="psc-arrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1L9 5L1 9Z" fill="#8da2bd"/></marker>
</defs>
<rect x="8" y="8" width="904" height="504" rx="24" fill="url(#psc-bg)" stroke="#33445c"/>
<text x="46" y="48" fill="#8fa3bc" font-size="14" font-family="system-ui,sans-serif" letter-spacing="1.5">EXECUTION → ATTRIBUTION → CONSOLIDATION → ADOPTION</text>
<rect x="42" y="82" width="170" height="104" rx="16" fill="url(#psc-node)" stroke="#526985"/>
<text x="127" y="117" fill="#f1f5f9" font-size="18" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">执行证据</text>
<text x="127" y="147" fill="#b9c7d8" font-size="14" text-anchor="middle" font-family="system-ui,sans-serif">状态 · 轨迹 · 结果</text>
<path d="M212 134H270" stroke="#8da2bd" stroke-width="2" marker-end="url(#psc-arrow)"/>
<rect x="274" y="82" width="170" height="104" rx="16" fill="url(#psc-node)" stroke="#6b8cb7"/>
<text x="359" y="117" fill="#f1f5f9" font-size="18" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">归因门</text>
<text x="359" y="146" fill="#b9c7d8" font-size="14" text-anchor="middle" font-family="system-ui,sans-serif">哪个 owner / stage</text>
<text x="359" y="168" fill="#7dd3fc" font-size="12" text-anchor="middle" font-family="system-ui,sans-serif">归不清：只留证据</text>
<path d="M444 134H502" stroke="#8da2bd" stroke-width="2" marker-end="url(#psc-arrow)"/>
<rect x="506" y="82" width="170" height="104" rx="16" fill="url(#psc-node)" stroke="#8c78c8"/>
<text x="591" y="117" fill="#f1f5f9" font-size="18" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">收敛门</text>
<text x="591" y="146" fill="#b9c7d8" font-size="14" text-anchor="middle" font-family="system-ui,sans-serif">两个任务共享什么</text>
<text x="591" y="168" fill="#c4b5fd" font-size="12" text-anchor="middle" font-family="system-ui,sans-serif">抽象粒度随关系变化</text>
<path d="M676 134H734" stroke="#8da2bd" stroke-width="2" marker-end="url(#psc-arrow)"/>
<rect x="738" y="82" width="140" height="104" rx="16" fill="url(#psc-node)" stroke="#5b9b7c"/>
<text x="808" y="117" fill="#f1f5f9" font-size="18" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">生效门</text>
<text x="808" y="146" fill="#b9c7d8" font-size="14" text-anchor="middle" font-family="system-ui,sans-serif">真实执行验收</text>
<text x="808" y="168" fill="#86efac" font-size="12" text-anchor="middle" font-family="system-ui,sans-serif">通过才进入部署</text>
<path d="M591 186V230" stroke="#8da2bd" stroke-width="2" marker-end="url(#psc-arrow)"/>
<rect x="42" y="248" width="190" height="92" rx="14" fill="#162235" stroke="#526985"/>
<text x="137" y="281" fill="#f1f5f9" font-size="16" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">完全相同</text>
<text x="137" y="310" fill="#b9c7d8" font-size="14" text-anchor="middle" font-family="system-ui,sans-serif">校验状态 → replay</text>
<rect x="258" y="248" width="190" height="92" rx="14" fill="#162235" stroke="#526985"/>
<text x="353" y="281" fill="#f1f5f9" font-size="16" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">结构相同</text>
<text x="353" y="310" fill="#b9c7d8" font-size="14" text-anchor="middle" font-family="system-ui,sans-serif">替换变量 → template</text>
<rect x="474" y="248" width="190" height="92" rx="14" fill="#162235" stroke="#8c78c8"/>
<text x="569" y="281" fill="#f1f5f9" font-size="16" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">共享解题骨架</text>
<text x="569" y="310" fill="#b9c7d8" font-size="14" text-anchor="middle" font-family="system-ui,sans-serif">prior → 局部再生成</text>
<rect x="690" y="248" width="190" height="92" rx="14" fill="#162235" stroke="#526985"/>
<text x="785" y="281" fill="#f1f5f9" font-size="16" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">没有共同结构</text>
<text x="785" y="310" fill="#b9c7d8" font-size="14" text-anchor="middle" font-family="system-ui,sans-serif">重新规划 → 暂不晋升</text>
<path d="M591 230C591 218 137 218 137 248M591 230C591 218 353 218 353 248M591 230V248M591 230C591 218 785 218 785 248" fill="none" stroke="#5d718a" stroke-width="1.5"/>
<path d="M137 340V388H808V186" fill="none" stroke="#5d718a" stroke-width="1.5" stroke-dasharray="5 6" marker-end="url(#psc-arrow)"/>
<path d="M353 340V388M569 340V388M785 340V388" fill="none" stroke="#5d718a" stroke-width="1.5" stroke-dasharray="5 6"/>
<rect x="245" y="418" width="430" height="58" rx="14" fill="#12261f" stroke="#4e8b6e"/>
<text x="460" y="453" fill="#d1fae5" font-size="17" text-anchor="middle" font-family="system-ui,sans-serif" font-weight="700">已部署经验：带适用范围、变量和回归证据</text>
<path d="M808 186V406C808 412 802 421 675 447" fill="none" stroke="#6fac8d" stroke-width="2" marker-end="url(#psc-arrow)"/>
</svg>
<figcaption>同一份执行材料，要先确定改谁，再决定抽象层级；进入部署是另一道需要真实执行证据的门。</figcaption>
</figure>

候选生成和部署验收也可以发生在不同时间。`[论文]` [PILOT](#ref-allspark2026)（AllSpark Team 2026）让 supervisor 在 worker 运行中提炼 procedure、project convention 和 failure mode，并同时做 live steering；候选在 verifier outcome 出现前形成，只有成功 run 的更新才跨 iteration 保留。在两个 frozen backbone、三个 benchmark 的六组设置里，它五组排名第一，Terminal-Bench 自改进设置报告 +14.6 和 +12.4 个百分点。由于 steering 与经验写回同时变化，而且保留 gate 看的是整次 run 成败，这些端到端提升不能拆成每条 procedure 的独立因果贡献。

`[本文归纳]` 这一区分很重要：运行中可以快速形成候选，但候选不应因为“看起来像经验”就获得长期影响力。SkillGLoW 用真实 execution 检查候选 prior 不降低已部署 library 后才 commit；Recuris 用 source task 和 held-out development set 验证组件级 patch。三种实现都在提示同一条工程边界：提炼发生得早，不代表采纳也必须早。

## 执行经验的记录要求

一套已经在工作的 Skill / memory 系统，不必立刻换成新的层级数据库。更小、也更能被验证的改动，是给每次写回补齐四个字段：

- **owner**：它要改变 working state、planning、execution、retrieval，还是训练 policy；
- **relation**：它预期服务 identical、parameterized、related-family，还是只作为 novel-case evidence；
- **variables**：哪些细节必须由当前任务重新绑定，哪些步骤在任务间保持不变；
- **adoption evidence**：在哪些真实执行和回归集上验证过，失败时如何撤回。

`[本文归纳]` 这四个字段的价值不在于 schema 本身，而在于它们阻止三种越权：把一次成功冒充稳定规律，把某个实例的路径冒充参数，把“总结完成”冒充“已经生效”。只有 related tasks 持续共享解题骨架，而且局部变量能够明确再绑定时，才值得把多条记录进一步收敛为程序族。

下一次 Agent 做完任务，问题不该是“要不要把这段对话写进 Skill”。更准确的问法是：**哪些步骤在下一类任务里仍然成立，哪些变量必须重新获得，哪个 owner 应该改变，以及什么执行证据允许这项改变进入部署。** 如果其中任何一项答不出来，最诚实的产物仍然是一条带来源的候选，而不是一条已经获得权力的经验。

## Reference

<a id="ref-yu2026"></a>
- **Recursive Experiential-Working Memory Evolution for Long-Horizon Agent Harnesses**. Zhaochen Yu, Yingcheng Wu, Zhenfei Yin, Kaiyuan Chen, Zhe Zhao, Mengdi Wang, Shuicheng Yan, Ling Yang. National University of Singapore, Princeton University, Stanford University, University of Oxford, 2026. [arXiv:2608.24876](https://arxiv.org/abs/2608.24876).

<a id="ref-allspark2026"></a>
- **PILOT in the Loop: Live Self-Improvement for Long-Horizon Agents**. AllSpark Team, 2026. [arXiv:2608.26530](https://arxiv.org/abs/2608.26530).

<a id="ref-wei2026"></a>
- **TRIAGE: Three-level Routing and Intelligent Agent Guidance for Efficient Execution**. Ruocan Wei. China Telecom Cloud, 2026. [arXiv:2609.01428](https://arxiv.org/abs/2609.01428).

<a id="ref-yang2026"></a>
- **Act More, Decide Less: Skill-Guided Adaptive Action Chunking for Long-Horizon LLM Agents**. Yanting Yang, Can Jin, Jinman Zhao, Jiahao Wu, Yang Zhou, Zhepeng Wang, Zhendong Wang, Mu Zhou, Dimitris N. Metaxas. Rutgers University, University of Toronto, The Hong Kong Polytechnic University, Amazon, Microsoft, 2026. [arXiv:2609.02042](https://arxiv.org/abs/2609.02042).

<a id="ref-ye2026"></a>
- **CHIME: Credit-Aware Hierarchical Memory Evolution for Long-Horizon Agentic Planning**. Yongshi Ye et al. Xiamen University, Zhejiang University, Alibaba Group, 2026. [arXiv:2609.02074](https://arxiv.org/abs/2609.02074).

<a id="ref-yan2026"></a>
- **SkillGLoW: Procedural-Family Skill Consolidation for Self-Improving Agents on Long-Horizon Task Streams**. Ao Yan, Xin Zhang, Jiawei Du, Joey Tianyi Zhou. National University of Singapore, 2026. [arXiv:2609.02217](https://arxiv.org/abs/2609.02217).

<a id="ref-ding2026"></a>
- **APEx: Distillation of Agent Procedural Experience for Adaptive Deep Research Question Answering**. Jie Ding, Rui Sun, Xinyuan Zhang, Zeyu Zhang, Xin Liu. University of Science and Technology of China, ByteDance Inc., Chinese Academy of Sciences, 2026. [arXiv:2609.02253](https://arxiv.org/abs/2609.02253).
