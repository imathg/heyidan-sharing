# AI repo，其实就是一套团队级 harness
<!-- source: Feishu G5ILdiUHLo1LAXxW42ucwcrQnru · revision 178 · 2026-08-07 -->

本文是我对 AI repo 的一点思考：我把一些跨项目可用的观点和设计抽出来，核心其实是这两句话：

> **AI repo 实际上是日常办公的团队级 harness。**
>
> **把 harness 当成产品来设计、做到 可复利，越用越好。**

这里以笔者曾经开发过的一套团队仓库为例：

- `fido_cc` 是团队 harness 的能力分发仓，里面放可分发的 plugin、skill、CLI 和工作流，AutoResearch 也可以作为一个 plugin 放进来；
- `fido_wiki` 是中心化知识库仓，用来管理来源、编译知识，再往外分发。

先放一张图，把 harness、workspace、各类 owner，还有现场经验怎么回流，串起来看一下：

<figure class="article-figure hero-diagram"><img src="assets/00-overview.jpg" alt="团队 harness、workspace、owner 与知识回流的整体关系"><figcaption>团队 harness、workspace、owner 与知识回流的整体关系</figcaption></figure>

## harness 仓与 workspace 隔离

> harness 包含：harness-plugin、harness-knowledge。

先说一个边界：harness 不是项目本身。harness 得足够可复用，workspace 得足够灵活。

harness 仓做的，就是把团队能力和团队知识打包成能安装、能升级的一套东西；workspace 才是 Agent 真正干活的地方，实验、代码、run、文档和 ledger 都留在现场。这样 harness 可以单独迭代，**每一个** workspace 也能按自己的需要安装、组合。

至于要开几个 workspace，我觉得主要看项目之间的关系。关系很近，放在一个 workspace 里会更好，很多项目知识可以直接共用；关系没那么大，就分开。即使分开，也还是可以挂同一份团队知识库。

### plugin 设计

<div class="image-grid columns-2">
<figure><img src="assets/01-team-harness-repo.png" alt="harness 仓里的 plugin、技能地图和 workspace 契约模板"><figcaption>harness 仓里的 plugin、技能地图和 workspace 契约模板</figcaption></figure>
<figure><img src="assets/02-fido-and-fido-exp.png" alt="fido 与 fido-exp 两个 plugin 的组织方式"><figcaption>fido 与 fido-exp 两个 plugin 的组织方式</figcaption></figure>
</div>

这里的 plugin，可以先简单理解成一组技能和工具的打包。一个团队仓里可以有多个 plugin，下游 workspace 需要哪个，就启用哪个。

拿 fido_cc 这个例子来说，目前主要就是 `fido` 和 `fido-exp` 这两个；我自己的 harness 也是同样的分发方式，但 owner 不混在一起：`work-tools` 放公司通用工具，`persona` 放个人交互和判断，`research-harness` 放 auto-research。

<div class="image-grid columns-2">
<figure><img src="assets/03-work-tools.png" alt="我的通用工具仓与 plugin 分发"><figcaption>我的通用工具仓与 plugin 分发</figcaption></figure>
<figure><img src="assets/04-persona-research-harness.png" alt="个人交互能力与 auto-research 能力分开维护"><figcaption>个人交互能力与 auto-research 能力分开维护</figcaption></figure>
</div>

安装、启用、更新其实是三件事。安装看能力有没有进当前环境，启用看这次哪些 plugin 生效，更新则决定什么时候接收新版本。装上了，不代表这次一定要启用；有了新版本，也可以先留在老版本，准备好了再升级。

这些仓和真正干活的 workspace 是分开的。像 AI Guest、rubrics、llm-mutate-factor，都是我自己不同项目的 workspace。每个项目的现场状态留在自己那边，harness 只把通用能力挂进去。

<figure class="article-figure"><img src="assets/05-harness-workspace-isolation.png" alt="harness 仓、知识库与多个实际 workspace 各自独立"><figcaption>harness 仓、知识库与多个实际 workspace 各自独立</figcaption></figure>

## 设计理念

我做这些设计，出发点其实都一样：怎么让 Agent 自己能干活，而不是每次都要人教。人面对的界面还是自然语言：研究员把目标、材料、判断说清楚，Agent 自己去找 skill、MCP、CLI 和知识入口，再执行、核验、落档。人不用先背一套工具菜单，也不用把问题翻译成命令。


所以我更关心的是，Agent 能不能把需要的能力一点点找出来。先用宿主原生的 skill description 和 MCP schema 匹配意图；单个描述不够、任务又跨了几个能力，或者宿主没有原生发现时，再去读**技能地图**，进到具体的 skill 和 reference。复杂性留在 Agent 这边，不推回给人。


