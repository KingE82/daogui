#!/usr/bin/env python3
"""
道归 · 哲学爬虫
每天自动补充东西方哲学内容
一天扒 10 篇 SEP + 2 部中国经典
"""

import json, os, re, urllib.request, time, sys

BASE = os.path.dirname(os.path.abspath(__file__))
SEP_FILE = os.path.join(BASE, 'seplib', 'sep_core.json')
PHIL_DIR = os.path.join(BASE, 'phil_texts')
LOG_FILE = os.path.join(BASE, 'seplib', 'crawl_log.json')

os.makedirs(os.path.join(BASE, 'seplib'), exist_ok=True)
os.makedirs(PHIL_DIR, exist_ok=True)

def log(msg):
    print(f"[{time.strftime('%H:%M')}] {msg}", flush=True)

# ===== SEP 待抓列表 =====
SEP_QUEUE = [
    # 古希腊
    ("heraclitus", "赫拉克利特"), ("parmenides", "巴门尼德"), ("epicurus", "伊壁鸠鲁"),
    ("stoicism", "斯多葛主义"), ("plotinus", "普罗提诺"),
    # 近代哲学
    ("locke", "洛克"), ("berkeley", "贝克莱"), ("hume", "休谟"),
    ("leibniz", "莱布尼茨"), ("spinoza", "斯宾诺莎"),
    ("rousseau", "卢梭"), ("schopenhauer", "叔本华"),
    # 现代哲学
    ("heidegger", "海德格尔"), ("wittgenstein", "维特根斯坦"),
    ("rawls", "罗尔斯"), ("foucault", "福柯"), ("derrida", "德里达"),
    ("camus", "加缪"), ("popper", "波普尔"), ("adorno", "阿多诺"),
    ("habermas", "哈贝马斯"), ("bertrand-russell", "罗素"),
    ("quine", "奎因"), ("proust", "普鲁斯特"), ("beardsworth", "未来哲学"),
    # 专题
    ("ethics", "伦理学"), ("metaethics", "元伦理学"),
    ("political-philosophy", "政治哲学"), ("aesthetics", "美学"),
    ("feminism", "女性主义"), ("rationalism", "理性主义"),
    ("empiricism", "经验主义"), ("pragmatism", "实用主义"),
    ("utilitarianism", "功利主义"), ("nihilism", "虚无主义"),
]

# ===== 中国经典列表 =====
CHINESE_CLASSICS = [
    ("诗经", "shijing"),
    ("尚书", "shangshu"),
    ("礼记", "liji"),
    ("周易", "zhouyi"),
    ("春秋", "chunqiu"),
    ("大学", "daxue"),
    ("中庸", "zhongyong"),
    ("墨子", "mozi"),
    ("韩非子", "hanfeizi"),
    ("孙子兵法", "sunzi"),
]

def fetch_sep(slug, name):
    """抓一篇 SEP 条目"""
    url = f"https://plato.stanford.edu/entries/{slug}/"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'PhilosophyBot/1.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode('utf-8', errors='ignore')
        tm = re.search(r'<title>([^<]+)', html)
        paras = re.findall(r'<p[^>]*>([^<]{50,})</p>', html)
        body = '\n\n'.join(p.strip() for p in paras[:10])
        return {'name': name, 'title': tm.group(1)[:80] if tm else name, 'body': body[:3000]}
    except Exception as e:
        return None

def load_sep():
    try:
        with open(SEP_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_sep(lib):
    with open(SEP_FILE, 'w', encoding='utf-8') as f:
        json.dump(lib, f, ensure_ascii=False, indent=2)

def crawl_sep(daily_limit=10):
    """每天扒 daily_limit 篇 SEP"""
    lib = load_sep()
    crawled = 0
    for slug, name in SEP_QUEUE:
        if slug in lib:
            continue
        if crawled >= daily_limit:
            break
        log(f"SEP: {name}...")
        entry = fetch_sep(slug, name)
        if entry:
            lib[slug] = entry
            crawled += 1
            log(f"  ✅ {name}")
        else:
            log(f"  ❌ {name}")
        time.sleep(1.5)  # 礼貌间隔
    
    save_sep(lib)
    log(f"SEP: 今日新增 {crawled} 篇，共 {len(lib)} 篇")
    return crawled

def crawl_chinese(daily_limit=2):
    """每天扒 daily_limit 部中国经典（占位，待接入古登堡或 GitHub 数据源）"""
    log(f"中国经典: 待扩展数据源")
    return 0

if __name__ == '__main__':
    log("=" * 30)
    log("哲学爬虫启动")
    sep_count = crawl_sep(10)
    ch_count = crawl_chinese(2)
    log(f"今日完成: SEP {sep_count} 篇 + 中国经典 {ch_count} 部")
    log("=" * 30)
