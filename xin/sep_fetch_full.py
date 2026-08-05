#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SEP (斯坦福哲学百科) 全量词条爬取（2026-08-05）
从 contents.html 抓全部 2512 个词条正文，合并进 data/sep_core.json
带断点续传：已存在的 slug 跳过，防止中断重来。

用法: python3 data/sep_fetch_full.py
"""
import json, re, time, os, sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE = "https://plato.stanford.edu"
DATA_FILE = "/home/honor/.openclaw/workspace/data/sep_core.json"
TIMEOUT = 30
SLEEP = 1.2

def extract_p_text(html: str) -> str:
    parts = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL | re.IGNORECASE)
    cleaned = []
    for p in parts:
        text = re.sub(r'<[^>]+>', '', p)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            cleaned.append(text)
    return '\n\n'.join(cleaned)

def get_all_slugs():
    """从目录页抓全部词条 slug"""
    url = f"{BASE}/contents.html"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urlopen(req, timeout=TIMEOUT).read().decode("utf-8", errors="replace")
    links = re.findall(r'href="([^"]*entries/[^"]*)"', html)
    slugs = []
    for l in links:
        m = re.search(r'entries/([a-z0-9\-]+)/', l)
        if m:
            slug = m.group(1).strip().rstrip('/')
            if slug:
                slugs.append(slug)
    return list(dict.fromkeys(slugs))

def main():
    print("=== SEP 全量词条爬取 ===", flush=True)
    slugs = get_all_slugs()
    print(f"目录共 {len(slugs)} 个词条", flush=True)

    # 加载已有数据（断点续传）
    data = {}
    if os.path.isfile(DATA_FILE):
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                data = json.load(f)
            print(f"已有 {len(data)} 条", flush=True)
        except Exception:
            data = {}

    todo = [s for s in slugs if s not in data or not isinstance(data.get(s), dict)]
    print(f"待抓 {len(todo)} 条（跳过已存在的 {len(data)} 条）", flush=True)

    ok = fail = 0
    for i, slug in enumerate(todo, 1):
        url = f"{BASE}/entries/{slug}/"
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            html = urlopen(req, timeout=TIMEOUT).read().decode("utf-8", errors="replace")
            text = extract_p_text(html)
            if text:
                data[slug] = {"name": slug, "title": slug.replace('-', ' ').title(), "body": text}
                ok += 1
            else:
                fail += 1
            time.sleep(SLEEP)
        except HTTPError as e:
            fail += 1
            if e.code == 404:
                print(f"  ⚠ {slug}: 404，跳过", flush=True)
        except Exception as e:
            fail += 1
            print(f"  ❌ {slug}: {str(e)[:40]}", flush=True)

        # 每 10 条存一次盘（防丢）
        if ok % 10 == 0 and ok > 0:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            print(f"  …进度 {i}/{len(todo)}: 成功{ok} 失败{fail} (共{len(data)}条)", flush=True)

    # 最终存盘
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"\n=== 完成: 新增{ok} 失败{fail}，SEP 词条总数 {len(data)} ===", flush=True)

if __name__ == "__main__":
    main()
