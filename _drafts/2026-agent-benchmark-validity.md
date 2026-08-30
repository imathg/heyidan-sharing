# 一条 failed 能说明什么：Agent Benchmark 的有效分母
<!-- domain: rubrics -->

`[本文归纳]` 评测跑完，结果里有一条 `failed`。最直接的读法是“这个 Agent 不会做这道题”，但这条读法要一连串前提同时成立才作数：题目本身得成立，对应的运行轨迹得真的走到要考的那一步，留下的证据得属于当前被测版本，判分的 Judge 得在这类任务上足够可靠。任何一条不成立，`failed` 就只是一个终态标签，不能直接解释成能力缺失。

`[本文归纳]` 总分也是一样。一个通过率，只有在分母里的每道题都有效、每次运行都承载了目标能力、每份证据都属于当前系统、每条判定都可靠时，才是模型或 Agent 系统的效果数。否则它仍是一个数，却没有有效分母。数据问题、运行问题、基础设施问题和判分问题都被同一个标签吞掉了。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../meta/#claim-tags)。

`[本文归纳]` 2026 年的七项工作分别研究网络诊断、安全任务、工程建模、科学复现、runtime 评测、Judge 评测和 Skill 评测，却指向同一个问题。要解释一条 `failed`，需要依次回答五个问题：题目是否成立、运行是否走到考点、证据是否属于当前对象、判定是否可靠，以及两个系统的结果是否可比。

## 1. 题目本身成立吗

