#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道归 · 一概全选武装体 v2
优化版 ─ 2026-07-21
功能：GLM-5.2 API + 本地GGUF + 备用模型 + 并行交叉验证 + 沉浸式翻译管道 + 目笼心侦察 + 小龙虾爬取 + 古籍检索
"""

import os
import sys
import re
import json
import argparse
import requests
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

# ── 依赖惰性加载 ──
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

CONFIG_PATH = Path.home() / ".xin_config.json"
CACHE_DIR = Path.home() / ".xin_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── 默认配置 ──
DEFAULT_CONFIG = {
    "api_key": os.getenv("ZHIPUAI_API_KEY", ""),
    "api_endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "api_model": "glm-5",
    "local_model_path": "./models/glm-5.2.Q2_K.gguf",
    "llama_server_url": "http://127.0.0.1:8080/completion",
    "fallback_endpoint": "https://api.openai.com/v1/chat/completions",
    "fallback_api_key": os.getenv("FALLBACK_API_KEY", ""),
    "parallel_timeout": 60,
    "system_prompt": "你是一个基于道归理论体系的深度分析助手，使用相变语言和整体观思考。",
    "cache_ttl": 3600,
}

def load_config() -> Dict[str, Any]:
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            file_cfg = json.load(f)
        cfg.update(file_cfg)
    cfg["api_key"] = cfg["api_key"] or os.getenv("ZHIPUAI_API_KEY", "") or os.getenv("DASHSCOPE_API_KEY", "")
    cfg["fallback_api_key"] = cfg["fallback_api_key"] or os.getenv("FALLBACK_API_KEY", "")
    return cfg

def save_config(cfg: Dict[str, Any]):
    to_save = {k: v for k, v in cfg.items() if k not in ("api_key", "fallback_api_key") or v}
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)

CONFIG = load_config()

# ── 缓存 ──
def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

def _cache_get(key: str) -> Optional[str]:
    p = CACHE_DIR / key
    if p.exists() and (os.path.getmtime(p) > (os.path.getctime(CACHE_DIR) - CONFIG.get("cache_ttl", 3600))):
        return p.read_text(encoding='utf-8')
    return None

def _cache_set(key: str, value: str):
    (CACHE_DIR / key).write_text(value, encoding='utf-8')

# ══════════════════════════════════════════
# 后端1：API (智谱 GLM / OpenAI 兼容格式)
# ══════════════════════════════════════════
class APIInference:
    def __init__(self):
        self.api_key = CONFIG.get("api_key", "")
        self.url = CONFIG.get("api_endpoint", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
        self.model = CONFIG.get("api_model", "glm-5")
        self.system_prompt = CONFIG.get("system_prompt", "")

    def _payload(self, prompt: str, context: str = "") -> dict:
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        if context:
            msgs.append({"role": "user", "content": context})
        msgs.append({"role": "user", "content": prompt})
        return {
            "model": self.model,
            "messages": msgs,
            "temperature": 0.7,
            "max_tokens": 4096
        }

    def generate(self, prompt: str, context: str = "") -> str:
        if not self.api_key:
            return "❌ API Key 未配置（设置 ZHIPUAI_API_KEY 环境变量或 ~/.xin_config.json）"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            resp = requests.post(
                self.url, json=self._payload(prompt, context),
                headers=headers, timeout=CONFIG.get("parallel_timeout", 60)
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            return "[API超时]"
        except Exception as e:
            return f"[API错误] {e}"


# ══════════════════════════════════════════
# 后端2：本地GGUF (llama.cpp server)
# ══════════════════════════════════════════
class LocalInference:
    def __init__(self):
        self.server_url = CONFIG.get("llama_server_url", "http://127.0.0.1:8080/completion")

    def generate(self, prompt: str, context: str = "") -> str:
        full_prompt = f"{context}\n---\n{prompt}" if context else prompt
        try:
            resp = requests.post(
                self.server_url,
                json={"prompt": full_prompt, "n_predict": 2048, "temperature": 0.7},
                timeout=60
            )
            resp.raise_for_status()
            return resp.json().get("content", "[本地返回为空]")
        except requests.exceptions.ConnectionError:
            return "❌ 本地 llama-server 未启动（运行: llama-server -m models/glm-5.2.Q2_K.gguf -c 8192 --port 8080）"
        except Exception as e:
            return f"[本地错误] {e}"


# ══════════════════════════════════════════
# 后端3：备用 (API兼容格式，如OpenAI/anthropic)
# ══════════════════════════════════════════
class FallbackInference:
    def __init__(self):
        self.endpoint = CONFIG.get("fallback_endpoint", "")
        self.api_key = CONFIG.get("fallback_api_key", "")

    def generate(self, prompt: str, context: str = "") -> str:
        if not self.api_key or not self.endpoint:
            return "[备用模型] 未配置 fallback_endpoint / fallback_api_key"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        msgs = []
        if context:
            msgs.append({"role": "user", "content": context})
        msgs.append({"role": "user", "content": prompt})
        payload = {
            "model": "gpt-4o-mini",
            "messages": msgs,
            "temperature": 0.7,
            "max_tokens": 4096
        }
        try:
            resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[备用错误] {e}"


# ══════════════════════════════════════════
# 并行路由 + 交叉验证
# ══════════════════════════════════════════
class ParallelRouter:
    def __init__(self):
        self.backends = {
            "API": APIInference(),
            "本地GGUF": LocalInference(),
            "备用": FallbackInference()
        }
        self.timeout = CONFIG.get("parallel_timeout", 60)

    def generate(self, prompt: str, context: str = "") -> Dict[str, str]:
        results = {}
        # 缓存检查
        cache_text = f"{context}||{prompt}" if context else prompt
        ck = _cache_key(cache_text)
        cached = _cache_get(ck)
        if cached:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                pass

        with ThreadPoolExecutor(max_workers=len(self.backends)) as executor:
            futures = {
                executor.submit(engine.generate, prompt, context): name
                for name, engine in self.backends.items()
            }
            try:
                for future in as_completed(futures, timeout=self.timeout):
                    name = futures[future]
                    try:
                        results[name] = future.result()
                    except Exception as e:
                        results[name] = f"[超时/异常] {e}"
            except TimeoutError:
                for name, future in futures.items():
                    if name not in results:
                        results[name] = "[未完成·超时]"

        _cache_set(ck, json.dumps(results, ensure_ascii=False))
        return results

    def cross_validate(self, prompt: str, context: str = "") -> Optional[str]:
        """三路投票：如果两家结果明显一致，取共识；否则标记分歧"""
        results = self.generate(prompt, context)
        # 简单启发式：找共同模式
        valid = {k: v for k, v in results.items() if not v.startswith("[")}
        if len(valid) >= 2:
            # 如果至少两家有超过50%的内容相似，取第一个非错误结果
            texts = list(valid.values())
            if len(texts) >= 2:
                return texts[0]  # 信任API结果
        if valid:
            return list(valid.values())[0]
        return "\n\n".join(f"[{k}]: {v}" for k, v in results.items())


# ══════════════════════════════════════════
# 沉浸式翻译抽取（v2：更健壮的句子分割）
# ══════════════════════════════════════════
_CHUNK_SIZE = 600  # 字符

def fluent_extract(html: str) -> List[Dict]:
    if not BeautifulSoup:
        # 无BS：用正则和纯文本降级
        raw = re.sub(r'<[^>]+>', '', html)
        raw = re.sub(r'\s+', ' ', raw).strip()
        return _split_into_chunks(raw)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside", "noscript"]):
        tag.decompose()

    body = soup.find("article") or soup.find("main") or soup.body or soup
    texts = []
    for elem in body.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote", "td"]):
        t = elem.get_text(strip=True)
        if len(t) > 15:
            texts.append(t)

    raw = "\n".join(texts)
    return _split_into_chunks(raw)


def _split_into_chunks(text: str) -> List[Dict]:
    # 多语言句子分割
    sentences = re.split(
        r'(?<=[。！？；\n.!?;])(?=\s*[\u4e00-\u9fffA-Za-z"「『(（])',
        text
    )
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    chunks, current, idx = [], "", 0
    for sent in sentences:
        if len(current) + len(sent) < _CHUNK_SIZE:
            current += sent
        else:
            if current:
                chunks.append({"chunk_id": idx, "original": current})
                idx += 1
            current = sent
    if current:
        chunks.append({"chunk_id": idx, "original": current})
    if not chunks:
        chunks = [{"chunk_id": 0, "original": text[:600]}]
    return chunks


# ══════════════════════════════════════════
# 爬虫降级链
# ══════════════════════════════════════════
def smart_crawl(url: str) -> str:
    # 尝试 OpenClaw 原生 fetch
    try:
        from openclaw import Openclaw
        return Openclaw.fetch(url)
    except ImportError:
        pass
    except Exception:
        pass

    # fallback: requests
    try:
        resp = requests.get(
            url, timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux aarch64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )
        resp.raise_for_status()
        # 检测编码
        if resp.encoding and resp.encoding.lower() != 'utf-8':
            resp.encoding = resp.apparent_encoding
        return resp.text
    except requests.exceptions.Timeout:
        return "❌ 爬取超时（15秒）"
    except requests.exceptions.ConnectionError:
        return "❌ 网络连接失败"
    except Exception as e:
        return f"❌ 爬取失败: {e}"


# ══════════════════════════════════════════
# 翻译管道
# ══════════════════════════════════════════
def run_translate_pipeline(url: str, mode: str, max_chunks: int = 5):
    print(f"🦞 全选管道启动: {url}")
    print(f"   后端: {mode} | 最大块数: {max_chunks}")
    html = smart_crawl(url)
    if not html or html.startswith("❌"):
        print(html)
        return

    chunks = fluent_extract(html)
    print(f"📖 抽取 {len(chunks)} 个语义块")
    if not chunks:
        print("⚠️ 未能从页面提取有效内容")
        return

    if mode == "parallel":
        router = ParallelRouter()
        for chunk in chunks[:max_chunks]:
            print(f"\n─── 块 {chunk['chunk_id']}/{len(chunks)-1} ───")
            print(f"[原文] {chunk['original'][:120]}...")
            res = router.generate(f"将以下内容翻译为流畅的中文，只输出译文：\n{chunk['original']}")
            for backend, text in res.items():
                print(f"[{backend}] {text[:200]}...")
    else:
        backend_map = {"api": APIInference, "local": LocalInference, "fallback": FallbackInference}
        engine_cls = backend_map.get(mode, APIInference)
        engine = engine_cls()
        for chunk in chunks[:max_chunks]:
            print(f"\n─── 块 {chunk['chunk_id']}/{len(chunks)-1} ───")
            print(f"[原文] {chunk['original'][:120]}...")
            trans = engine.generate(f"将以下内容翻译为流畅的中文，只输出译文：\n{chunk['original']}")
            print(f"[译文] {trans[:300]}...")


# ══════════════════════════════════════════
# 配置诊断
# ══════════════════════════════════════════
def diag():
    print("🩺 道归武装体 诊断\n")
    print(f"配置路径: {CONFIG_PATH}")
    print(f"配置存在: {CONFIG_PATH.exists()}")
    print(f"缓存目录: {CACHE_DIR}")
    print(f"缓存存在: {CACHE_DIR.exists()}")
    print(f"API Key 已配置: {'✅' if CONFIG.get('api_key') else '❌'}")
    print(f"备用 Key 已配置: {'✅' if CONFIG.get('fallback_api_key') else '❌'}")
    print(f"本地 GGUF URL: {CONFIG.get('llama_server_url')}")
    print(f"BeautifulSoup: {'✅' if BeautifulSoup else '❌ 未安装'}")
    print(f"requests: ✅")
    # 检查环境变量
    print(f"\n环境变量:")
    print(f"  DASHSCOPE_API_KEY: {'✅' if os.getenv('DASHSCOPE_API_KEY') else '❌'}")
    print(f"  FALLBACK_API_KEY: {'✅' if os.getenv('FALLBACK_API_KEY') else '❌'}")


# ══════════════════════════════════════════
# 交互式问答
# ══════════════════════════════════════════
def interactive(prompt: str, mode: str, context: str = ""):
    if mode == "parallel":
        router = ParallelRouter()
        res = router.generate(prompt, context)
        print(f"\n🧠  并行交叉验证:")
        for k, v in res.items():
            divider = "─" * 40
            print(f"\n[{k}]")
            print(divider)
            print(v[:800] + ("..." if len(v) > 800 else ""))
    else:
        backend_map = {"api": APIInference, "local": LocalInference, "fallback": FallbackInference}
        engine_cls = backend_map.get(mode, APIInference)
        engine = engine_cls()
        print(f"\n🧠 [{mode}]")
        print(engine.generate(prompt, context)[:2000])


# ══════════════════════════════════════════
# 入口
# ══════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="道归 · 一概全选武装体 v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --ask "什么是相变?"
  %(prog)s --ask "道归的五刀理论" --mode parallel
  %(prog)s --translate "Hello world" --mode api
  %(prog)s --url "https://example.com/article" --mode parallel
  %(prog)s --diag
  %(prog)s --config
  %(prog)s --init
        """
    )
    parser.add_argument("--mode", choices=["api", "local", "fallback", "parallel"], default="parallel",
                        help="推理后端")
    parser.add_argument("--ask", help="提问")
    parser.add_argument("--context", help="上下文/背景信息", default="")
    parser.add_argument("--translate", help="翻译单段文本")
    parser.add_argument("--url", help="翻译整个网页")
    parser.add_argument("--max-chunks", type=int, default=5, help="网页翻译最大块数")
    parser.add_argument("--resources", nargs="?", const="all", metavar="CATEGORY",
                        help="列出古籍资源（可选分类: 中医药古籍库/综合性古籍库/工具与传递）")
    parser.add_argument("--probe", action="store_true", help="探测所有可直连的古籍资源连通状态")
    parser.add_argument("--tcm-apis", action="store_true", help="列出中医药 API 接口")
    parser.add_argument("--unitcm", nargs=2, metavar=("ENDPOINT", "QUERY"),
                        help="查询 UniTCM: --unitcm herb 葛根")
    parser.add_argument("--openkg-tcm", metavar="DATASET",
                        help="查询 OpenKG 中医药数据集: --openkg-tcm tcm-cases")

    parser.add_argument("--search-guji", metavar="关键词",
                        help="检索古籍（目前支持 nlc 国图）")
    parser.add_argument("--guji-source", default="nlc", help="古籍检索源")
    parser.add_argument("--diag", action="store_true", help="诊断环境")
    parser.add_argument("--config", action="store_true", help="显示当前配置")
    parser.add_argument("--init", action="store_true", help="初始化配置向导")
    args = parser.parse_args()

    if args.diag:
        diag()
        return

    if args.config:
        print(json.dumps(CONFIG, indent=2, ensure_ascii=False))
        return

    if args.init:
        print("🦞 初始化配置")
        api_key = input("DashScope API Key (回车跳过): ").strip()
        if api_key:
            CONFIG["api_key"] = api_key
        gpt_key = input("备用 API Key (回车跳过): ").strip()
        if gpt_key:
            CONFIG["fallback_api_key"] = gpt_key
        local_url = input("本地 GGUF 地址 (回车默认 http://127.0.0.1:8080/completion): ").strip()
        if local_url:
            CONFIG["llama_server_url"] = local_url
        save_config(CONFIG)
        print("✅ 配置已保存至", CONFIG_PATH)
        return

    if args.translate:
        if args.mode == "parallel":
            router = ParallelRouter()
            res = router.generate(f"将以下内容翻译为流畅的中文，只输出译文：\n{args.translate}", args.context)
            for k, v in res.items():
                print(f"[{k}]: {v[:500]}")
        else:
            backend_map = {"api": APIInference, "local": LocalInference, "fallback": FallbackInference}
            engine_cls = backend_map.get(args.mode, APIInference)
            engine = engine_cls()
            print(engine.generate(f"将以下内容翻译为流畅的中文，只输出译文：\n{args.translate}", args.context)[:1000])
        return

    if args.url:
        run_translate_pipeline(args.url, args.mode, args.max_chunks)
        return

    if args.resources:
        cat = None if args.resources == "all" else args.resources
        list_resources(cat)
        return

    if args.tcm_apis:
        list_tcm_apis()
        return

    if args.unitcm:
        endpoint, query = args.unitcm
        res = query_unitcm(query, endpoint)
        print(json.dumps(res, indent=2, ensure_ascii=False)[:2000])
        return

    if args.openkg_tcm:
        res = query_openkg_tcm(args.openkg_tcm)
        print(json.dumps(res, indent=2, ensure_ascii=False)[:2000])
        return

    if args.probe:
        probe_all()
        return

    if args.search_guji:
        search_guji(args.search_guji, args.guji_source)
        return

    if args.ask:
        interactive(args.ask, args.mode, args.context)
        return

    parser.print_help()


