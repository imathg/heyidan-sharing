# 低精度训练的共同主线：损伤集中在分布的尖锐处

<!-- domain: training-infra -->

2026 年 6 月，六个互不隶属的团队在同一个月里把 4-bit 数值精度推到了 LLM 生命周期的每一段。`[论文]` [UFP4](#ref-ufp4)（蚂蚁 Ling Team，Zhao et al. 2026）做 FP4 预训练；`[tech report]` [Nemotron 3 Ultra](#ref-nemotron3)（NVIDIA，2026）把 NVFP4 预训练用到 550B MoE 量产规模；`[论文]` [ReQAT](#ref-reqat)（Hanyang AIHA Lab，Lee et al. 2026）做 W4A4KV4 的量化感知训练；`[论文]` [TWLA](#ref-twla)（Houmo AI，Zhao et al. 2026）做训练后量化；`[论文]` [UltraQuant](#ref-ultraquant)（AMD，Chakrabarti et al. 2026）压 KV cache；`[论文]` [ReSET](#ref-reset)（Hanyang + Xenoscube，Lee et al. 2026）管 NVFP4 推理解码。

把这六篇放到一起读，会发现它们调的是同一组旋钮、针对的是同一个失败模式。

> **核心论点：低精度省下的 bit，在分布的平坦主体上代价小，在尖锐的尾部上代价大。每个配方本质上都在做同一件事，把稀缺的 bit、训练信号或 scale 粒度往尖锐处分配。**

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
  <text x="380" y="36" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="19" font-weight="600" fill="#e8eef2">低精度配方：损伤集中在尖锐处，每个 recipe 把 bit 挪过去</text>
  <text x="380" y="60" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="12.5" fill="#8a96a0">同一组旋钮 · 把稀缺的 bit / 训练信号 / scale 粒度往分布的尖锐处分配</text>
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
    <text x="140" y="184" text-anchor="middle" font-size="10.5" fill="#8a96a0">蒸馏找回</text>
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
  <text x="380" y="288" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="13" font-weight="600" fill="#f0a868">"尖锐处" 是同一现象在三个层上的投影</text>
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
    <text x="600" y="374" text-anchor="middle" font-size="10.5" fill="#7d8893">TWLA · heavy-tail 钉住精度</text>
  </g>
  <text x="380" y="414" text-anchor="middle" font-family="-apple-system,Segoe UI,sans-serif" font-size="10.5" fill="#5b6a76">平坦的高熵主体丢精度无感，尖锐的低熵尾部丢精度掉能力</text>
</svg>

*图：六个 2026 年 6 月的低精度配方按生命周期位置铺开，底部三张卡片是同一个尖锐处在几何 / 语义 / 分布三层的投影。*

## 同一个损伤，三种语言

三篇工作各自描述低精度在哪里出问题，落在不同的抽象层，但指向同一件事。

| 层 | 工作 | 损伤描述 |
|---|---|---|
| 几何 | [UFP4](#ref-ufp4) | E2M1 的可表示值间距不等，高幅值区系统性欠表示 |
| 语义 | [ReQAT](#ref-reqat) | low-entropy token（数字、运算符）被量化噪声放大成级联错误 |
| 分布 | [TWLA](#ref-twla) | heavy-tailed 激活 outlier 把激活钉在高精度 |

`[论文]` [UFP4](#ref-ufp4) 把 NVIDIA/AMD 硬件用的 E2M1（FP4）格式拆开看：可表示值之间间距不等，量化时产生系统性的负向 rounding 误差，论文称之为 shrinkage bias。这个偏置逐层乘性累积，还被训练里常用的 Random Hadamard Transform 进一步放大，解释了既有 E2M1 配方的训练不稳定。问题落在格式的网格几何上。

`[论文]` [ReQAT](#ref-reqat) 看的是 token 分布：把 weight、activation、KV cache 全量化到 4-bit 后，失效集中在 low-entropy token 上。这些是数字、运算符这类精确符号，模型在这里几乎没有不确定性，量化噪声一旦改写就触发级联错误。问题落在分布最尖锐的那批 token 上。

`[论文]` [TWLA](#ref-twla) 看的是激活的形状：heavy-tailed 分布里少数 outlier 决定了量化范围，既有方法因此只能把激活留在高精度，限制端到端加速。问题落在分布的长尾上。

`[本文归纳]` 网格几何的不对称、low-entropy token、激活 outlier，是同一现象在三个层上的投影：损伤集中在分布的尖锐处。平坦的高熵主体丢精度几乎无感，尖锐的低熵尾部丢精度直接掉能力。把有限的精度预算挪到尖锐处，下一节的四组机制做的都是这件事。

## 把精度预算挪到尖锐处的四种机制

| 机制 | 代表 | 做法 |
|---|---|---|
| 换网格几何 | [UFP4](#ref-ufp4) | 用均匀 4-bit（E1M2/INT4）替掉非均匀 E2M1，对三个训练 matmul 都做 RHT，只对梯度做 stochastic rounding |
| 旋转分布 | [TWLA](#ref-twla) | Kronecker 结构正交旋转把权重重塑成 ternary-friendly 的三峰分布，共享旋转同时统计性压制激活 outlier |
| 加细 scale 粒度 | [UltraQuant](#ref-ultraquant) | FP4 KV + FP8 query + UE8M0 group scale，吃 CDNA4 的 native scaled-MFMA |
| 偏置训练信号 | [ReQAT](#ref-reqat) | Trace-Aligned QAT 复访相同 reasoning trace 优先关键决策，Selective Entropy Minimization 强化 low-entropy 位置 |

`[论文]` [UFP4](#ref-ufp4) 的处理直接动格式：既然 E2M1 的网格不对称是病根，就换成均匀的 4-bit 网格。在 Dense 1.5B、MoE 7.9B、MoE 124B 三个规模上，均匀格式的 BF16-relative loss degradation 低于强 E2M1 基线。

`[论文]` [TWLA](#ref-twla) 不动格式动数据：用 Kronecker 结构的正交旋转把权重旋成三峰分布，配合三值量化，同一个旋转还顺手把激活的 outlier 在统计意义上摊平，于是激活也能降到 **4-bit**，权重压到 **1.58-bit**。这是训练后量化，不需要重训。

`[论文]` [UltraQuant](#ref-ultraquant) 的对象是 KV cache，尖锐处在长前缀被多轮复用时的驻留压力。它给 KV 用 FP4、query 用 FP8、group scale 用 UE8M0，在 AMD CDNA4 上 late-round 的 P50 首 token 延迟降到原来的 **1/3.47**（整体 2.3 倍），相对 FP8 KV 基线吞吐 **1.63 倍**。

`[论文]` [ReQAT](#ref-reqat) 既然知道损伤集中在 low-entropy token，就把训练信号往那里偏：Trace-Aligned QAT 反复在同一条 reasoning trace 上对齐关键的低熵决策，Selective Entropy Minimization 强化这些位置的置信。在同等训练预算下，它不只恢复、还超过了 BF16 微调精度，NVIDIA DGX Spark 上 **3.9 倍**、B200 上 **3.1 倍**吞吐。

## 格式几何本身就是个 knob

E2M1 长期被当成硬件给定的常量。[UFP4](#ref-ufp4) 的贡献是把它变回一个可选项：在 4-bit 这个 bit 预算下，非均匀格式（指数位多、把分辨率堆在 0 附近）和均匀格式（INT4/E1M2，分辨率等距铺开）是两种取舍，前者对小值友好、对大值欠表示，后者反过来。LLM 权重和激活经过 Hadamard 旋转后接近高斯，尾部的大值恰恰是尖锐处，于是均匀网格在这个分布上反而吃亏更小。

这条 knob 不限于训练。`[论文]` [ReSET](#ref-reset) 在推理解码端同样面对 NVFP4 的两个问题：reasoning 精度下降，以及 small-batch 自回归解码拿不到低精度本该带来的延迟收益。它按 token 级和 step 级 entropy 在线估计每一步的不确定性、自适应调解码温度，再配一个针对 small-M 的 NVFP4 CUDA-core kernel 补延迟。跨 reasoning benchmark 和模型规模，相对 NVFP4 基线精度提升至多约 **2 点**。entropy 在这里又一次成了判据：高熵步可以容忍更激进的采样，低熵步要收紧。

工业量产规模也在押注这条线。`[tech report]` [Nemotron 3 Ultra](#ref-nemotron3) 是 550B total / 55B active 的 MoE Hybrid Mamba-Attention，20T token 预训练即用 NVFP4，后训练串 SFT、RL 和多教师在线蒸馏（MOPD）把低精度引入的精度差找回，自报相对公开 LLM 约 **6 倍**推理吞吐，checkpoint 和配方已开源。低精度预训练在 100B+ 规模从论文走到了量产 recipe。

## 四个正交 knob

`[本文归纳]` 把这六个方案放到一张表上，它们的差异落在四个彼此正交的维度上。任何一个 2026 的低精度配方，都对应四维空间里的一个具体位点。

| 方案 | K1 lifecycle 位置 | K2 量化张量 | K3 格式几何 | K4 尖锐再分配机制 |
|---|---|---|---|---|
| [UFP4](#ref-ufp4) | 预训练 | weight+activation+gradient | 均匀 INT4/E1M2 | 换网格 + RHT |
| [Nemotron 3 Ultra](#ref-nemotron3) | 预训练 | weight+activation | 非均匀 NVFP4 | MOPD 找回 |
| [ReQAT](#ref-reqat) | QAT | weight+activation+KV | FP4 | token-selective 训练信号 |
| [TWLA](#ref-twla) | 训练后量化 | weight+activation | ternary + INT4 | 正交旋转 |
| [UltraQuant](#ref-ultraquant) | 推理（KV cache） | KV | 非均匀 FP4 | UE8M0 group scale |
| [ReSET](#ref-reset) | 推理（解码） | weight+activation | 非均匀 NVFP4 | step-entropy 调温 |

K1 决定你在哪一段付精度的代价，也就决定了什么会先坏：预训练坏在 loss 不稳，QAT 坏在 reasoning 掉点，推理坏在 KV 驻留和解码延迟。K2 决定哪些张量进低精度，UFP4 把三个训练 matmul 全收进来（含梯度），UltraQuant 只动 KV。K3 是格式几何，UFP4 证明它可调。K4 是把 bit 挪到尖锐处的具体手法，旋转、group scale、token-selective 训练信号各占一种。

把这六篇当六个独立技术看，不如放进四维参数空间里当六个位点，反而更清楚。表里还有大片空格，比如"预训练 + 只 KV + ternary"或"QAT + 格式几何可调"目前没人占，这些空格就是下一批工作的位置。

## 边界：低精度之外的效率杠杆

`[tech report]` [DeepSeek-V4](#ref-deepseekv4)（DeepSeek-AI，2026）是一个有用的对照。它是 1.6T total / 49B active 的 MoE，把上下文推到 100 万 token，相对前代单 token 推理 FLOPs 降到 **27%**、KV cache 降到 **10%**。这些效率的杠杆是 Compressed Sparse Attention、Heavily Compressed Attention 和注意力架构压缩，数值精度在这份报告里是次要项。效率有很多条路径，数值格式是其中一个 knob，注意力架构压缩是另一个。

跨域也有同样的 knob 在转。`[论文]` [Ideogram 4.0 的 fused INT8 GEMM](#ref-int8dit)（Ideogram，Asaria et al. 2026）在图像 diffusion transformer 上做 W8A8，单 GEMM 比 bf16 快 **2.8 到 4.2 倍**，1024px 出图比 FP8 基线快约 **9.5%**，反量化输出与 bf16 余弦相似度 1.0、画质指标无可测退化。LLM 和图像 DiT 不共享架构，但共享"低精度 kernel"这个 knob，说明这条主线不限于语言模型。

## 开放问题

`[本文归纳]` 三个口子还开着。

其一，尖锐处目前有三种代理度量：网格几何的不对称、token 的 entropy、激活的 kurtosis。它们是同一个量的三个侧面，还是各管一段分布？如果能统一成一个可计算的 sharpness 指标，bit 分配就能从启发式变成优化目标。

其二，K3（格式几何）和 K4（再分配机制）有耦合迹象。[UFP4](#ref-ufp4) 换均匀格式后对 RHT 的依赖、[TWLA](#ref-twla) 旋转后对格式的要求，提示"先选格式还是先旋分布"可能彼此牵制。四维正交是从这六篇里归纳出来的工作假设，耦合一旦坐实就要降维。

其三，[Nemotron 3 Ultra](#ref-nemotron3) 用 MOPD 在后训练找回低精度预训练的精度差，把低精度和蒸馏接到了一起。低精度引入的损伤和蒸馏要补的能力，是不是同一批尖锐处？如果是，预训练阶段的格式选择和后训练阶段的蒸馏配方应该联合设计。

## Reference

<a id="ref-ufp4"></a>
**[Rethinking Shrinkage Bias in LLM FP4 Pretraining: Geometric Origin, Systemic Impact, and UFP4 Recipe]** Qian Zhao, Kunlong Chen, Changxin Tian et al.，蚂蚁集团 Ling Team，2026. [arXiv:2606.20381](https://arxiv.org/abs/2606.20381)。本文用到它的 shrinkage bias 几何成因，以及均匀 4-bit 格式 + RHT + 梯度 stochastic rounding 的配方。`[arxiv 论文]`

<a id="ref-nemotron3"></a>
**[Nemotron 3 Ultra: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning]** NVIDIA，2026. [arXiv:2606.15007](https://arxiv.org/abs/2606.15007)。本文用到它的 NVFP4 量产规模预训练 + MOPD 精度找回。`[tech report]`

<a id="ref-reqat"></a>
**[ReQAT: Achieving Full-Precision Reasoning Accuracy with 4-bit Floating-Point Quantization-Aware Training]** Janghwan Lee, Sihwa Lee, Jungwook Choi et al.，韩国 Hanyang University AIHA Lab，ICML 2026. [arXiv:2606.15682](https://arxiv.org/abs/2606.15682)。本文用到它的 low-entropy token 失效定位，以及 Trace-Aligned QAT + Selective Entropy Minimization。`[arxiv 论文 / 同行评审]`

<a id="ref-twla"></a>
**[TWLA: Achieving Ternary Weights and Low-Bit Activations for LLMs via Post-Training Quantization]** Zhixiong Zhao, Zukang Xu, Xing Hu, Dawei Yang et al.，Houmo AI，2026. [arXiv:2606.13054](https://arxiv.org/abs/2606.13054)。本文用到它的 Kronecker 正交旋转压制激活 outlier，以及 1.58-bit 权重 + 4-bit 激活。`[arxiv 论文]`

<a id="ref-ultraquant"></a>
**[UltraQuant: 4-bit KV Caching for Context-Heavy Agents]** Inesh Chakrabarti, David Limpus et al.，AMD（含 UCLA / Purdue 实习），2026. [arXiv:2606.20474](https://arxiv.org/abs/2606.20474)。本文用到它的 FP4 KV + FP8 query + UE8M0 group scale，以及 CDNA4 上的 TTFT / 吞吐数据。`[arxiv 论文]`

<a id="ref-reset"></a>
**[ReSET: Accurate Latency-Critical NVFP4 Reasoning via Step-Aware Temperature Scaling]** Sihwa Lee, Janghwan Lee, Jungwook Choi et al.，Hanyang University + Xenoscube，2026. [arXiv:2606.13233](https://arxiv.org/abs/2606.13233)。本文用到它的 step-entropy 自适应调温 + small-M NVFP4 CUDA kernel。`[arxiv 论文]`

<a id="ref-int8dit"></a>
**[Realizing Native INT8 Compute for Diffusion Transformers on Consumer GPUs: A Fused INT8 GEMM Kernel for Ideogram 4.0]** Ali Asaria, Tony Salomone, Deep Gandhi，Ideogram，2026. [arXiv:2606.14598](https://arxiv.org/abs/2606.14598)。本文用作跨域对照：低精度 kernel 这个 knob 在图像 DiT 上同样成立。`[arxiv 论文]`

<a id="ref-deepseekv4"></a>
**[DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence]** DeepSeek-AI，2026. [arXiv:2606.19348](https://arxiv.org/abs/2606.19348)。本文用作边界对照：长上下文效率主要来自注意力架构压缩这一杠杆。`[tech report]`
