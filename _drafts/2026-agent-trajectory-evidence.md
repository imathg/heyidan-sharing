# Agent RL 的轨迹证据：环境如何把执行过程变成训练信号
<!-- domain: agentic-rl -->
<!-- edition_date: 2026-08-02 -->

`[本文归纳]` 一个漏洞检测 Agent 猜对了 vulnerable / safe，却没有调查相关代码；另一个 Agent 完成了任务，却走了大量无用步骤。如果训练数据只留下最终答案和成功标签，这些轨迹很难与真正可靠的执行区分。要从过程中学习，环境必须额外记录动作改变了什么、结论引用了哪个对象，以及过程质量如何。

下文对照任务合成、游戏求解、漏洞检测、环境交互和过程评测中的证据设计，说明这些记录怎样进入任务入池、SFT、RL、辅助训练与轨迹筛选。失败恢复轨迹和场景覆盖也在讨论范围内，但不与证据质量混成一个指标。

其中一个基础区别是：SFT 可以使用固定示范，on-policy RL 则需要能由当前策略重新执行的任务环境。两者需要保存的训练对象不同。

> **核心论点：终局奖励只保留整条轨迹的成败。Agent 要从执行过程学习，环境还需为每次动作留下可核验、可寻址、能与具体 turn 绑定的证据。tests、solver value、稳定对象 ID、next observation、process rubric 与 execution log 都是这类证据的不同载体。**

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<figure class="diagram"><svg width="100%" viewBox="0 0 820 620" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="trajectory-evidence-title trajectory-evidence-desc"><title id="trajectory-evidence-title">Agent RL 的轨迹证据拓扑</title><desc id="trajectory-evidence-desc">可执行任务闭包中的动作产生四类轨迹证据，证据进入训练的五个位置；环境 schema 限定 verifier 可以核验的对象。</desc><defs><linearGradient id="panelGrad" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#131922"/><stop offset="1" stop-color="#1a2230"/></linearGradient><linearGradient id="nodeGrad" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#1a2230"/><stop offset="1" stop-color="#131922"/></linearGradient><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#8b97a4"/></marker><marker id="accentArrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#5fd0c8"/></marker></defs><rect width="820" height="620" rx="22" fill="#131922"/><text x="32" y="46" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="24" font-weight="700">执行轨迹如何成为训练信号</text><text x="32" y="72" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="13">从可执行闭包，到可寻址证据，再到训练介入点</text><path d="M238 308 H256" stroke="#8b97a4" stroke-width="1.5" marker-end="url(#arrow)"/><path d="M548 308 H572" stroke="#8b97a4" stroke-width="1.5" marker-end="url(#arrow)"/><rect x="28" y="100" width="210" height="420" rx="18" fill="url(#panelGrad)" stroke="#2a3441"/><text x="48" y="132" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="700">可执行任务闭包</text><text x="48" y="153" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="12.5">task / action / state / verifier</text><rect x="48" y="180" width="170" height="56" rx="11" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="64" y="204" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">task</text><text x="64" y="224" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">任务输入与目标</text><rect x="48" y="250" width="170" height="56" rx="11" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="64" y="274" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">action</text><text x="64" y="294" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">允许的执行操作</text><rect x="48" y="320" width="170" height="56" rx="11" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="64" y="344" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">state</text><text x="64" y="364" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">动作后的环境状态</text><rect x="48" y="390" width="170" height="92" rx="11" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="64" y="416" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">verifier</text><text x="64" y="437" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">判断成功的规则</text><text x="64" y="457" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">与可核验对象</text><rect x="258" y="100" width="290" height="420" rx="18" fill="url(#panelGrad)" stroke="#2a3441"/><text x="278" y="132" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="700">每次动作留下的轨迹证据</text><text x="278" y="153" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="12.5">与动作前后状态绑定并可回查</text><rect x="278" y="177" width="250" height="66" rx="11" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="294" y="202" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">solver value delta</text><text x="294" y="224" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">动作带来的状态价值变化</text><rect x="278" y="257" width="250" height="66" rx="11" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="294" y="282" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">stable object ID</text><text x="294" y="304" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">稳定、可寻址的环境对象</text><rect x="278" y="337" width="250" height="66" rx="11" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="294" y="362" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">next observation</text><text x="294" y="384" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">动作实际造成的后果</text><rect x="278" y="417" width="250" height="66" rx="11" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="294" y="442" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">rubric + audit</text><text x="294" y="464" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">过程质量与确定性审计</text><rect x="572" y="100" width="220" height="420" rx="18" fill="url(#panelGrad)" stroke="#2a3441"/><text x="592" y="132" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="700">证据进入训练的位置</text><text x="592" y="153" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="12.5">从入池到训练后筛选</text><rect x="592" y="174" width="180" height="50" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="608" y="204" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">admission</text><rect x="592" y="238" width="180" height="50" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="608" y="268" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">SFT</text><rect x="592" y="302" width="180" height="50" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="608" y="332" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">RL reward</text><rect x="592" y="366" width="180" height="50" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="608" y="396" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">auxiliary objective</text><rect x="592" y="430" width="180" height="50" rx="10" fill="url(#nodeGrad)" stroke="#2a3441"/><text x="608" y="460" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">filtering</text><rect x="52" y="548" width="716" height="44" rx="12" fill="none" stroke="#5fd0c8" stroke-width="1.5" stroke-dasharray="7 5"/><text x="72" y="575" fill="#5fd0c8" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">环境 schema</text><path d="M177 570 H366" stroke="#5fd0c8" stroke-width="1.5" stroke-dasharray="7 5" marker-end="url(#accentArrow)"/><text x="248" y="560" fill="#8b97a4" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="11.5">限定</text><text x="390" y="575" fill="#e6edf3" font-family="-apple-system, PingFang SC, Microsoft YaHei, sans-serif" font-size="14" font-weight="600">verifier 可核验的对象</text></svg></figure>

