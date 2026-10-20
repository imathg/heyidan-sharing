# 换一个 Agent，任务怎样接着做
<!-- domain: claude-code-ecosystem -->
<!-- edition_date: 2026-10-18 -->

任务做到一半，需要换模型、开新会话，或者交给另一个 Agent。通常会留一段总结，或者把完整聊天记录交过去。下一位读完了，却未必知道：代码改到哪里了？哪些结论有依据？还有什么没完成？哪些操作不能再做一次？

`[本文归纳]` **交接要让下一个 Agent 从当前结果继续工作。** 为此，需要留下实际成果、结论依据、未完成事项和操作边界，再由接收方验证自己能否继续。历史记录是辅助材料，多少不是成功标准。

## 多给历史，不一定更好

`[论文]` [The Handoff Tax](#ref-ganz2026) 在 Claude 和 GPT 模型族内分别测试编程任务的中途切换。实验比较完整保留、压缩和删除执行记录，始终保留仓库改动。

从低能力模型切到高能力模型时，完整记录只能追回不到一半的质量差距，还增加了成本；减少旧记录反而更好。反过来，高能力模型完成困难推理后再降档，删掉它的记录又会损害质量。

这说明执行记录既能留下有用发现，也可能延续原来的错误思路。`[本文归纳]` 已经改好的代码应由仓库保存，关键发现应注明依据；搜索过程是否要带过去，要看它对下一步有没有帮助。

完整规格也不保证通用。`[论文]` [Specification Portability](#ref-grynets2026) 在 Oracle→PostgreSQL 迁移中发现，同一份规格给不同 Agent，结果差异很大。其中，Gemini 直接使用 Kiro 生成的规格时，SQL 语法有效率只有 2.33%。重写在该配置下有帮助，压缩却没有普遍收益；按质量与成本权衡，检索式读取是 Gemini 和 Copilot 各自最优策略集合中唯一共同的策略。

这只是数据库迁移中的结果，但足以提醒：**文档写得完整，不等于另一个 Agent 能用好。**

## 留下成果，也留下结论的依据

接收方首先需要知道工作现在是什么样，而不是只知道上一位做过什么。

`[论文]` [StateHarness](#ref-zou2026) 持续记录当前问题、假设、发现、决定、相关文件和未完成工作，配合运行提示与独立诊断会话。它在三个编程评测中改善了多项指标。例如，ChainSWE 的修复率从 35.1% 升到 39.5%，遗留问题从 60 项降到 43 项；但原本通过、后来失败的回归也增加了。记录状态有助于继续工作，不能替代回归检查，收益也不能归因于某一个字段。

总结还会带来另一种风险：把猜测写得像事实。`[论文]` [Prune the Summary, Not the History](#ref-min2026) 分析一种常用压缩器时发现，83% 的失败运行可追溯到执行了某条总结内容，其中多数没有环境输出支持。检查条目能否回到环境输出或先前总结、删除无来源条目后，两个 Agent 模型在 AppWorld 和 OfficeBench 上的跨运行可靠性提高了 2.1%–8.9%，未增加 Agent 的 token 用量。

`[本文归纳]` 因此，交接时要分清“观察到了什么”和“据此推测了什么”。比如，“测试已通过”应能回查测试结果；“问题可能出在缓存”可以保留，但要标为待验证假设。总结能帮助定位依据，不能替依据作证。

## 接收方怎么读，也会影响结果

相同材料，换一种呈现方式，Agent 可能就不会用了。

`[论文]` 一项[状态表示实验](#ref-nie2026)在确定性工具任务中发现：经过精简状态训练的 1.7B 模型，在 16 步流程测试中，三个训练种子都完成了精简视图下的 50/50 个任务；切到完整视图后，却都是 0/50。提示哪些信息相关能缓解问题，但未消除差距。另一组 ScienceWorld 实验又显示，精简状态训练能同时改善两种视图。论文没有完全分离信息删减与其他呈现变化，不能据此认定精简总比完整好。

Agent 的行为也有差别。`[论文]` [Same Context, Different Agents](#ref-sourati2026) 比较七个模型、1,514 个数据任务：有的习惯调查，有的未查看数据就回答，有的过早放弃。同一种上下文方法可能帮助一组、损害另一组。例如，多 Agent 编排让调查型 Agent 过度自信，准确率损失 5 个百分点；压缩则让它们重复步骤。

`[本文归纳]` 所以，交接材料要说明给谁用、怎么读：直接读取、按需检索，还是转换成它熟悉的结构。选择取决于接收方和任务，不能只按模型名固定，更不能统一压缩到某个字数就算完成。

## 怎样确认交接成功

结合以上证据，`[本文归纳]` 交接材料可以分成四类：

| 留下什么 | 具体内容 |
|---|---|
| 当前成果 | 文件、数据、配置和外部对象的准确位置与版本，必要时附 commit 或 hash |
| 结论依据 | 已核验的事实及来源；决定由谁作出、适用到哪里；仍待验证的假设 |
| 未完成事项与边界 | 阻塞点、负责人、权限，以及已尝试或不能重复的操作 |
| 验收与恢复办法 | 接收方怎样验证能继续；失败后从哪里恢复、退回或重新开始 |

这是一组跨论文的工程归纳，尚未在统一评测中整体验证。[来源标签](../../meta/#claim-tags)用来区分论文结果与本文解释。

`[本文归纳]` **材料送达之后，还要让接收方回查当前成果，完成一个用得上关键结论的代表性下一步，并检查是否破坏了原有结果。** 只验证工具能启动不够；核验通过后，才在原有授权范围内接管任务，并记录所用版本和验收结果。

<figure class="diagram">
<svg width="100%" viewBox="0 0 900 610" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="handoffTitle handoffDesc">
<title id="handoffTitle">Agent 交接：交什么，怎样验收</title>
<desc id="handoffDesc">发送方固定当前成果，记录事实依据、未完成事项与权限边界。接收方按任务调整信息格式，回查成果、完成关键下一步并核查操作后果；通过后接管，失败则恢复、退回或重开。</desc>
<defs>
<linearGradient id="handoffBg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111820"/><stop offset="1" stop-color="#182431"/></linearGradient>
<linearGradient id="handoffNode" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#172635"/><stop offset="1" stop-color="#101a24"/></linearGradient>
<filter id="handoffShadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#05080d" flood-opacity="0.34"/></filter>
<marker id="handoffArrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="#5fd0c8"/></marker>
</defs>
<rect width="900" height="610" rx="20" fill="url(#handoffBg)"/>
<g font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif">
<text x="450" y="42" text-anchor="middle" font-size="24" font-weight="700" fill="#e6edf3">Agent 交接：交什么，怎样验收</text>
<text x="450" y="69" text-anchor="middle" font-size="13" fill="#98a7b5">发出材料不等于成功，接收方能继续才算通过</text>
<rect x="36" y="124" width="146" height="198" rx="18" fill="url(#handoffNode)" stroke="#334456"/>
<text x="109" y="155" text-anchor="middle" font-size="16" font-weight="700" fill="#e6edf3">发送方</text>
<text x="109" y="187" text-anchor="middle" font-size="12" fill="#b9c5cf">搜索记录</text>
<text x="109" y="210" text-anchor="middle" font-size="12" fill="#b9c5cf">分析与解释</text>
<text x="109" y="233" text-anchor="middle" font-size="12" fill="#b9c5cf">现有改动</text>
<path d="M78 266 H140" stroke="#44576a" stroke-width="1.2"/>
<text x="109" y="292" text-anchor="middle" font-size="11.5" fill="#8fa0af">先固定版本，再交接</text>
<path d="M182 223 H221" fill="none" stroke="#5fd0c8" stroke-width="2.2" marker-end="url(#handoffArrow)"/>
<rect x="222" y="95" width="288" height="365" rx="20" fill="url(#handoffNode)" stroke="#5fd0c8" filter="url(#handoffShadow)"/>
<text x="366" y="128" text-anchor="middle" font-size="17" font-weight="700" fill="#e6edf3">交接材料：四类信息</text>
<rect x="248" y="153" width="236" height="58" rx="12" fill="#10252d" stroke="#5fd0c8"/>
<text x="268" y="178" font-size="13.5" font-weight="700" fill="#5fd0c8">1 · 当前成果</text>
<text x="268" y="198" font-size="11.5" fill="#c8d2dc">文件与数据、准确位置和版本</text>
<rect x="248" y="226" width="236" height="68" rx="12" fill="#14222f" stroke="#476277"/>
<text x="268" y="251" font-size="13.5" font-weight="700" fill="#e6edf3">2 · 事实、决定与依据</text>
<text x="268" y="271" font-size="11.5" fill="#c8d2dc">事实与假设分开，摘要不能替代证据</text>
<rect x="248" y="309" width="236" height="68" rx="12" fill="#14222f" stroke="#476277"/>
<text x="268" y="334" font-size="13.5" font-weight="700" fill="#e6edf3">3 · 未完成事项与边界</text>
<text x="268" y="354" font-size="11.5" fill="#c8d2dc">阻塞、负责人、权限、不可重复操作</text>
<rect x="248" y="392" width="236" height="46" rx="12" fill="#14222f" stroke="#476277"/>
<text x="268" y="421" font-size="13.5" font-weight="700" fill="#e6edf3">4 · 验收与恢复办法</text>
<path d="M510 223 H549" fill="none" stroke="#5fd0c8" stroke-width="2.2" marker-end="url(#handoffArrow)"/>
<rect x="550" y="124" width="142" height="198" rx="18" fill="url(#handoffNode)" stroke="#334456"/>
<text x="621" y="155" text-anchor="middle" font-size="16" font-weight="700" fill="#e6edf3">接收方</text>
<text x="621" y="187" text-anchor="middle" font-size="12" fill="#b9c5cf">按需检索</text>
<text x="621" y="210" text-anchor="middle" font-size="12" fill="#b9c5cf">调整信息格式</text>
<text x="621" y="233" text-anchor="middle" font-size="12" fill="#b9c5cf">改写，不只压缩</text>
<path d="M590 266 H652" stroke="#44576a" stroke-width="1.2"/>
<text x="621" y="292" text-anchor="middle" font-size="11.5" fill="#8fa0af">能否续做要实测</text>
<path d="M692 223 H731" fill="none" stroke="#5fd0c8" stroke-width="2.2" marker-end="url(#handoffArrow)"/>
<rect x="732" y="124" width="132" height="198" rx="18" fill="url(#handoffNode)" stroke="#5fd0c8"/>
<text x="798" y="155" text-anchor="middle" font-size="16" font-weight="700" fill="#e6edf3">接续验收</text>
<text x="798" y="187" text-anchor="middle" font-size="12" fill="#b9c5cf">回查当前成果</text>
<text x="798" y="210" text-anchor="middle" font-size="12" fill="#b9c5cf">完成关键下一步</text>
<text x="798" y="233" text-anchor="middle" font-size="12" fill="#b9c5cf">核查操作后果</text>
<path d="M767 266 H829" stroke="#44576a" stroke-width="1.2"/>
<text x="798" y="292" text-anchor="middle" font-size="11.5" fill="#8fa0af">验证任务，不只启动</text>
<path d="M798 322 V380" fill="none" stroke="#5fd0c8" stroke-width="2.2" marker-end="url(#handoffArrow)"/>
<rect x="674" y="390" width="190" height="66" rx="14" fill="#10252d" stroke="#5fd0c8"/>
<text x="769" y="416" text-anchor="middle" font-size="14" font-weight="700" fill="#5fd0c8">通过：接收方接管</text>
<text x="769" y="438" text-anchor="middle" font-size="11.5" fill="#c8d2dc">记录版本、结果与回执</text>
<path d="M732 422 H554" fill="none" stroke="#d99a66" stroke-width="1.8" stroke-dasharray="7 5" marker-end="url(#handoffArrow)"/>
<text x="644" y="411" text-anchor="middle" font-size="11.5" fill="#d9ad84">失败退回</text>
<rect x="52" y="500" width="796" height="66" rx="14" fill="#101821" stroke="#334456"/>
<text x="450" y="527" text-anchor="middle" font-size="13.5" font-weight="700" fill="#e6edf3">能否接续，取决于发送方、交接材料、接收方和任务</text>
<text x="450" y="551" text-anchor="middle" font-size="12" fill="#98a7b5">材料多、摘要短、文档全，都不等于交接成功；能续做、能恢复才算接住</text>
</g>
</svg>
</figure>

消息、上传等外部操作尤其要交代清楚：未尝试、成功、明确失败、结果不确定，需要的后续动作不同。调用超时或回执丢失时，应先核对外部对象；不能把“不知道是否成功”写成“没成功”，再自动执行一次。其他 Agent 正在修改的文件，也不能仅凭一份交接文档就接手覆盖。

切换也不必等到失败。`[论文]` [Humanize MLE Agents](#ref-li2026hma) 让两个 Agent 共用工作区，限定每个会话的实验次数，再重置上下文。在 75 个 MLE-bench 任务上，六个配置、五组异构 Agent 搭配平均比组成它们的基线高 6.4 个百分点的获奖率。这支持在成果已落入共享工作区时，把轮换作为工作流的一部分；并不证明固定轮换频率适用于所有任务或有外部副作用的流程。

训练方法 `[论文]` [VH-GPO](#ref-li2026vhgpo) 提供了一个有限类比：教师修复学生的失败后，在有限搜索预算内寻找最早经独立结果确认、学生可以继续成功的位置，再交还控制权。训练有环境验证器，目标是让成功的后续轨迹由学生生成，不能直接套到生产交接；它提示我们，交接时点应看下一位能否继续，而不只看上一位认为自己做完了多少。

`[本文归纳]` 最终要留下的，是下一步所依赖的成果、依据和边界。**交接是否成功，要看接收方能否在不越权、不重复外部操作、且能检查后果的前提下继续工作。**

## Reference

<a id="ref-ganz2026"></a>
- **The Handoff Tax: Continuing Non-Native Trajectories in LLM Agents**. Roy Ganz, Mor Shpigel Nacson, Adi Kalyanpur, Ron Litman. 2026. [arXiv:2608.24358](https://arxiv.org/abs/2608.24358).

<a id="ref-grynets2026"></a>
- **Specification Portability Across LLM Development Agents: Cross-Agent Compatibility in Specification-Driven Software Migration**. Oleg Grynets, Oleksii Ilchuk, Dariia Zatulna, Vasyl Lyashkevych. 2026. [arXiv:2608.21208](https://arxiv.org/abs/2608.21208).

<a id="ref-li2026hma"></a>
- **Humanize MLE Agents: Multi-Agent Session Alternation Beyond Single-Agent Limits**. Changye Li et al. 2026. [arXiv:2610.13494](https://arxiv.org/abs/2610.13494).

<a id="ref-zou2026"></a>
- **StateHarness: Maintaining Evolving Project State for Long-Horizon Coding Agents**. Chuan Zou, Yujun Zhou, Xiaonan Luo, Xiangliang Zhang. 2026. [arXiv:2610.17616](https://arxiv.org/abs/2610.17616).

<a id="ref-nie2026"></a>
- **State Representation Shapes Long-Horizon Agent Learning and Transfer: An Empirical Study**. Dong Nie, Rui Lan, Yixin Nie, Lingzi Hong. 2026. [arXiv:2610.15407](https://arxiv.org/abs/2610.15407).

<a id="ref-min2026"></a>
- **Prune the Summary, Not the History: Source-Judged Compaction for Long-Horizon Agents**. Guanghui Min, Chen Chen. 2026. [arXiv:2610.20927](https://arxiv.org/abs/2610.20927).

<a id="ref-sourati2026"></a>
- **Same Context, Different Agents: A Behavioral Study of Semantic Layers, Orchestration and Compaction in Data Agents**. Zhivar Sourati et al. 2026. [arXiv:2610.20959](https://arxiv.org/abs/2610.20959).

<a id="ref-li2026vhgpo"></a>
- **VH-GPO: Verified Handoff for LLM Agent Reinforcement Learning**. Haoze Li, Peng Zhou, Peiyuan Wu, Weijie Zhao, Yinan Xin. 2026. [arXiv:2610.14000](https://arxiv.org/abs/2610.14000).
