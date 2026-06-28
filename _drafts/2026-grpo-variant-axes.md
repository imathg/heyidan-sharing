# GRPO 变体的设计轴：谁在承载更新信号

<!-- domain: agentic-rl -->

`[本文归纳]` 2026 年再看 GRPO，一堆新名词容易让人误以为算法空间变碎了：Dr-GRPO 去掉标准化，DAPO 改 clip 和采样，BPPO 只更新最短正负 prefix，CARL 把 tool-use rollout 切到 segment。这组名字可以压回一个问题：**更新信号到底由谁承载、在哪里归一化、和什么参照系比较**。这些旋钮在内部可组合，在小 group、单一 carrier、agentic segment 这些边界上又会耦合。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<figure style="margin: 18px 0 24px;">
<svg viewBox="0 0 760 250" width="100%" role="img" aria-label="GRPO variant axes map" style="border:1px solid #2a3441;border-radius:4px;background:#0a1018;">
  <defs>
    <style>
      .axis{fill:#e6edf3;font:600 16px Charter,Georgia,serif}
      .small{fill:#8b97a4;font:13px Charter,Georgia,serif}
      .tag{fill:#5fd0c8;font:12px JetBrains Mono,monospace}
      .box{fill:#131922;stroke:#3aa89f;stroke-width:1.2}
      .muted{stroke:#2a3441;stroke-width:1}
    </style>
  </defs>
  <line x1="80" y1="126" x2="680" y2="126" class="muted"/>
  <rect x="40" y="36" width="125" height="78" rx="4" class="box"/>
  <text x="58" y="66" class="tag">A1</text><text x="58" y="91" class="axis">normalization</text>
  <rect x="185" y="136" width="125" height="78" rx="4" class="box"/>
  <text x="203" y="166" class="tag">A2</text><text x="203" y="191" class="axis">ratio / clip</text>
  <rect x="330" y="36" width="125" height="78" rx="4" class="box"/>
  <text x="348" y="66" class="tag">A3</text><text x="348" y="91" class="axis">baseline</text>
  <rect x="475" y="136" width="125" height="78" rx="4" class="box"/>
  <text x="493" y="166" class="tag">A4</text><text x="493" y="191" class="axis">carrier / group</text>
  <rect x="620" y="36" width="100" height="78" rx="4" class="box"/>
  <text x="638" y="66" class="tag">A5</text><text x="638" y="91" class="axis">credit</text>
  <text x="48" y="236" class="small">Dr-GRPO / DAPO / CISPO / BPPO / CARL 是五个旋钮上的不同位点。</text>
</svg>
</figure>

## 先把名字压回五个旋钮

`[本文归纳]` 一个 GRPO-style 变体至少能被问五个问题。答不出来时，它更像某个轴上的实现细节。

| 轴 | 问题 | 典型改法 | 代表 |
|---|---|---|---|
| A1 normalization scale | advantage 怎么标尺化 | 去 group std、去 response length normalization | Dr-GRPO |
| A2 ratio / clip channel | 概率比怎么被截断 | Clip-Higher、CISPO asymmetric clipping | DAPO / CISPO |
| A3 baseline / value source | advantage 和谁比 | group mean、greedy baseline、segment critic | GRPO / ReMax / CARL |
| A4 update carrier / group key | 哪些样本或 token 承载梯度 | full group、shortest correct/incorrect prefix、state-aligned group | BPPO / GiGPO / Tree-GRPO |
| A5 credit granularity / reward pressure | reward 或 credit 落在哪个粒度 | trajectory、token、segment、overlong shaping | DAPO / CARL |

`[论文]` [DAPO](#ref-yu2025)（ByteDance Seed + AIR Tsinghua + HKU + SIA-Lab，Yu et al. 2025）是最好的入门切面，因为它在同一篇系统报告里把多个旋钮放进 ablation：Naive GRPO 在 AIME 2024 上是 30，逐步加入 Overlong Filtering、Clip-Higher、Soft Overlong、Token-level loss、Dynamic Sampling 后到 50。这个表本身说明：GRPO 更像一套可以局部替换的 update-signal 管线。

`[tech report]` [Dr-GRPO pin](#ref-drgrpo) 暴露出另一个旋钮：原贴把 Cursor Composer 2 技术报告里的改法概括为去掉 group std normalization 和 response length normalization。这个点不足以形成一篇论文结论，但足够说明很多新 GRPO 的主要动作落在 A1。

## BPPO 是最干净的 A4 案例

`[论文]` [BPPO](#ref-zhao2026)（TeleAI + 上海交通大学，Zhao et al. 2026）问的问题很窄：同一个 prompt group 里，是不是每条 completion 都提供同等有用的更新信号。它的 gradient-similarity 分析给出答案：same-class completions 的方向高度相似，correct-incorrect pair 更能提供区分信号。于是 BPPO 只拿最短 correct completion 和最短 incorrect completion 做 compact update unit，并且只更新 prefix。

`[论文]` 这个设计的价值在于独立性。[BPPO](#ref-zhao2026) 明确保留 full-group sampling、reward 和 group-relative advantage normalization，只改 update 作用在哪里。MATH setup 下，BPPO 报告 mean response length 降低 50.6%，训练 wall-clock speedup 到 6.08x；abstract 把 30-50% 长度下降放在 prefix-focused optimization 这条路径上。BPPO 的核心旋钮是 A4：**谁承载更新信号**。

`[本文归纳]` 这也是判断“真轴”的模板。一个轴要成立，最好像 BPPO 这样能固定其他组件，只移动一个旋钮，并给出对应可观测量：训练 token 变少、长度变短、速度变快，准确率仍可接近 GRPO。如果一个改法同时改 reward、clip、sample filtering 和 aggregation，它仍可能有效，但更难被当成 clean design axis。

## DAPO / CISPO 解释长 CoT 的 clip 压力

`[论文]` [DAPO](#ref-yu2025) 的 Clip-Higher 直接指向 A2。论文解释 upper clip 会限制 low-probability token 的 probability increase，而长 CoT 里的探索词往往本来就低概率。Clip-Higher 给这些 token 留出更大的上升空间；Dynamic Sampling 则把全对或全错的 prompt 过滤掉，避免 batch 被没有有效梯度的样本占满。

`[论文]` 同一篇 [DAPO](#ref-yu2025) 还把 A5 拉进来：sample-level loss 会让长 CoT 的影响被不合适地压平，token-level loss 让长序列按 token 数贡献梯度；Soft Overlong / Overlong Filtering 则把长度压力通过 reward shaping 或过滤表达出来。这些改法属于长推理训练动力学，比表层 reward 调整更底层。

`[tech report]` [CISPO 发现过程](#ref-cispo) 来自 MiniMax 相关贡献者的复盘，证据等级低于论文，但机制直觉很具体：off-policy clip=0.2 会抑制 response length 增长，被 clip 的少数 token 里包含 `wait`、`but`、`let me` 这类 long-CoT 涌现关键词。CISPO 第一版 loss 对正 advantage 走 detach-clip importance sampling 乘 `log pi`，对负 advantage 走 standard PPO，因为负梯度对 entropy 更友好。

`[本文归纳]` DAPO 和 CISPO 的共同点在于：二者都承认 A2 会改变探索 token 的命运。长 CoT 训练里，ratio clipping、advantage normalization、length aggregation 会共同决定低概率 token 是被放大、被截断，还是被长度项稀释。

## agentic RL 把 group 从 prompt 迁到 state / segment

`[tech report]` [Long-horizon GRPO 综述](#ref-longhorizon) 给出的核心句子很有用：agentic GRPO 的关键变化落在“什么样本进入同一个 group 比较”。Vanilla GRPO / Search-R1 / RAGEN-StarPO 仍按同 prompt 的完整 trajectory 分组；GiGPO 换成 episode + anchor-state；HGPO 要求 context-consistent；Tree-GRPO 比较 sibling branches；ARPO / AEPO 把预算集中到高熵 tool-use 点。

`[论文]` [CARL](#ref-kumar2026)（Microsoft AI，Kumar et al. 2026）把这个迁移写得更结构化。它指出 trajectory-level reward 无法隔离一次成功 episode 里哪个工具调用真正有用，也无法惩罚不必要调用；因此把 rollout 按自然工具边界拆成 segment，用 critic 学每个 segment 对最终正确率的增减。7B setup 上，GRPO 到 PPO 是 +4.0 EM，PPO 到 CARL 还有 +6.7 EM；Tier2 easy questions 上，CARL tool-use rate 38.6%，GRPO 是 87.5%，同时 CARL EM 更高。

`[本文归纳]` 这说明 A4 和 A5 在 agentic 场景会贴得很近：group key 迁到 state 或 branch，credit 粒度自然也从 trajectory 迁到 segment。它们仍可分开讨论，但边界不像 BPPO 那么干净。agent 任务里真正的单位是“同一个可决策局面”，而非单条 prompt。

## baseline/value source 是第三条主线

`[tech report]` [ReMax 背后的故事](#ref-remax) 回到更早的 baseline 选择：ReMax 用 greedy decoding response 当 baseline，是为了解耦“采样随机性到 response”的偏差，也和当时 rollout 基础设施昂贵有关。到 GRPO，baseline 变成同 prompt group 的相对比较；到 CARL，value source 变成 segment-level critic。

`[本文归纳]` 所以 A3 不能被 A1 吸收。normalization scale 问的是 advantage 怎么缩放，baseline/value source 问的是 advantage 和什么参照系比较。group mean、greedy response、segment critic 会带来不同方差、不同 bias，也会把 credit 的可解释边界推向不同位置。

## 退化角：小 group 会让 A1 / A3 / A4 数值重合

`[本文归纳]` group size 属于核心结构超参。GRPO 的“relative”来自同 prompt group 内的对比；当有效 group 变小，A1 normalization、A3 baseline、A4 update carrier 会一起退化。极端到 `G = 1` 时，group mean 不再提供相对参照，std normalization 失去稳定意义，full-group update carrier 也只剩一个样本。

`[论文]` [BPPO](#ref-zhao2026) 的 clean case 之所以干净，是因为它保留 full-group advantage normalization，只把 carrier 换成最短 correct / incorrect prefix。`[tech report]` [Dr-GRPO pin](#ref-drgrpo) 之所以单独列出，是因为它直接碰 A1：去掉 group std normalization 和 response length normalization。两者放在一起看，能解释这个退化角：当 group 的相对比较变弱，baseline、normalization、carrier 不再像五轴表里那样清楚分离。

| 边界条件 | A1 | A3 | A4 |
|---|---|---|---|
| 正常 group | advantage 可缩放 | group mean / critic | 多样本、多 token |
| 小 group / 单一 completion | std 不稳或被移除 | group mean 变弱 | carrier 近单样本 |
| agentic segment | 按 state / segment 重定 | critic 更自然 | key 迁到 state / branch / segment |

`[本文归纳]` 这就是“边界上耦合”的硬含义。五轴表适合读算法差异；退化角提醒工程实现时别把轴当完全正交。一个方案如果同时调 group size、去标准化、换 carrier，看起来是三项改动，实际可能是在修同一个退化点。

## 伪轴的判据：独立性和干净性

`[本文归纳]` “伪轴”指有效但暂时缺少独立坐标资格的改法。这里有两种不同的 disqualification，必须拆开看。

`[本文归纳]` 第一关是**独立性**：它是否能被已有轴张成。BPPO 通过这关，因为它固定 sampling、reward、group-relative normalization，只移动 A4 update carrier。长度下降出现在结果里，但 BPPO 没有把长度当独立旋钮直接优化，所以长度在这里更像 A4 的副产物，缺少新轴资格。

`[本文归纳]` 第二关是**干净性**：效果有没有被转嫁。一个改法可以独立，却仍然不干净；它压住目标 proxy 的同时，可能把优化压力推到相邻 proxy。overlong shaping、length penalty、entropy trigger 这类改法常常落在这里。它们可能有效，但需要同时监控长度、正确率、entropy、tool-use rate 或其他相邻指标，验证优化压力停在目标 proxy 上。

`[论文]` [BPPO](#ref-zhao2026) 在这里提供了一个反例参照：不显式加 length penalty，也能让平均长度下降 30-50%。这意味着长度不天然是一条独立轴。长度可能是 reward pressure 的目标，也可能是 update carrier 的副产物，还可能是 clip/normalization 对探索 token 的间接影响。

`[本文归纳]` 更实用的读法是：看到一个 GRPO 新名词，先填这张表，再判断它的论文定位。如果某个名字只能填进一个格子，它是局部旋钮；如果它跨多个格子，需要看 ablation 是否能把格子拆开；如果它通过独立性但过不了干净性，就把它写成 pressure routing，保留新轴资格的判断。

| 新方法读法 | 应问的问题 |
|---|---|
| A1 | advantage 的标尺有没有变，是否改变 std/length/group-size 敏感性 |
| A2 | probability ratio 的正负梯度通路有没有变，低概率 token 是否更容易上升 |
| A3 | baseline/value 的参照系来自 group、greedy rollout、critic 还是外部 judge |
| A4 | update 到底落在 full group、pair、prefix、state group 还是 branch group |
| A5 | reward/credit 是 trajectory、token、segment，还是通过 shaping 间接施压 |

## 工程读法：论文名和实践配置落在同一张轴表

`[本文归纳]` 论文名适合检索，配置名适合落地，两者不该分成两套语言。工程上遇到训练症状时，先填轴表，再决定读哪篇论文。

| 症状 | 先查的轴 | 对应读法 |
|---|---|---|
| 长 CoT 不长、探索词起不来 | A2 + A1 | 看 Clip-Higher、CISPO、去 std / length normalization |
| token 开销大、response 变啰嗦 | A4 | 优先看 BPPO 的 prefix carrier，再考虑 length penalty |
| tool call 太多且 easy question 也调用 | A4 + A5 | 看 CARL 的 segment boundary 和 competence critic |
| 方差大、同组 advantage 不稳 | A1 + A3 | 区分 normalization 问题和 baseline/value source 问题 |
| reward shaping 看起来生效但副作用变多 | A5 的干净性 | 查相邻 proxy 是否承接了优化压力 |

`[本文归纳]` 这样读，Dr-GRPO / DAPO / CISPO / BPPO / CARL / ReMax 不再是六个并列名字，而是同一组旋钮的不同取值。新论文如果只改一个旋钮，就按该轴吸收；如果同时改多个旋钮，就先要求拆 ablation；如果声称开了新轴，就要求给出独立性和干净性证据。

## 可证伪问题

`[本文归纳]` 这篇 brief 的主结论可以被三类实验推翻。第一，如果有主流 GRPO 变体无法映射到 A1-A5 任意一轴，五轴表不完备。第二，如果 BPPO 的收益在 random pair 或 same-class pair 上同样成立，A4 的 correct/incorrect contrast 解释就弱。第三，如果 CARL 的 segment critic 被 token-level PPO 完全追平，agentic 场景里的主因就要从“边界对齐 credit”转向其他机制。

`[本文归纳]` 在这些反例出现前，把 GRPO 变体当成五个 update-signal 旋钮，比按论文名堆列表更有操作性：要省 token，先看 A4；要修长 CoT 探索，先看 A2 和 A1；要做 tool-use agent，先看 A4/A5 的 state 或 segment 边界；要解释方差和 bias，先看 A3。

## Reference

<a id="ref-yu2025"></a>
**[DAPO: An Open-Source LLM Reinforcement Learning System at Scale]** Qiying Yu et al.，ByteDance Seed / Institute for AI Industry Research (AIR), Tsinghua University / The University of Hong Kong / SIA-Lab，2025. [arXiv:2503.14476](https://arxiv.org/abs/2503.14476) / [Project](https://dapo-sia.github.io/)。本文用它定位 GRPO baseline、Clip-Higher、Dynamic Sampling、token-level loss 和 overlong shaping。`[论文]`

<a id="ref-zhao2026"></a>
**[BPPO: Binary Prefix Policy Optimization for Efficient GRPO-Style Reasoning RL with Concise Responses]** Qingfei Zhao, Huan Song, Shuyu Tian, Jiawei Shao, Xuelong Li，TeleAI / Shanghai Jiao Tong University，2026. [arXiv:2605.28028](https://arxiv.org/abs/2605.28028)。本文用它作为 update carrier 轴的 clean case。`[论文]`

<a id="ref-kumar2026"></a>
**[Knowing When to Ask: Segment-Level Credit Assignment for LLM Tool Use]** Abhijit Kumar, Zoey Wu, Mohit Suley，Microsoft AI，2026. [arXiv:2605.27788](https://arxiv.org/abs/2605.27788)。本文用它说明 agentic RL 里 group key 和 credit granularity 如何迁到 segment。`[论文]`

<a id="ref-longhorizon"></a>
**[Long-horizon Agentic RL 中 GRPO / GRPO-like 算法调研]** Curtis，知乎长文，2026. [Zhihu](https://zhuanlan.zhihu.com/p/2040798695432647193)。本文用它整理 agentic GRPO 的 group construction 分类。`[tech report]`

<a id="ref-cispo"></a>
**[CISPO 的发现过程]** 炼熵师（前 MiniMax），知乎长文，2026. [Zhihu](https://zhuanlan.zhihu.com/p/1962307894105048283)。本文用它说明 off-policy clipping 对 long-CoT response length 的压力。`[tech report]`

<a id="ref-drgrpo"></a>
**[Composer 2 技术报告里的 Dr-GRPO 去标准化]** 香港市民董先生（知乎用户），知乎想法，2026. [Zhihu pin](https://www.zhihu.com/pin/2029888667460822187)。本文用它标注 group std normalization 和 response length normalization 这条设计轴。`[tech report]`

<a id="ref-remax"></a>
**[ReMax 背后的故事]** 李子牛，知乎长文，2026. [Zhihu](https://zhuanlan.zhihu.com/p/1963218041199387877)。本文用它说明 greedy decoding baseline 的历史动机。`[tech report]`
