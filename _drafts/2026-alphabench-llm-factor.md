# AlphaBench：LLM 能否判断因子的回测表现

<!-- domain: hf-alpha-factor -->
<!-- edition_date: 2026-06-11 -->
<!-- revised_date: 2026-09-06 -->
<!-- revision_note: 补充官方论文入口，区分二手数据与一手框架说明，修正 Ref 算子的未来数据依赖判断。 -->

LLM 能生成因子公式，不等于能仅凭公式文本判断它的回测表现。[AlphaBench](#ref-alphabench) 将公式化 alpha 因子挖掘分成生成、评估和搜索三部分，使用 CSI300 数据与 [Qlib](#ref-qlib) 回测；本文重点看模型对因子回测表现的判断：零样本预测是否可靠，成对选择微调带来什么改善。这里的表现主要指 IC、RankIC 等衡量因子与后续收益相关性的指标。

本稿所引结果显示，零样本判别在模型和市场之间并不稳定，成对选择 SFT 则改善了所测配置。分类准确率回答的是模型能否判断因子相对表现，不等于因子投入实盘后的收益。

> 来源范围：三类任务的定义已对照 [AlphaBench 官方项目页](https://alphabench.cc/)，Reference 补有其 ICLR 2026 论文入口。下文具体实验数字仍据 [QuantML 的公开解读](#ref-alphabench-explainer) 转述，尚未逐表核验；工程建议与实验结果分开表述。

## 三个维度怎么测

据 [QuantML 解读](#ref-alphabench-explainer)，AlphaBench 将因子挖掘分成三个部分：

1. **因子生成**：Text2Alpha（自然语言→DSL 公式，84 Easy / 106 Medium / 121 Hard）+ 定向挖掘（给技术主题如波动率突破，8 大类 90 细分自主发挥）。
2. **因子评估**：Factor Ranking + Scoring，再分出两个原子任务，即 Signal Classification（有效信号 vs 噪声）、Pairwise Selection（两个公式二选一谁 RankIC 更优）。
3. **因子搜索**：CoE（经验链）/ ToT（思维树）/ EA（进化算法，LLM 当突变 + 交叉算子）。

解读介绍了以下质量过滤条件：算子嵌套 ≤5 层、Qlib 算子合法性与参数个数校验、单因子两周计算 ≤30s、NaN ≤1%；涉及未来数据的因子标为 Noise 并给最低分。这里应检查表达式的数据依赖，不能按 `Ref` 名称直接拦截：按 [Qlib 的定义](#ref-qlib)，`Ref(feature, N)` 在 `N > 0` 时读取历史滞后值，`N < 0` 时才读取未来值。

<a id="核心发现-零样本判别力≈掷硬币"></a>

## 零样本因子评估跨市场不稳定

[公开解读](#ref-alphabench-explainer) 列出的零样本结果包括：DeepSeek-V3 的信号 / 噪声分类准确率为 0.46，成对选择为 0.48；GPT-5 的成对选择在 CSI300 为 0.64，在 SP500 为 0.52。这些配置的结果跨市场差异明显，不能据此承诺模型能稳定判断因子的回测表现，也不足以断言所有 LLM 都没有判别能力。

解读将失效归因于输入只包含公式文本，缺少调仓频率、信息滞后、平滑策略和市场环境等执行信息。这个解释提示了需要补充的变量，但本稿没有可核验的数学证明，不能把它写成“纯公式推断必然欠定”的定理。解读还报告，所测 CoT 配置在评分排名任务中降低了 NDCG@K；是否由额外方差造成，仍需原实验支持。

<a id="但成对选择-pairwise-sft-效果极强"></a>

## 成对选择微调改善了所测配置

公开解读报告了两种微调任务的不同结果：

| SFT 任务 | 结果 |
|----------|------|
| 噪声二分类微调 | 解读报告其过拟合特定市场噪声模式，未得到预期泛化 |
| 成对选择微调 | GPT-4.1-Mini 在 CSI300 上 0.44→0.83（CoT 0.86），且 CSI300 微调直接评 SP500 仍保 0.64 |

`[本文归纳]` 这组结果支持在所测配置中尝试成对微调，但没有直接证明模型学到了哪些可迁移特征。算子单调性、窗口交互或分母防零等因素，可以作为后续消融的候选解释，不能当作已确认的泛化原因。

公开解读另外报告：在其搜索实验中，EA 总体表现较好，Gemini-2.5-Flash / GPT-4.1-Mini 的成本效益较高，温度 0.75 优于所比较的高温设置；温度 1.5 增加了不合规公式和搜索成本。这些取值是该实验的结果，不是跨任务通用配置。

公开解读列出的生成失败还包括：Word Salad（长 CoT + 高温→输出乱码）；代码专用模型（Qwen2.5-Coder、CodeLlama-70B）在 FAFM 上无优势；Hard 难度集上 Accuracy 普遍大幅下降（GPT-5 0.99→0.10）。

## 落地建议

[公开解读](#ref-alphabench-explainer)提出的工程建议包括：

1. **LLM 零样本过滤不作为主路径**：硬规则交给 Python AST，或把 LLM 微调成 pairwise 比较器，真实性能交回 Qlib / 自研回测做最终约束。
2. **SFT 输入用 AST / 算子图结构化 JSON**，并补执行元数据（调仓频率 / lag / 板块 / NaN 处理），补充公式文本中缺失的执行条件。
3. **构建对比度高的 pairwise 训练集**：将确定 Noise 与确定 Signal 配对。
4. **EA crossover 需要代码层检查表达式**：限制嵌套深度，并检查包括 `Ref` 参数方向在内的未来数据依赖；prompt 约束仅作辅助。

`[本文归纳]` LLM 适合充当变异 / 杂交算子的候选生成器，回测承担最终约束。这是当前较稳妥的 LLM 量化因子挖掘路径：LLM 负责生成候选多样性，成对微调模型可以辅助筛选，对因子表现的判断仍需通过实际回测核验。

## Reference

<a id="ref-alphabench"></a>
**[AlphaBench: Benchmarking Large Language Models in Formulaic Alpha Factor Mining]** Haochen Luo et al.，ICLR 2026。[论文](https://openreview.net/forum?id=d97Q8r7ZKZ) · [官方项目页](https://alphabench.cc/)。项目页确认生成、评估与搜索三类任务以及 Qlib 回测框架；本文具体数字仍经下列公开解读引用，未逐表复核论文。`[论文入口 / 官方项目说明]`

<a id="ref-qlib"></a>
**[Qlib: An AI-oriented Quantitative Investment Platform]** Microsoft，Yang et al. 2020. [arXiv:2009.11189](https://arxiv.org/abs/2009.11189) · [Ref 官方 API 定义](https://qlib.readthedocs.io/en/stable/reference/api.html#qlib.data.ops.Ref)。AlphaBench 使用其回测框架；本文的历史滞后与未来引用区分已核对官方 API。`[论文 / 官方文档]`

<a id="ref-alphabench-explainer"></a>
**[哪款大模型更适合因子挖掘？]** QuantML，知乎专栏，2026. [zhuanlan.zhihu.com/p/2042339790650077676](https://zhuanlan.zhihu.com/p/2042339790650077676)。本文对 AlphaBench 各项数据与落地建议的解读来自这篇公开解读。`[公开解读]`
