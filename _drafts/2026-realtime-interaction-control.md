# 实时交互 Agent：话轮控制、后台协作与延迟预算

<!-- domain: realtime-interactive-agent -->
<!-- edition_date: 2026-07-26 -->

`[本文归纳]` 用户还在说话时，一句迟到的附和可能听起来像抢话；后台正在查资料时，前台也不能等任务结束才回应用户。这类问题涉及的不只是回答内容，还包括是否应开口、何时让出话轮、什么时候委派后台，以及动作能否按时完成。

下文从 TML 的 200 ms 微话轮、JoyAI 的每秒事件决策，以及话轮指令评测、前后台协作和服务延迟研究中，分别梳理三个问题：模型怎样选择互动动作，前后台怎样协作，服务与安全检查怎样消耗延迟预算。研究使用的动作表和场景并不相同；这里比较接口和证据，不把它们拼成已经验证的统一训练配方。

> 正文每条 claim 都带 `[论文]` / `[tech report]` / `[个人实验]` / `[本文归纳]` 四档 tag 之一。tag 体系见 [本站约定](../../meta/#claim-tags)。

<figure class="diagram">
<svg width="100%" viewBox="0 0 820 620" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="ric-title ric-desc">
<title id="ric-title">实时交互 agent 的分层控制策略</title>
<desc id="ric-desc">音频、视频和 worker 状态构成连续事件流。前台根据说话活动与话轮归属选择控制动作，后台负责较慢的任务执行；服务链路和安全检查引入的延迟会改变实际交互行为。</desc>
<defs>
<linearGradient id="ric-bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#131922"/><stop offset="1" stop-color="#1a2230"/></linearGradient>
<linearGradient id="ric-panel" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#202b38"/><stop offset="1" stop-color="#18212c"/></linearGradient>
<linearGradient id="ric-node" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#273443"/><stop offset="1" stop-color="#1c2632"/></linearGradient>
<linearGradient id="ric-accent-node" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#24464a"/><stop offset="1" stop-color="#1a3037"/></linearGradient>
<marker id="ric-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L8 4L0 8Z" fill="#8b97a4"/></marker>
<marker id="ric-accent-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L8 4L0 8Z" fill="#5fd0c8"/></marker>
</defs>
<rect width="820" height="620" fill="url(#ric-bg)"/>
<text x="42" y="43" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="24" font-weight="650">实时交互 agent 的分层控制策略</text>
<text x="42" y="68" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="13">说话活动、话轮归属、控制动作与任务调度分层；动作时机和执行延迟共同决定最终行为</text>
<rect x="42" y="92" width="736" height="76" rx="18" fill="url(#ric-panel)" stroke="#2a3441"/>
<text x="60" y="117" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="600">连续事件流</text>
<line x1="154" y1="132" x2="744" y2="132" stroke="#5d6977" stroke-width="2" marker-end="url(#ric-arrow)"/>
<path d="M178 132v-10M266 132v-10M354 132v-10M442 132v-10M530 132v-10M618 132v-10M706 132v-10" stroke="#5d6977" stroke-width="1.5"/>
<rect x="174" y="104" width="84" height="22" rx="10" fill="#1c2632" stroke="#2a3441"/><text x="216" y="119" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">音频输入</text>
<rect x="338" y="104" width="84" height="22" rx="10" fill="#1c2632" stroke="#2a3441"/><text x="380" y="119" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">视频输入</text>
<rect x="502" y="104" width="112" height="22" rx="10" fill="#1c2632" stroke="#2a3441"/><text x="558" y="119" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">worker 状态</text>
<text x="164" y="153" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="12.5">200 ms 微话轮</text>
<text x="548" y="153" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="12.5">1 s 事件周期</text>
<path d="M400 168V190" stroke="#8b97a4" stroke-width="1.5" marker-end="url(#ric-arrow)"/>
<rect x="42" y="192" width="504" height="255" rx="18" fill="url(#ric-panel)" stroke="#2a3441"/>
<text x="64" y="222" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="650">前台话轮控制</text>
<text x="64" y="243" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="12.5">依据说话活动、话轮归属、语境与风险选择动作</text>
<rect x="64" y="264" width="136" height="68" rx="11" fill="url(#ric-node)" stroke="#2a3441"/><text x="82" y="290" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="600">listen</text><text x="82" y="312" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">持续接收线索</text>
<rect x="220" y="264" width="136" height="68" rx="11" fill="url(#ric-node)" stroke="#2a3441"/><text x="238" y="290" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="600">backchannel</text><text x="238" y="312" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">短确认与承接</text>
<rect x="376" y="264" width="136" height="68" rx="11" fill="url(#ric-node)" stroke="#2a3441"/><text x="394" y="290" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="600">take floor</text><text x="394" y="312" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">接过话轮或打断</text>
<rect x="142" y="350" width="136" height="68" rx="11" fill="url(#ric-node)" stroke="#2a3441"/><text x="160" y="376" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="600">hold floor</text><text x="160" y="398" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">保持话轮并继续说</text>
<rect x="298" y="350" width="136" height="68" rx="11" fill="url(#ric-node)" stroke="#2a3441"/><text x="316" y="376" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="600">yield floor</text><text x="316" y="398" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">停止输出并让出话轮</text>
<path d="M512 332C570 332 572 292 600 292" fill="none" stroke="#5fd0c8" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#ric-accent-arrow)"/>
<text x="548" y="324" fill="#5fd0c8" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">任务调度</text>
<rect x="600" y="224" width="178" height="160" rx="18" fill="url(#ric-panel)" stroke="#2a3441"/>
<text x="622" y="254" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="650">后台任务调度</text>
<rect x="622" y="272" width="134" height="24" rx="10" fill="url(#ric-accent-node)" stroke="#5fd0c8"/><text x="689" y="288" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">delegate async</text>
<rect x="622" y="306" width="62" height="24" rx="10" fill="url(#ric-node)" stroke="#2a3441"/><text x="653" y="322" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">cancel</text>
<rect x="694" y="306" width="62" height="24" rx="10" fill="url(#ric-node)" stroke="#2a3441"/><text x="725" y="322" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">defer</text>
<path d="M688 342C688 420 559 431 516 410" fill="none" stroke="#5fd0c8" stroke-width="2" marker-end="url(#ric-accent-arrow)"/>
<text x="570" y="435" fill="#5fd0c8" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">整合、延后或丢弃过期结果</text>
<rect x="42" y="475" width="736" height="82" rx="18" fill="url(#ric-panel)" stroke="#2a3441"/>
<text x="64" y="502" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="650">执行窗口</text>
<rect x="174" y="492" width="108" height="42" rx="10" fill="url(#ric-node)" stroke="#2a3441"/><text x="228" y="518" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14">感知</text>
<rect x="292" y="492" width="108" height="42" rx="10" fill="url(#ric-node)" stroke="#2a3441"/><text x="346" y="518" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14">决策</text>
<rect x="410" y="492" width="108" height="42" rx="10" fill="url(#ric-node)" stroke="#2a3441"/><text x="464" y="518" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14">安全约束</text>
<rect x="528" y="492" width="108" height="42" rx="10" fill="url(#ric-node)" stroke="#2a3441"/><text x="582" y="518" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14">执行</text>
<text x="694" y="510" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">P50 / P95</text>
<text x="694" y="529" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">jitter</text>
<path d="M464 475C464 456 410 456 340 447" fill="none" stroke="#8b97a4" stroke-width="2" stroke-dasharray="1 7" marker-end="url(#ric-arrow)"/>
<text x="250" y="466" fill="#8b97a4" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="11.5">服务链路与安全检查的延迟改变实际行为</text>
<line x1="42" y1="582" x2="778" y2="582" stroke="#2a3441"/>
<text x="410" y="607" text-anchor="middle" fill="#e6edf3" font-family="-apple-system,'PingFang SC','Microsoft YaHei',sans-serif" font-size="14" font-weight="600">说话活动与话轮归属 × 控制动作 × 任务调度 × 执行延迟 = 最终行为</text>
</svg>
</figure>

<a id="能力对象-带时序约束的控制动作"></a>

## 区分谁在说话、谁持有话轮与系统该做什么

`[tech report]` [Interaction Models](#ref-tml-interaction)（Thinking Machines Lab，2026）将连续交互编码为模型输入。音频、视频和文本被切成 200 ms 的微话轮，沉默、重叠、用户插话与模型输出在统一时间轴上展开。该工作的交互性评测同时要求回答语义正确，并在规定的时间窗口内送达；内容相同而时机不同，会得到不同分数。

`[论文]` [JoyAI-VL-Interaction](#ref-yao2026)（JD.com，Yao et al. 2026）采用每秒一次的事件决策。8B 前台模型持续观看视频，在 `silent / respond / delegate` 三个动作中选择；ASR、TTS、记忆、界面和后台模型均可替换。作者在自建测试中分别比较 JoyAI 与豆包、Gemini，报告的胜率为 77.6% 和 87.9%；这些结果只适用于上述测试条件。

`[论文]` [对话系统与人机交互中的话轮转换综述](#ref-skantze2021)（KTH Royal Institute of Technology，Skantze 2021）以对话分析为理论基础，区分当前说话者保持或让出话轮、听者接过话轮，并将简短附和与用户打断作为需要单独处理的互动现象。综述还指出，只看 VAD 发声模式不能可靠判定一次重叠是否构成打断。这套研究传统提供了稳定概念，但没有形成适用于所有系统的单一互斥动作表。

`[本文归纳]` 不同研究会按任务设置动作表；跨文献较稳定的做法，是把可观测的说话活动、话轮组织和系统动作分开。工程系统还会单独处理后台任务的执行、生命周期和结果处置。本文据此采用三层分类：第一层记录当前观察到的说话活动和推断出的话轮归属；第二层从五个话轮控制原语中选择动作；第三层处理内部任务。行业通用层对应前述话轮概念，五个原语则是本文用于跨系统对齐的具体接口。在这个接口中，`silent` 对齐为 `listen` 或无口头输出的结果，`interrupt` 对齐为用户持有话轮时的 `take floor`，`delegate` 对齐为内部任务调度。

| 层 | 触发状态 | 规范动作 | 含义 |
|---|---|---|---|
| 说话活动 | 持续观测 | user-only / agent-only / overlap / silence | 记录音频中谁在说话；重叠只说明同时发声，不自动表示谁持有话轮 |
| 话轮归属 | 结合语境推断 | user holds / agent holds / floor open / contested | 表示谁可以继续说；这是五类控制动作的条件 |
| 话轮控制 | 任意话轮归属 | listen / backchannel / take floor / hold floor / yield floor | 继续听；简短附和；接过话轮；保持话轮；让出话轮 |
| 内容功能 | 控制动作已经选定 | answer / warning / progress update / repair | 决定具体说什么；主动打断是“用户持有话轮时 take floor”，确认并调整则是“yield floor 后 repair” |
| 任务执行 | 任意话轮状态 | execute inline / delegate asynchronously | 选择前台直接处理或委派后台 |
| 任务生命周期 | 后台任务运行中 | continue / suspend / resume / cancel or preempt | 控制任务继续、暂停、恢复、取消或抢占 |
| 结果处置 | 后台结果返回 | integrate / defer / discard stale result | 立即纳入前台、延后使用，或丢弃已经过期的结果 |

`[本文归纳]` 这里的“实时”同时包含系统性能和动作时机。系统需要回答三个问题：执行什么动作、何时开始、能否在动作有效期内完成。任一项缺失，都会让离线看来正确的输出在交互中变成错误行为。

## 流畅与可控是两项指标

`[论文]` [Instruct-FD](#ref-tang2026)（Boson AI，Tang et al. 2026）测试六个全双工语音系统能否按自然语言指令调整话轮策略。它按当前说话者区分两类动作：用户说话时测试 `listen / backchannel / interrupt`，模型说话且用户插话时测试 `continue / acknowledge`。映射到本文采用的话轮控制原语，`interrupt` 是用户持有话轮时的 `take floor`，`continue` 是 `hold floor`，`acknowledge` 则由 `yield floor` 与后续语义修复组成。表现最好的系统指令遵循率为 64.4%，主动附和与主动打断尤其困难。系统即使对话流畅，也可能忽略“辅导时及时纠错”或“咨询时尽量少打断”这类应用策略。

`[论文]` 绝对遵循率仍不足以证明策略受指令控制。Instruct-FD 还比较同一段对话在有指令和无指令条件下的表现，用 `ΔIAS` 衡量指令带来的行为变化。部分系统在用户插话后倾向于继续说，难以区分简短附和与纠正、改口；个别动作甚至在加入指令后下降。这说明评测既要检查动作是否正确，也要检查指令是否真正改变了默认策略。

`[本文归纳]` 因此，语音自然度和话轮可控性需要分开测量。自然度衡量输出听起来怎样；可控性衡量策略能否随角色、风险和场景切换。若产品只优化 MOS、语义正确率或响应速度，它仍可能把默认社交习惯照搬到不同应用中。

`[论文]` [多人对话中的连续受话指向研究](#ref-mori2026)（京都大学，Mori et al. 2026）提供了更细的观测变量。多位标注者给出的受话指向强度（address level，指话语对某位参与者的指向程度）比离散受话人标签更贴合数据；除下一位说话者外，视线与简短附和（backchannel）也和受话指向有关。这项工作研究人类多人对话，说明受话指向和话轮转换不能只用离散的下一位说话者标签表示。

`[论文]` [Silence Thresholds](#ref-arnold2026)（University of Richmond + ALTAE, Université Paris Cité，Arnold et al. 2026）比较 30 部美国情景喜剧与 51 个 NotebookLM 合成播客中的停顿，分析性别和制作场景带来的差异。论文摘要没有给出可直接引用的统一阈值。

`[本文归纳]` 这项研究把对话类型作为变量，说明固定超时阈值至少需要经过跨场景验证；当前摘要不足以给出效应方向或统一阈值。

`[本文归纳]` 可观测信号可按三层组织：

| 层 | 信号 | 对控制策略的作用 |
|---|---|---|
| 内容 | 语义完整度、问题类型、风险等级 | 判断是否需要回应、提醒或升级 |
| 互动 | 停顿、重叠、语调、视线、简短附和、受话指向强度 | 判断话轮状态与介入强度 |
| 系统 | 推理队列、工具状态、端到端延迟、安全检查结果 | 判断某个动作能否在窗口内完成 |

`[本文归纳]` 将这些信号简化为一个“用户是否说完”的标签，会漏掉两种状态：用户仍在说但允许附和，以及用户已经停顿但系统仍应沉默。连续交互更适合预测话轮状态、控制动作和时间窗口，再由产品策略约束动作选择。

<a id="前台负责协调-后台负责深度"></a>

## 前台持续对话，后台执行长任务

`[tech report]` TML 的交互模型与异步后台模型共享上下文。前台维持随时可用的交互循环，后台执行较长推理和工具调用；结果返回后，由前台判断何时向用户传达。`[论文]` JoyAI 使用 `delegate` 动作连接 8B 前台与可替换后台模型。`[论文]` [JarvisBench](#ref-chen2026)（NVIDIA，Chen & Chen 2026）则由两个 agent 分担前后台职责：语音协调 agent 回应进度询问、报告遇到的困惑，并将用户的指导传给仍在运行的 worker。

`[本文归纳]` 三种方案都把低延迟协调与较慢的任务处理分成两个协同循环：

| 循环 | 优化目标 | 典型动作 | 失败表现 |
|---|---|---|---|
| 前台协调 | 持续在场、时机、用户控制 | 听、附和、提醒、打断、委派 | 反应迟、抢话、错过介入点 |
| 后台推理 | 任务深度、工具使用、完成质量 | 搜索、规划、执行、长答案 | 推理浅、任务未完成、证据不足 |

`[论文]` JarvisBench 包含 agent-collaboration 与 user-interaction 两组评测。34 个 WildClaw 文本任务上的初步结果显示，基于 worker 当前轨迹的回答和时机合适的指导可以改善任务表现，效果明显依赖协调 agent 所用的模型。这组结果属于小规模初步验证；这项工作由此定义了“前台继续对话、后台继续工作、指导可传回后台”的控制接口。

`[本文归纳]` 双循环对应两个不同的时钟。前台以数百毫秒到秒为单位维护互动；后台以任务步骤和工具返回为单位推进工作。两者需要共享事件、状态和来源记录，也需要明确的委派、取消、抢占和结果返回动作。把所有计算串在一条同步链上，会迫使短时互动与长时推理争用同一延迟预算。

## 部署栈约束动作能否按时执行

`[论文]` [FlashRT](#ref-agarwal2026)（Carnegie Mellon University + AMD + University at Buffalo，Agarwal et al. 2026）用 agent 执行框架优化实时多模态应用的设备放置、流式执行和并行策略。论文按其测试口径报告：在 NVIDIA B200 上，时延最多降至优化前的约 1/70，吞吐量提升 2.8 倍；在 AMD MI355X 上，峰值吞吐量最高提升 3.6 倍，并将 Qwen3-Omni text-to-audio 相对专家实现的响应延迟降低 65%。这些数值描述特定硬件与工作负载，说明同一模型的可用动作窗口会随部署实现变化。

`[论文]` [Speech2Speech Safeguards](#ref-endler2026)（codemanufaktur + BMW Group，Endler et al. 2026）以汽车语音助手为例，说明安全检查带来的另一重约束。转写检查与基于工具的检查会给每次回答增加 0 到 1.4 秒；工具路径还会引入非确定性。这个区间属于论文测试的汽车系统。它揭示的共同约束是，外置安全决策和对话动作占用同一段端到端延迟预算。

`[本文归纳]` 延迟会改变交互行为的语义。事实回答稍晚送达可能仍然正确；附和稍晚送达会显得在抢话，打断稍晚发生可能错过风险窗口，拒绝稍晚发生则可能让不安全输出先行。服务优化与安全架构因此共同构成最终策略的执行层。

`[本文归纳]` 一条端到端时间预算可以拆成：

| 时间段 | 主要来源 | 可调手段 |
|---|---|---|
| 感知 | 音视频编码、分帧、ASR | 流式编码、时间粒度、触发模态 |
| 决策 | 前台模型推理、动作采样 | 小模型、缓存、早退、动作空间 |
| 约束 | 安全分类、规则、工具检查 | 同步或异步、风险分级、可撤回输出 |
| 执行 | TTS、渲染、网络发送 | 流式合成、并行、设备放置 |
| 后台 | 长推理、检索、工具调用 | 委派、取消、结果返回时机 |

`[本文归纳]` 一个待业务验证的设计方向，是按风险和可逆性分配延迟预算。需要阻断的高风险动作进入同步路径；低风险提示、日志审计和较慢复核可以异步运行；允许撤回的输出与不可逆工具动作使用不同门槛。现有来源证明了外置检查会增加延迟，尚未验证这套分层对所有业务都成立。

## 系统、训练与评测需要同一套字段

`[本文归纳]` 现有工作可以用七个设计维度描述。把各维度的取值写清楚后，模型、产品和基础设施团队便能使用同一套描述。

| 维度 | 典型取值 | 代表来源 |
|---|---|---|
| 决策位置 | 外部 VAD / 规则；模型原生策略；前台协调 agent | TML、JoyAI、JarvisBench |
| 时间粒度 | 完整话轮；停顿阈值；1 秒事件；200 ms 微话轮 | Silence Thresholds、JoyAI、TML |
| 触发模态 | 音频；音频 + 视频；worker 状态 | TML、JoyAI、JarvisBench |
| 控制动作 | listen / backchannel / take floor / hold floor / yield floor | Instruct-FD、TML |
| 控制来源 | 学到的默认策略；自然语言指令；可编程安全规则 | Instruct-FD、Speech2Speech Safeguards |
| 任务执行与生命周期 | inline / delegate；continue / suspend / resume / cancel；integrate / defer / discard | TML、JoyAI、JarvisBench |
| 延迟预算 | 模型推理；多模态服务；安全检查；工具调用 | FlashRT、Speech2Speech Safeguards |

`[本文归纳]` 这些维度可以分别描述和配置，但当前没有来源联合消融决策位置、控制来源与延迟预算，不能预设它们彼此独立。训练样本至少需要保存以下字段：

| 样本字段 | 应保存的内容 | 作用 |
|---|---|---|
| 活动与话轮 | user-only / agent-only / overlap / silence；话轮归属；多方受话指向 | 分开记录声学活动与话轮归属，避免把所有重叠或沉默视为同一种状态 |
| 策略指令 | 角色、场景、风险规则、主动程度 | 区分人类默认行为与产品要求的目标行为 |
| 控制动作 | listen / backchannel / take floor / hold floor / yield floor | 监督前台话轮控制 |
| 时间约束 | 触发点、允许起始窗口、截止时间、结束或取消时间 | 让“内容正确但时机错误”成为可训练、可评测的失败 |
| 内容与任务调度 | 回答、提醒、进度说明、语义修复；任务执行、生命周期和结果处置 | 分开学习说什么、何时说以及由哪条计算路径完成 |
| 来源与质量 | 人类行为、产品规则、偏好反馈、自动标注及其置信度 | 保留监督信号的来源和噪声边界 |

`[本文归纳]` 训练和评测都需要显式保留“不行动”的机会点，否则模型只会学习何时说，不会学习何时继续听。同一段对话可以配多条策略指令和一个无指令基线，用成组样本测量指令是否真正改变策略。Instruct-FD 已验证这种构造适合评测，但还不能据此断言它是有效的训练配方。

`[本文归纳]` 对应的评测需要从单一答案分数扩展为五个评测面。内容质量评估“说了什么”；其余四项评估“是否该说、何时说、指令是否改变策略，以及真实系统能否按时执行”。

| 评测面 | 最小观测 | 容易遗漏的失败 |
|---|---|---|
| 内容质量 | 正确性、相关性、语音自然度 | 内容好但抢话 |
| 动作选择 | 各动作的准确率、误介入率、漏介入率 | 默认策略不适合当前角色，或沉默占多数导致总体准确率虚高 |
| 时间窗口 | 触发点、开始时间、停止时间、截止时间命中率 | 语义正确但动作已经过期 |
| 策略可控 | IAS；同一输入有无指令时的 ΔIAS | 提示词改变措辞却不改变话轮行为 |
| 系统执行 | P50/P95 端到端延迟、停止延迟、响应延迟、取消成功率 | 平均值合格，但尾部延迟让动作频繁错过时间窗口 |

`[论文]` Instruct-FD 覆盖 29 个英文场景，主要由约两轮模型发言的合成对话组成，并依赖 ASR、时间对齐和 LLM judge。论文用人类标注验证了判分方法，但简短附和仍存在离线标注与在线因果感知不一致。64.4% 适用于这组评测条件，不能直接推及其他语言、场景或更长对话。

## 尚待回答的三个问题

`[本文归纳]` 第一个问题是动作监督从哪里来。人类对话的停顿、视线和简短附和能提供弱标签，产品规则能提供明确边界，用户是否接受打断则构成偏好信号。人类行为描述“通常怎么做”，不自动等于特定产品“应该怎么做”。这些信号的时间粒度与噪声水平不同，训练数据需要保留事件时间戳、策略指令、动作来源和原始信号形态。

`[本文归纳]` 第二个问题是前台与后台如何共享状态。共享完整上下文成本高，压缩状态又可能漏掉用户刚才的语气、当前 worker 步骤或取消指令。可检验的接口应至少包含事件时间、系统已经作出的承诺、后台进度、可取消动作和证据位置，让前台能解释、打断或改写后台计划。

`[本文归纳]` 第三个问题是安全检查放在哪条时间路径上。同步检查适合不可逆动作，异步检查适合可撤回内容，模型内约束适合高频、低延迟决策。不同组合会改变用户感受到的打断、沉默和拒绝，因此安全评测需要同时记录动作结果与发生时刻。

> **结论：实时交互 agent 的核心，是根据连续事件流反复作出控制决策。话轮状态决定当前有哪些动作可选，前后台分工决定任务由哪条路径完成，服务与安全栈决定动作能否在时间窗口内执行。**

## Reference

<a id="ref-skantze2021"></a>
**[Turn-taking in Conversational Systems and Human-Robot Interaction: A Review]** Gabriel Skantze，KTH Royal Institute of Technology，2021. [Computer Speech & Language, 67:101178](https://www.sciencedirect.com/science/article/pii/S088523082030111X)。本文据此区分说话活动、话轮保持与让出、接过话轮、简短附和和用户打断，并界定 VAD 对话轮语义判断的能力边界。`[同行评审综述]`

<a id="ref-tml-interaction"></a>
**[Interaction Models: A Scalable Approach to Human-AI Collaboration]** Thinking Machines Lab，2026. [Official technical post](https://thinkingmachines.ai/blog/interaction-models/)。本文据此讨论 200 ms 微话轮、模型原生交互、前台与异步后台共享上下文，以及内容与时机联合评测。`[tech report / 业界自报]`

<a id="ref-yao2026"></a>
**[JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence]** Dingyu Yao, Junhao Zhou, Chenxu Yang, Chuanyu Qin, Haowen Hou, Zheming Liang, Congcong Wang, Yuhang Cao, Shenglong Ye, Shuai Xie, Shuhuan Gu, Haoyang Huang, Qingyi Si, Nan Duan, Jiaqi Wang，JD.com，2026. [arXiv:2606.14777](https://arxiv.org/abs/2606.14777)。本文据此讨论每秒 `silent / respond / delegate` 动作、8B 前台模型、可替换系统组件，以及六类流式场景的作者评测。`[arxiv 论文]`

<a id="ref-tang2026"></a>
**[Instruct-FD: Can Your Full-Duplex Speech System Follow Turn-Taking Instructions?]** Yuzhi Tang, Wentao Ma, Xiling Zhao, Ahmad Salimi, Sepehr Harfi Moridani, Dongming Shen, Jixuan Wang, Abdulrahman Abdulrazzag, Murdock Aubry, Yu-Hua Chen, Daniel Lee, Jaewon Lee, Jonah Mackey, Silin Meng, Nicholas Stranges, Chenxu Xiong, Hao Yu, Yi Zhu, Mu Li, Alex Smola，Boson AI，2026. [arXiv:2607.20460](https://arxiv.org/abs/2607.20460)。本文据此讨论基于指令的话轮管理评测、六系统比较，以及主动附和和打断的可控性缺口。`[arxiv 论文]`

<a id="ref-mori2026"></a>
**[On the Structure of Address in Multi-Party Dialogue: From Discrete Labels to Continuous Levels]** Taiga Mori, Koji Inoue, Divesh Lala, Tatsuya Kawahara，Graduate School of Informatics, Kyoto University，2026. [arXiv:2607.15648](https://arxiv.org/abs/2607.15648)。本文据此讨论连续受话指向强度、多标注者数据，以及视线、简短附和与话轮转换的关系。`[arxiv 论文]`

<a id="ref-agarwal2026"></a>
**[FlashRT: Agent Harness for Guiding Agents to Deploy Real-Time Multimodal Applications]** Krish Agarwal, Zhuoming Chen, Yanyuan Qin, Zhenyu Gu, Atri Rudra, Beidi Chen，Carnegie Mellon University + AMD + University at Buffalo，2026. [arXiv:2607.18171](https://arxiv.org/abs/2607.18171)。本文据此讨论其对设备放置、流式执行和并行策略的测量驱动优化，以及特定硬件上的延迟和吞吐量结果。`[arxiv 论文]`

<a id="ref-endler2026"></a>
**[Safeguards for Speech2Speech LLM-Assistants: A Case Study in Automotive Applications]** Gregor Endler, Sebastian Kraus, Lukas Stappen，codemanufaktur GmbH + BMW Group，2026. [arXiv:2607.21180](https://arxiv.org/abs/2607.21180)。本文据此讨论基于转写与工具的安全检查在汽车场景中的比较，以及 0 到 1.4 秒延迟观测。`[arxiv 论文]`

<a id="ref-chen2026"></a>
**[Just a Rather Very Intelligent Spoken Agent]** Chen Chen, Zhehuai Chen，NVIDIA，2026. [arXiv:2607.16610](https://arxiv.org/abs/2607.16610)。本文据此讨论 JarvisBench 的前台协调 agent / 后台 worker 架构、两组评测和 34 个 WildClaw 任务的初步结果。`[arxiv 论文]`

<a id="ref-arnold2026"></a>
**[Modeling Turn-Taking with Distant Viewing: Investigating Silence Thresholds in Human and AI-Generated Discourse]** Taylor Arnold, Nicolas Ballier, Artem Saloev，Data Science and Statistics, University of Richmond + ALTAE, Université Paris Cité，2026. [arXiv:2607.18076](https://arxiv.org/abs/2607.18076)。本文据此讨论情景喜剧和合成播客停顿的跨场景分析设计，用来界定固定停顿阈值的适用边界。`[arxiv 论文]`
