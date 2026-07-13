# 用 OPD 给领域后训练模型继续叠加能力：组件已有先例，组合仍待验证

<!-- domain: agentic-rl -->

`[tech report]` [Thinking Machines Lab](#ref-tml)（2025）以完成 post-training（后训练）的 Qwen3-8B 为学生，先通过 midtrain 注入一批新知识，再让注入前的自身作为 teacher，进行 on-policy distillation 以恢复退化的 instruction following。`[论文]` [CaMOPD](#ref-camopd)（快手，2026）让 post-trained 的领域模型同时担任学生和 domain teacher，并以其谱系上的通用旧版担任 general teacher；两个 teacher 按 prompt 分槽路由。`[论文]` [MOPD](#ref-mopd)（北大 + 小米，2026）是公开多 teacher on-policy distillation 中目前最强的结果：学生从通用 SFT checkpoint 初始化，多个领域 RL expert 按域路由充当 teacher，一次训练整合全部领域能力，并给出了第二轮迭代的做法。

三者都在做「把能力蒸进一个模型」，但工程中更常见的情形是：**已有一个先经通用后训练、再经领域后训练的模型（业务模型的第 N 版），现要为它增量加入一项新能力（新领域知识、新工具、新任务），后续还会有第 N+1 轮。学生起点应是这个领域特化 checkpoint 本身，还是回到通用对齐模型，将旧业务能力和新能力重新合入？防遗忘要守的也不止一层：既要守领域对齐，也要守更基础的通用能力。** 对 2016 年至今的相关文献逐条核验到一手源（其中有两条常见推断经核实并不成立，正文分别指出），结论可归纳为一句需严格限定范围的判断：

> **每个组件均有直接文献支持，完整组合尚无单篇论文验证；最接近的三个先例各差至少一个维度。**

`[本文归纳]` 风险集中在组件之间的交互，这正是现有文献的空白。讨论范围限于「学生起点范式 + 防遗忘设计」；on-policy distillation 机制本身（on-policy 数据在抗遗忘中所起的作用、KL 几何、high-probability overlap window）属于另一个正交层面，见姊妹篇《[OPD：on-policy 数据是抗遗忘的真正承担者](../on-policy-distillation/)》。

> 正文每条 claim 均标注 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

## 问题的构成：一个学生起点轴，一个防遗忘轴

这个「给领域模型继续叠加能力」的工程问题可分为两个正交的设计轴。

**第一个轴：学生起点取领域后训练 checkpoint，还是回到通用后训练 checkpoint。** 两个候选都是 post-trained 模型：在已领域特化的 checkpoint 上继续增量训练，或者回到它的通用对齐祖先，将旧业务能力和新能力重新合入。on-policy 蒸馏以学生具备基本生成能力为前提，因此裸基座不在这条轴上（见下节的边界注记）。这个轴决定第 N+1 轮采用「增量叠加」还是「全量重新整合」，两端的成本结构和遗忘风险完全不同。

**第二个轴：防遗忘靠什么。** 增量训练会将权重推离原分布、削弱旧能力（catastrophic forgetting），需要用某种机制维持其在原有能力分布附近。一种常见手法是保留模型自身的冻结旧版本，让它在训练中充当 teacher。下文将这套手法称为**自蒸馏锚**（self-distillation anchor）：锚是停止更新的旧版自身，蒸馏是让当前模型与其对齐。文献里没有统一叫法，这一名称仅用于本文讨论。锚可以是冻结旧 checkpoint、学生参数的指数滑动平均（EMA），或谱系上更早的祖先模型；当学生已经领域特化时，需要保留的对象可能不止一个，领域对齐和通用能力可能需要分别设置锚（后文「守成槽」一节）。

这两个轴的组合中，最缺乏直接证据的一格是「领域特化起点 × 冻结自身守成」；在此基础上再加上任务所需的外部 teacher 注入，便是本文的**目标组合**。下文从证据最扎实的部分谈到最稀薄的部分。

## 主轴：领域点续叠与通用点重合入，文献没有正面对比

`[本文归纳]` **已检索文献中，尚无工作对「面对同一新能力，在领域特化 checkpoint 上续叠，或回到通用对齐点重新合入」作受控对比**：效果、成本与遗忘三轴均无直接证据。目前只有两侧的单侧先例与结构近似证据。

**续叠一侧：多轮在同一演化 checkpoint 上添加能力，2025-2026 已被反复验证。** `[论文]` [Shenfeld et al. 2026](#ref-shenfeld) 在同一个累积 checkpoint 上链式叠加三项技能（Tool Use → Science → Medical），采用自蒸馏形态，保留既有技能与预存通用能力；第 2、3 轮均从已叠加能力的 checkpoint 继续训练。`[论文]` [RFT-continual](#ref-rftcl) 在严格顺序的任务流上训练 7 轮，RFT/GRPO 保留旧知识，最终达到与联合多任务训练相当的效果（基座是视觉语言模型，提供机制证据，而非文本 LLM 的直接证据）。`[论文]` [On-Policy Replay](#ref-opr) 通过回放由当前 checkpoint 生成并经 reward 过滤的 rollout 防遗忘，`[论文]` [MoE-CL](#ref-moecl) 通过每任务 LoRA expert 做参数隔离。防遗忘手段各异，但「第 N 轮继续在演化 checkpoint 上叠加」这一形态已有先例。

**通用点一侧：多 teacher 融合路径的学生起点均为通用模型。** `[论文]` FuseLLM（ICLR 2024）主实验的目标模型是通用 base Llama-2 7B（附录包含 instruction-tuned 目标的补充实验，仍是通用模型），采用 off-policy；FuseChat（EMNLP 2025）以通用 chat 模型 OpenChat-3.5-7B 为 pivot，结合 off-policy 与参数合并；[MOPD](#ref-mopd) 的学生是通用 Stage-1 SFT checkpoint。这条路径支持「将多方能力合入通用模型」，尚未支持「将能力合入已领域特化的模型」；其中只有 MOPD 采用 on-policy，不宜将 on-policy 视为整条融合路径的共性。

**MOPD 的迭代设计介于两侧之间，也是文献中最接近「第 N 轮如何进行」的公开做法。** 它仅在第 1 轮从通用 SFT 起点整合；迭代轮的原文是：

> We propose using the post-MOPD model as a new student and repeating the procedure: retrain each per-domain teacher from this student, then perform another MOPD integration with the new teachers.

`[论文]` 迭代轮以合入后的**累积模型**为新学生，teacher 也以它为起点重新 fork；每轮均将所有领域槽全量重蒸（同一批领域的精炼，归一化分 0.937→0.986），而非单独新增一个新能力槽。`[本文归纳]` 对第 N 轮问题，MOPD 介于两极之间：起点上属于「续叠」侧（从当前累积模型继续），训练配方上属于「重整合」侧（全域槽重蒸、teacher 重训）。与目标组合相比，它尚缺守成锚：teacher 均为领域 expert，未设置冻结旧自身以守既有能力的槽，也尚未验证过每轮加入**全新**能力。

**工业先例均从通用 instruct 起步，明确以深度领域特化模型为起点的公开先例仍然缺失。** `[tech report]` [IBM Granite](#ref-granite) 在 granite-3.1-8b-instruct 上直接通过 RL 补充推理能力；Meta Llama 3.2 Vision 冻结整个 LM，仅训练视觉 adapter（[官方博客](https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/)）；DeepSeek-V2.5 合并了通用 chat 和代码特化两个 post-trained checkpoint，但没有发布合并算法的技术报告（[官方公告](https://api-docs.deepseek.com/news/news0905/)）。这些都支持「复用已 post-trained 的 checkpoint 继续添加能力」，但被复用的起点是通用 instruct 模型；「明确从业务特化 checkpoint 出发叠加新能力」的公开记录，已检索文献中尚未找到。

**成本方面的先验仅限预训练层。** `[论文]` 续训 + replay 能以较少算力匹配全量重训（[continual pretraining](#ref-cpt)，TMLR 2024；NVIDIA "Reuse, Don't Retrain" 同方向），但这些对照中的 "from scratch" 是随机初始化；主轴两端均保留对齐，成本量级不能直接外推。post-training 层「续叠与重合入」的成本对比（训练量、teacher 准备、回归评测）尚无文献。

### 边界注记：裸基座为何不在轴上

`[论文]` [GKD](#ref-gkd)（on-policy distillation 的方法学起源）将学生起点明确为前提："As opposed to a randomly initialized student, we assume access to a student that can generate sequences of adequate quality"。on-policy 蒸馏依靠学生采样的 rollout 提供训练 state，学生必须已能产出 teacher 可给出有意义反馈的样本。GKD 实验从任务级 SFT checkpoint 起步，官方实现 TRL GKDTrainer 的规范用例是 instruction-tuned 模型，[MiniLLM](#ref-minillm) 也先 SFT 再蒸馏。`[tech report]` [Qwen3](#ref-qwen3) 的 strong-to-weak distillation 属于另一类任务：从 base 模型蒸出小模型，整条管线**替代**四阶段 post-training（能力压缩，非增量合入）；进入 on-policy 阶段的学生也已是 off-policy 蒸馏冷启动后的 checkpoint。它 §4.7 那句「on-policy distillation 优于直接 RL、约 1/10 GPU hours」比较的是同一 off-policy 起点下 RL 与 OPD 的差别，与学生起点选择无关，因而不能作为本文主轴中学生起点选择的依据。

## 自蒸馏锚：从离线软标签到 on-policy

用「冻结的旧自身」作为 teacher 防遗忘，这一组件的文献先例可追溯至深度学习早期，演进链也较完整。

`[论文]` [Learning without Forgetting](#ref-lwf)（ECCV 2016）是奠基形态：更新网络前，先记录原网络在新任务数据上对旧任务的输出，再用 knowledge distillation loss（知识蒸馏损失）让更新后的网络逼近这些输出。关键性质是「uses only new task data」：不回放旧任务数据，只将「更新前的自己」在新数据上的输出作为锚。

`[论文]` [SDFT](#ref-sdft)（ACL 2024）将这套方法应用于 LLM：学生是已对齐的 Llama-2-7b-chat，微调前的自身离线改写任务数据，形成与原始分布匹配的 distilled dataset，再以此引导微调，显式缓解 catastrophic forgetting，并保留 helpfulness 与 safety alignment。它仍是**离线**形态：数据级改写加标准 NLL，不包含学生 rollout。这里的 SDFT 指 Yang et al. 的 ACL 2024 工作，与 Shenfeld et al. 的 2026 工作是两篇不同的论文。

`[论文]` [Shenfeld et al. 2026](#ref-shenfeld) 将自蒸馏锚扩展到 on-policy：学生从 post-trained 模型初始化（主实验 Qwen2.5-7B-Instruct），严格采用 on-policy（只从学生策略采样、最小化学生与 teacher 分布的 reverse KL），并将 on-policy self-distillation 定位为 "a practical path to continual learning from demonstrations"。

| 工作 | 年份 | 自蒸馏锚形态 | 采样 | 领域 |
|---|---|---|---|---|
| LwF | 2016 | 冻结旧网络软标签 | 离线固定输入 | CNN 视觉分类 |
| SDFT (Yang et al.) | 2024 | 微调前自身改写数据 | 离线 | LLM 对齐保持 |
| Shenfeld et al. | 2026 | 学生参数 EMA | on-policy rollout | LLM continual learning |

`[本文归纳]` 「冻结旧自身防遗忘」从 2016 到 2026 由离线软标签发展到 on-policy reverse KL，各阶段均有文献支持，组件层面的先验充分。

## 三个最接近的先例，各差至少一个维度

「领域特化学生 + 自蒸馏锚守既有能力 + 外部 teacher 注入新能力」这一目标组合尚无单篇论文完整覆盖，但有三个先例从不同侧面接近它。

**先例一，顺序式、同方向：`[tech report]` [Thinking Machines Lab](#ref-tml)。** 以 post-trained 的 Qwen3-8B 为学生，先通过 midtrain 注入一批内部文档知识（这批文档上的 QA 准确率 18%→36%，代价 IF-eval 85%→79%），再让 midtrain 前的自身作为 teacher 进行 on-policy distillation，IF-eval 恢复到 83%、该 QA 进一步升至 41%。博客将「用模型更早版本作为 teacher，重新调用微调中丢失的能力」作为 continual learning 机制，建议在「新数据微调 ↔ 蒸馏恢复」之间交替。HuggingFaceH4 用 TRL GKDTrainer 复现，数字接近（IFEval 83.4→79.5→82.8）。与目标组合的差异在于：注入依靠 midtrain 而非蒸馏，恢复是事后的独立阶段，并非训练中常驻的多槽设计；学生也是通用 post-trained，而非领域特化模型。

**先例二，并发式、反方向：`[论文]` [CaMOPD](#ref-camopd)。** 唯一以**领域特化模型**为学生起点的先例：学生自身的冻结副本守一个 prompt 槽（保留新获得的领域能力），谱系上的通用旧版作为 general teacher 守另一槽（恢复因特化而削弱的通用能力）；按 prompt 槽路由，学生自采 rollout，并接受 token 级 teacher log-prob 监督。原文直接说明这一结构：

> the original open-source model serves as the general teacher, and the specialized model serves as both the student initialization and the domain teacher.

差异在于方向相反：它冻结自身守的是**新**能力、通用旧版负责**恢复**旧能力；目标组合中冻结自身守的是**旧**能力、外部 teacher 负责**注入**新能力。

**先例三，迭代式、无守成锚：`[论文]` [MOPD](#ref-mopd)。** 它是多 teacher 按域路由的 on-policy 蒸馏当前最佳公开结果，迭代轮从累积模型继续训练（见主轴一节）。差异在于没有守成锚（全部 teacher 都是领域 expert），且迭代只验证了同域精炼，尚未验证每轮加入全新能力。

| 维度 | TML | CaMOPD | MOPD | 目标组合 |
|---|---|---|---|---|
| 学生起点 | 通用 post-trained | 领域特化 ✓ | 第 1 轮通用 SFT；迭代轮累积模型 | 领域特化 |
| 新能力注入 | midtrain（非蒸馏） | domain teacher 蒸馏（守新） | 领域 expert teacher 蒸馏 | 外部 teacher 蒸馏 |
| 冻结自身当锚 | ✓（守旧，事后恢复） | ✓（守新） | 无 | ✓（守旧，常驻） |
| 多槽 teacher 路由 | 否（事后单阶段） | ✓ | ✓（按域） | ✓ |
| 多轮迭代 | 单轮（建议交替） | 单轮 | ✓（2 遍、同域精炼） | 每轮加新能力 |

`[本文归纳]` 表中每个维度均有先例，但没有一列与最右列完全对应；尚待实验回答的是多槽并发时的组件交互，包括注入与守成是否相互干扰、多 teacher 信号是否冲突。CaMOPD 标题中的 Counteraction-Aware 正是冲突处理机制，本文未展开其细节。

## 守成槽：锚定什么、设置几个、采用何种形态

学生已经领域特化时，「守成」要保留两层能力：领域/业务对齐，以及更基础的通用能力。这引出三个设计问题：锚的形态、锚的数量和选择判据。

**形态应按槽位角色确定，而非全局统一。** `[论文]` [Shenfeld et al. 2026](#ref-shenfeld) 的消融结论是冻结 teacher 虽然稳定，效果却持续较差，EMA 最好；TML 的成功案例用的恰是冻结旧版。两个结论可以并存，因为两个 teacher 对应的槽位角色不同：

| 槽位角色 | teacher 要不要跟踪学生进度 | 该用的形态 | 证据 |
|---|---|---|---|
| 学新能力槽 | 要（teacher 得带着学生往前） | 跟踪型：EMA / 当前学生 | Shenfeld 2026 消融：frozen "consistently underperforms" |
| 守既有能力槽 | 不要（要的正是不动的回拉目标） | 冻结锚：冻结旧版 / 谱系祖先 | TML 冻结旧版恢复成功；LwF / SDFT 冻结自身守成 |

`[本文归纳]` 这条分工是从三篇不同研究场景的工作归纳出的推论，没有单篇在同一个守成槽上对比过冻结与 EMA；它是可证伪的设计假设，尚非定论。

**双槽守成只有一个先例，且属于跨模态工作。** `[论文]` [MulKI](#ref-mulki)（AAAI 2025）在持续学习中同时保留两个蒸馏 teacher，并自适应地逐样本加权：冻结的原始模型守零样本泛化（通用祖先），上一轮模型守累积的任务知识，每轮均注入新任务。它是「一槽守通用祖先 + 一槽守适配后的自身」的直接结构先例；但它是 CLIP/视觉语言模型上的图像分类工作。**在已检索的 LLM post-training 文献中，尚未找到**将「特化自身」和「通用祖先」作为两个槽分别守住的工作。

**判据：通用能力能否保留，关键看 KL 距离。** 有一种流行说法是「RFT 保护通用能力、SFT 摧毁通用能力，范式决定存活」，但它并不成立：`[论文]` [RL's Razor](#ref-rlrazor)（MIT，2025）系统测试了权重变化范数、稀疏度、梯度秩和 RL-vs-SFT 范式，发现对 base 模型的 KL 距离才是决定因素，其他指标与训练范式均非决定因素。RFT 抗遗忘的经验现象本身有多篇独立佐证，其机制是「行为已正确的样本不产生参数更新」的隐式选择性更新；注入全新能力时必须发生大量更新，这一机制无法直接覆盖。`[本文归纳]` 对守成设计，可控变量是「对想守住的参考模型的 KL 距离」：不同的锚对应不同的守成目标，训练范式本身不会自动提供保护。

**多锚既有理论构造，也有尚未核验的负向实证线索。** 以下线索仅经检索定位、本文未及核实，引用前请自行查证一手源：多参考模型 KL 正则 RLHF 的精确解与样本复杂度（arXiv 2502.01203）给出了双锚构造的数学形式；MRPO（arXiv 2512.10040）的实证结果是单参考 DPO 在 7 个参考中 6 个情况下优于所有多参考变体，多锚的理论吸引力与实际收益之间仍有未解的落差。另有金融领域 CPT 专家与通用祖先做参数合并、找回特化中丢失的通用知识的报告（arXiv 2511.02451），提示「参数算术恢复通用性」可能是守成之外的第三条路径。

## 边界与开放问题

`[本文归纳]` 这套做法的文献边界如下。

**两个明确的空白（已检索的阴性结果）。** 第一，主轴正面对比：没有工作对「同一新能力，领域特化点续叠与通用点重合入」作受控对比，效果、成本、遗忘任一轴均无直接证据。第二，干净的单侧先例：工业界复用 post-trained checkpoint 的公开案例（IBM Granite 等）起点均为通用 instruct，「明确从业务特化 checkpoint 出发、用外部 teacher OPD 注入新能力」尚无公开记录。

**三个待验证的组合缺口。** 第一，多轮 on-policy 蒸馏且每轮加入**全新**能力，尚未见先例（Shenfeld 链式三轮是自蒸馏形态，MOPD 迭代是同域精炼）。第二，LLM 上的双槽守成（一槽守业务对齐、一槽守通用祖先）尚无先例，唯一结构先例 MulKI 是跨模态的。第三，守成槽上冻结、EMA 与谱系祖先三种锚形态缺少直接对比。

**一批未核验线索。** 上节列出的多参考 KL 理论、MRPO 负结果、参数合并恢复通用性，以及 MergeBench（arXiv 2505.10833，领域特化模型合回一体的系统评测）均只经检索定位、本文未及核实，引用前请自行查证。

`[本文归纳]` 多轮续叠已有 Shenfeld / RFT-continual / MOPD 迭代等先例，成本先验也偏向复用；但「业务特化学生 + 外部 teacher 注入 + 冻结自身守成」这一精确组合尚无公开先例，风险集中在组件交互。文献中最接近、可供借鉴的第 N 轮形态是 MOPD 的迭代设计（累积模型为学生、teacher 从它重新 fork、全域槽重蒸），它缺少守成锚这一维；将 CaMOPD 的双槽路由反向设置以补上这一维，便构成本文目标组合的最小实现路径。这一步尚无公开验证，需要通过实验补足。

## Reference

<a id="ref-tml"></a>
**[On-Policy Distillation]** Thinking Machines Lab 博客，2025-10。[thinkingmachines.ai/blog/on-policy-distillation](https://thinkingmachines.ai/blog/on-policy-distillation/)。其中的 personalization/continual-learning 实验采用 post-trained Qwen3-8B 学生 + midtrain 注入 + 冻结旧自身当 teacher 恢复能力；HuggingFaceH4 用 TRL GKDTrainer 复现。`[工程博客]`

<a id="ref-camopd"></a>
**[CaMOPD: Counteraction-Aware Multi-Teacher On-Policy Distillation]** 快手（Kuaishou），2026-05。[arXiv:2605.27115](https://arxiv.org/pdf/2605.27115)。唯一以领域特化模型为学生起点的先例：冻结特化自身守新能力槽、谱系通用旧版守通用槽、按 prompt 槽路由。单一近期 preprint，评审状态未知。`[arxiv 论文]`

<a id="ref-mopd"></a>
**[MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training]** Ma et al.，北大 + 小米 + 港大 + 人大，2026-06。[arXiv:2606.30406](https://arxiv.org/abs/2606.30406)。学生为通用 Stage-1 SFT；各领域 RL expert（均由同一 Stage-1 fork 而来）按域路由担任 teacher；学生自采 rollout 上 reverse-KL；迭代轮以 post-MOPD 累积模型为新学生、teacher 重训（0.937→0.986，同域精炼）。MiMo-V2-Flash 部署。近期 preprint。`[arxiv 论文]`

<a id="ref-shenfeld"></a>
**[Self-Distillation Enables Continual Learning]** Idan Shenfeld, Mehul Damani, Jonas Hübotter, Pulkit Agrawal，MIT + ETH Zurich，2026-01。[arXiv:2601.19897](https://arxiv.org/abs/2601.19897)。将 on-policy self-distillation 定位为 continual learning 路径；同一累积 checkpoint 链式叠加 Tool Use → Science → Medical 三技能；teacher 形态消融（EMA 最好、frozen 的表现持续较差）。与 ACL 2024 SDFT 为不同论文。`[arxiv 论文]`

<a id="ref-rftcl"></a>
**[Reinforcement Fine-Tuning Naturally Mitigates Forgetting in Continual Post-Training]** Lai et al.，2025-07。[arXiv:2507.05386](https://arxiv.org/abs/2507.05386)。7 轮顺序任务流中，RFT/GRPO 保留旧知识，效果与联合多任务训练相当；机制是 reward 方差门控的隐式选择性更新。基座 Qwen2.5-VL-7B-Instruct（VLM）。该文可支持 RFT/GRPO 保留旧知识的事实，不宜延伸为「范式决定通用层存活」。`[arxiv 论文]`

<a id="ref-opr"></a>
**[On-Policy Replay]** 2026-05。[arXiv:2605.29495](https://arxiv.org/abs/2605.29495)。多轮 continual SFT，回放使用由当前 checkpoint 生成并经 reward 过滤的 rollout；无 teacher、无蒸馏损失。`[arxiv 论文]`

<a id="ref-moecl"></a>
**[MoE-CL]** WWW 2026。[arXiv:2509.18133](https://arxiv.org/abs/2509.18133)。为每项任务设置 LoRA expert，借参数隔离进行持续指令微调，含工业数据集验证。`[arxiv 论文]`

<a id="ref-mulki"></a>
**[MulKI: Multi-Stage Knowledge Integration of Vision-Language Models for Continual Learning]** AAAI 2025。[arXiv:2411.06764](https://arxiv.org/abs/2411.06764)。双槽守成的唯一先例：冻结原始模型守通用祖先（零样本泛化），上一轮模型守累积知识，并自适应地逐样本加权，方向为注入新任务。CLIP/VLM，非 LLM。`[arxiv 论文]`

<a id="ref-rlrazor"></a>
**[RL's Razor]** Shenfeld et al.，MIT，2025。[arXiv:2509.04259](https://arxiv.org/abs/2509.04259)。系统测试后发现，对 base 模型的 KL 距离决定遗忘程度，范式、权重范数、稀疏度与梯度秩均非决定因素。与本文 Shenfeld 2026 为同作者的不同论文。`[arxiv 论文]`

<a id="ref-granite"></a>
**[Bringing reasoning to Granite]** IBM，2025。[ibm.com/new/announcements/bringing-reasoning-to-granite](https://www.ibm.com/new/announcements/bringing-reasoning-to-granite)。以 granite-3.1-8b-instruct 为起点，直接通过 RL 补充推理能力（通用 instruct 起点的复用先例）。`[tech report]`

<a id="ref-gkd"></a>
**[On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes (GKD)]** Rishabh Agarwal, Nino Vieillard et al.，Google DeepMind，ICLR 2024（arXiv 2023-06）。[arXiv:2306.13649](https://arxiv.org/abs/2306.13649)。on-policy distillation 的方法学起源，明确了「学生起点须具备基本能力」这一前提；官方实现 TRL GKDTrainer（学生 Qwen2-0.5B-Instruct）。`[arxiv 论文 / 同行评审]`

<a id="ref-minillm"></a>
**[MiniLLM: Knowledge Distillation of Large Language Models]** Yuxian Gu, Li Dong et al.，清华 + 微软，ICLR 2024（arXiv 2023-06）。[arXiv:2306.08543](https://arxiv.org/abs/2306.08543)。采用 reverse-KL policy-gradient 蒸馏，学生起点为 SFT 后的 checkpoint；防退化使用 pre-training LM loss（另一条路径，非自蒸馏锚）。`[arxiv 论文 / 同行评审]`

<a id="ref-qwen3"></a>
**[Qwen3 Technical Report]** Qwen Team（阿里），2025。[arXiv:2505.09388](https://arxiv.org/pdf/2505.09388)。strong-to-weak distillation：base 学生、整条管线替代四阶段 post-training（能力压缩，非增量合入）；§4.7 RL 与 OPD 为同 off-policy 起点对比，不能作为学生起点选择的依据。`[tech report]`

<a id="ref-lwf"></a>
**[Learning without Forgetting]** Zhizhong Li, Derek Hoiem，UIUC，ECCV 2016 / TPAMI 2017。[arXiv:1606.09282](https://arxiv.org/abs/1606.09282)。自蒸馏锚的奠基先验：冻结原网络软标签、只用新任务数据保留旧能力。`[arxiv 论文 / 同行评审]`

<a id="ref-sdft"></a>
**[Self-Distillation Bridges Distribution Gap in Language Model Fine-Tuning (SDFT)]** Zhaorui Yang et al.，浙江大学 + Sea AI Lab，ACL 2024。[aclanthology 2024.acl-long.58](https://aclanthology.org/2024.acl-long.58/)，repo sail-sg/sdft。微调前自身离线改写数据、缓解 catastrophic forgetting；离线形态（无 on-policy）。与 Shenfeld 2026 同缩写不同篇。`[arxiv 论文 / 同行评审]`

<a id="ref-cpt"></a>
**[Simple and Scalable Strategies to Continually Pre-train Large Language Models]** TMLR 2024。[arXiv:2403.08763](https://arxiv.org/abs/2403.08763)。LR re-warm + re-decay + replay 以全量重训的一小部分算力达到相当效果（预训练层、对照臂为随机初始化）；NVIDIA "Reuse, Don't Retrain"（[arXiv:2407.07263](https://arxiv.org/abs/2407.07263)）提供同方向的续训配方。`[arxiv 论文 / 同行评审]`

**未核验线索**（仅经检索定位、本文未及核实，引用前请查证一手源）：多参考 KL-RLHF 精确解 [arXiv:2502.01203](https://arxiv.org/abs/2502.01203)；MRPO 多参考 DPO 及其单参考更优的负结果 [arXiv:2512.10040](https://arxiv.org/abs/2512.10040)；MergeBench 领域模型合并评测 [arXiv:2505.10833](https://arxiv.org/abs/2505.10833)；金融 CPT 专家与通用祖先合并找回通用知识 [arXiv:2511.02451](https://arxiv.org/abs/2511.02451)；风险门控 KL 锚 [arXiv:2602.17546](https://arxiv.org/abs/2602.17546)。
