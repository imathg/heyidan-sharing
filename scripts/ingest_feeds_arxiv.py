#!/usr/bin/env python3
"""
arxiv radar ingester（RSS 版）— heyidan-sharing 公开仓版。

历史：原本住在 imathg/knowledge-base（私有仓）。2026-05-28 后挪到 imathg/heyidan-sharing
（公开仓）让雷达产物对外部可见。云端 routine 现在直接 commit 到这个仓。

行为不变：从 interests.yaml 读取 categories / keywords，
拉 https://rss.arxiv.org/rss/{cat} 的当日 feed，按关键词过滤后写到
raw/feeds/arxiv/{YYYY-MM-DD}.jsonl。

约定：
- 一行 JSON 一篇论文；同 arxiv_id 跨天去重（state 记录 seen ids）
- 多 domain 命中合并 matched_domains 数组

interests.yaml 是公开子集（domains / arxiv / rss_feeds / exclude），与
私有仓 knowledge-base/compiler/interests.yaml 的同名段保持同步——以私有仓为 canonical，
编辑后用 scripts/sync_interests.py 同步到本仓。

用法：
    python3 scripts/ingest_feeds_arxiv.py
    python3 scripts/ingest_feeds_arxiv.py --dry-run
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
INTERESTS_FILE = REPO_ROOT / "interests.yaml"
OUTPUT_DIR = REPO_ROOT / "raw" / "feeds" / "arxiv"
STATE_FILE = REPO_ROOT / "state" / "feeds_arxiv_state.json"

RSS_BASE = "https://rss.arxiv.org/rss"

# arxiv RSS 的 announce_type:
#   "new"      = 全新提交，最高优先级
#   "cross"    = 跨学科 cross-listing（同一篇出现在多个 category）
#   "replace"  = v2/v3 修订版本
DEFAULT_KEEP_ANNOUNCE_TYPES = {"new", "cross"}


def load_interests() -> dict:
    with INTERESTS_FILE.open() as f:
        return yaml.safe_load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_ids": [], "last_run": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_rss(category: str) -> list[dict]:
    """拉一个 category 的当日 RSS，解析成 entry list。"""
    url = f"{RSS_BASE}/{category}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 heyidan-sharing-radar/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()

    root = ET.fromstring(body)
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        cats = [c.text for c in item.findall("category") if c.text]

        announce_type = ""
        for child in item:
            if child.tag.endswith("}announce_type"):
                announce_type = (child.text or "").strip()
                break
        creator = ""
        for child in item:
            if child.tag.endswith("}creator"):
                creator = (child.text or "").strip()
                break

        m = re.search(r"abs/([\d\.]+)(?:v\d+)?$", link)
        arxiv_id = m.group(1) if m else ""

        abstract = desc
        if "Abstract:" in desc:
            abstract = desc.split("Abstract:", 1)[1].strip()
        abstract = re.sub(r"\s+", " ", abstract)

        items.append({
            "arxiv_id": arxiv_id,
            "title": re.sub(r"\s+", " ", title),
            "abstract": abstract,
            "abs_url": link,
            "authors": [a.strip() for a in creator.split(",")] if creator else [],
            "categories": cats,
            "published": pub,
            "announce_type": announce_type,
        })
    return items


def match_keywords(entry: dict, keywords: list[str]) -> list[str]:
    """返回命中的关键词。在 title + abstract + categories 里找。"""
    haystack = " ".join([entry["title"], entry["abstract"], " ".join(entry["categories"])]).lower()
    hits = []
    for kw in keywords:
        kw_lower = kw.lower()
        if len(kw) <= 5 and " " not in kw and "-" not in kw and "." not in kw:
            pattern = rf"\b{re.escape(kw_lower)}\b"
        else:
            pattern = re.escape(kw_lower)
        if re.search(pattern, haystack):
            hits.append(kw)
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    parser.add_argument("--include-replace", action="store_true",
                        help="也保留 v2/v3 修订版本（默认只保留 new + cross）")
    args = parser.parse_args()

    interests = load_interests()
    arxiv_cfg = interests.get("arxiv", {})
    categories = arxiv_cfg.get("categories", ["cs.LG", "cs.CL"])

    keep_types = DEFAULT_KEEP_ANNOUNCE_TYPES | ({"replace"} if args.include_replace else set())

    state = load_state()
    seen = set(state.get("seen_ids", []))

    all_items: dict[str, dict] = {}
    for cat in categories:
        print(f"[arxiv-rss] fetching {cat}...", file=sys.stderr)
        try:
            items = fetch_rss(cat)
        except Exception as e:
            print(f"  ✗ {cat} failed: {e}", file=sys.stderr)
            continue
        kept = 0
        for item in items:
            if not item["arxiv_id"]:
                continue
            if item["announce_type"] and item["announce_type"] not in keep_types:
                continue
            if item["arxiv_id"] in all_items:
                all_items[item["arxiv_id"]]["categories"] = sorted(
                    set(all_items[item["arxiv_id"]]["categories"]) | set(item["categories"])
                )
            else:
                all_items[item["arxiv_id"]] = item
            kept += 1
        print(f"  ✓ {cat}: {len(items)} items, {kept} kept after announce_type filter", file=sys.stderr)

    print(f"[arxiv-rss] {len(all_items)} unique papers today across categories", file=sys.stderr)

    domains = interests.get("domains", [])
    matched: dict[str, dict] = {}
    for d in domains:
        domain_id = d["id"]
        keywords = d.get("keywords", [])
        if not keywords:
            continue
        for aid, entry in all_items.items():
            hits = match_keywords(entry, keywords)
            if not hits:
                continue
            if aid in matched:
                matched[aid]["matched_domains"].append(domain_id)
                matched[aid]["matched_keywords"].extend(hits)
            else:
                e = dict(entry)
                e["matched_domains"] = [domain_id]
                e["matched_keywords"] = hits
                matched[aid] = e

    new_hits = {aid: e for aid, e in matched.items() if aid not in seen}
    print(f"[arxiv-rss] {len(matched)} matched keywords, {len(new_hits)} new (not in state)", file=sys.stderr)

    if not new_hits:
        print("[arxiv-rss] no new matches, exiting", file=sys.stderr)
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    out_path = OUTPUT_DIR / f"{today}.jsonl"

    if args.dry_run:
        print(f"\n--- DRY RUN, would write {len(new_hits)} entries to {out_path} ---", file=sys.stderr)
        for e in list(new_hits.values())[:10]:
            print(f"  • [{','.join(sorted(set(e['matched_domains'])))}] "
                  f"{e['title'][:90]} ({e['arxiv_id']}, kw={sorted(set(e['matched_keywords']))})")
        if len(new_hits) > 10:
            print(f"  ... ({len(new_hits) - 10} more)", file=sys.stderr)
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as f:
        for e in new_hits.values():
            e["matched_keywords"] = sorted(set(e["matched_keywords"]))
            e["matched_domains"] = sorted(set(e["matched_domains"]))
            e["ingested_at"] = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    state["seen_ids"] = sorted(set(state.get("seen_ids", [])) | set(new_hits.keys()))
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    print(f"[arxiv-rss] wrote {len(new_hits)} entries to {out_path}", file=sys.stderr)
    print(f"[arxiv-rss] state now tracks {len(state['seen_ids'])} arxiv_ids", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
