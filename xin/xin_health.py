#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道归 · 健康档案系统 v1
- 个人健康记录存档（JSON本地存储）
- 手环/穿戴设备数据导入
- 趋势分析 + 月度报告
- 与 xin_claw_doctor.py 集成
"""

import json
import os
import re
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# ── 存储路径 ──
HEALTH_DIR = Path.home() / ".xin_health"
RECORDS_DIR = HEALTH_DIR / "records"
DAILY_DIR = HEALTH_DIR / "daily"
REPORTS_DIR = HEALTH_DIR / "reports"
HEALTH_DIR.mkdir(parents=True, exist_ok=True)
RECORDS_DIR.mkdir(exist_ok=True)
DAILY_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# ── 数据模型 ──

# 可穿戴设备支持的指标
DEVICE_METRICS = {
    "heart_rate": {"label": "心率", "unit": "bpm", "range": "60-100"},
    "hrv": {"label": "心率变异性", "unit": "ms", "range": "20-70"},
    "sleep_duration": {"label": "睡眠时长", "unit": "h", "range": "7-9"},
    "deep_sleep": {"label": "深睡时长", "unit": "h", "range": "1.5-2"},
    "light_sleep": {"label": "浅睡时长", "unit": "h", "range": "3-4"},
    "rem_sleep": {"label": "REM时长", "unit": "h", "range": "1.5-2"},
    "steps": {"label": "步数", "unit": "步", "range": "6000-10000"},
    "calories": {"label": "消耗热量", "unit": "kcal", "range": "1500-2500"},
    "spo2": {"label": "血氧", "unit": "%", "range": "95-100"},
    "stress": {"label": "压力指数", "unit": "", "range": "0-50"},
    "bp_systolic": {"label": "收缩压", "unit": "mmHg", "range": "90-130"},
    "bp_diastolic": {"label": "舒张压", "unit": "mmHg", "range": "60-85"},
    "blood_glucose": {"label": "血糖", "unit": "mmol/L", "range": "3.9-6.1"},
}

# ── 功能函数 ──

def today_str() -> str:
    return date.today().isoformat()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def record_new(name: str = "", birth_year: int = 0, gender: str = "",
               notes: str = "") -> Dict:
    """创建新的健康档案"""
    rec = {
        "patient_name": name or input("姓名: ").strip(),
        "birth_year": birth_year or int(input("出生年份: ").strip()),
        "gender": gender or input("性别 (male/female): ").strip(),
        "created_at": now_str(),
        "updated_at": now_str(),
        "records": [],
        "daily_logs": [],
        "notes": notes,
    }
    path = RECORDS_DIR / f"{rec['patient_name']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    print(f"✅ 健康档案已创建: {path}")
    return rec


def load_record(name: str) -> Optional[Dict]:
    """加载已有健康档案"""
    path = RECORDS_DIR / f"{name}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 尝试模糊匹配
    for p in RECORDS_DIR.glob("*.json"):
        if name in p.stem:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def list_records() -> List[Dict]:
    """列出所有健康档案"""
    records = []
    for p in RECORDS_DIR.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            records.append({
                "name": data.get("patient_name", p.stem),
                "age": _calc_age(data.get("birth_year", 0)),
                "gender": data.get("gender", "?"),
                "records": len(data.get("records", [])),
                "daily_logs": len(data.get("daily_logs", [])),
                "updated": data.get("updated_at", "")[:10],
            })
        except:
            pass
    return records


def _calc_age(birth_year: int) -> int:
    if birth_year:
        return date.today().year - birth_year
    return 0


def add_consultation(name: str, symptoms: List[str], diagnosis: str,
                     principle: str, tcm_syndrome: str = "",
                     treatment: str = "", tongue: str = "",
                     pulse: str = "", notes: str = "") -> Dict:
    """添加一次辨证记录"""
    rec = load_record(name)
    if not rec:
        print(f"❌ 未找到档案: {name}，请先创建（--new）")
        return {}

    entry = {
        "date": now_str(),
        "type": "consultation",
        "symptoms": symptoms,
        "diagnosis": diagnosis,
        "tcm_syndrome": tcm_syndrome,
        "principle": principle,
        "treatment": treatment,
        "tongue": tongue,
        "pulse": pulse,
        "notes": notes,
    }
    rec["records"].append(entry)
    rec["updated_at"] = now_str()

    path = RECORDS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    return entry


def add_daily_log(name: str, metrics: Dict[str, float], symptoms: List[str] = None,
                  notes: str = "") -> Dict:
    """
    添加每日健康数据（可从手环导入/手动录入）
    metrics 支持的键: heart_rate, hrv, sleep_duration, deep_sleep, steps, calories, spo2, stress, bp_systolic, bp_diastolic, blood_glucose
    """
    rec = load_record(name)
    if not rec:
        print(f"❌ 未找到档案: {name}，请先创建（--new）")
        return {}

    log = {
        "date": today_str(),
        "timestamp": now_str(),
        "metrics": metrics,
        "symptoms": symptoms or [],
        "notes": notes,
    }
    rec["daily_logs"].append(log)
    rec["updated_at"] = now_str()

    # 也存一份每日独立文件
    daily_path = DAILY_DIR / f"{name}_{today_str()}.json"
    with open(daily_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    path = RECORDS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    return log


def import_honor_csv(csv_text: str) -> list:
    """
    导入荣耀运动健康导出的CSV数据
    荣耀CSV格式一般是：日期,时间,指标名,值,单位
    """
    records = []
    lines = csv_text.strip().split('\n')
    if not lines:
        return records
    
    # 跳过表头，检测格式
    header = lines[0].lower()
    # 常见格式: "日期,时间,类型,数值,单位" 或 "date,time,type,value,unit"
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.strip().split(',')
        if len(parts) < 4:
            continue
        try:
            date_str = parts[0].strip()
            time_str = parts[1].strip() if len(parts) > 1 else ''
            metric_type = parts[2].strip()
            value_str = parts[3].strip()
        except:
            continue
        
        # 映射指标名
        metric_map = {
            '心率': 'heart_rate', 'heart rate': 'heart_rate',
            'HRV': 'hrv', '心率变异性': 'hrv',
            '睡眠': 'sleep_duration', 'sleep': 'sleep_duration',
            '深睡': 'deep_sleep', 'deep sleep': 'deep_sleep',
            '浅睡': 'light_sleep', 'light sleep': 'light_sleep',
            '步数': 'steps', 'steps': 'steps',
            '血氧': 'spo2', 'spo2': 'spo2', 'SpO2': 'spo2',
            '压力': 'stress', 'stress': 'stress',
            '热量': 'calories', 'calories': 'calories',
            '收缩压': 'bp_systolic', 'systolic': 'bp_systolic',
            '舒张压': 'bp_diastolic', 'diastolic': 'bp_diastolic',
        }
        
        metric_key = metric_map.get(metric_type, metric_type.lower().replace(' ','_'))
        
        try:
            value = float(value_str.replace('\"','').strip())
        except:
            continue
        
        records.append({
            'date': date_str,
            'time': time_str,
            'metric': metric_key,
            'value': value,
        })
    
    return records


def import_band_data(name: str, data_path: str) -> int:
    """
    从 JSON/CSV 文件批量导入手环数据
    支持格式: JSON数组 / CSV（用逗号分隔）
    """
    rec = load_record(name)
    if not rec:
        print(f"❌ 未找到档案: {name}")
        return 0

    path = Path(data_path)
    if not path.exists():
        print(f"❌ 文件不存在: {data_path}")
        return 0

    try:
        content = path.read_text(encoding="utf-8")
    except:
        content = path.read_text()

    count = 0
    if data_path.endswith(".json"):
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict):
                        rec["daily_logs"].append({
                            "date": entry.get("date", today_str()),
                            "timestamp": entry.get("timestamp", now_str()),
                            "metrics": {k: v for k, v in entry.items()
                                       if k in DEVICE_METRICS and v is not None},
                            "symptoms": entry.get("symptoms", []),
                            "notes": entry.get("notes", ""),
                        })
                        count += 1
        except json.JSONDecodeError:
            print("❌ JSON 解析失败")
            return 0
    elif data_path.endswith(".csv"):
        import csv
        import io
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            metrics = {}
            for metric in DEVICE_METRICS:
                if metric in row and row[metric].strip():
                    try:
                        metrics[metric] = float(row[metric])
                    except ValueError:
                        pass
            rec["daily_logs"].append({
                "date": row.get("date", today_str()),
                "timestamp": row.get("timestamp", now_str()),
                "metrics": metrics,
                "symptoms": [],
                "notes": "",
            })
            count += 1

    rec["updated_at"] = now_str()
    path = RECORDS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    print(f"✅ 成功导入 {count} 条记录到 {name}")
    return count


def analyze_trends(name: str, days: int = 30) -> Dict:
    """
    趋势分析：最近 N 天的数据变化
    """
    rec = load_record(name)
    if not rec:
        return {"error": f"未找到档案: {name}"}

    cutoff = (date.today() - timedelta(days=days)).isoformat()
    logs = [l for l in rec.get("daily_logs", []) if l.get("date", "") >= cutoff]

    if not logs:
        return {"error": f"{name} 在过去 {days} 天内没有数据"}

    # 收集所有指标的变化
    metrics_data: Dict[str, List[float]] = {}
    symptom_freq: Dict[str, int] = {}

    for log in logs:
        # 指标
        for key, val in log.get("metrics", {}).items():
            if val is not None:
                if key not in metrics_data:
                    metrics_data[key] = []
                metrics_data[key].append(val)
        # 症状
        for s in log.get("symptoms", []):
            symptom_freq[s] = symptom_freq.get(s, 0) + 1

    # 计算统计
    trends = {}
    for key, values in metrics_data.items():
        if len(values) >= 2:
            avg = sum(values) / len(values)
            first = values[0]
            last = values[-1]
            diff = last - first
            trends[key] = {
                "label": DEVICE_METRICS.get(key, {}).get("label", key),
                "unit": DEVICE_METRICS.get(key, {}).get("unit", ""),
                "avg": round(avg, 1),
                "min": round(min(values), 1),
                "max": round(max(values), 1),
                "first": round(first, 1),
                "last": round(last, 1),
                "trend": "↑" if diff > 0 else ("↓" if diff < 0 else "→"),
                "change": round(diff, 1),
                "samples": len(values),
            }

    # 辨证频次
    syndrome_freq: Dict[str, int] = {}
    for rec_entry in rec.get("records", []):
        if rec_entry.get("date", "") >= cutoff:
            s = rec_entry.get("tcm_syndrome", "")
            if s:
                syndrome_freq[s] = syndrome_freq.get(s, 0) + 1

    return {
        "patient": name,
        "period": f"{days}天",
        "date_range": f"{logs[0].get('date','?')} → {logs[-1].get('date','?')}" if logs else "无数据",
        "log_count": len(logs),
        "metrics": trends,
        "symptom_frequency": dict(sorted(symptom_freq.items(), key=lambda x: -x[1])),
        "syndrome_history": dict(sorted(syndrome_freq.items(), key=lambda x: -x[1])),
    }


def print_record(rec: Dict):
    """打印健康档案摘要"""
    if not rec:
        return
    name = rec.get("patient_name", "?")
    age = _calc_age(rec.get("birth_year", 0))
    gender = rec.get("gender", "?")
    records = rec.get("records", [])
    logs = rec.get("daily_logs", [])

    print(f"\n{'═' * 50}")
    print(f"📋 健康档案: {name} ({age}岁/{gender})")
    print(f"  创建: {rec.get('created_at','')[:10]}")
    print(f"  更新: {rec.get('updated_at','')[:16]}")
    print(f"{'═' * 50}")

    if records:
        print(f"\n📝 辨证记录 ({len(records)} 次):")
        for r in records[-5:]:  # 最近5次
            print(f"  [{r.get('date','')[:10]}] {r.get('tcm_syndrome','?')}")
            print(f"    → {r.get('principle','')[:30]}")
    else:
        print(f"\n📝 辨证记录: 暂无")

    if logs:
        print(f"\n📊 日常数据 ({len(logs)} 条):")
        # 统计有几天数据
        days_with_data = len(set(l.get("date") for l in logs))
        print(f"   有数据天数: {days_with_data}")

        # 最新一天的数据摘要
        latest = logs[-1]
        metrics = latest.get("metrics", {})
        if metrics:
            print(f"   最新数据 ({latest.get('date','')}):")
            for key in ["heart_rate", "sleep_duration", "steps", "spo2", "stress", "hrv"]:
                if key in metrics:
                    info = DEVICE_METRICS.get(key, {})
                    print(f"     {info.get('label', key)}: {metrics[key]} {info.get('unit','')}")
    else:
        print(f"\n📊 日常数据: 暂无")

    print()


def print_trends(trends: Dict):
    """打印趋势分析"""
    if "error" in trends:
        print(f"\n⚠️  {trends['error']}")
        return

    print(f"\n{'═' * 50}")
    print(f"📈 趋势分析: {trends.get('patient','?')}")
    print(f"  周期: {trends.get('period','')} ({trends.get('date_range','')})")
    print(f"  数据点: {trends.get('log_count',0)} 条")
    print(f"{'═' * 50}")

    metrics = trends.get("metrics", {})
    if metrics:
        print(f"\n📊 指标变化趋势:")
        for key, t in sorted(metrics.items()):
            label = t.get("label", key)
            unit = t.get("unit", "")
            avg = t.get("avg", 0)
            trend_icon = t.get("trend", "→")
            change = t.get("change", 0)
            print(f"  {label}: 均{avg}{unit}  |  {trend_icon} {change:+}{unit}  |  [{t.get('min','')}–{t.get('max','')}]")
    else:
        print(f"\n📊 指标数据不足，无法分析趋势")

    symptoms = trends.get("symptom_frequency", {})
    if symptoms:
        print(f"\n🔴 高频症状:")
        for s, freq in list(symptoms.items())[:5]:
            print(f"  · {s} ({freq}次)")

    syndromes = trends.get("syndrome_history", {})
    if syndromes:
        print(f"\n🔄 证型历史:")
        for s, freq in list(syndromes.items())[:5]:
            print(f"  · {s} ({freq}次)")

    print()


# ── 与 xin_claw_doctor 的集成 ──
def save_doctor_consultation(name: str, dx_result: Dict, diet_result: Dict,
                              tongue: str = "", pulse: str = "",
                              symptoms: List[str] = None) -> str:
    """将 xin_claw_doctor 的辨证结果保存到健康档案"""
    rec = load_record(name)
    if not rec:
        # 自动创建
        rec = {
            "patient_name": name,
            "birth_year": 0,
            "gender": "",
            "created_at": now_str(),
            "updated_at": now_str(),
            "records": [],
            "daily_logs": [],
            "notes": "自动创建于 xin_claw_doctor",
        }

    syndrome = dx_result.get("syndrome", "")
    principle = dx_result.get("principle", "")
    entry = {
        "date": now_str(),
        "type": "consultation",
        "symptoms": symptoms or [],
        "diagnosis": dx_result.get("match_detail", ""),
        "tcm_syndrome": syndrome,
        "principle": principle,
        "treatment": f"食疗: {', '.join(diet_result.get('recommended_ingredients', []))}" if diet_result else "",
        "tongue": tongue,
        "pulse": pulse,
        "special_pattern": dx_result.get("special_pattern", ""),
        "phase_state": dx_result.get("phase_state", {}).get("phase", ""),
    }
    rec["records"].append(entry)
    rec["updated_at"] = now_str()

    path = RECORDS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)

    return path


# ── CLI ──
def cli():
    import argparse
    parser = argparse.ArgumentParser(
        description="道归 · 健康档案系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --new --name 道归 --birth 2007 --gender male
  %(prog)s --record 道归 --symptoms 失眠 心悸 --syndrome 心血虚证
  %(prog)s --log 道归 --heart-rate 72 --sleep 7.5 --steps 8000
  %(prog)s --import 道归 data.json
  %(prog)s --show 道归
  %(prog)s --trend 道归 --days 30
  %(prog)s --list
        """
    )
    parser.add_argument("--new", action="store_true", help="新建健康档案")
    parser.add_argument("--name", help="姓名")
    parser.add_argument("--birth", type=int, help="出生年份")
    parser.add_argument("--gender", choices=["male", "female"], help="性别")
    parser.add_argument("--show", metavar="姓名", help="查看健康档案")
    parser.add_argument("--list", action="store_true", help="列出所有档案")
    parser.add_argument("--record", metavar="姓名", help="添加辨证记录")
    parser.add_argument("--symptoms", nargs="+", help="症状列表")
    parser.add_argument("--syndrome", help="证型")
    parser.add_argument("--principle", help="治则")
    parser.add_argument("--log", metavar="姓名", help="添加日常健康数据（配合--heart-rate等）")
    parser.add_argument("--heart-rate", type=float, help="心率 bpm")
    parser.add_argument("--sleep", type=float, help="睡眠时长 h")
    parser.add_argument("--deep-sleep", type=float, help="深睡时长 h")
    parser.add_argument("--steps", type=int, help="步数")
    parser.add_argument("--spo2", type=float, help="血氧 %")
    parser.add_argument("--stress", type=float, help="压力指数")
    parser.add_argument("--hrv", type=float, help="心率变异性 ms")
    parser.add_argument("--bp-sys", type=float, help="收缩压 mmHg")
    parser.add_argument("--bp-dia", type=float, help="舒张压 mmHg")
    parser.add_argument("--glucose", type=float, help="血糖 mmol/L")
    parser.add_argument("--trend", metavar="姓名", help="趋势分析")
    parser.add_argument("--days", type=int, default=30, help="分析天数")
    parser.add_argument("--import-data", nargs=2, metavar=("姓名", "文件路径"),
                        help="批量导入手环数据（JSON/CSV）")

    args = parser.parse_args()

    if args.list:
        records = list_records()
        if not records:
            print("\n📋 暂无健康档案")
            return
        print(f"\n📋 健康档案列表 ({len(records)}):")
        print(f"{'─' * 60}")
        for r in records:
            print(f"  {r['name']}  ({r['age']}岁/{r['gender']})")
            print(f"    辨证: {r['records']}次 | 日常: {r['daily_logs']}条 | 更新: {r['updated']}")
        return

    if args.new:
        rec = record_new(args.name, args.birth or 0, args.gender or "")
        print_record(rec)
        return

    if args.show:
        rec = load_record(args.show)
        if rec:
            print_record(rec)
        else:
            print(f"\n❌ 未找到档案: {args.show}")
            print("  可用 --list 查看所有档案")
        return

    if args.record:
        if not args.symptoms:
            print("❌ 请提供 --symptoms")
            return
        entry = add_consultation(
            args.record, args.symptoms,
            f"{args.syndrome or '？'} | {args.principle or ''}",
            args.principle or "",
            tcm_syndrome=args.syndrome or "",
            treatment=args.principle or "",
        )
        if entry:
            print(f"✅ 已记录: {args.record} → {args.syndrome or '?'}")
        return

    if args.log:
        metrics = {}
        if args.heart_rate: metrics["heart_rate"] = args.heart_rate
        if args.hrv: metrics["hrv"] = args.hrv
        if args.sleep: metrics["sleep_duration"] = args.sleep
        if args.deep_sleep: metrics["deep_sleep"] = args.deep_sleep
        if args.steps: metrics["steps"] = args.steps
        if args.spo2: metrics["spo2"] = args.spo2
        if args.stress: metrics["stress"] = args.stress
        if args.bp_sys: metrics["bp_systolic"] = args.bp_sys
        if args.bp_dia: metrics["bp_diastolic"] = args.bp_dia
        if args.glucose: metrics["blood_glucose"] = args.glucose
        if not metrics:
            print("❌ 请提供至少一个指标（--heart-rate / --sleep / --steps 等）")
            return
        log = add_daily_log(args.log, metrics, symptoms=args.symptoms)
        if log:
            print(f"✅ 数据已记录: {args.log} / {log['date']}")
            for key, val in metrics.items():
                info = DEVICE_METRICS.get(key, {})
                print(f"  {info.get('label',key)}: {val} {info.get('unit','')}")
        return

    if args.trend:
        trends = analyze_trends(args.trend, args.days)
        print_trends(trends)
        return

    if args.import_data:
        count = import_band_data(args.import_data[0], args.import_data[1])
        return

    parser.print_help()


if __name__ == "__main__":
    cli()