状态这块，我尽量走 source-first、file-first。**`fido_cli`** 不额外搞数据库；配置、metadata、文档、run 和 ledger 都落在 workspace 的文件里。人看到的、Agent 改的、Git 管的，其实就是同一份状态。

### 具体分发什么

- **`fido_cli`**：file-first 的底座，init、状态、文档、升级这些基础操作都走它。
- **`fido` plugin**：执行层，团队工具能力和 skill family 都从这里分发。
- **`fido-exp` plugin**：实验生命周期层，把立项、落地、训练、评测、对比、归档和升格串起来；具体执行继续调用 `fido`。
- **`CLAUDE.md.tmpl`**：workspace 的 Agent 工作契约；允许下游个性化 merge。
- **技能地图**：给 Agent 做长尾能力的渐进式发现。
- **知识库 out**：把团队知识编译并挂载到 workspace。

> 附件：[CLAUDE.md](assets/CLAUDE.md.txt)

初始化的时候，宿主会生成各自的加载配置，适配 Claude Code、Codex 和 TRAE；但底下复用的还是同一套业务能力和 fido_cli 契约。入口可以不一样，业务能力没必要重做三遍。

`CLAUDE.md.tmpl` 就是给 workspace 用的 Agent 工作契约模板。没有现成 workspace 时，`fido_cli init` 会用它生成一份 `CLAUDE.md`；已经有自己用顺手的 workspace，就和现有的 `CLAUDE.md` merge 一下。这样团队协议能进来，自己的习惯也不用丢。

### plugin、skill、MCP、CLI 怎么分

这几个东西，我自己的划分是：skill 和 reference 更偏 runtime，告诉 Agent 这次任务怎么做、边界在哪；CLI 负责结构化执行，把状态写回文件；MCP 只接边界清楚、调用频繁、结构稳定的动作。原生 plugin 不光能装 skill，后面还可以继续装 subagent、command 和 hook。

<div class="image-grid columns-2">
<figure><img src="assets/06-fido-layering.png" alt="fido、fido-exp、fido_cli 与 workspace 的分层"><figcaption>fido、fido-exp、fido_cli 与 workspace 的分层</figcaption></figure>
<figure><img src="assets/07-plugin-extension.png" alt="原生 plugin 后续可以继续承载 subagent、command 与 hook"><figcaption>原生 plugin 后续可以继续承载 subagent、command 与 hook</figcaption></figure>
</div>

能力多起来以后，也不能最后摊成一个大菜单。像 AB、Ark、数据分析，很多时候都不是一个工具能讲清楚，而是一整个能力 family：

<div class="image-grid columns-3">
<figure><img src="assets/08-ab-capability-family.png" alt="AB 由平台读取、下钻、session 质量分析和横向对比组合而成"><figcaption>AB 由平台读取、下钻、session 质量分析和横向对比组合而成</figcaption></figure>
<figure><img src="assets/09-ark-capability-family.png" alt="Ark 会继续依赖 Devbox、TOS 等执行面"><figcaption>Ark 会继续依赖 Devbox、TOS 等执行面</figcaption></figure>
<figure><img src="assets/10-data-capability-family.png" alt="数据查询、HDFS、对象存储和 case 分析共同组成数据能力 family"><figcaption>数据查询、HDFS、对象存储和 case 分析共同组成数据能力 family</figcaption></figure>
</div>

## 仓库与数据边界

harness 能分发能力，但不能顺手把所有东西都吞进来。我自己的划分大概是这样：

- **fido_cc（能力分发仓）**：团队可分发的 plugin、skill、CLI 和工作流都放这里。AutoResearch 也可以作为插件放进来；个人实验数据不进这个仓。
- backend 仓：训练、评测和产品代码；workspace 记录精确版本或链接。
- **fido_wiki（中心化知识库仓）**：团队长期知识放这里，source、registry、compile、out 这一套都在这边管理。
- HDFS / 远端文档 owner 桶：大产物、过程镜像和需要远端共享的数据。
- workspace：当前项目的 config、docs、code、runs、ledger，以及 Agent 实际干活的 local truth。
- 个人知识库与个人 harness：个人长期知识、交互偏好和 rules，不混进团队公共契约。

这么拆，主要是想让每类状态都有真正的 owner：能力仓升级不会动到实验状态，知识编译不去接管 backend，个人偏好也不会变成全团队的默认规则。


工具仓和知识库分成两个仓，还有一个很实际的原因：两者的更新频率不一样。工具仓按需更新，有新能力或者修了问题再发版本；知识库则是日常更新，每天持续 ingest 和 compile。如果放在一个仓里，知识更新会和工具版本搅在一起，两边都不好管。

## 中心化管理知识库

