#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 道归 · 古籍爬虫（自动探索+批量下载）
Daogui专用 · 出门找食吃
"""

import requests, re, os, json, time, random
from urllib.parse import urljoin, urlparse, unquote
from datetime import datetime

SAVE_DIR = os.path.expanduser("~/.openclaw/workspace/xin_sources/crawled")
os.makedirs(SAVE_DIR, exist_ok=True)

UAS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile',
    'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 Chrome/120.0.0.0',
]

class TCMCollector:
    def __init__(self, delay=2):
        self.delay = delay
        self.stats = {'tried':0, 'got':0, 'failed':0}

    def _headers(self):
        return {
            'User-Agent': random.choice(UAS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://www.baidu.com/',
        }

    def _get(self, url):
        self.stats['tried'] += 1
        time.sleep(self.delay * (0.5 + random.random()))
        for retry in range(2):
            try:
                r = requests.get(url, headers=self._headers(), timeout=15)
                if r.status_code == 200 and len(r.content) > 200:
                    self.stats['got'] += 1
                    return r.content
            except:
                time.sleep(2)
        self.stats['failed'] += 1
        return None

    def _save(self, name, data):
        safe = re.sub(r'[^\w\-\u4e00-\u9fff]', '_', name)[:80]
        fp = os.path.join(SAVE_DIR, f"{safe}.html")
        with open(fp, 'wb') as f:
            f.write(data[:500000])
        return fp

    def explore_jicheng(self):
        print("🌐 探索中医笈成...")
        html = self._get("https://jicheng.tw/tcm/book/index.html")
        if not html:
            print("   ❌ 连不上"); return

        links = re.findall(b'href="([^"]*)"', html)
        books = []
        for l in links:
            ls = l.decode('utf-8', errors='replace')
            if ls.endswith('/index.html') and not ls.startswith('..') and not ls.startswith('http'):
                books.append({'path': ls, 'name': ls.replace('/index.html', '')})

        kws = ['素問','靈樞','難經','傷寒','金匱','本草','溫病','黃帝','內經','脈','針灸','醫']
        filtered = [b for b in books if any(k in b['name'] for k in kws)]
        print(f"   📚 {len(books)}本 → 🎯 {len(filtered)}本中医")

        self._save("书单_笈成中医", json.dumps(filtered, ensure_ascii=False, indent=2).encode())

        for b in filtered[:10]:
            url = f"https://jicheng.tw/tcm/book/{b['path']}"
            name = b['name']
            print(f"   📖 {name} ... ", end='', flush=True)
            data = self._get(url)
            if data:
                fp = self._save(f"笈_{name}", data)
                print(f"✅ {os.path.getsize(fp)//1024}KB")
                # 子页面
                subs = re.findall(b'href="([^"]*\\.html)"', data)
                for s in subs[:10]:
                    s_str = s.decode('utf-8', errors='replace')
                    if s_str in ('index.html','../../index.html','../index.html') or s_str.startswith('http'):
                        continue
                    sub_url = "https://jicheng.tw/tcm/book/" + b['path'].replace('/index.html','/') + s_str
                    sub_data = self._get(sub_url)
                    if sub_data:
                        self._save(f"笈_{name}_{s_str.replace('.html','')}", sub_data)
            else:
                print("❌")

        print(f"   📊 笈成: 尝试{self.stats['tried']}, 成功{self.stats['got']}, 失败{self.stats['failed']}")

    def explore_shidianguji(self):
        print("🌐 探索识典古籍...")
        for kw in ['黄帝内经','素问','灵枢','伤寒论','金匮要略','神农本草']:
            url = f"https://www.shidianguji.com/search?q={kw}"
            data = self._get(url)
            if data and len(data) > 500:
                fp = self._save(f"识典_{kw}", data)
                print(f"   ✅ {kw}: {os.path.getsize(fp)//1024}KB")
            else:
                print(f"   ⚠️ {kw}: 没内容")

    def run(self):
        print(f"🦞 道归古籍爬虫 · {datetime.now()}")
        print(f"   保存: {SAVE_DIR}  |  延迟: {self.delay}s\n")
        self.explore_jicheng()
        print()
        self.explore_shidianguji()
        print()
        files = os.listdir(SAVE_DIR)
        total = sum(os.path.getsize(os.path.join(SAVE_DIR,f)) for f in files)
        print(f"📊 尝试{self.stats['tried']}, 成功{self.stats['got']}, 失败{self.stats['failed']}")
        print(f"📁 {len(files)}个文件, {total//1024//1024}MB")
        print("🦞 完毕")

if __name__ == '__main__':
    TCMCollector(delay=2).run()
