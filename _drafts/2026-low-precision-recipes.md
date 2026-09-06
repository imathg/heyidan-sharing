# 4-bit LLM 的精度损失：格式偏置、激活异常值与关键 token

<!-- domain: training-infra -->
<!-- edition_date: 2026-06-21 -->
<!-- revised_date: 2026-09-06 -->
<!-- revision_note: 将不同量化失效机制分开，不再把格式偏置、低熵token和激活异常值视为已验证的统一“尖锐度”规律。 -->

同样使用 4-bit，问题可能发生在不同位置：数值格式带来累积舍入偏置，少量激活异常值扩大量化范围，关键数字或运算符被改写后使推理出错。诊断对象不同，改格式、旋转激活分布和补训练信号就不能当作可互换的修法。

下文对照 UFP4、ReQAT、TWLA，以及预训练和推理侧的相关配方，分别说明它们改了什么、在哪种设置上获得收益。KV cache 容量和小批量解码延迟也纳入比较，但它们是效率问题，不自动证明同一种精度损失机制。

> **先定位误差发生在哪个对象，再选量化修复方法。网格偏置、激活异常值和低熵 token 是三种不同测量；现有材料没有证明它们服从同一个“尖锐度”指标。**

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<svg viewBox="0 0 760 430" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="六个低精度配方按生命周期位置分布，底部列出尖锐处的三种语言">
  <defs>
    <linearGradient id="lpbg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#131922"/>
      <stop offset="1" stop-color="#1a2230"/>
    </linearGradient>
    <marker id="lparrow" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto">
      <path d="M0 0 L8 4 L0 8 Z" fill="#5b6a76"/>
    </marker>
  </defs>
  <rect x="0" y="0" width="760" height="430" rx="14" fill="url(#lpbg)"/>
  <text x="380" y="36" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="19" font-weight="600" fill="#e8eef2">4-bit LLM：不同失效机制与对应修复</text>
  <text x="380" y="60" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="12.5" fill="#8a96a0">按应用阶段比较配方；分别核对误差来源与硬件收益</text>
  <line x1="140" y1="215" x2="140" y2="90" stroke="#2f3b46" stroke-width="1.5"/>
  <line x1="320" y1="215" x2="320" y2="148" stroke="#2f3b46" stroke-width="1.5"/>
  <line x1="480" y1="215" x2="480" y2="148" stroke="#2f3b46" stroke-width="1.5"/>
  <line x1="620" y1="215" x2="620" y2="90" stroke="#2f3b46" stroke-width="1.5"/>
  <g font-family="-apple-system,Segoe UI,sans-serif">
    <rect x="74" y="90" width="132" height="44" rx="8" fill="#1c2630" stroke="#33414c"/>
    <text x="140" y="110" text-anchor="middle" font-size="13" font-weight="600" fill="#5fd0c8">UFP4</text>
    <text x="140" y="126" text-anchor="middle" font-size="10.5" fill="#8a96a0">换网格几何</text>
    <rect x="74" y="148" width="132" height="44" rx="8" fill="#1c2630" stroke="#33414c"/>
    <text x="140" y="168" text-anchor="middle" font-size="13" font-weight="600" fill="#5fd0c8">Nemotron 3 Ultra</text>
    <text x="140" y="184" text-anchor="middle" font-size="10.5" fill="#8a96a0">NVFP4 + 后训练</text>
    <rect x="254" y="148" width="132" height="44" rx="8" fill="#1c2630" stroke="#33414c"/>
    <text x="320" y="168" text-anchor="middle" font-size="13" font-weight="600" fill="#5fd0c8">ReQAT</text>
    <text x="320" y="184" text-anchor="middle" font-size="10.5" fill="#8a96a0">token-selective 训练</text>
    <rect x="414" y="148" width="132" height="44" rx="8" fill="#1c2630" stroke="#33414c"/>
    <text x="480" y="168" text-anchor="middle" font-size="13" font-weight="600" fill="#5fd0c8">TWLA</text>
    <text x="480" y="184" text-anchor="middle" font-size="10.5" fill="#8a96a0">正交旋转</text>
    <rect x="554" y="90" width="132" height="44" rx="8" fill="#1c2630" stroke="#33414c"/>
    <text x="620" y="110" text-anchor="middle" font-size="13" font-weight="600" fill="#5fd0c8">UltraQuant</text>
    <text x="620" y="126" text-anchor="middle" font-size="10.5" fill="#8a96a0">UE8M0 group scale</text>
    <rect x="554" y="148" width="132" height="44" rx="8" fill="#1c2630" stroke="#33414c"/>
    <text x="620" y="168" text-anchor="middle" font-size="13" font-weight="600" fill="#5fd0c8">ReSET</text>
    <text x="620" y="184" text-anchor="middle" font-size="10.5" fill="#8a96a0">step-entropy 调温</text>
  </g>
  <line x1="56" y1="215" x2="700" y2="215" stroke="#3a4550" stroke-width="2" marker-end="url(#lparrow)"/>
  <g font-family="-apple-system,Segoe UI,sans-serif">
    <circle cx="140" cy="215" r="5" fill="#5fd0c8"/>
    <circle cx="320" cy="215" r="5" fill="#5fd0c8"/>
    <circle cx="480" cy="215" r="5" fill="#5fd0c8"/>
    <circle cx="620" cy="215" r="5" fill="#5fd0c8"/>
    <text x="140" y="238" text-anchor="middle" font-size="12" fill="#c2ccd4">预训练</text>
    <text x="320" y="238" text-anchor="middle" font-size="12" fill="#c2ccd4">QAT</text>
    <text x="480" y="238" text-anchor="middle" font-size="12" fill="#c2ccd4">训练后量化</text>
    <text x="620" y="238" text-anchor="middle" font-size="12" fill="#c2ccd4">推理</text>
    <text x="708" y="219" text-anchor="start" font-size="11" fill="#6b7785">生命周期</text>
  </g>
  <text x="380" y="288" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="13" font-weight="600" fill="#f0a868">三类机制测量不同对象，不能直接等同</text>
  <g font-family="-apple-system,Segoe UI,sans-serif">
    <rect x="62" y="306" width="196" height="86" rx="10" fill="#20191320" stroke="#4a3a2c"/>
    <text x="160" y="332" text-anchor="middle" font-size="13" font-weight="600" fill="#f0a868">几何</text>
    <text x="160" y="354" text-anchor="middle" font-size="11" fill="#b9c3cb">E2M1 网格不对称</text>
    <text x="160" y="374" text-anchor="middle" font-size="10.5" fill="#7d8893">UFP4 · 高幅值区欠表示</text>
    <rect x="282" y="306" width="196" height="86" rx="10" fill="#20191320" stroke="#4a3a2c"/>
    <text x="380" y="332" text-anchor="middle" font-size="13" font-weight="600" fill="#f0a868">语义</text>
    <text x="380" y="354" text-anchor="middle" font-size="11" fill="#b9c3cb">low-entropy token</text>
    <text x="380" y="374" text-anchor="middle" font-size="10.5" fill="#7d8893">ReQAT · 数字 / 运算符掉点</text>
    <rect x="502" y="306" width="196" height="86" rx="10" fill="#20191320" stroke="#4a3a2c"/>
    <text x="600" y="332" text-anchor="middle" font-size="13" font-weight="600" fill="#f0a868">分布</text>
    <text x="600" y="354" text-anchor="middle" font-size="11" fill="#b9c3cb">激活 outlier</text>
    <text x="600" y="374" text-anchor="middle" font-size="10.5" fill="#7d8893">TWLA · heavy-tail 限制精度</text>
  </g>
  <text x="380" y="414" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="10.5" fill="#5b6a76">格式、激活与输出 token 的误差需要分别检验</text>
