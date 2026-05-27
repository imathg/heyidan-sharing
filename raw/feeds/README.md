# raw/feeds/ — 雷达原始抓取缓存

每日云端 routine 抓回的论文 / 博客增量。**这是原料，不是成品**——格式是 JSONL，未经渲染、未经筛选。

| 子目录 | 内容 | 抓取方 |
|--------|------|--------|
| `arxiv/{YYYY-MM-DD}.jsonl` | arxiv `cs.LG` / `cs.CL` / `cs.AI` 按 `interests.yaml::domains` 关键词命中的当日新论文 | `scripts/ingest_feeds_arxiv.py` |
| `rss/{YYYY-MM-DD}.jsonl` | `interests.yaml::rss_feeds` 列表里 7 个 blog 的近 30 天更新 | `scripts/ingest_feeds_rss.py` |

## 这些数据怎么来的

云端每日 routine（claude.ai routine）在 UTC 09:00（北京 17:00）自动跑两个 ingest 脚本，
按 `interests.yaml` 配置过滤 / 抓取，写到这个目录，git push 回 `imathg/heyidan-sharing`。

**硬边界**（routine prompt 里写死的）：
- 只动 `raw/feeds/` 和 `state/feeds_*_state.json`
- 不动 `_drafts/` / `briefs/` / 其他文章目录
- 不 amend / force-push / rebase
- 抓取报错时不 retry，原样报错退出

## 这些数据给谁用

- **私有仓 `imathg/knowledge-base`**：触发 reading-list 编排时，从这里捞回素材；触发跨外部源 reduce 时，捞 arxiv abstract 当证据来源
- **外部读者**：可以扫一眼 `arxiv/{today}.jsonl` 看我每天关注哪些方向（domains 配置见根目录 `interests.yaml`）

## 为什么不渲染成 HTML

raw/feeds/ 量大、噪声多（一天可能几十条 arxiv 命中），渲染所有 hit 没意义。
渲染过的成品在另外两个地方：
- `_drafts/` → 已写好的长文（手动产物）
- `briefs/` → LLM 自动产出的轻量简报（如果有的话）

如果想看"筛选过的"输出，关注那两个目录，不是这个。

## 历史

- 2026-05-28 这条线整体从 `imathg/knowledge-base/raw/feeds/{arxiv,rss}/` 挪过来
  （私有仓→公开仓，让外部可见）。云端 routine 也同步切到本仓
