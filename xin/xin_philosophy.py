#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心哥 · 东方哲学 × 西方哲学 × 道归
莫名心的三栏哲学小站
"""

import json, os, sys, html, re, urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

PORT = 8081

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<title>三栏哲学 · 东哲 · 西哲 · 道归</title>
<style>
:root{--bg:#0f0f14;--card:#1a1a22;--text:#e0dcd0;--text2:#908a7a;--accent:#b8604a;--gold:#c9a84c;--blue:#4a7a9c;--green:#5a8a5a;--red:#c06050}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'PingFang SC','Noto Sans SC',sans-serif;background:var(--bg);color:var(--text);padding:16px;max-width:800px;margin:0 auto}
.header{text-align:center;padding:20px 0}
.header h1{font-size:20px;font-weight:600;letter-spacing:1px}
.header .sub{font-size:12px;color:var(--text2);margin-top:4px}
.tabs{display:flex;gap:4px;background:#22222a;border-radius:12px;padding:4px;margin-bottom:16px}
.tab{flex:1;text-align:center;padding:10px 6px;border-radius:10px;font-size:13px;font-weight:500;cursor:pointer;transition:.2s;color:var(--text2);user-select:none}
.tab.active{background:var(--card);color:var(--text);box-shadow:0 1px 4px rgba(0,0,0,.3)}
.tab-content{display:none}
.tab-content.active{display:block}
.card{background:var(--card);border-radius:14px;padding:16px;margin-bottom:14px}
.card-title{font-size:14px;font-weight:600;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.search-row{display:flex;gap:8px}
.search-row input{flex:1;padding:10px 14px;border:1px solid #333;border-radius:10px;font-size:14px;background:#22222a;color:var(--text);outline:0}
.search-row input:focus{border-color:var(--accent)}
.search-row button{padding:10px 16px;border:none;border-radius:10px;font-size:13px;cursor:pointer;font-weight:500;color:#fff}
.btn-east{background:var(--gold)}
.btn-west{background:var(--blue)}
.btn-daogui{background:var(--accent)}
.result{font-size:14px;line-height:1.8;padding:10px 0;color:var(--text)}
.result .entry{border-bottom:1px solid #2a2a32;padding:10px 0}
.result .entry:last-child{border:none}
.result .entry-title{font-weight:600;font-size:15px;color:var(--accent);cursor:pointer}
.result .entry-title:hover{color:var(--gold)}
.result .entry-snippet{font-size:13px;color:var(--text2);margin-top:4px}
.loading{text-align:center;padding:30px;color:var(--text2)}
.loading .spinner{display:inline-block;width:28px;height:28px;border:3px solid #333;border-top:3px solid var(--accent);border-radius:50%;animation:spin .8s linear infinite;margin-bottom:10px}
@keyframes spin{to{transform:rotate(360deg)}}
.footer{text-align:center;font-size:11px;color:var(--text2);padding:20px 0}
.cat-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.cat-item{text-align:center;padding:10px;border-radius:10px;font-size:13px;cursor:pointer;background:#22222a;transition:.2s}
.cat-item:hover{background:#2a2a34}
</style>
</head>
<body>

<div class="header">
  <h1>📖 三栏哲学</h1>
  <div class="sub">东方 · 西方 · 道归</div>
</div>

<div class="tabs">
  <div class="tab active" onclick="sw('east')">🌏 东方哲学</div>
  <div class="tab" onclick="sw('west')">🌍 西方哲学</div>
  <div class="tab" onclick="sw('daogui')">🔥 道归</div>
</div>

<!-- 东方哲学 -->
<div class="tab-content active" id="teast">
  <div class="card">
    <div class="card-title">🔍 东方哲学查询</div>
    <div class="search-row">
      <input type="text" id="eastInput" placeholder="搜索儒家、道家、佛教、中医哲学…" onkeydown="if(event.key==='Enter')searcheast()">
      <button class="btn-east" onclick="searcheast()">搜索</button>
    </div>
  </div>
  <div class="card">
    <div class="card-title">📂 经典分类</div>
    <div class="cat-grid">
      <div class="cat-item" onclick="qe('儒家')">儒家</div>
      <div class="cat-item" onclick="qe('道家')">道家</div>
      <div class="cat-item" onclick="qe('佛教')">佛教</div>
      <div class="cat-item" onclick="qe('禅宗')">禅宗</div>
      <div class="cat-item" onclick="qe('黄帝内经')">中医哲学</div>
      <div class="cat-item" onclick="qe('周易')">易经</div>
    </div>
  </div>
  <div id="eastResult"></div>
</div>

<!-- 西方哲学 -->
<div class="tab-content" id="twest">
  <div class="card">
    <div class="card-title">🔍 西方哲学查询</div>
    <div class="search-row">
      <input type="text" id="westInput" placeholder="搜索柏拉图、康德、尼采、存在主义…" onkeydown="if(event.key==='Enter')searchwest()">
      <button class="btn-west" onclick="searchwest()">搜索</button>
    </div>
  </div>
  <div class="card">
    <div class="card-title">📂 经典分类</div>
    <div class="cat-grid">
      <div class="cat-item" onclick="qw('柏拉图')">古希腊</div>
      <div class="cat-item" onclick="qw('康德')">德国观念论</div>
      <div class="cat-item" onclick="qw('尼采')">尼采</div>
      <div class="cat-item" onclick="qw('存在主义')">存在主义</div>
      <div class="cat-item" onclick="qw('分析哲学')">分析哲学</div>
      <div class="cat-item" onclick="qw('现象学')">现象学</div>
    </div>
  </div>
  <div id="westResult"></div>
</div>

<!-- 道归 -->
<div class="tab-content" id="tdaogui">
  <div class="card">
    <div class="card-title">🔥 道归·三栏哲学</div>
    <div style="font-size:14px;line-height:1.8;color:var(--text2);">
      <p style="margin-bottom:10px;">道归不是东方哲学，也不是西方哲学。它是第三栏。</p>
      <p>东哲提供"是什么"，西哲提供"为什么"，道归提供"怎么办"。</p>
    </div>
  </div>
  <div class="card">
    <div class="card-title">📖 体系全文</div>
    <div style="font-size:14px;line-height:1.8;">
      <div style="padding:8px 0;cursor:pointer;color:var(--accent);" onclick="window.open('/daogui')">📄 道归文库 →</div>
      <div style="padding:8px 0;cursor:pointer;color:var(--accent);" onclick="window.open('https://github.com/KingE82/daogui')">🌱 GitHub 仓库 →</div>
    </div>
  </div>
</div>

<div class="footer">🌙 莫名心 · 三栏哲学小站</div>

<script>
function sw(t){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab-content').forEach(x=>x.classList.remove('active'));document.querySelector('.tab[onclick*=\"\\''+t+'\\'\"]').classList.add('active');document.getElementById('t'+t).classList.add('active')}
async function searcheast(){const q=document.getElementById('eastInput').value.trim();if(!q)return;const r=document.getElementById('eastResult');r.innerHTML='<div class=\"loading\"><div class=\"spinner\"></div><div>搜索中…</div></div>';try{const d=await(await fetch('/east',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})})).json();r.innerHTML=d.error?('<div class=\"card\"><div class=\"result\">'+d.error+'</div></div>'):('<div class=\"card\"><div class=\"result\">'+d.results.map(x=>'<div class=\"entry\"><div class=\"entry-title\">'+x.title+'</div><div class=\"entry-snippet\">'+x.body.slice(0,200)+'</div></div>').join('')+'</div></div>')}catch(e){r.innerHTML='<div class=\"card\"><div class=\"result\">请求失败</div></div>'}}
async function searchwest(){const q=document.getElementById('westInput').value.trim();if(!q)return;const r=document.getElementById('westResult');r.innerHTML='<div class=\"loading\"><div class=\"spinner\"></div><div>正在查询斯坦福哲学百科…</div></div>';try{const d=await(await fetch('/west',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q})})).json();r.innerHTML=d.error?('<div class=\"card\"><div class=\"result\">'+d.error+'</div></div>'):(d.results.map(x=>'<div class=\"card\"><div class=\"result\">'+x+'</div></div>').join(''))}catch(e){r.innerHTML='<div class=\"card\"><div class=\"result\">请求失败</div></div>'}}
function qe(q){document.getElementById('eastInput').value=q;searcheast()}
function qw(q){document.getElementById('westInput').value=q;searchwest()}
</script>
</body>
</html>"""

class PhilHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(PAGE.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404')

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        try:
            data = json.loads(body)
        except:
            data = {}
        
        if self.path == '/east':
            self._handle_east(data)
        elif self.path == '/west':
            self._handle_west(data)
        else:
            self._json(404, {'error': 'not found'})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _handle_east(self, data):
        """东方哲学：从本地古籍搜索"""
        query = data.get('query', '').strip()
        if not query:
            self._json(400, {'error': '请输入搜索词'})
            return
        
        # 从古籍+道归等多目录搜索
        base = os.path.expanduser('~/.openclaw/workspace/xin_sources')
        results = []
        seen = set()
        
        for dname in ['cleaned', 'tcmoc', '../../道归', '../../数字中医有感', '../../phil_texts']:
            dpath = os.path.join(base, dname)
            if not os.path.isdir(dpath):
                continue
            for root, _, files in os.walk(dpath):
                for f in files:
                    if not (f.endswith('.md') or f.endswith('.txt') or f.endswith('.docx')):
                        continue
                    if '识典' in f or 'copyright' in f or 'privacy' in f:
                        continue
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                            content = fh.read(5000)
                            if query in content:
                                title = f.replace('.md','').replace('.txt','').replace('.docx','')
                                if title in seen:
                                    continue
                                seen.add(title)
                                idx = content.find(query)
                                s = max(0, idx-80)
                                e = min(len(content), idx+len(query)+120)
                                snippet = content[s:e].replace('\n',' ').strip()
                                results.append({'title': title[:50], 'body': snippet[:400]})
                                if len(results) >= 10:
                                    break
                    except:
                        continue
                if len(results) >= 10:
                    break
            if len(results) >= 10:
                break
        
        self._json(200, {'results': results})

    def _handle_west(self, data):
        """西方哲学：先从本地SEP库查找，没找到再联网"""
        query = data.get('query', '').strip().lower()
        if not query:
            self._json(400, {'error': '请输入搜索词'})
            return
        
        seplib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seplib', 'sep_core.json')
        entries = []
        
        # 1. 先查本地库
        try:
            with open(seplib_path, 'r', encoding='utf-8') as f:
                lib = json.load(f)
            for slug, entry in lib.items():
                if query in entry['name'] or query in entry['title'].lower():
                    body = entry['body'][:500].replace('\n', '<br>')
                    entries.append(f'<div class="entry-title" style="color:var(--green);">📚 {entry["title"]}</div>')
                    entries.append(f'<div class="entry-snippet">{body}…</div>')
        except:
            pass
        
        if entries:
            self._json(200, {'results': entries})
            return
        
        # 2. 本地没有，联网抓
        try:
            from urllib.parse import quote as uq
            possible = [query.lower().replace(' ', '-'), query.lower().replace(' ', '')]
            for slug in possible:
                url = f'https://plato.stanford.edu/entries/{slug}/'
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    resp = urllib.request.urlopen(req, timeout=5)
                    html = resp.read().decode('utf-8', errors='ignore')
                    tm = re.search(r'<title>([^<]+)', html)
                    title = tm.group(1) if tm else slug
                    paras = re.findall(r'<p[^>]*>([^<]{50,})</p>', html)
                    body = '\n\n'.join(p.strip() for p in paras[:5])[:600]
                    entries.append(f'<div class="entry-title" onclick="window.open(\'{url}\')">{title}</div>')
                    if body:
                        entries.append(f'<div class="entry-snippet">{body}…</div>')
                    entries.append(f'<div class="entry-snippet"><a href="{url}" style="color:var(--blue);font-size:12px;">📖 阅读全文 →</a></div>')
                    break
                except:
                    continue
            
            if not entries:
                entries.append(f'<div class="entry-title">未找到 "{query}"</div>')
                entries.append(f'<div class="entry-snippet"><a href="https://plato.stanford.edu/search/searcher.py?query={uq(query)}" target="_blank" style="color:var(--blue);">在 SEP 搜索 →</a></div>')
        except Exception as e:
            entries.append(f'<div class="entry-title">联网查询失败</div>')
            entries.append(f'<div class="entry-snippet">{str(e)[:60]}</div>')
        
        self._json(200, {'results': entries})

    def log_message(self, format, *args):
        print(f"[哲思小站] {args[0]} {args[1]} {args[2]}")

if __name__ == '__main__':
    print(f"\n{'═'*40}")
    print("📖 三栏哲学小站")
    print(f"  → http://localhost:{PORT}")
    print(f"{'═'*40}\n")
    HTTPServer(('0.0.0.0', PORT), PhilHandler).serve_forever()
