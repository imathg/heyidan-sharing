#!/usr/bin/env python3
"""
通用 RSS/Atom blog ingester — heyidan-sharing 公开仓版。

历史：原本住在 imathg/knowledge-base（私有仓）。2026-05-28 后挪到 imathg/heyidan-sharing
（公开仓）让雷达产物对外部可见。云端 routine 现在直接 commit 到这个仓。

从 interests.yaml 的 rss_feeds 列表里拉 feed，解析成统一结构，写到
raw/feeds/rss/{YYYY-MM-DD}.jsonl。

为什么不用 feedparser：避免新依赖。RSS 2.0 + Atom 用 stdlib xml.etree 够用。

与 arxiv ingester 的差异：
- RSS 不做 keyword 过滤（量小，几个 blog 一天合计可能 < 20 条）
- 全部存下来，按 source 分类
- 仍跨天 dedupe by guid/link

用法：
    python3 scripts/ingest_feeds_rss.py
    python3 scripts/ingest_feeds_rss.py --dry-run
    python3 scripts/ingest_feeds_rss.py --window-days 30
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
INTERESTS_FILE = REPO_ROOT / "interests.yaml"
OUTPUT_DIR = REPO_ROOT / "raw" / "feeds" / "rss"
STATE_FILE = REPO_ROOT / "state" / "feeds_rss_state.json"

ATOM_NS = "http://www.w3.org/2005/Atom"


def load_interests() -> dict:
    with INTERESTS_FILE.open() as f:
        return yaml.safe_load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_keys": [], "last_run": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 heyidan-sharing-radar/0.1",
                 "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date_any(s: str | None) -> str:
    if not s:
        return ""
    s = s.strip()
    try:
        return parsedate_to_datetime(s).isoformat()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return s


def parse_feed(body: bytes, source_name: str) -> list[dict]:
    root = ET.fromstring(body)
    items = []

    rss_items = root.findall(".//item")
    atom_entries = root.findall(f".//{{{ATOM_NS}}}entry")

    if rss_items:
        for item in rss_items:
            title = strip_html(item.findtext("title") or "")
            link = (item.findtext("link") or "").strip()
            guid = (item.findtext("guid") or "").strip()
            desc = strip_html(item.findtext("description") or "")
            pub = item.findtext("pubDate") or item.findtext("date") or ""
            cats = [c.text for c in item.findall("category") if c.text]

            author = ""
            for child in item:
                tag = child.tag.split("}")[-1]
                if tag == "creator" or tag == "author":
                    author = strip_html(child.text or "")
                    if author:
                        break

            items.append({
                "source": source_name,
                "title": title,
                "link": link,
                "guid": guid or link,
                "summary": desc[:1500],
                "published": parse_date_any(pub),
                "categories": cats,
                "author": author,
            })
    elif atom_entries:
        for entry in atom_entries:
            title = strip_html(entry.findtext(f"{{{ATOM_NS}}}title") or "")
            link = ""
            for ln in entry.findall(f"{{{ATOM_NS}}}link"):
                if ln.attrib.get("rel", "alternate") == "alternate":
                    link = ln.attrib.get("href", "")
                    break
            if not link:
                first_link = entry.find(f"{{{ATOM_NS}}}link")
                link = first_link.attrib.get("href", "") if first_link is not None else ""
            guid = entry.findtext(f"{{{ATOM_NS}}}id") or link
            summary = strip_html(entry.findtext(f"{{{ATOM_NS}}}summary") or entry.findtext(f"{{{ATOM_NS}}}content") or "")
            pub = entry.findtext(f"{{{ATOM_NS}}}published") or entry.findtext(f"{{{ATOM_NS}}}updated") or ""
            cats = [c.attrib.get("term", "") for c in entry.findall(f"{{{ATOM_NS}}}category")]
            author_el = entry.find(f"{{{ATOM_NS}}}author")
            author = ""
            if author_el is not None:
                author = strip_html(author_el.findtext(f"{{{ATOM_NS}}}name") or "")

            items.append({
                "source": source_name,
                "title": title,
                "link": link,
                "guid": guid,
                "summary": summary[:1500],
                "published": parse_date_any(pub),
                "categories": cats,
                "author": author,
            })
    return items


def entry_key(e: dict) -> str:
    if e.get("guid"):
        return f"{e['source']}::{e['guid']}"
    return f"{e['source']}::{hashlib.sha256((e['source'] + e['title']).encode()).hexdigest()[:16]}"


def within_window(entry: dict, days: int) -> bool:
    if not entry.get("published"):
        return True
    try:
        dt = datetime.fromisoformat(entry["published"].replace("Z", "+00:00"))
    except ValueError:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= datetime.now(timezone.utc) - timedelta(days=days)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--window-days", type=int, default=30,
                        help="只保留过去 N 天内发布的（默认 30）")
    args = parser.parse_args()

    interests = load_interests()
    feeds = interests.get("rss_feeds", [])
    if not feeds:
        print("[rss] no feeds in interests.yaml", file=sys.stderr)
        return 0

    state = load_state()
    seen = set(state.get("seen_keys", []))

    all_new: list[dict] = []
    for f in feeds:
        name = f["name"]
        url = f["url"]
        cat = f.get("category", "other")
        print(f"[rss] {name} ({url})...", file=sys.stderr)
        try:
            body = fetch_url(url)
        except Exception as e:
            print(f"  ✗ fetch failed: {e}", file=sys.stderr)
            continue
        try:
            entries = parse_feed(body, source_name=name)
        except Exception as e:
            print(f"  ✗ parse failed: {e}", file=sys.stderr)
            continue
        kept = 0
        for e in entries:
            e["category"] = cat
            if not within_window(e, args.window_days):
                continue
            k = entry_key(e)
            if k in seen:
                continue
            e["_key"] = k
            all_new.append(e)
            kept += 1
        print(f"  ✓ {len(entries)} parsed, {kept} new within {args.window_days}d", file=sys.stderr)

    print(f"\n[rss] {len(all_new)} new entries total", file=sys.stderr)

    if not all_new:
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    out_path = OUTPUT_DIR / f"{today}.jsonl"

    if args.dry_run:
        print(f"\n--- DRY RUN, would write {len(all_new)} entries to {out_path} ---", file=sys.stderr)
        for e in all_new[:20]:
            pub = (e.get("published") or "")[:10]
            print(f"  • [{e['source']}] {pub}  {e['title'][:90]}")
        if len(all_new) > 20:
            print(f"  ... ({len(all_new) - 20} more)", file=sys.stderr)
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as f:
        for e in all_new:
            e["ingested_at"] = datetime.now(timezone.utc).isoformat()
            key = e.pop("_key")
            seen.add(key)
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    state["seen_keys"] = sorted(seen)
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    print(f"[rss] wrote {len(all_new)} entries to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
