# 工具调用错误的归因顺序：先定位监督缺口，再选择 SFT 或 RL
<!-- domain: agentic-rl -->
<!-- edition_date: 2026-09-20 -->

工具 Agent 出现调用错误时，复盘往往直接转向训练方法选择：这种错误该靠 SFT 修，还是直接上 RL。这个问题往往问得太早。同一表述下的“工具调用不准”至少对应五类失败位置：训练数据没有覆盖正确动作；模型没有学会工具调用之后环境会怎样变化；终局 reward 没有约束“这一步该不该调用”；局部 reward 把 credit 分配到错误的结构层级；RL 训练过程中调用结构本身已经崩溃。

这些失败表面上同名，需要的训练信号却彼此不同。对示范缺失的问题增加 reward、对结构崩溃的问题扩充数据、对不必要调用仅考核终局成功，都可能提升训练指标，却没有触及真正的失败点。

`[本文归纳]` 所以 SFT 与 RL 不是第一层选择，首先应定位当前缺的是哪一种监督：合格示范、动作后果、工具必要性、调用内部的层级 credit，还是输出结构约束。方法选择应跟随缺口定位，而不是反过来用方法名解释所有错误。文中的[来源标签](../../meta/#claim-tags)只表示材料角色，不替代实验边界。

## SFT 与 RL 的相对排名取决于数据分布与评测 slice

回答这个问题需要一次尽量受控的对照。`[论文]` [SFT or RL for Tool-Calling Agents?](#ref-laskar2026)（Dialpad，Laskar et al. 2026）做了一组对齐数据预算的比较：三份公开 function-calling 语料及其均匀混合，六个 Qwen3 规模（0.6B–32B），比较 LoRA SFT、直接 GRPO 与先 SFT 后 GRPO 的两阶段方案。所有设置统一 prompt 与 tool serialization、移除近重复；SFT→GRPO 还把同一份训练集对半拆开，使两个阶段不重复使用同一条数据。

结果不支持“RL 更强”的单一结论。在 18 个 in-distribution 设置中，LoRA SFT 有 15 个最强，而且 18 个都高于 zero-shot。换到 cross-dataset transfer，GRPO 在 54 个设置中赢 29 个、SFT 赢 19 个，但 GRPO 对 SFT 的平均优势不足 1 point；SFT→GRPO 只赢 6 个。数据侧的影响同样大：训练语料的选择可以让 in-distribution accuracy 相差最多 55 points，均匀混合在专门化与 transfer 之间是更稳定的默认项。

这组结果的价值在于分离方法效应与数据效应，而非证明 SFT 普遍更优。它的边界也写得很清楚：reward 与 exact-match evaluation 使用同一条判分规则，比较没有按 compute 归一，全部模型来自 Qwen3 一家族，任务主要是 gold tool call 的静态匹配。如果实际问题是多步执行、环境恢复或长程终局，它没有证明 SFT 仍然占优。

`[本文归纳]` 因此，只写“训练方法”而不写训练集分布和评测 slice，实验记录是不完整的。一次 SFT / RL 对比至少要说明四件事：训练数据里 call / no-call、单轮 / 多轮和参数结构的构成；测试是否换了工具或任务分布；reward 与 eval 是否使用同一条规则；比较是否包含真实执行后果。

## SFT 的预测目标决定后续 RL 的初始化

数据分布对齐之后，“SFT”本身仍不是一个确定的信号。标准 Agent 轨迹同时记录 agent action 与 environment observation，但常见 SFT 只对模型自己生成的 action token 计算 loss，工具返回仅作为下一步的上下文。`[论文]` [Don't Mask the Environment](#ref-zhang2026actobs)（University of Maryland、AWS AI Labs，Zhang et al. 2026）只改变这一点：ActObs 让同一条轨迹里的 action 与 observation 都成为预测目标，而部署时模型仍然只生成 action。

两种 checkpoint 在 SFT 结束时任务表现接近，差异进入 GRPO 之后才放大。在 Qwen3-4B 上，ActObs→GRPO 在论文报告的所有 sampling budget 都高于 ActionSFT→GRPO。8B 上，ActionSFT 的单次成功率不弱，但 ActObs 在更多次采样时能覆盖更多任务，相对 ActionSFT 的 pass@16 高 3.4 points。论文给出的解释是：预测 observation 迫使模型同时表示“这个动作会带来什么后果”，减少 action-only imitation 对单条 teacher 命令的过度收缩，为后续 on-policy exploration 保留更多可采样路径。

这不是“把所有环境文本都塞进 loss”的普遍配方。实验主要是 Terminal-Bench 2.0 与代码编辑，只覆盖 Qwen3 4B / 8B 和一个 teacher；SFT、RL、evaluation 的 context construction 与 shell session 也不完全一致。它支持的判断更窄：**同一批 trajectory，因为 supervised target 不同，可以成为不同的 RL initialization。** 所以只写“SFT 数据相同”，仍然不足以说明实验到底控制住了什么。

## RL reward 的判定层级：工具必要性与调用完整性

SFT 一侧的变量是“预测什么”，RL 一侧的变量是“reward 判到哪一层”。这一层级至少包含两个互不替代的问题。

第一个问题是工具必要性：Agent 最终答对，并不说明中间每次工具调用都有必要。`[论文]` [Spurious Tool Use](#ref-yang2026spurious)（University of Washington、UC San Diego、Stanford，Yang et al. 2026）在事实问答与数学推理任务中加入与 search / Python 相关、但与当前问题是否需要工具无关的 cue，再对同一道题构造 cue-present 与 cue-absent 两个版本。

当 search 能力已经学会、cue 又与 search 语义一致时，模型在不需要检索的数学题上额外调用 search，调用率最高增加 39.2 points。反过来，同样的数据不平衡并没有让尚未学好的 Python 工具出现同量级 shortcut。这个反差说明，shortcut 不是“数据有偏就一定出现”，而是能力已经建立之后，policy 找到的一条成本更低的表面触发路径。

论文给每一次工具决策增加了一个 necessity reward，判断当前问题是否真的需要该工具。在它的合成环境里，这个信号消除了 cue 驱动的多余调用，且未降低任务表现。边界同样要写明：核心模型是 Qwen2.5-7B-Instruct，任务来自公开 QA / math benchmark，必要性标签由 GPT-5 Nano judge 生成。`[本文归纳]` 可迁移的不是这个 judge，而是它完成的失败定位——如果终局 reward 对“答对但乱调工具”无感，继续放大终局 reward 只会进一步强化 shortcut。

第二个问题在调用内部：即使工具该调，一次调用内部也不是一组可以随意相加的字段。工具名错了，参数 key 或 value 恰好相同也没有执行意义。`[论文]` [MATCH](#ref-liu2026match)（University of the Chinese Academy of Sciences、Honor，Liu et al. 2026）把 reward 设计为一条层级 gate：tool name 正确后才开放 argument key credit，key 正确后才开放 value credit，避免错误工具名仍因参数巧合获得 credit；同时用同一 reward 的动态估计，选择当前 policy 能力边界附近的样本，并保留一部分更难案例。

在同一 4,000 条 ToolRL training set 上，MATCH 的 Qwen2.5-7B-Instruct 在 API-Bank 与 BFCL V3 上的 overall accuracy 分别为 72.19% 与 62.87%，高于论文列出的 SFT 与 RL baselines；ablation 与四个 backbone、两家族结果支持 curriculum 与 hierarchical reward 都有独立贡献。

但这仍不是完整的“工具 reward”。训练把多步轨迹拆成 single-step instance，只是把历史保留在 prompt；HTGR 依赖 reference call，未匹配的额外调用也不另罚。它适合判断 reference tool / key / value 的内部一致性，不能替代前面说的工具必要性，也不能验证开放环境的长程终局结果。

`[本文归纳]` 合起来看，工具 reward 至少要沿两条不同的轴分配：**这个工具是否该调**，以及**决定调以后，调用是否完整**。前者需要状态与任务目标，后者可以按 tool / key / value 的依赖链判断。把两者压成一个 exact-match 分数，会让“完全不该调用”和“该调用但参数错了”共享同一个修复动作。

## 训练崩溃的鉴别：能力失败与序列化结构失败

还有一类失败比 reward 错配更直接：RL 训练曲线明显下降。这也不一定意味着模型失去了工具能力。`[论文]` [Why Multi-Step Tool-Use Reinforcement Learning Collapses](#ref-hao2026)（CASIA、UCAS，Hao et al. 2026）观察到，部分 multi-turn 设置在训练后期出现 control-token 概率集中：自然语言与工具调用之间的结构边界被污染，输出最终收缩到退化的终止序列。而改变输出格式之后，部分底层能力仍能显现，说明 capability 与 serialization stability 不能合并解释。

论文比较了 SFT warm start、off-policy supervision、hint、错误轨迹和过程反思等同步或交错信号。交错监督在它的设置里更稳定，但并没有导出一个无条件配方：SFT 会在 format OOD 上明显退化，部分 SFT→RL 组合也会再次崩溃，训练数据规模受可验证工具环境限制。

`[本文归纳]` 所以训练失败至少要分两层判读。第一层看 capability：改变 serialization、约束 decoding，或者回到受控 scaffold 之后，模型是否仍能完成工具任务。第二层看 policy：能力既然还在，为什么当前 rollout 会选错、漏调或乱调。如果结构修复就能恢复表现，却把问题写成“需要更多 Agentic 数据”，修复方向就被指错了。

## 按失败位置匹配训练信号

把五篇证据放在一起，可以得到一条更实用的实验路由。这不是在统一 benchmark 上学出来的最优 selector，而是把常见工具错误与它们真正缺失的监督对齐：

| 观察到的失败 | 先核对什么 | 更接近缺失的信号 | 方法边界 |
|---|---|---|---|
| 已知 schema / 场景里不会生成正确 call | 合格示范是否覆盖，call / no-call 比例是否失衡 | demonstration 与 data mix | SFT 的 in-distribution 优势不外推真实执行 |
| 会模仿动作，却不会根据工具返回调整下一步 | trajectory 是否保留 action→observation | consequence / transition target | observation supervision 尚缺跨环境复验 |
| 最终答对，但被表面 cue 诱发多余工具 | reward 是否只看终局 | tool necessity | LLM judge 不是无噪声真值 |
| 选对工具，但参数层级 credit 混乱 | 错 tool 是否仍能拿 argument 分 | gated call integrity | reference call 不等于开放任务终局 |
| 训练后 tool tag / control token 结构破裂 | 换格式或受控 decoding 后能力是否恢复 | structural supervision | 结构稳定不等于策略正确 |

`[本文归纳]` 这张表也解释了为什么“先 SFT 冷启动，再 RL”并不自动正确。冷启动数据分布太窄，SFT 会同时拟合格式与内容；SFT target 没有保留动作后果，RL 就从一个收缩的 initialization 开始；RL reward 只看终局，policy 可能学会 shortcut；结构 token 已经失稳，训练收益甚至无法从合法调用中显现。组合方法只有在两个阶段各自承担明确、互补的信号时才有意义。

## 可复核对照的最低记录要求

训练实验不需要先建一套庞大的统一 schema，但至少要让四类事实可以分别回读：

1. **数据分布**：任务、工具、call / no-call、单轮 / 多轮、成功 / 失败和关键状态覆盖；
2. **监督目标**：哪些 token 参与 SFT loss，observation 与工具返回如何进入模型；
3. **reward attachment**：终局、工具必要性、tool / key / value、结构合法性分别由谁判；
4. **评测对象**：测已知分布复现、跨分布 transfer、真实执行终局，还是多次采样后的 task coverage。

在这些事实之上，再分别报告三个容易混在一起的工具行为：**会不会做**，即给定需要工具的任务能否完成；**该不该做**，即当前状态是否真的需要调用；**调用是否完整**，即 tool、arguments 与结构是否正确。更长 horizon 的任务成功、事实正确和安全结果仍是下一层，不能被这三个局部指标替代。

回到开头的问题，答案不再是抽象的“SFT 还是 RL”。错误来自缺少合格示范，就先修正示范质量与数据分布；模型没有表示动作后果，就调整 supervised target；终局 reward 没有覆盖工具决策，就补充 decision-level signal；局部 credit 越级，就按调用依赖关系设置 gate；serialization 已经崩溃，就先恢复结构，再判断 policy 是否真正改善。只有失败位置和训练信号对上了，SFT / RL 的比较才是在比较方法，而不是在比较两套不同的问题。

## Reference

<a id="ref-laskar2026"></a>
- **SFT or RL for Tool-Calling Agents? A Controlled Study Across Data, Method, and Scale**. Md Tahmid Rahman Laskar, Xue-Yong Fu, Shashi Bhushan TN. Dialpad Inc., 2026. [arXiv:2609.17848](https://arxiv.org/abs/2609.17848).

<a id="ref-zhang2026actobs"></a>
- **Don't Mask the Environment: Observation Supervision Changes How Agents Explore Under RL**. Juzheng Zhang, Disha Makhija, Manoj Ghuhan Arivazhagan, Vinayshekhar Bannihatti Kumar, Rashmi Gangadharaiah. University of Maryland, AWS AI Labs, 2026. [arXiv:2609.20715](https://arxiv.org/abs/2609.20715).

<a id="ref-yang2026spurious"></a>
- **Spurious Tool Use: When RL Agents Learn the Wrong Reason to Act**. Yiwei Yang et al. University of Washington, University of California San Diego, Stanford University, 2026. [arXiv:2609.16268](https://arxiv.org/abs/2609.16268).

<a id="ref-hao2026"></a>
- **Why Multi-Step Tool-Use Reinforcement Learning Collapses and How Supervisory Signals Fix It**. Yupu Hao, Zhuoran Jin, Huanxuan Liao, Kang Liu, Jun Zhao. Institute of Automation, Chinese Academy of Sciences; University of Chinese Academy of Sciences, 2026. [arXiv:2606.26027](https://arxiv.org/abs/2606.26027).

<a id="ref-liu2026match"></a>
- **MATCH: Model-Aware Tool Learning with Curriculum Scheduling and Hierarchically Gated Rewards**. Shihao Liu, Hao Yin, Lijun Liu, Zhengzong Chen, Yuanyuan Zhao, Fei Huang. University of the Chinese Academy of Sciences, Honor Device Co., Ltd, 2026. [arXiv:2609.20082](https://arxiv.org/abs/2609.20082).