harness 更多是在管“怎么做”。但“团队已经知道什么”，得靠知识库来承接。我不想把它只做成一个搜索框，而是想做成一条能持续维护的生产线。

### 可配置来源

来源这块，我先从可管理的 seed 开始：文档根目录、参考文档、IM 群聊、妙记、分享会、论文、代码仓这些。先对 seed 做发现，结果进 manifest；只有经过维护者确认，或者命中明确自动激活规则的来源，才会进 `activated_sources`。

<div class="image-grid columns-3">
<figure><img src="assets/11-source-inventory.png" alt="source inventory：冷启动由维护者筛选，routine 处理后续来源"><figcaption>source inventory：冷启动由维护者筛选，routine 处理后续来源</figcaption></figure>
<figure><img src="assets/12-im-discovery-contract.png" alt="IM 一次发现、Activation 与 routine ingest 契约"><figcaption>IM 一次发现、Activation 与 routine ingest 契约</figcaption></figure>
<figure><img src="assets/13-secondary-discovery-manifest.png" alt="IM、meeting、sharing 等二次发现 manifest 与人工决策保留策略"><figcaption>IM、meeting、sharing 等二次发现 manifest 与人工决策保留策略</figcaption></figure>
</div>

可管理入口包括：

- 文档根目录
- 参考文档 seed
- IM 群聊 seed
- 辅助补查关键词
- 智能纪要 / 妙记 seed
- 分享会妙记 seed

### automations / routines 日更新

routine 会一直跑 ingest 和 compile。不过，一个链接被发现了，还不能直接算团队知识。我会把 stable identity、人工 decision、首次和最后出现时间、来源状态、消失策略都留下来。这样日常增量可以自动跑，后面也还能追溯这个来源是怎么进来的。

<figure class="article-figure"><img src="assets/14-knowledge-daily-update.png" alt="日常 ingest 与增量 compile 的提交链路"><figcaption>日常 ingest 与增量 compile 的提交链路</figcaption></figure>

### AutoWiki 式分层编译

<blockquote><p>这里是一位同事的设计。</p></blockquote>

最后编译出来的东西，我不希望是一摞统一口径的摘要。比如团队签署的事实、方法学规范、团队讨论、AI 推理，它们的权威性本来就不一样。事实主来源、可复用规范、过程判断、导航和待验证线索，都得在内容里明确分层，不能只靠目录名去暗示。

<div class="image-grid columns-2">
<figure><img src="assets/15-fido-wiki-compile-structure.png" alt="编译后的 wiki 按概念、数据、模型、问题、团队等入口组织"><figcaption>编译后的 wiki 按概念、数据、模型、问题、团队等入口组织</figcaption></figure>
<figure><img src="assets/16-source-authority-levels.png" alt="签署事实、方法学规范、团队讨论与 AI 推理的权威分级"><figcaption>签署事实、方法学规范、团队讨论与 AI 推理的权威分级</figcaption></figure>
</div>

AutoWiki 是一个通用的分层编译引擎，具体业务可以在上面加自己的编译逻辑。比如 fido 那边代码很重，代码本身就包含很多知识，所以我在 fido_wiki 里又加了一层代码解析，把概念和相关代码片段单独抽出来组织。这样下游用起来会更顺手。


在 AutoWiki 的基础上，我又把 source、activation、routine、compile、owner 这些约束，继续收进了 fido_wiki harness。

> 附件：[HANDOFF_harness.md](assets/HANDOFF_harness.md.txt)

## 技能与知识库的联动设计

> 技能 / reference 偏现场 runtime；知识库偏静态、通用、可泛化。
>
> 下面直接看三个【runtime 现场使用方式】vs【知识】的例子。

### 示例 1：下钻可以看什么子维度 vs AB 指标协议

skill 管这次怎么读平台、怎么下钻、失败以后 fallback 怎么走；知识库里则放团队的 AB 指标协议、主对照怎么选、历史判断用什么口径。前者是现场怎么拿，后者是拿到以后怎么看。

<figure class="article-figure"><img src="assets/17-ab-runtime-vs-knowledge.png" alt="AB 下钻能力与团队指标协议分开维护"><figcaption>AB 下钻能力与团队指标协议分开维护</figcaption></figure>

### 示例 2：数据分析 vs 看板解读

`data-query` 走 Aeolus、Coral、TQS、Dorado、Manta 这些平台的执行入口；知识库里的 Data Assets 记看板字段、指标入口、查询配方、快照读数和业务解释。Agent 应该先去看团队已经沉淀好的 Data Assets，再决定要不要从零写 SQL。

Data Assets 里的业务解释，我会尽量挑可泛化的专家解读，不只存一次性的 case。比如寒暑假会影响某类指标，这种规律放进去，下游遇到类似的异常波动就能先参考，不用每次都从头分析。

