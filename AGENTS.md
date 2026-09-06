# heyidan-sharing

这是公开表达与 GitHub Pages 分发仓，不是知识真源。
`_drafts/` 和 `_topics/` 是公开仓中的 Markdown 源稿目录，禁止放凭据、内部原文或私人工作底稿。

- 写作和等义润色跟随当前 Persona；synthesis 的来源、双仓一致性和发布边界见
  `~/knowledge-base/.claude/skills/synthesis/SKILL.md`。
- brief 的源稿在 `_drafts/`，渲染器和 release checker 在
  `~/knowledge-base/compiler/scripts/`；不要直接修改生成 HTML 正文。
- 方向专题源在 `_topics/<slug>.md`，渲染到 `topics/<slug>/`；`topics/index.html`
  由 renderer 生成。专题组织读序与文章关系，不镜像知识；Brief URL 不搬迁，Tags 继续过滤。
  分工与维护合同见 synthesis 的 `references/brief_and_topic_lifecycle.md`。
- 期次日期来自源稿的 `edition_date`。weekly 属于该期周日，延迟合并不改变期次；
  实际上线状态另查 PR 和 Pages，不能用目录存在或文件 mtime 推断。
- 实质修订用源稿的 `revised_date` 与 `revision_note` 单列最近变化，不改原期次；
  勘误融入原正文，完整历史在 Git，不按日期无限追加材料。
- 实质修正先核对来源，再同步 KB 的相关归纳、正文与图；不把公开稿倒当原始证据。
- 改稿或修工具不授权发布。公开变更在特性分支完成；push / PR 与 merge 分别按用户授权执行。

本机缺少上述工具或 skill 时说明缺口，不猜一个替代发布流程。站点约定见 `meta/index.html`。