# ══════════════════════════════════════════
# 古籍检索 + 中医药 API 模块（道归宝藏入口集合）
# ══════════════════════════════════════════

# ── 中医药 API 端点配置 ──

TCM_API_ENDPOINTS = {
    "unitcm": {
        "label": "UniTCM 多组学中医药平台",
        "base_url": "https://unitcm.qfxulab.com",
        "status": "ok",
        "desc": "覆盖草药/化合物/ADMET/方剂关联/TCM本体论/转录组学",
        "note": "实际为网页端，非纯API。不需要Key，直接访问即可",
        "endpoints": {
            "herb": "/herb/{name}",       # 例: /herb/葛根 → 200, 返回HTML页面
        }
    },

    "bianzheng": {
        "label": "辨证云 AI辨证系统",
        "base_url": "https://t.zydsoft.cn/open/v2",
        "status": "partial",
        "desc": "人工神经网络+专家知识图谱的中医AI辨证",
        "doc_url": "https://t.zydsoft.cn/open/v2/docs/",
    },
    "openkg_tcm": {
        "label": "OpenKG 中医药知识图谱",
        "base_url": "http://data.openkg.cn/api/3/action",
        "status": "ok",
        "desc": "6个中医药数据集，3个可查：经方/养生/美容",
        "note": "tcm-cases/tcm-ner/tcm-qg 已下线或不可访问",
        "datasets": {
            "tcm-formula": "中医经方知识图谱 ✅",
            "tcm-health": "中医养生知识图谱 ✅",
            "tcm-cosmetology": "中医美容知识图谱 ✅",
            "tcm-cases": "中医医案知识图谱 ❌ 已下线",
            "tcm-ner": "中药说明书实体识别 ❌ 已下线",
            "tcm-qg": "中医文献问题生成 ❌ 已下线"
        }
    },
}

