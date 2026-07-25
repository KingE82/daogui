#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道归 · 知识库月更脚本
每月自动刷新 TCM-MKG + OpenKG 数据
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = Path.home() / ".xin_knowledge"
UPDATE_LOG = DATA_DIR / "update_log.json"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{ts}] {msg}")

def load_log():
    if UPDATE_LOG.exists():
        try:
            return json.loads(UPDATE_LOG.read_text())
        except: pass
    return {"last_update": None, "history": []}

def save_log(log_data):
    UPDATE_LOG.write_text(json.dumps(log_data, ensure_ascii=False, indent=2))

def check_zenodo_update():
    """检查 Zenodo TCM-MKG 是否有新版本"""
    log("检查 Zenodo TCM-MKG 更新…")
    try:
        import requests
        # Zenodo API: get latest version of the record
        r = requests.get(
            "https://zenodo.org/api/records/19804367",
            timeout=15,
            headers={"Accept": "application/json"}
        )
        if r.status_code == 200:
            data = r.json()
            published = data.get("metadata", {}).get("publication_date", "unknown")
            doi = data.get("metadata", {}).get("doi", "10.5281/zenodo.19804367")
            title = data.get("metadata", {}).get("title", "TCM-MKG")[:60]
            log(f"  Zenodo 版本日期: {published}")
            log(f"  DOI: {doi}")
            return {"published": published, "doi": doi, "title": title}
        else:
            log(f"  Zenodo API 返回 {r.status_code}")
    except Exception as e:
        log(f"  Zenodo 检查失败: {e}")
    return None

def download_tcm_mkg():
    """下载 TCM-MKG 知识图谱数据（最新版）"""
    log("下载 TCM-MKG 数据包…")
    import requests
    import zipfile
    import io
    
    # 直接从 Zenodo 下载最新版
    url = "https://zenodo.org/records/19804367/files/TCM-MKG_Open_Source_Documentation.zip"
    try:
        r = requests.get(url, timeout=60)
        if r.status_code != 200:
            log(f"  下载失败: HTTP {r.status_code}")
            return False
        
        z = zipfile.ZipFile(io.BytesIO(r.content))
        tcm_dir = DATA_DIR / "tcm_mkg"
        tcm_dir.mkdir(parents=True, exist_ok=True)
        
        extracted = 0
        for name in z.namelist():
            if name.endswith('.tsv'):
                target = tcm_dir / os.path.basename(name)
                with z.open(name) as source, open(target, 'wb') as dest:
                    dest.write(source.read())
                extracted += 1
        
        log(f"  解压 {extracted} 个 TSV 文件到 {tcm_dir}")
        return True
    except Exception as e:
        log(f"  下载失败: {e}")
        return False

def refresh_openkg_datasets():
    """刷新 OpenKG 数据集"""
    log("刷新 OpenKG 数据集…")
    try:
        from xin_harvester import download_openkg_data
        datasets = [
            ("tcm-health", "中医养生"),
            ("tcm-formula", "中医经方"),
        ]
        for ds_id, ds_name in datasets:
            log(f"  收割 {ds_name}({ds_id})…")
            data = download_openkg_data(ds_id)
            if data:
                log(f"    ✅ {len(data)} 条")
            else:
                log(f"    ⚠️ 不可达")
    except Exception as e:
        log(f"  OpenKG 刷新失败: {e}")

def full_update():
    """执行全量更新"""
    log("=" * 50)
    log("🌙 道归知识库 · 月度更新开始")
    log("=" * 50)
    
    logs = load_log()
    
    # 1. 检查 Zenodo 版本
    zenodo = check_zenodo_update()
    
    # 2. 下载 TCM-MKG
    log("\n→ 更新 TCM-MKG 知识图谱…")
    ok = download_tcm_mkg()
    if ok:
        log("  ✅ TCM-MKG 已更新")
    else:
        log("  ⚠️ TCM-MKG 更新失败（保留旧数据）")
    
    # 3. 刷新 OpenKG
    log("\n→ 刷新 OpenKG 数据集…")
    refresh_openkg_datasets()
    
    # 4. 记录
    record = {
        "timestamp": datetime.now().isoformat(),
        "zenodo": zenodo,
        "tcm_mkg_updated": ok,
    }
    logs["last_update"] = record["timestamp"]
    logs["history"].append(record)
    logs["history"] = logs["history"][-24:]  # 保留最近24次
    save_log(logs)
    
    log("\n" + "=" * 50)
    log("🌙 月度更新完成")
    log("=" * 50)
    return ok

def status():
    """查看更新状态"""
    log = load_log()
    lu = log.get("last_update", "从未更新")
    print(f"上次更新: {lu}")
    print(f"更新记录: {len(log.get('history', []))} 次")
    if log.get("history"):
        last = log["history"][-1]
        if last.get("zenodo"):
            z = last["zenodo"]
            print(f"Zenodo 版本: {z.get('published','?')}")
        print(f"TCM-MKG 状态: {'✅' if last.get('tcm_mkg_updated') else '❌'}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        status()
    else:
        full_update()