## 终局成败抹掉了哪些信息

`[本文归纳]` 终局标签从一条长程轨迹中只保留成败，任务有效性、动作贡献和过程可复现性随之消失。任务证据用于区分自洽的任务与存在漏洞的检查器；动作后果证据标出哪些动作推动了状态，哪些动作只消耗步数；过程质量证据区分可复现的调查与偶然成功（lucky pass）。

| 只看终局结果时的盲区 | 环境需要保留的对象 | 代表工作 |
|---|---|---|
| `[tech report]` 题目、答案和证据可能互不一致 | 可执行任务、证据图、分阶段验证结果 | SearchArt |
| `[论文]` 胜负无法说明某一步推进还是后退 | 动作前后的 solver cost-to-go | CAST |
| `[论文]` verdict 虽正确，仍可能未经调查 | agent 实际读取并引用的稳定 node ID | Graph Is the Verifier |
| `[论文]` task reward 没记录动作造成的状态变化 | `(state, action, next observation)` | TAPO |
| `[论文]` 成功结果可能掩盖低质量过程 | 逐 turn 的过程 rubric、audit log、snapshot | ClawTrack |
| `[tech report]` 总分本身不能沉淀可复用操作经验 | 可执行操作、运行反馈和结构化经验记录 | Frontis-MA1 |