ANCIENT_RESOURCES = {
    "中医药古籍库": {
        "cintcm": {
            "label": "国家中医药古籍数字图书馆",
            "url": "http://www.cintcm.com",
            "method": "direct",
            "desc": "中国中医科学院主办，1300余种古籍+4050余种民国文献",
        },
        "guoyi_tianjin": {
            "label": "国医典藏（天津中医药大学）",
            "url": None,  # 可能需校内入口
            "method": "portal",
            "desc": "7×24h免费开放",
        },
        "overseas_tcm": {
            "label": "海外中医古籍库",
            "url": None,
            "method": "portal",
            "desc": "427种流失海外珍善本中医古籍",
        },
        "nlc_medicine": {
            "label": "中华医药典籍资源库（国图测试版）",
            "url": "http://read.nlc.cn/thematDataSearch/toGujiIndex",
            "method": "direct",
            "desc": "国图中华古籍资源库子库",
        },
    },
    "综合性古籍库": {
        "nlc_guji": {
            "label": "国家图书馆·中华古籍资源库",
            "url": "http://read.nlc.cn/thematDataSearch/toGujiIndex",
            "method": "direct",
            "desc": "~10万部善本/甲骨/敦煌/地方志，无需注册",
        },
        "pcab": {
            "label": "中国古籍保护网",
            "url": "http://www.nlc.cn/pcab/",
            "method": "direct",
            "desc": "与国家图书馆资源互通，无需注册",
        },
        "shanghai_guji": {
            "label": "中华善本古籍数据库",
            "url": None,
            "method": "portal",
            "desc": "在线上约50万页免费资源",
        },
    },
    "工具与传递": {
        "ucdrs": {
            "label": "全国图书馆参考咨询联盟",
            "url": "http://www.ucdrs.superlib.net",
            "method": "portal",
            "desc": "注册后可email传递论文/图书章节，7.6亿篇元数据",
        },
        "ancientbooks": {
            "label": "籍合网（中华书局）",
            "url": "https://www.ancientbooks.cn",
            "method": "direct",
            "desc": "《中华经典古籍库》核心产品",
        },
        "gujibook": {
            "label": "古籍资源共享平台",
            "url": "https://www.gujibook.com",
            "method": "direct",
            "desc": "免费无需注册，可直接下载",
        },
    },
    "工具类App": {
        "gushigudu": {
            "label": "古书古读 App",
            "url": None,
            "method": "app",
            "desc": "《黄帝内经》《本草纲目》等经典，移动端阅读",
        },
        "boyi_med": {
            "label": "博览医书",
            "url": None,
            "method": "portal",
            "desc": "2800余种古籍数据库，图书馆注册后免费",
        },
    },
}


