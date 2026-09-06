# LLM Judge 用作奖励：误判偏差与校准方法

<!-- domain: rubrics -->
<!-- edition_date: 2026-07-12 -->
<!-- revised_date: 2026-09-06 -->
<!-- revision_note: 撤回未经核实的通用上限公式，区分判分分歧、训练风险与已测得的改进。 -->

同样取得较高 F1 的两个 LLM Judge，可能一个经常放过错误引用，另一个经常拒绝正确引用。用它们评测，可能改变排名；把分数用作强化学习奖励，改变的则是模型被鼓励做什么。**选 Judge 不能只看平均分，还要看它在哪些要求上误放、误拒，以及这些错误进入训练后是否损害真实质量。**

本文比较引用核验、代码判分和结构化反馈中的研究结果：先分清误差来自判分模型还是判据，再选择校准与改进方法。这些研究支持检查具体失效，不足以推出一个适用于所有任务的“Verifier 决定训练上限”定理。

<a id="判官就是-reward-model"></a>
<a id="标量准确率盖不住方向性偏差"></a>

## F1 相近，不代表奖励信号相同

[论文 · Citation Verifier](#ref-pwc2026) 比较了八个 Judge，使用 1,248 条人工复核的引用判断，分别检查“来源是否相关”和“来源是否支持论断”。GPT-5-mini 的来源相关性 F1 为 0.908；事实支持这一维，各模型置信区间重叠，没有一个模型在所有维度占优。但 F1 相近的 Judge，误放率、误拒率和通过率偏移仍有明显差异。

| 判分错误 | 在引用核验里意味着什么 | 用作奖励时需要检查的风险 |
|---|---|---|
| 误放：错误输出被判通过 | 来源相关，但并不支持文章的论断 | 错误引用也能得到奖励 |
| 误拒：正确输出被判不通过 | 来源确实支持论断，却未被接受 | 合格输出的训练信号被压低 |
| 通过率偏移 | 相比人工标准持续偏松或偏严 | 奖励密度与实际质量脱节 |

F1 是有用的综合指标，但不能单独还原这两类错误。[论文讨论](#ref-pwc2026) 指出了它们对训练目标的风险；这里比较的是 Judge 的判分表现，并未直接测量各 Judge 训练出的策略，更没有测出通用能力上限。

[RuVerBench](#ref-ruverbench2026) 把问题扩展到深度研究与代码 Agent 的长输出。在 2,458 个实例中，先进模型仍会误判细粒度要求。同一 Judge 多次投票能减少采样波动，但收益递减：该实验中主要收益在三至五次投票内出现。**这是投票次数，不是模型自我改进能持续多少轮。** 一致地判错，不会因为重复同一个判断就自动纠正。

<a id="verifier-的定义方式本身注入噪声"></a>

## 先区分 Judge 误判与判据写错

程序化判分也不等于业务标准天然正确。测试可以稳定运行，却只接受某一种实现，或者漏检重要功能。

[DeepSWE](#ref-deepswe2026) 针对原创代码任务手写功能验证器，目标是接受满足需求的不同实现。独立 LLM Judge 复审时，与这些验证器的分歧率为 1.4%；与 SWE-Bench Pro 继承测试的分歧率为 32.4%。

这里的指标是**与独立 Judge 的分歧率，不是真实错误率**：独立 Judge 也可能判错，两个 benchmark 的任务集合也不同。因此，不能把差值全部归因于测试编写方式。它提示的具体工作是回看争议样本：究竟是代码错了、测试限制过窄，还是复审 Judge 漏读了证据？没有这一步，换一个更强的 Judge 也可能继续服务于错误的判据。

<a id="提高上限的五种途径"></a>

## 改进方法要对应已经定位的错误

这些方法处理的问题不同，不是一套按顺序安装就能提高可靠性的流程。

- **要求或证据难以审计时，细化反馈。** [SEVA](#ref-seva2026) 让事实核验器输出证据对齐、推理说明和错误诊断，并用分解后的过程奖励训练。3B 模型在 ClearFacts 上从 SFT 转为 GRPO 后，macro-F1 从 64.9 提高到 69.0。论文另一组 7B 模型实验也暴露了限制：四轮自我演化后，在 HaluEval 的提升伴随 TruthfulQA 的下降。能审计、单项变好，不等于全面改进。
- **判分标准漏掉重要维度时，补充视角。** [Many Voices, One Reward](#ref-manyvoices2026) 从多个角色生成互补标准，在偏好判断与开放式生成训练中优于单角色基线。它补的是标准的覆盖面，不能据此保证任意多 Judge 投票都能消除偏差。
- **已定位的训练样本过于容易时，生成更有挑战性的样本。** [Hallucination Self-Play](#ref-hsp2026) 先用人工标注初始化检测器，再交替训练生成器与检测器，在 RAGTruth 上取得改进。它支持这组任务里的训练方法，不证明检测器可以无限变强。
- **多 Agent 任务失败但责任不清时，核验不同轨迹解释。** [AgentLocate](#ref-agentlocate2026) 结合多评估者、置信度聚合和轻量微调，改善责任 Agent 与关键失败步的定位。这个结果属于故障归因，不是对所有奖励模型校准方法的统一比较。

<a id="天花板从何而来"></a>

## 这些证据还不能证明什么

<span id="ref-autoresearch2026"></span>

旧稿将一份未经原件核实的综述转述称为定理，进一步给出了上限公式、“棋类无限变强”和“LLM 自评三到五轮饱和”的解释。本版撤回这些断言，也删除据此绘制的上升与饱和曲线。已有可核验研究足以支持对 Judge 偏差的警惕，不需要借一个未成立的统一理论加强语气。

还有两条边界值得保留：弱 Judge 并不意味着训练必然失败，关键要看它提供什么方向的信号；投票、结构化输出或共进化取得局部收益，也不意味着消除了所有系统性误差。

<a id="落到工程上"></a>

## 把判分校准与训练效果分别验证

准备把 Judge 接入奖励时，可以先在目标任务上建立人工复核样本，按要求分别看误放、误拒和证据缺口；再选择修改判据、提示词、反馈结构或训练数据。真正进入训练后，还需用独立样本检查模型行为是否改善，而不只看原 Judge 的分数是否上涨。

本文的结论是这两次验证不能合并：**Judge 能按标准判分，是奖励可用的前提之一；训练是否提高真实质量，仍需要单独证明。**

## Reference

<a id="ref-pwc2026"></a>
**[Do You Need a Frontier Model as a Citation Verifier? Benchmarking Rubric LLMs for Deep-Research Source Attribution]** Ethan Leung, Elias Lumer, Corey Feld, Austin Huber, Vamse Kumar Subbiah, Kevin Paul，Commercial Technology and Innovation Office, PricewaterhouseCoopers, U.S.，2026. [arXiv:2607.08700](https://arxiv.org/abs/2607.08700)。比较 citation judge 的 F1、误放率与误拒率；讨论这些偏差对奖励设计的影响，未直接测量训练上限。`[arxiv 论文]`

<a id="ref-ruverbench2026"></a>
**[Can LLM-as-a-Judge Reliably Verify Rubrics in Agentic Scenarios?]** Yangda Peng, Yunjia Qi, Hao Peng, Haotian Xia, Guanzhong He, Xintong Shi, Richeng Xuan, Songyuanyi Lu, Yixian Liu, Zhichao Hu, Yuhong Liu, Lei Hou, Bin Xu, Juanzi Li，清华大学计算机科学与技术系 + Tencent Hunyuan，2026. [arXiv:2606.29920](https://arxiv.org/abs/2606.29920)。RuVerBench，2,458 实例；frontier 判官仍有可观噪声，同一 Judge 的多数投票收益在该设置下边际递减。`[arxiv 论文]`

<a id="ref-deepswe2026"></a>
**[DeepSWE: Measuring Frontier Coding Agents on Original, Long-Horizon Engineering Tasks]** Wenqi Huang, Charley Lee, Leonard Tng, Serena Ge，Datacurve，2026. [arXiv:2607.07946](https://arxiv.org/abs/2607.07946)。手写 verifier（接受任意正确实现）与独立 judge 分歧 1.4%，SWE-Bench Pro 继承测试分歧 32.4%。`[arxiv 论文]`

<a id="ref-seva2026"></a>
**[SEVA: Self-Evolving Verification Agent with Process Reward for Fact Attribution]** Aojie Yuan, Yi Nian, Haiyue Zhang, Zijian Su, Yue Zhao，University of Southern California + University of Michigan，2026（ICML 2026 Workshop on Trustworthy AI for Good）. [arXiv:2606.29713](https://arxiv.org/abs/2606.29713)。结构化事实核验与过程奖励；同时报告自我演化后的跨基准性能取舍。`[arxiv 论文]`

<a id="ref-hsp2026"></a>
**[Hallucination Self-Play: Bootstrapping Reinforced Detector via Evolved Generator]** Shiping Yang, Shining Liang, Weihao Liu, Wenbiao Ding, Linjun Shou, Lu Cheng, Angel X. Chang，Simon Fraser University + Microsoft + University of Illinois at Chicago，2026（COLM 2026）. [arXiv:2607.07993](https://arxiv.org/abs/2607.07993)。detector 与 generator 同基座共进化，小模型迭代后匹敌更大系统，不构成普适自我改进上限的证明。`[arxiv 论文]`

<a id="ref-manyvoices2026"></a>
**[Many Voices, One Reward: Multi-Role Rubric Generation for LLM Judging and Reward Modeling]** Dazhi Fu, Jiuding Yang, Yiwen Guo, Jicong Fan，香港中文大学（深圳）+ Tencent，2026. [arXiv:2607.01830](https://arxiv.org/abs/2607.01830)。多角色 rubric 生成补单判官的维度盲区，用作 reward 时提升开放式生成的 RL 质量。`[arxiv 论文]`

<a id="ref-agentlocate2026"></a>
**[Who Broke the System? Failure Localization in LLM-Based Multi-Agent Systems]** Yufei Xia, Anjun Gao, Yueyang Quan, Zhuqing Liu, Minghong Fang，University of Louisville + University of North Texas，2026（COLM 2026）. [arXiv:2607.07989](https://arxiv.org/abs/2607.07989)。AgentLocate，LLM 判官 + 多独立评估者置信度感知聚合 + 轻量微调，结论限于多 Agent 故障定位任务。`[arxiv 论文]`