`[论文]` [Graph Is the Verifier](#ref-li2026graph) 中，结果正确的轨迹仍可能缺少真实调查。在跨过程漏洞检测中，只奖励 vulnerable / safe 的最终 verdict，policy 会利用类别先验，减少调查。完整的 reward 同时检查 verdict、CWE 类别和被引用的 CPG node。论文报告，138 个真实漏洞函数中有 **71.7%** 需要函数外证据；同样能查询 CPG、但不核验引用证据的基线仍明显落后。工具可用只说明能否查询；稳定地址才能核验查过什么。

`[论文]` [ClawTrack](#ref-wu2026) 同时保留结果分与过程分。它在 8 个领域构造 320 个任务和 25 个以上的确定性 mock services，对 21 个模型运行 **16,000 次以上 trials**。Task Score 衡量最终完成度，Process Score 逐 turn 评估目标对齐、效率、信息利用和结果核验。过程分能剔除结果分看不见的 lucky pass，并将失败定位到具体维度；按过程分筛选轨迹后，不同规模模型的 post-training 都获得提升。

<a id="任务先形成可执行闭包"></a>

## 训练任务需要环境、动作、状态与验收规则

`[tech report]` [SearchArt](#ref-mei2026) 将任务生成与核验置于同一条数据管线中。系统从网页文档构造问答、证据图和搜索轨迹，再联合检查 QA 一致性、轨迹质量与证据相关性。通过验证的轨迹才能用于 SFT 和 RL。SearchArt-27B 在报告中取得 BrowseComp-ZH 74.39、BrowseComp 70.06、DeepResearch-Bench 52.55。这些数字来自 Huawei Cloud 报告。对应的入池规则是：任务、轨迹和证据共同闭合，样本才能进入训练。

`[tech report]` [Frontis-MA1](#ref-yang2026) 将这种闭合关系扩展到机器学习工程。OpenMLE-Gym 提供可验证任务环境和 execution feedback，OpenMLE-ERL 训练 Draft、Improve、Debug、Crossover 四种程序演化操作，OpenMLE-Evo 在推理期组合相同操作做长程搜索。训练和推理共享操作语义，经验因而可表述为“某种操作在某类状态下造成什么结果”，并在搜索时复用。报告在单张 RTX 4090、每题 12 小时预算的 MLE-Bench Lite 上，将 35B base model 的 Medal Average 从 39.39% 提到 60.61%，加入 OpenMLE-Evo-Max 后达到 71.21%。

`[tech report]` [OpenThoughts-Agent-RL-5K](#ref-raoof2026) 的官方数据卡明确区分 SFT 与 on-policy RL 的训练对象。SFT 的数据项是完整的固定 `(task, trajectory)` pair；RL-5K 则提供 5,000 个自包含的可执行任务，policy 在 sandbox 中实时执行，由任务自带的 test verifier 给 reward，数据项中没有 teacher trajectory。两者的差别在于训练时是否重新采样轨迹：SFT 直接使用固定示范，on-policy RL 从 `environment + task + verifier` 组成的任务分布出发，由当前 policy 在每一轮重新生成轨迹。

`[本文归纳]` 可执行闭包至少包含四个对象：任务输入、允许的动作、执行后的状态、判断成功的 verifier。训练数据若只保存 prompt 和最终答案，后两项会被丢掉。环境合同把它们固定在同一套 schema 中，使失败样本能够区分为任务无效、动作错误、状态异常或 verifier 不完整。不同原因对应不同处理方式，数据管线才有条件做局部修复、拒绝或保留诊断。

## 一次动作可以留下四类证据

`[论文]` [CAST](#ref-wang2026) 使用精确 solver 评价中间状态。Sokoban、Minesweeper 和 Rush Hour 的 solver 可以从任意状态估算 cost-to-go；动作前后 cost-to-go 的变化可转为 solver advantage，作为 turn-level 信号加入 RLVR。最优动作获得正向进度，停滞动作接近零，有害动作得到负向 credit。在 soft-optimal solver 假设下，这个标量还等价于 solver 对动作的 log-preference，因此可以在不传递 teacher logits 的情况下完成 on-policy distillation。

`[论文]` [TAPO](#ref-li2026tapo) 直接复用环境产生的 transition。标准 online RL rollout 已记录动作后的 next observation，TAPO 在 policy optimization 与 next-observation prediction 之间交替训练，共享同一 backbone。它不新增专家数据、环境采样或推理时开销，在 WebShop、ALFWorld、不同模型规模和不同 policy optimization 算法上均报告了相对纯 policy optimization 的提升。与精确 solver 的信号相比，这类证据只记录动作后果，不直接判断后果与目标的距离。

`[论文]` [Graph Is the Verifier](#ref-li2026graph) 以稳定的证据地址连接工具调用与核验。CPG node ID 同时出现在工具返回和 reward 核验中，agent 的调查轨迹可以追溯至具体 caller、callee 或 dataflow 节点。整数集合比较避开了重命名、格式调整对文本匹配的干扰。这种设计依赖环境中稳定、可寻址的对象；缺少这层结构时，系统仍需依赖更易受文本表面变化影响的匹配，或带噪声的 LLM judge。

`[论文]` [ClawTrack](#ref-wu2026) 使用过程 rubric 与环境审计。逐 turn rubric 记录软质量，audit log 与 snapshot 记录可由确定性规则核验的结果和安全状态。前者评估过程是否合格，后者记录环境中实际发生了什么。Process Grader 使用 LLM，因而带有模型评分噪声；环境审计则只覆盖 schema 已经记录的对象。两种证据覆盖的范围不同，不能相互替代。

| 证据载体 | 回答的问题 | 优势 | 边界 |
|---|---|---|---|
| `[论文]` solver value delta | 这一步让状态离成功更近了吗 | 方向明确，可直接形成 turn-level credit | 需要精确或足够可靠的 solver |
| `[论文]` stable object ID | 结论引用了哪些真实对象 | 可寻址，核验不依赖文本表面 | 环境需先提供稳定对象空间 |
| `[论文]` next observation | 这一步实际造成了什么 | rollout 原生包含，无需额外采样 | 不直接判断后果好坏 |
| `[论文]` rubric + audit | 过程质量如何，最终状态如何 | 兼顾软质量与确定性状态 | rubric 仍受 LLM judge 噪声影响 |

`[论文]` [TermiGen](#ref-zhu2026termigen) 改变的是训练中采样到的轨迹组成，而非证据载体。它在已验证的 Docker 任务中主动注入受控错误，再让生成器根据 stderr 和环境状态诊断失败、恢复执行，形成 `error → diagnosis → correction` 的多 turn 片段。错误、诊断和修复共同构成恢复轨迹；承载证据的仍是 tests、执行反馈和环境状态。

## 证据进入训练的五个位置

`[本文归纳]` 轨迹证据可在五个位置进入从数据生成到训练后筛选的链路。证据越早进入，越能阻止有问题的任务进入数据池；越晚进入，越接近 policy 的真实行为，但修复成本也更高。

| 位置 | 证据做什么 | 代表工作 |
|---|---|---|
| task admission | 任务、答案、轨迹、证据共同通过验证后才入池 | SearchArt、Frontis-MA1、TermiGen |
| SFT / cold start | 用固定示范轨迹训练可核验工具行为或失败恢复能力 | Graph Is the Verifier、Frontis-MA1、TermiGen、OpenThoughts-Agent |
| RL reward | 将 solver delta、证据 grounding 或执行结果直接写进优化信号 | CAST、Graph Is the Verifier、Frontis-MA1、OpenThoughts-Agent-RL-5K |
| auxiliary objective | 复用既有 rollout 中的 transition，训练动作后果预测 | TAPO |
| post-training filtering | 用 outcome 与 process 双评分选择更可复现的轨迹 | ClawTrack、SearchArt |

`[论文]` [Graph Is the Verifier](#ref-li2026graph) 中，policy 从不调用工具时，group-relative RL 就没有“调查得好”和“调查得差”的 rollout 可以比较。论文先用 teacher investigation 做 SFT warm start，再用带证据 grounding 的 GRPO。环境证据因此还承担启动探索的职责：先让可核验行为进入 policy 的支持集，RL 才能优化它。

`[本文归纳]` 失败样本也应按证据位置分流。task admission 失败适合修任务或拒绝入池；动作后果证据为负可以直接进入 credit；过程分低但 outcome 成功的轨迹适合保留作诊断，通常不宜直接当优质示范；执行环境异常则应隔离为基础设施失败，避免给 policy 错误惩罚。统一写成一个 success / failure 标量，会将四类处置压缩为一种处置方式。

## 环境与 verifier 是同一份合同的前后两面

`[本文归纳]` 环境设计决定 agent 能做哪些动作、每次动作改变哪些状态、哪些对象拥有稳定地址；verifier 只能检查环境已经显式记录的对象。任务生成时写下 tests 和 evidence graph，执行时保留 state transition 与对象 ID，评测时才能把 claim、action 和 outcome 接回同一条证据链。环境 schema 的表达能力限定 verifier 的上限。

`[论文]` [Graph Is the Verifier](#ref-li2026graph) 将这条关系置于同一个数据结构中：CPG 在推理时是 tool，在训练时是 verifier。`[tech report]` [SearchArt](#ref-mei2026) 和 [Frontis-MA1](#ref-yang2026) 则将同一原则扩展到系统层，任务构造、执行、训练和评测共享环境合同。`[论文]` [ClawTrack](#ref-wu2026) 表明，环境合同之外仍有一部分问题：效率、目标对齐和信息利用仍需要过程 rubric，确定性状态无法覆盖全部软质量。

`[本文归纳]` 轨迹证据工程、credit assignment 与 verifier reliability 分属不同环节。轨迹证据工程规定环境先记录什么，使信号能绑定到具体对象并供 verifier 核验；credit assignment 讨论已有信号怎样沿轨迹分配；verifier reliability 讨论 verifier 对已有对象能否判断准确。轨迹证据为后两者提供前提：环境没有记录动作后果，后续的细粒度 credit 和高质量 verifier 都无法恢复已经消失的信息。

## 五个轨迹证据设计维度

`[本文归纳]` 任务合成、agent RL、过程评测和自我改进中的轨迹证据，可沿五个维度对照。

| 维度 | 取值范围 | 设计问题 |
|---|---|---|
| 证据载体 | tests / evidence graph / solver value / stable ID / next observation / rubric + audit | 哪个对象保存动作后果 |
| 附着粒度 | task / trajectory / turn / action / evidence item | 证据能精确绑定到哪一层 |
| 核验者 | deterministic test / solver / structured graph / environment / LLM grader | 谁判断证据成立 |
| 进入训练的位置 | admission / SFT / RL reward / auxiliary objective / filtering | 证据在哪一步改变数据或梯度 |
| 失败处理 | repair / reject / negative credit / diagnostic retain / filter | 失败样本进入哪条后续路径 |

`[论文]` [SkillSynth](#ref-fan2026skillsynth) 将高层执行轨迹表示为 scenario 与 skill 的交替序列，再从 skill graph 采样 workflow path，以控制训练任务覆盖哪些场景与技能组合。路径采样决定 agent 经历哪些场景、使用哪些技能；五个轨迹证据维度则描述这些经历留下什么证据，以及证据怎样进入训练。

`[本文归纳]` 五个维度覆盖轨迹证据的载体、绑定、核验、训练位置和失败处理。完整的 Agent 数据分类还需描述任务来源、环境可重置性、scenario / skill path coverage 等采样轴。

`[本文归纳]` 五个维度依照信息产生的顺序衔接：证据载体及其动作绑定是起点，核验者及其噪声决定可信度，进入 admission、SFT、RL 或 filtering 的位置决定证据如何改变训练，失败类型则对应修复、拒绝、负向学习或诊断保留。缺少证据载体与动作绑定时，训练系统只能在轨迹末尾得到一个分数，后续优化无法还原执行过程。

## Reference

<a id="ref-mei2026"></a>
**[SearchArt: Training Long-Horizon Search Agent with Scalable Synthetic and Verified Tasks]** Lang Mei, Xiaohan Yu, Chong Chen, Liyan Liu, Xiangnan Chen, Jinchao Ma, Chao Feng, Li Huang, Siyu Mo, Sichen Kang, Yunkun Xu, Zhihan Yang, Zhujun Xue, Jingren Zhang, Qing He, Yingdi Huang, Hao Jiang, Ziao Ma, Zewei Pan, Minhao Sun, Zhuo Tao, Jinzhao Xiao, Gangtao Xin, Huanyao Zhang, Wenjian Zhang, Jiangshan Zhang, Guojie Zhu, Jiaxin Mao, Wentao Zhang，Huawei Cloud Post-Training Team，2026. [arXiv:2607.24850](https://arxiv.org/abs/2607.24850)。用于任务合成、证据图、轨迹验证和多阶段训练闭环。`[tech report]`

<a id="ref-wang2026"></a>
**[CAST: Game Solvers as Turn-Level Teachers for LLM Agents]** Yu Wang, Yi-Kai Zhang, Wentao Shi, Ziang Ye, Yuchun Miao, Yueqing Sun, Qi Gu, Xunliang Cai, Lan-Zhe Guo, Han-Jia Ye, Fuli Feng，中国科学技术大学、南京大学、武汉大学、美团，2026. [arXiv:2607.25308](https://arxiv.org/abs/2607.25308)。用于 solver state value、turn-level credit 与 logit-free on-policy distillation。`[arxiv 论文]`

<a id="ref-li2026graph"></a>
**[Graph Is the Verifier: Agentic Reinforcement Learning for Interprocedural Vulnerability Detection]** Yikun Li, Ting Zhang, Jiakun Liu, Jinfeng Jiang, Yieh Yuheng, Yixin Yang, Leow Wen Bin, Yin Yide, Yintong Huo, Eng Lieh Ouh, Lwin Khin Shar, David Lo，Singapore Management University、Harbin Institute of Technology、GovTech Singapore，2026. [arXiv:2607.26656](https://arxiv.org/abs/2607.26656)。用于同一 CPG 同时作为工具与 verifier、稳定 node ID grounding，以及 verdict-only reward 的退化。`[arxiv 论文]`

<a id="ref-li2026tapo"></a>
**[TAPO: Transition-Aware Policy Optimization for LLM Agents]** Cong Li, Peixi Peng, Yisen Zhao, Xinyu Hu, Shudong Liu, Zhan Su, Zhuojian Li，北京大学电子与计算机工程学院、鹏城实验室，2026. [arXiv:2607.27973](https://arxiv.org/abs/2607.27973)。用于复用 online rollout 中的 action-conditioned next observation 进行 transition supervision。`[arxiv 论文]`

<a id="ref-wu2026"></a>
**[ClawTrack: Towards Trace-Level Evaluation and Improvement of Real-World Autonomous Agents]** Xingjian Wu, Xuhang Zhu, Xingchen Liu, Junlin Liu, Jianing Wang, Linsen Guo, Xiaoyu Li, Xuezhi Cao, Xunliang Cai，美团，2026. [arXiv:2607.28037](https://arxiv.org/abs/2607.28037)。用于 outcome / process 双评分、lucky pass 识别、失败归因和 process-aware trajectory filtering。`[arxiv 论文]`

<a id="ref-yang2026"></a>
**[Frontis-MA1: Training an AI4AI Model towards Recursive Self-Improvement in Machine Learning Engineering]** Junlin Yang, Che Jiang, Yu Fu, Tianwei Luo, Can Ren, Weizhi Wang, Kaikai Zhao, Hongyi Liu, Yuxin Zuo, Yuru Wang, Yuchen Fan, Kai Tian, Zhenzhao Yuan, Xiaojian Lin, Li Sheng, Rushi Qiang, Guoli Jia, Xingtai Lv, Ermo Hua, Dianqiao Lei, Youbang Sun, Ning Ding, Bowen Zhou, Kaiyan Zhang，Horizon Research、Frontis.AI、清华大学，2026. [arXiv:2607.28568](https://arxiv.org/abs/2607.28568)。用于可验证 MLE 环境、训练与搜索共享的原子操作，以及 execution-grounded 经验闭环。`[tech report]`

<a id="ref-zhu2026termigen"></a>
**[TermiGen: High-Fidelity Environment and Robust Trajectory Synthesis for Terminal Agents]** Kaijie Zhu, Yuzhou Nie, Yijiang Li, Yiming Huang, Jialian Wu, Jiang Liu, Ximeng Sun, Zhenfei Yin, Lun Wang, Zicheng Liu, Emad Barsoum, William Yang Wang, Wenbo Guo，UC Santa Barbara、UC San Diego、AMD、University of Oxford、Google，2026. [arXiv:2602.07274](https://arxiv.org/abs/2602.07274)。用于受控错误注入，以及错误、诊断、修复组成的恢复轨迹。`[arxiv 论文]`

<a id="ref-raoof2026"></a>
**[OpenThoughts-Agent: Data Recipes for Agentic Models]** Negin Raoof, Richard Zhuang, Marianna Nezhurina, Etash Guha, Atula Tejaswi, Ryan Marten, Charlie F. Ruan, Tyler Griggs, Alexander Glenn Shaw, Hritik Bansal, E. Kelly Buchanan, Artem Gazizov, Reinhard Heckel, Chinmay Hegde, Sankalp Jajee, Daanish Khazi, Emmanouil Koukoumidis, Xiangyi Li, Hange Liu, Shlok Natarajan, Harsh Raj, Nicholas Roberts, Ethan Shen, Nishad Singhi, Michael Siu, Ashima Suvarna, Hanwen Xing, Patrick Yubeaton, Robert Zhang, Leon Liangyu Chen, Xiaokun Chen, Steven Dillmann, Saadia Gabriel, Xunyi Jiang, Anurag Kashyap, Boxuan Li, Yein Park, Minh Pham, Sujay Sanghavi, Lin Shi, Ke Sun, Yixin Wang, Zhiwei Xu, Erica Zhang, Siyan Zhao, Wanjia Zhao, Jenia Jitsev, Alex Dimakis, Benjamin Feuer, Ludwig Schmidt，UC Berkeley、Stanford University、JSC、LAION、Open-Ψ、UT Austin、Bespoke Labs 等，2026. [arXiv:2606.24855](https://arxiv.org/abs/2606.24855)；[OpenThoughts-Agent-RL-5K 官方数据卡](https://huggingface.co/datasets/open-thoughts/OpenThoughts-Agent-RL-5K/blob/main/README.md)。用于区分 SFT 的固定 `(task, trajectory)` pair 与 on-policy RL 的可执行任务包。`[arxiv 论文 / 官方数据卡]`

<a id="ref-fan2026skillsynth"></a>
**[Toward Scalable Terminal Task Synthesis via Skill Graphs]** Zhiyuan Fan, Tinghao Yu, Yuanjun Cai, Jiangtao Guan, Yun Yang, Dingxin Hu, Jiang Zhou, Xing Wu, Zhuo Han, Feng Zhang, Lilin Wang，Hunyuan Team, Tencent，2026. [arXiv:2604.25727](https://arxiv.org/abs/2604.25727)。用于 scenario-mediated skill graph、workflow path 采样，以及 scenario / skill coverage 这一独立设计轴。`[arxiv 论文]`