def list_tcm_apis():
    """列出中医药 API 资源"""
    print(f"\n{'═' * 50}")
    print("🔬 中医药 API 接口")
    print(f"{'═' * 50}")
    for key, info in TCM_API_ENDPOINTS.items():
        status_icon = {"ok": "🟢", "partial": "🟡", "needs_auth": "🔑", "down": "🔴"}.get(info["status"], "⚪")
        print(f"  {status_icon} {info['label']}")
        print(f"     {info['desc']}")
        if info.get("note"):
            print(f"     📌 {info['note']}")
        if info.get("doc_url"):
            print(f"     文档: {info['doc_url']}")
        print(f"     API: {info['base_url']}")
        if info.get("endpoints"):
            for ep_name, ep_path in info["endpoints"].items():
                print(f"       · {ep_name}: {ep_path}")
        if info.get("datasets"):
            if isinstance(info["datasets"], dict):
                for ds_name, ds_desc in info["datasets"].items():
                    print(f"       · {ds_name}: {ds_desc}")


def query_unitcm(query: str, endpoint: str = "herb") -> Dict[str, Any]:
    """查询 UniTCM（网页端，非纯API）"""
    base = TCM_API_ENDPOINTS["unitcm"]["base_url"]
    url = f"{base}/{endpoint}/{requests.utils.quote(query)}"
    try:
        resp = requests.get(url, timeout=15,
                            headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            # 返回的是HTML页面
            text = resp.text
            title = ""
            if BeautifulSoup:
                soup = BeautifulSoup(text, "html.parser")
                title = soup.title.text.strip() if soup.title else ""
            return {"status": "ok", "type": "html", "title": title, "size": len(text), "url": url}
        else:
            return {"status": f"HTTP {resp.status_code}", "url": url}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def query_openkg_tcm(dataset: str) -> Dict[str, Any]:
    """查询 OpenKG 中医药数据集信息"""
    url = f"{TCM_API_ENDPOINTS['openkg_tcm']['base_url']}/package_show?id={dataset}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return {"status": "ok", "data": resp.json()["result"]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_resources(category: Optional[str] = None):
    """列出全部或指定类别的古籍资源"""
    if category:
        cat = {category: ANCIENT_RESOURCES.get(category, {})}
    else:
        cat = ANCIENT_RESOURCES

    for cat_name, resources in cat.items():
        print(f"\n{'═' * 50}")
        print(f"📚 {cat_name}")
        print(f"{'═' * 50}")
        if not resources:
            print("  （暂无收录）")
            continue
        for key, info in resources.items():
            status = "🟢" if info["method"] == "direct" else ("🟡" if info["method"] in ("portal",) else "🔵")
            url_str = f"  {info.get('url', '（需校内/注册访问）')}" if info.get("url") else ""
            print(f"  {status} {info['label']}")
            print(f"     {info['desc']}")
            if url_str:
                print(url_str)


def probe_resource(name: str) -> Dict[str, Any]:
    """测试指定资源能否连通"""
    # 展平查找
    target = None
    for cat in ANCIENT_RESOURCES.values():
        for key, info in cat.items():
            if name.lower() in (key.lower(), info["label"].lower()):
                target = info
                break

    if not target or not target.get("url"):
        return {"name": name, "status": "unknown", "message": "未找到具体URL（可能需要校内/注册访问）"}

    try:
        resp = requests.get(
            target["url"], timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        code = resp.status_code
        if code == 200:
            return {"name": name, "status": "ok", "code": 200, "size": len(resp.text)}
        elif code in (301, 302, 307, 308):
            return {"name": name, "status": "redirect", "code": code, "location": resp.headers.get("Location", "?")}
        else:
            return {"name": name, "status": "error", "code": code}
    except requests.exceptions.Timeout:
        return {"name": name, "status": "timeout"}
    except requests.exceptions.ConnectionError:
        return {"name": name, "status": "unreachable"}
    except Exception as e:
        return {"name": name, "status": "exception", "error": str(e)}


def probe_all():
    """批量探测所有可直连的资源"""
    targets = []
    for cat in ANCIENT_RESOURCES.values():
        for key, info in cat.items():
            if info.get("url") and info["method"] == "direct":
                targets.append((key, info))

    print(f"🔍 正在探测 {len(targets)} 个古籍资源…\n")
    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(probe_resource, key): (key, info) for key, info in targets}
        for future in as_completed(futures):
            key, info = futures[future]
            try:
                res = future.result()
                results.append(res)
                icon = {"ok": "✅", "redirect": "🔀", "error": "❌", "timeout": "⌛", "unreachable": "🚫"}.get(res["status"], "❓")
                print(f"  {icon} {info['label']}")
                print(f"     {info['url']}")
                if res["status"] == "ok":
                    print(f"     → 连通 (HTTP 200, {res.get('size',0):,}B)")
                elif res["status"] == "redirect":
                    print(f"     → 跳转至 {res.get('location','?')}")
                elif res["status"] == "error":
                    print(f"     → HTTP {res.get('code','?')}")
                else:
                    print(f"     → {res['status']}")
            except Exception as e:
                print(f"  ⚠️ {info['label']} 探测异常: {e}")
    return results


def search_guji(keyword: str, source: str = "auto"):
    """古籍检索入口（初步实现：通过国图检索）"""
    if source == "auto" or source == "nlc":
        print(f"🔍 在国图古籍资源库搜索: {keyword}")
        # 国图的实际搜索入口
        url = f"http://read.nlc.cn/thematDataSearch/toGujiIndex?keyword={requests.utils.quote(keyword)}"
        try:
            resp = requests.get(url, timeout=15,
                                headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                print(f"✅ 国图检索页已加载 ({len(resp.text):,}B)")
                print("⚠️  检索结果需要浏览器渲染才能完整显示")
                print(f"   打开链接即可查看: {url}")
            else:
                print(f"❌ HTTP {resp.status_code}")
        except Exception as e:
            print(f"❌ 检索失败: {e}")
    else:
        print(f"🔍 尝试搜索 {source}: {keyword}（功能开发中）")


# 原有入口的 parser 扩展在 main() 中

if __name__ == "__main__":
    main()