<figure class="article-figure"><img src="assets/18-data-assets.png" alt="执行路由与看板业务解释的分工"><figcaption>执行路由与看板业务解释的分工</figcaption></figure>

### 示例 3：往期 prompt / 常用业务表 vs 历史上线版本取数逻辑

项目 reference 里可以放当前常用的业务表、字段、prompt 和 SQL 模式；历史上线版本真正跑过的取数逻辑，则按版本沉淀进团队知识库。新任务可以复用历史口径，但执行还是回到 skill。

<figure class="article-figure"><img src="assets/19-sql-runtime-history.png" alt="项目 reference 中的当前取数方式，与知识库中的历史版本取数逻辑"><figcaption>项目 reference 中的当前取数方式，与知识库中的历史版本取数逻辑</figcaption></figure>

> 附件：[format-tables.md](assets/format-tables.md.txt)

## 实际 Agent 干活

### 【Agent 原生发现】

Agent 真正在 workspace 里干活时，会同时受到 AGENTS.md、CLAUDE.md、`.agents/`、`.claude/` 和已启用 plugin 的影响。一般先从宿主原生入口找能力，需要时再展开 skill 和 reference。

<figure class="article-figure"><img src="assets/20-agent-native-discovery.png" alt="项目级技能、团队插件、实验区和知识库共同进入 Agent 的工作现场"><figcaption>项目级技能、团队插件、实验区和知识库共同进入 Agent 的工作现场</figcaption></figure>

### 【使用分发的知识库】

workspace 里会挂上团队 KB 的编译产物。下游主要读的是 **知识库 out** 和 protocol，庞大的 source 不会原样分发到每个 workspace；再由 AGENTS.md 和 CLI 契约引导 Agent 从正确的入口开始读。

<div class="image-grid columns-2">
<figure><img src="assets/21-team-knowledge-entry.png" alt="团队事实、实验、个人知识、外部材料和临时产物各有落点"><figcaption>团队事实、实验、个人知识、外部材料和临时产物各有落点</figcaption></figure>
<figure><img src="assets/22-personal-knowledge-entry.png" alt="个人 harness 中的 knowledge-first 入口"><figcaption>个人 harness 中的 knowledge-first 入口</figcaption></figure>
</div>

### 【个人知识库】

每个人的 auto-research 都不太一样，所以个人知识库也会是个性化的。它可以服务当前任务，但不会替代团队事实，也不会替代项目现场状态。

### 【ws 中管理多个 code repo】

可以在 `backends/` 下用超链接挂载真实代码；也可以在知识库里用 source registry 记录 repo、branch、commit 和校验点。

<div class="image-grid columns-2">
<figure><img src="assets/23-backend-symlink.png" alt="方法 1：在 backends/ 下挂载真实代码仓"><figcaption>方法 1：在 backends/ 下挂载真实代码仓</figcaption></figure>
<figure><img src="assets/24-backend-repo.png" alt="真实 backend 代码继续保留自己的目录与工程结构"><figcaption>真实 backend 代码继续保留自己的目录与工程结构</figcaption></figure>
</div>

<figure class="article-figure"><img src="assets/25-code-repo-registry.png" alt="方法 2：在知识库中用指针记录 repo 位置、分支与校验点"><figcaption>方法 2：在知识库中用指针记录 repo 位置、分支与校验点</figcaption></figure>

所以我说 Agent 的上下文，不等于把所有东西都塞进 prompt。它来自工作契约、能力发现、知识入口、项目状态和代码指针；更关键的是，每一类内容都知道自己该写回哪里。

## 结语

- harness 与 workspace 解耦：harness 足够可复用，workspace 足够灵活。
- 一线 workspace 里积累的业务知识，稳定以后升格到知识层：harness-knowledge。
- 与 Agent 交互形成的固定流程，如果可以跨项目使用，就升格到 harness-plugin。
- 与 Agent 交互过程里的个人偏好，可以积累成 rules，进入个人 harness。

这三条路径，其实分别在积累三件事：团队知道了什么、Agent 稳定下来会做什么、Agent 应该怎么和某个人协作。它们各归各的 owner，才能一起往前长。

> 希望 Agent 挑战你？帮你提升认知？那么需要素材 + 指令。敬请期待我即将开源的 sameself harness。

## 参考

- [AutoWiki](https://code.byted.org/aweme/open_autoresearch_team/tree/main/autowiki?ref_type=heads)
- [通用工具仓 work-tools](https://code.byted.org/heyidan/work-tools/tree/main)
- [团队能力仓 fido_cc](https://code.byted.org/aweme/fido_cc)
- [团队知识库 fido_wiki](https://code.byted.org/aweme/fido_wiki)【暂不开放，属于团队内部知识库】
