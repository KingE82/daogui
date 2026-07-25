#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 xin_cleaner.py — 爬虫后处理：去乱码·转简体·分类归档
"""
import os, re, json, glob
from html.parser import HTMLParser
from zhconv import convert

CRAWLED_DIR = os.path.expanduser("~/.openclaw/workspace/xin_sources/crawled")
CLEAN_DIR = os.path.expanduser("~/.openclaw/workspace/xin_sources/cleaned")
os.makedirs(CLEAN_DIR, exist_ok=True)

# 分类关键词
CATEGORIES = {
    '素问': ['素問','素问','上古天真','四气调神','生气通天'],
    '灵枢': ['靈樞','灵枢'],
    '难经': ['難經','难经','八十一难'],
    '伤寒': ['傷寒','伤寒'],
    '金匮': ['金匱','金匮'],
    '本草': ['本草','神农'],
    '温病': ['溫病','温病','温热'],
    '针灸': ['針灸','针灸','腧穴'],
    '脉诊': ['脈','脉诊','濒湖'],
    '医案': ['醫案','医案','医话'],
    '方剂': ['方','汤头'],
    '综合': [],
}

# 需要清除的乱码字符
GARBAGE = re.compile(r'[\u0000-\u0008\u000b\u000c\u000e-\u001f\u200b\u200c\u200d\ufeff\u00b6\u2028\u2029]')
# 页码标记
PAGE_MARKS = re.compile(r'<pb[^>]*>|¶')

class TextExtractor(HTMLParser):
    """从HTML中提取纯正文"""
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','nav','footer','header','aside'):
            self.skip = True
    def handle_endtag(self, tag):
        if tag in ('script','style','nav','footer','header','aside'):
            self.skip = False
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())
    def get_text(self):
        return '\n'.join(self.parts)

def clean_text(raw_text):
    """清理文本：去乱码·去页码·去冗余"""
    t = raw_text
    t = GARBAGE.sub('', t)
    t = PAGE_MARKS.sub('', t)
    t = re.sub(r'\u3000', ' ', t)
    t = re.sub(r'○新校正云[^。]*。', '', t)  # 去掉宋校注（可保留的，但先清了）
    t = re.sub(r'\n{4,}', '\n\n\n', t)
    t = re.sub(r' {3,}', '  ', t)
    return t.strip()

def html_to_text(html_bytes):
    """HTML提取正文"""
    try:
        html = html_bytes.decode('utf-8', errors='replace')
    except:
        html = html_bytes.decode('latin-1', errors='replace')
    
    # 修复mojibake：检查body内容
    body_m = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    if body_m:
        body_text = body_m.group(1)[:2000]
        # 如果body里有ä¸等乱码且没有正确中文，就是mojibake
        if 'ä¸' in body_text and not any('一' <= c <= '鿿' for c in body_text):
            try:
                html = html.encode('latin-1', errors='replace').decode('utf-8', errors='replace')
            except:
                pass
    
    # 先去除script/style内容
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    
    # 提取正文
    body_match = re.search(r'<body[^>]*>(.*)</body>', html, re.DOTALL)
    if body_match:
        body = body_match.group(1)
    else:
        body = html
    
    # 去标签
    text = re.sub(r'<[^>]+>', '\n', body)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    
    return clean_text(text)

def guess_category(filename):
    """按文件名猜分类"""
    for cat, kws in CATEGORIES.items():
        if any(k in filename for k in kws):
            return cat
    return '综合'

def process_file(filepath):
    """清洗单个爬虫文件"""
    fname = os.path.basename(filepath)
    # 跳过无意义的通用页
    skip_keywords = ['privacy', 'copyright', 'about', 'help', 'contact']
    if any(k in fname.lower() for k in skip_keywords):
        return None
    if os.path.getsize(filepath) < 500:  # 太小的文件跳过
        return None
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    # 提取纯文本
    text = html_to_text(raw)
    if len(text) < 50:
        return None  # 没啥内容
    
    # 繁体转简体（保留原文）
    try:
        simplified = convert(text, 'zh-cn')
    except:
        simplified = text
    
    # 分类
    category = guess_category(fname)
    
    # 生成输出文件名
    safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', fname.replace('.html','').replace('.md',''))[:60]
    
    # 保存清理版
    cat_dir = os.path.join(CLEAN_DIR, category)
    os.makedirs(cat_dir, exist_ok=True)
    out_path = os.path.join(cat_dir, f"{safe_name}.md")
    
    # 简体版
    output = f"""---
source: {fname}
cleaned_at: 2026-07-23
category: {category}
chars: {len(simplified)}
---

{simplified}
"""
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(output)
    # 繁体版（去乱码但保留原文）
    trad_path = out_path.replace('.md', '.trad.md')
    trad_out = f"""---
source: {fname}
cleaned_at: 2026-07-23
category: {category}
chars: {len(text)}
---

{text}
"""
    with open(trad_path, 'w', encoding='utf-8') as f:
        f.write(trad_out)
    
    return {
        'file': fname,
        'category': category,
        'chars': len(simplified),
        'chars_trad': len(text),
        'cleaned_file': out_path,
        'preview': simplified[:200],
    }

def process_all():
    """清洗全部爬虫文件"""
    results = []
    files = sorted(glob.glob(os.path.join(CRAWLED_DIR, '*.html')))
    print(f"🦞 清洗器启动 · {len(files)} 个文件需处理\n")
    
    for fp in files:
        fname = os.path.basename(fp)
        print(f"   {fname} ... ", end='', flush=True)
        r = process_file(fp)
        if r:
            results.append(r)
            print(f"✅ {r['category']} ({r['chars']}字)")
        else:
            print("⚠️ 内容太少")
    
    # 按分类汇总
    by_cat = {}
    for r in results:
        by_cat.setdefault(r['category'], []).append(r)
    
    print(f"\n📊 汇总:")
    for cat, items in sorted(by_cat.items()):
        total_chars = sum(i['chars'] for i in items)
        print(f"   📁 {cat}: {len(items)}篇, {total_chars}字")
    
    # 保存索引
    index_path = os.path.join(CLEAN_DIR, '_index.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(results),
            'by_category': {cat: [{'file': r['file'], 'chars': r['chars'], 'title': r['file'].replace('.html','')} for r in items]
                           for cat, items in sorted(by_cat.items())}
        }, f, ensure_ascii=False, indent=2)
    print(f"\n📁 索引: {index_path}")
    print(f"📁 清理目录: {CLEAN_DIR}")
    print("🦞 清洗完毕")
    
    return results

if __name__ == '__main__':
    process_all()