`[论文]` 网络诊断是最直观的例子。[FaulT-Bench](#ref-tseng2026)（The University of Sydney，Tseng et al. 2026）把这类 Benchmark 的默认前提翻了过来：过去的任务默认工单描述准确，而且网络里一定有故障。作者构造了 200 个场景，把真实故障、错误报告、错误设备归因和错误故障原因放进同一套评测；其中 72 个错误前提工单又被改写成五种 reporter persona，只改变表达的信心和可核细节，底层网络状态保持不变。

`[论文]` 三类 Agent 在准确工单上接近饱和，面对“网络健康但工单说有故障”的输入时却明显退化：它们会持续探测，直到把一个正常现象解释成故障原因。只含正例的 Benchmark 测到的是“已知有故障时怎样定位”，回答不了“报告本身是否成立”。题目的世界状态缺了一半，分数自然高估真实诊断能力。

`[论文]` 另一类风险出在题目来源：它是否来自可追溯的真实任务。[Pufibara](#ref-wang2026)（TU Dresden，Wang 2026）为 Modelica 工程建模建了 232 道 source-grounded task，覆盖 Model Repair、Model Generation 和 Model Tuning；每道题由 Benchmark 自己的 evaluator 在 Agent loop 之外评分。任务来自可追溯的工程来源，预期物理行为由独立 evaluator 持有：程序编译和仿真成功只证明它可执行，方程和轨迹是否符合题目里的工程约束，由另一层验收判断。

`[本文归纳]` 评测结果的解释取决于题目本身。输入描述未必等同于底层世界，信息不足时目标结论可能无解，验收条件也可能偏离测量意图。任一情况没有被排除，失败都不能先记在模型头上。

## 2. 运行走到考点了吗

`[论文]` 题目成立，运行也可能根本没走到要考的那一步。[Beyond End-to-End Success](#ref-shao2026)（University of California, Davis / Rochester Institute of Technology，Shao et al. 2026）研究的长程安全任务要求 Agent 先发现一段状态，经过若干步骤后再复用它。如果 Agent 从头到尾没观察到这段状态，最终失败不能证明它缺少状态复用能力，因为能力从未进入可行使的区间。

`[论文]` 论文用 checkpoint 标出 capability exposure：轨迹第一次取得目标能力所需信息的时刻。预注册的 92-seed 实验里，针对协议歧义的 guidance 把 Gemini 2.5 Flash 的状态观察率从 65.5% 提到 95.4%；换到 Gemini 3.7 Flash 后，同一干预的效果方向反转，状态观察也不再稳定预测终局完成。故障位置会随模型版本移动，旧模型上的上游诊断不能自动解释新模型。

`[本文归纳]` exposure 把两种失败分开：“没有走到考点”和“走到考点后做错”。前者仍影响端到端可靠性，但属于任务入口、工具发现、状态取得或前序策略；后者才直接提供目标能力的证据。报告可以同时保留整体成功率和 exposure 条件下的成功率，但不能用后者替换前者，也不能让前者独自承担能力结论。

## 3. 证据属于当前被测对象吗

`[论文]` 即使运行走到了考点，“被测对象到底是什么”也要先说清楚。[ClawProBench](#ref-xiao2026)（The Chinese University of Hong Kong，Xiao 2026）把评测对象从 model 改成“声明的 model + runtime configuration”：102 个 full-profile 场景同时覆盖 workspace 与八类 runtime-native surface，另有 68 个冻结场景作为 holdout；执行 trace 里保留 correctness、process quality、efficiency、safety gate 和 execution status。结果上，runtime-native 场景平均 0.5238，workspace-live 场景为 0.6415；holdout 的 pass@k-any 是 0.6638，严格要求三次都通过时只有 0.2890。

`[本文归纳]` 同一个模型，如果换了 runtime release、tool catalog、turn renderer、state owner 或 retry policy，测量对象就已经变了。只记录 model name，会把 harness 差异算进模型能力；只记录最终答案，又会漏掉错误 surface、越权动作、无证据重试和偶然通过。

`[论文]` 被测对象明确之后，证据还要绑到具体版本。Pufibara 还暴露了一类更隐蔽的运行错误：多轮修改中，Agent 可能拿旧 candidate 的仿真结果证明新 candidate。两份文件都来自同一任务，结果也确实成功执行，问题在于证据与被评对象没有绑定。Pufibara 把 execution / simulation evidence 绑定到生成它的 candidate revision，并把 submission 设为显式动作，Benchmark 才知道哪一版正式进入判分。

`[论文]` 绑定还有语义一层。[ABE-Ralph](#ref-yu2026)（Zhejiang University / Zhejiang Lab，Yu et al. 2026）发现，科学实验里的 Agent 可以静默缩小 dataset 或训练预算，用 lookup / oracle 替代失败的学习组件，或者在方法优势尚未出现的小规模设置上得出结论。代码照样 exit 0，metrics 也可能很像论文，实验却已经没有在测原 claim。

`[论文]` ABE-Ralph 先把 claim、protocol、required component、baseline、metric 和 resource bound 写进结构化合同，再分别检查数值对齐、语义逻辑与代码结构。30 次长程复现实验覆盖 12 个机器学习领域，系统报告 93% robust execution rate，同时识别出五类 methodological hallucination。执行稳定与实验保真是两条独立轴，前者通过不替代后者。

`[本文归纳]` 到这里，一条结果要过的绑定有两种。版本绑定回答“当前 evidence 属于哪个 model、runtime、candidate 和 source revision”；语义绑定回答“当前 execution 是否仍在测试已声明的题目与 claim”。hash、manifest 和 explicit submission 解决前一类，constraint、scenario 与 evidence mapping 解决后一类。两种绑定都闭合，成功回执才有资格进入判分。

## 4. 判定本身可靠吗

`[论文]` 证据齐了，还要判得准。[AgentJudgeBench](#ref-verma2026)（ServiceNow AI，Verma et al. 2026）专门测试 Judge 在 agentic tool-calling workflow DAG 上的可靠性：3,808 个实例覆盖六种 DAG topology 和三档难度，五个 generator 与六个 Judge 分别在有 / 无 ground truth 的条件下配对评测。任务越难，Judge alignment 越低；没有 ground truth 时，下降速度是有 ground truth 的 1.5 倍。

`[论文]` hard query 且无 ground truth 时，六个 Judge 收敛在 77–82% 的窄区间，扩大模型规模没有离开这一区间。Chain-of-thought 和 temperature 基本无效，structured rubric 最多提高 6.5 个百分点，却没有在所有 judge-generator pair 上稳定泛化。向 Judge 展示 ground truth 也并非单向增益：GPT-5.4 和 Gemini-2.5-Pro 分别下降 1.5 与 3.9 个百分点，论文将其解释为 over-anchoring 的一致证据。

`[本文归纳]` 所以判分不能只记录“用了哪个大模型”。它还要绑定任务难度、ground-truth 可见性、rubric、prompt、generator 分布与 programmatic reference。如果当前证据不足以支持稳定判定，正确状态是 `indeterminate`；把它强压成 pass / fail，只会把 Judge 的不确定性转嫁给被评 Agent。

## 5. 两个系统的分数能比吗

`[论文]` 单系统的结果能解释之后，才谈得上对比。[ACES](#ref-kevin2026)（NVIDIA，Kevin et al. 2026）对 58 个 production Skill 做有 / 无 Skill 的 paired live trial：每对运行固定 task、model、sandbox、harness、workspace 和 scorer，轨迹统一成 Agent Trajectory Interchange Format（ATIF），再计算 Skill Lift。947 个配对 case 的 mean composite lift 为 0.2134，95% CI 为 [0.1967, 0.2301]；72.8% 的 case 为正。

`[论文]` 同一研究也划出了静态 gate 的边界：Skill 的 structural score 与 LLM-judge score 的 Spearman 相关只有 0.14；最大的 process gain 出现在 Skill execution、behavior check 和 efficiency，这些对象不运行就看不到。静态扫描适合发现文档与安全问题，live paired trial 才回答这个能力包在当前 runtime 里增加了什么。

`[本文归纳]` 对比的最小单位因此是“同一道有效题 + 两侧都完成的运行绑定 + 两侧都可判定的结果”。只有这部分交集能承担差异归因；单侧 compile blocked、run error、evidence missing 或 Judge indeterminate 都属于限制项，不进入胜负统计。

## 6. 分母是逐题算出来的

`[本文归纳]` 效果统计里的每个 Case 都需要五类分母证据，以及一项用来解释失败位置的诊断维度：

| 要补的证据 | 它回答什么 | 缺了它，这条结果实际是 |
|---|---|---|
| 题目有效性 | 输入前提、信息边界与验收条件是否真的在测目标能力 | 题的问题，被记成了模型失败 |
| 配置与版本绑定 | model、runtime、工具与 source revision 是否冻结并声明 | 换了对象的结果 |
| 执行终态 | 物理执行是否有确定终态 | 没跑成或运行报错 |
| 证据完整 | trace 与结果是否绑定当前 candidate 和 claim | 当前结果缺少可核证据 |
| 判定可决 | 当前 Judge 合同能否稳定给出判定 | 判分不确定性 |
| 能力暴露（诊断维度） | 运行是否已经到达目标能力可行使的位置 | 考点前的上游失败 |

`[本文归纳]` 单系统报告里，分母由表中前五类条件共同确定；能力暴露单独用于区分端到端可靠性与目标能力表现。双系统对比还要取两边有效分母的交集。这个交集可能比原始题量小很多，所以报告必须同时列出各类排除的数量。缺少这些数量时，留下的可能只是容易题，报告却仍沿用全量覆盖的语气。

`[本文归纳]` 这些检查按发生位置可以归到题目、运行、判定三层：未通过的题不消失，按原因回到能修它的那一层（下图）。

<figure class="diagram">
<svg width="100%" viewBox="0 0 820 620" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="abv-title abv-desc">
<title id="abv-title">Agent Benchmark 的有效分母</title>
<desc id="abv-desc">Case、Runtime 与 Judge 三道资格门筛选逐题结果，只有三层闭合的 Case 才进入效果分母。</desc>
<defs>
<linearGradient id="panelGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#131922"/><stop offset="1" stop-color="#1a2230"/></linearGradient>
<linearGradient id="nodeGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#17212c"/><stop offset="1" stop-color="#202b39"/></linearGradient>
<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#05080c" flood-opacity="0.34"/></filter>
<marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#5fd0c8"/></marker>
</defs>
<rect x="20" y="20" width="780" height="580" rx="24" fill="url(#panelGrad)" stroke="#2a3441"/>
<text x="54" y="68" fill="#e6edf3" font-size="24" font-weight="700" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">Agent Benchmark 的有效分母</text>
<text x="54" y="94" fill="#8b97a4" font-size="13" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">先验证资格，再解释分数；失败回到对应 owner</text>
<g filter="url(#shadow)">
<rect x="58" y="132" width="212" height="150" rx="18" fill="url(#nodeGrad)" stroke="#3a4858"/>
<rect x="304" y="132" width="212" height="150" rx="18" fill="url(#nodeGrad)" stroke="#3a4858"/>
<rect x="550" y="132" width="212" height="150" rx="18" fill="url(#nodeGrad)" stroke="#3a4858"/>
</g>
<text x="82" y="171" fill="#5fd0c8" font-size="14" font-weight="700" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">01 · CASE GATE</text>
<text x="82" y="203" fill="#e6edf3" font-size="16" font-weight="650" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">题目真的测到目标能力</text>
<text x="82" y="233" fill="#8b97a4" font-size="12.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">前提 · 信息边界 · Rubric</text>
<text x="82" y="256" fill="#8b97a4" font-size="12.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">false premise / no-fault 也覆盖</text>
<text x="328" y="171" fill="#5fd0c8" font-size="14" font-weight="700" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">02 · RUNTIME GATE</text>
<text x="328" y="203" fill="#e6edf3" font-size="16" font-weight="650" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">声明配置真实执行</text>
<text x="328" y="233" fill="#8b97a4" font-size="12.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">exposure · version · trace</text>
<text x="328" y="256" fill="#8b97a4" font-size="12.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">evidence 绑定当前 candidate</text>
<text x="574" y="171" fill="#5fd0c8" font-size="14" font-weight="700" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">03 · JUDGE GATE</text>
<text x="574" y="203" fill="#e6edf3" font-size="16" font-weight="650" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">当前证据能够稳定判定</text>
<text x="574" y="233" fill="#8b97a4" font-size="12.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">difficulty · GT · rubric</text>
<text x="574" y="256" fill="#8b97a4" font-size="12.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">不确定结果保持 indeterminate</text>
<path d="M270 207 H294" stroke="#5fd0c8" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#arrow)"/>
<path d="M516 207 H540" stroke="#5fd0c8" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#arrow)"/>
<rect x="104" y="336" width="612" height="108" rx="18" fill="#10151d" stroke="#5fd0c8" stroke-width="1.4"/>
<text x="410" y="374" text-anchor="middle" fill="#5fd0c8" font-size="14" font-weight="700" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">EFFECT DENOMINATOR</text>
<text x="410" y="407" text-anchor="middle" fill="#e6edf3" font-size="18" font-weight="700" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">Case ∩ Runtime ∩ Evidence ∩ Judge</text>
<text x="410" y="431" text-anchor="middle" fill="#8b97a4" font-size="12.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">双系统比较再取双方可判定结果的共同交集</text>
<path d="M164 282 V322 H314 V336" fill="none" stroke="#5fd0c8" stroke-width="1.5" stroke-dasharray="7 5" marker-end="url(#arrow)"/>
<path d="M410 282 V326" fill="none" stroke="#5fd0c8" stroke-width="1.5" stroke-dasharray="7 5" marker-end="url(#arrow)"/>
<path d="M656 282 V322 H506 V336" fill="none" stroke="#5fd0c8" stroke-width="1.5" stroke-dasharray="7 5" marker-end="url(#arrow)"/>
<g>
<rect x="58" y="496" width="152" height="58" rx="12" fill="#151b25" stroke="#2a3441"/>
<rect x="242" y="496" width="152" height="58" rx="12" fill="#151b25" stroke="#2a3441"/>
<rect x="426" y="496" width="152" height="58" rx="12" fill="#151b25" stroke="#2a3441"/>
<rect x="610" y="496" width="152" height="58" rx="12" fill="#151b25" stroke="#2a3441"/>
<text x="134" y="522" text-anchor="middle" fill="#e6edf3" font-size="12.5" font-weight="650" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">invalid / repair</text>
<text x="134" y="541" text-anchor="middle" fill="#8b97a4" font-size="11.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">数据与题目 owner</text>
<text x="318" y="522" text-anchor="middle" fill="#e6edf3" font-size="12.5" font-weight="650" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">binding / run error</text>
<text x="318" y="541" text-anchor="middle" fill="#8b97a4" font-size="11.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">Harness / runner owner</text>
<text x="502" y="522" text-anchor="middle" fill="#e6edf3" font-size="12.5" font-weight="650" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">evidence missing</text>
<text x="502" y="541" text-anchor="middle" fill="#8b97a4" font-size="11.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">trace / artifact owner</text>
<text x="686" y="522" text-anchor="middle" fill="#e6edf3" font-size="12.5" font-weight="650" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">indeterminate</text>
<text x="686" y="541" text-anchor="middle" fill="#8b97a4" font-size="11.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">Judge owner</text>
</g>
<path d="M410 444 V476" stroke="#8b97a4" stroke-width="1.2" stroke-dasharray="1 7"/>
<text x="410" y="478" text-anchor="middle" fill="#8b97a4" font-size="11.5" font-family="-apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif">未过门的 Case 不消失，按原因回流</text>
</svg>
</figure>

`[本文归纳]` 有效分母是效果结论的最低证据合同。它让“这批题里通过了多少”变成“哪些题真的测到了目标能力，哪些结果属于当前系统，哪些判定足够可靠”。这些条件分别成立后，分数才重新指向它声称测量的对象。

## Reference

<a id="ref-shao2026"></a>
**[Beyond End-to-End Success: Diagnosing Failures in Long-Horizon Security LLM Agents]** Wei Shao, Chongzhou Fang, Zuxiong Tan, Zequan Liang, Setareh Rafatirad, Avesta Sasan, Houman Homayoun，University of California, Davis / Rochester Institute of Technology，2026. [arXiv:2608.20563](https://arxiv.org/abs/2608.20563)。本文用它定义 capability exposure，并区分考点前失败与考点后表现。[arXiv 论文]

<a id="ref-kevin2026"></a>
**[Evaluating Skills, Not Just Agents: Agentic Continuous Evaluation of Skills]** Christopher Kevin, Narendran Raghavan, Jean-Francois Puget, Roshni Malani, Meghana Puvvadi, Moshe Abramovitch, Mohit Gupta, Rama Akkiraju, Subodh Prabhu, Yogesh Dangi, Wei Luo, Seong Hee Lee，NVIDIA，2026. [arXiv:2608.20614](https://arxiv.org/abs/2608.20614)。本文用它说明冻结运行条件下的 paired live trial 如何承担组件增量归因。[arXiv 论文]

<a id="ref-xiao2026"></a>
**[ClawProBench: Trace-Aware Evaluation of Declared Agent Configurations with Runtime Coverage and Frozen Holdouts]** YuanHang Xiao，The Chinese University of Hong Kong，2026. [arXiv:2608.22510](https://arxiv.org/abs/2608.22510)。本文用它说明 Agent Benchmark 的对象应包含 runtime configuration、trace 与重复执行状态。[arXiv 论文 / 独立研究者单人]

<a id="ref-wang2026"></a>
**[Beyond Executable Models: The Pufibara Agent Harness and the Modelica Agent Workflow Benchmark for Physical System Modeling]** Zizhe Wang，TU Dresden，2026. [arXiv:2608.23653](https://arxiv.org/abs/2608.23653)。本文用它说明 source-grounded task、candidate-bound evidence 与 explicit submission 的作用。[arXiv 论文 / 独立研究者单人]

<a id="ref-yu2026"></a>
**[Beyond Execution: Auditing Experimental Fidelity in LLM-Driven Scientific Research]** Lezhi Yu, Xiaogang Xu, Yuhua Zhou, Shuibing He, Aimin Pan，Zhejiang University / Zhejiang Lab，2026. [arXiv:2608.26753](https://arxiv.org/abs/2608.26753)。本文用它区分代码执行成功与实验方法、协议和结论的保真。[arXiv 论文]

<a id="ref-verma2026"></a>
**[AgentJudgeBench: A Multi-Difficulty Benchmark for Evaluating LLM Judges on Agentic Tool-Calling]** Abhigya Verma, Amit Kumar Saha, Seganrasan Subramanian, Sai Harshitha Aluru，ServiceNow AI，2026. [arXiv:2608.26623](https://arxiv.org/abs/2608.26623)。本文用它说明 Judge validity 依赖任务难度、ground truth 和 rubric 合同。[arXiv 论文]

<a id="ref-tseng2026"></a>
**[FaulT-Bench: Towards Benchmarking Network Troubleshooting LLM Agents under Unreliable User Tickets]** Kuan-Hao Tseng, Niruth Bogahawatta, Yasod Ginige, Kunjan Patel, Kosta Dakic, Suranga Seneviratne，The University of Sydney，2026. [arXiv:2608.27021](https://arxiv.org/abs/2608.27021)。本文用它说明 Case validity 必须覆盖错误前提、无故障世界与输入表达变化。[arXiv 论文]