</svg>

*图：六个配方按应用阶段排列；底部区分数值格式、输出 token 与激活分布三类失效机制，不将它们视为同一个量。*

<a id="同一个损伤-三种语言"></a>

## 三类精度损失，发生在不同对象上

三篇工作分别测量数值网格、输出 token 和激活分布。它们都涉及低精度误差，但测量对象和修复机制不同。

| 层 | 工作 | 损伤描述 |
|---|---|---|
| 几何 | [UFP4](#ref-ufp4) | E2M1 的可表示值间距不等，高幅值区系统性欠表示 |
| 语义 | [ReQAT](#ref-reqat) | low-entropy token（数字、运算符）被量化噪声放大成级联错误 |
| 分布 | [TWLA](#ref-twla) | heavy-tailed 激活 outlier 把激活钉在高精度 |

`[论文]` [UFP4](#ref-ufp4) 分析 NVIDIA/AMD 硬件使用的 E2M1（FP4）格式：可表示值之间间距不等，量化时产生系统性的负向 rounding 误差，论文称之为 shrinkage bias。这个偏置逐层乘性累积，训练中常用的 Random Hadamard Transform 还会进一步放大它，解释了既有 E2M1 配方的训练不稳定。问题落在格式的网格几何上。

`[论文]` [ReQAT](#ref-reqat) 看的是 token 分布：把 weight、activation、KV cache 全量化到 4-bit 后，失效集中在 low-entropy token 上。这些是数字、运算符这类精确符号，模型在这里几乎没有不确定性，量化噪声一旦改写就触发级联错误。问题落在分布最尖锐的那批 token 上。

`[论文]` [TWLA](#ref-twla) 看的是激活的形状：heavy-tailed 分布里少数 outlier 决定了量化范围，既有方法因此只能把激活留在高精度，限制端到端加速。问题落在分布的长尾上。

`[本文归纳]` 这些结果支持按失效位置选择修法，不支持把三种测量直接等同。token 熵描述输出分布的不确定性，激活异常值描述张量中的数值范围，网格偏置描述数值格式与舍入误差；不能由其中一项推算另外两项。下一节按实际干预对象比较配方。

<a id="把精度预算挪到尖锐处的四种机制"></a>

## 对应修法：改格式、旋转分布、细化scale或补训练

| 机制 | 代表 | 做法 |
|---|---|---|
| 换网格几何 | [UFP4](#ref-ufp4) | 用均匀 4-bit（E1M2/INT4）替代非均匀 E2M1，对三个训练 matmul 都做 RHT，只对梯度做 stochastic rounding |
| 旋转分布 | [TWLA](#ref-twla) | Kronecker 结构正交旋转将权重重塑成 ternary-friendly 的三峰分布，共享旋转同时从统计上减弱激活 outlier |
| 加细 scale 粒度 | [UltraQuant](#ref-ultraquant) | FP4 KV + FP8 query + UE8M0 group scale，利用 CDNA4 的 native scaled-MFMA |
| 偏置训练信号 | [ReQAT](#ref-reqat) | Trace-Aligned QAT 复访相同 reasoning trace 优先关键决策，Selective Entropy Minimization 强化 low-entropy 位置 |

`[论文]` [UFP4](#ref-ufp4) 的处理直接改变格式：针对 E2M1 的网格不对称，换成均匀的 4-bit 网格。在 Dense 1.5B、MoE 7.9B、MoE 124B 三个规模上，均匀格式的 BF16-relative loss degradation 低于强 E2M1 基线。

`[论文]` [TWLA](#ref-twla) 不改变数值格式，而是重塑数据分布：用 Kronecker 结构的正交旋转将权重旋成三峰分布，配合三值量化；同一个旋转还会在统计意义上减弱激活 outlier，于是激活也能降到 **4-bit**，权重降到 **1.58-bit**。这是训练后量化，不需要重训。

`[论文]` [UltraQuant](#ref-ultraquant) 的对象是 KV cache，目标是降低长前缀在多轮复用时的内存压力。它给 KV 用 FP4、query 用 FP8、group scale 用 UE8M0，在 AMD CDNA4 上 late-round 的 P50 首 token 延迟降到原来的 **1/3.47**（整体 2.3 倍），相对 FP8 KV 基线吞吐 **1.63 倍**。这组效率结果不能用来证明输出 token 或激活异常值上的共同误差规律。

`[论文]` [ReQAT](#ref-reqat) 针对 low-entropy token 集中的损伤，将训练信号集中到这些位置：Trace-Aligned QAT 反复在同一条 reasoning trace 上对齐关键的低熵决策，Selective Entropy Minimization 强化这些位置的置信。在同等训练预算下，它恢复并超过了 BF16 微调精度，NVIDIA DGX Spark 上 **3.9 倍**、B200 上 **3.1 倍**吞吐。

## 格式几何本身也是维度

E2M1 可以作为配方的一项选择来检验。[UFP4](#ref-ufp4) 在 4-bit 预算下比较非均匀 E2M1 与均匀格式，关注各数值区间的表示误差及其训练影响。本文采用的是该研究在所测设置上的格式对照，不据此断言均匀网格对任意权重、激活或输出分布都更好。

这条维度不限于训练。`[论文]` [ReSET](#ref-reset) 在推理解码端同样面对 NVFP4 的两个问题：reasoning 精度下降，以及 small-batch 自回归解码没有获得低精度应有的延迟收益。它按 token 级和 step 级 entropy 在线估计每一步的不确定性、自适应调解码温度，再配一个针对 small-M 的 NVFP4 CUDA-core kernel 补足延迟表现。跨 reasoning benchmark 和模型规模，相对 NVFP4 基线精度提升至多约 **2 点**。entropy 在这里再次成为判据：高熵步可以容忍更激进的采样，低熵步需收紧。

工业量产规模也在采用这条路线。`[tech report]` [Nemotron 3 Ultra](#ref-nemotron3) 是 550B total / 55B active 的 MoE Hybrid Mamba-Attention，20T token 预训练即用 NVFP4，后训练串 SFT、RL 和多教师在线蒸馏（MOPD），自报相对公开 LLM 约 **6 倍**推理吞吐，checkpoint 和配方已开源。这表明该系统组合采用了低精度预训练与后训练；摘要未提供归因对照，不能单独断言 MOPD 找回了量化损失。

<a id="四个正交维度"></a>

## 配方对照：应用阶段、张量、格式与修复方法

`[本文归纳]` 下表用四项信息比较这六个方案。它是阅读已有配方的清单，不声称各项独立、覆盖所有方法，或任意组合都可实现。

| 方案 | 应用阶段 | 量化张量 | 格式 | 修复或效率方法 |
|---|---|---|---|---|
| [UFP4](#ref-ufp4) | 预训练 | weight+activation+gradient | 均匀 INT4/E1M2 | 换网格 + RHT |
| [Nemotron 3 Ultra](#ref-nemotron3) | 预训练 | weight+activation | 非均匀 NVFP4 | SFT / RL / MOPD 后训练 |
| [ReQAT](#ref-reqat) | QAT | weight+activation+KV | FP4 | token-selective 训练信号 |
| [TWLA](#ref-twla) | 训练后量化 | weight+activation | ternary + INT4 | 正交旋转 |
| [UltraQuant](#ref-ultraquant) | 推理（KV cache） | KV | 非均匀 FP4 | UE8M0 group scale |
| [ReSET](#ref-reset) | 推理（解码） | weight+activation | 非均匀 NVFP4 | step-entropy 调温 |

应用阶段说明在哪个环节实施量化；张量列说明哪些数值降精度；格式列说明怎样编码；最后一列说明采用何种修复或加速。预训练的 loss、QAT 的推理准确率和推理侧的延迟不是同一个指标，比较时需要分别看其原实验。

表格中的空组合不自动构成研究方向。格式与硬件、张量分布、训练方式可能互相制约；只有先说明可实现性和要修复的具体问题，才有必要检验新的组合。

## 边界：低精度之外的效率杠杆

`[tech report]` [DeepSeek-V4](#ref-deepseekv4)（DeepSeek-AI，2026）适合作为对照。它是 1.6T total / 49B active 的 MoE，将上下文推到 100 万 token，相对前代单 token 推理 FLOPs 降到 **27%**、KV cache 降到 **10%**。这些效率主要来自 Compressed Sparse Attention、Heavily Compressed Attention 和注意力架构压缩，数值精度在这份报告里是次要项。效率有多种路径，数值格式是其中一个维度，注意力架构压缩是另一个。

相同维度也能跨域迁移。`[论文]` [Ideogram 4.0 的 fused INT8 GEMM](#ref-int8dit)（Ideogram，Asaria et al. 2026）在图像 diffusion transformer 上做 W8A8，单 GEMM 比 bf16 快 **2.8 到 4.2 倍**，1024px 出图比 FP8 基线快约 **9.5%**，反量化输出与 bf16 余弦相似度 1.0、画质指标无可测退化。LLM 和图像 DiT 不共享架构，但共享「低精度 kernel」这一维度，说明这条主线不限于语言模型。

## 开放问题

`[本文归纳]` 三个问题仍然开放。

其一，能否在同一模型与数据上同时测量格式偏置、token 熵和激活异常值，并比较它们对精度损失的独立解释力？现有材料不足以把三者合成一个 sharpness 指标。

其二，格式和修复方法怎样相互影响？[UFP4](#ref-ufp4) 的格式与 RHT 配套使用，[TWLA](#ref-twla) 的旋转与量化格式也有联系。这里需要联合消融，不能预设二者正交。

其三，[Nemotron 3 Ultra](#ref-nemotron3) 把低精度预训练和后训练蒸馏放在同一管线。蒸馏改善了哪些任务、其中多少可归因于量化损失的恢复，仍需匹配训练预算的对照；不能仅由两者串联就判断它们修复同一批误差。

## Reference

<a id="ref-ufp4"></a>
**[Rethinking Shrinkage Bias in LLM FP4 Pretraining: Geometric Origin, Systemic Impact, and UFP4 Recipe]** Qian Zhao, Kunlong Chen, Changxin Tian et al.，蚂蚁集团 Ling Team，2026. [arXiv:2606.20381](https://arxiv.org/abs/2606.20381)。本文用到它的 shrinkage bias 几何成因，以及均匀 4-bit 格式 + RHT + 梯度 stochastic rounding 的配方。`[arxiv 论文]`

<a id="ref-nemotron3"></a>
**[Nemotron 3 Ultra: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning]** NVIDIA，2026. [arXiv:2606.15007](https://arxiv.org/abs/2606.15007)。本文用到它组合采用 NVFP4 预训练与 MOPD 等后训练的报告；未据此确认量化损失的恢复量。`[tech report]`

<a id="ref-reqat"></a>
**[ReQAT: Achieving Full-Precision Reasoning Accuracy with 4-bit Floating-Point Quantization-Aware Training]** Janghwan Lee, Sihwa Lee, Jungwook Choi et al.，韩国 Hanyang University AIHA Lab，ICML 2026. [arXiv:2606.15682](https://arxiv.org/abs/2606.15682)。本文用到它的 low-entropy token 失效定位，以及 Trace-Aligned QAT + Selective Entropy Minimization。`[arxiv 论文 / 同行评审]`

<a id="ref-twla"></a>
**[TWLA: Achieving Ternary Weights and Low-Bit Activations for LLMs via Post-Training Quantization]** Zhixiong Zhao, Zukang Xu, Xing Hu, Dawei Yang et al.，Houmo AI，2026. [arXiv:2606.13054](https://arxiv.org/abs/2606.13054)。本文用到它的 Kronecker 正交旋转压制激活 outlier，以及 1.58-bit 权重 + 4-bit 激活。`[arxiv 论文]`

<a id="ref-ultraquant"></a>
**[UltraQuant: 4-bit KV Caching for Context-Heavy Agents]** Inesh Chakrabarti, David Limpus et al.，AMD（含 UCLA / Purdue 实习），2026. [arXiv:2606.20474](https://arxiv.org/abs/2606.20474)。本文用到它的 FP4 KV + FP8 query + UE8M0 group scale，以及 CDNA4 上的 TTFT / 吞吐数据。`[arxiv 论文]`

<a id="ref-reset"></a>
**[ReSET: Accurate Latency-Critical NVFP4 Reasoning via Step-Aware Temperature Scaling]** Sihwa Lee, Janghwan Lee, Jungwook Choi et al.，Hanyang University + Xenoscube，2026. [arXiv:2606.13233](https://arxiv.org/abs/2606.13233)。本文用到它的 step-entropy 自适应调温 + small-M NVFP4 CUDA kernel。`[arxiv 论文]`

<a id="ref-int8dit"></a>
**[Realizing Native INT8 Compute for Diffusion Transformers on Consumer GPUs: A Fused INT8 GEMM Kernel for Ideogram 4.0]** Ali Asaria, Tony Salomone, Deep Gandhi，Ideogram，2026. [arXiv:2606.14598](https://arxiv.org/abs/2606.14598)。本文用作跨域对照：低精度 kernel 这个维度在图像 DiT 上同样成立。`[arxiv 论文]`

<a id="ref-deepseekv4"></a>
**[DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence]** DeepSeek-AI，2026. [arXiv:2606.19348](https://arxiv.org/abs/2606.19348)。本文用作边界对照：长上下文效率主要来自注意力架构压缩这一杠杆。`[tech report]`
