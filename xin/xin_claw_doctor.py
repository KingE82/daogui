#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道归 · 本地辨证食疗工具 v2
含：辨证引擎 + 风险预警 + 西医参考建议

理论根基：道归五刀方法论 + 相变语言 + 传统八纲五脏辨证
数据来源：OpenKG 中医药知识图谱 + 国图古籍 + 本地知识库
"""

import json
import re
import os
import sys
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════
# 第一部分：证型知识库
# ═══════════════════════════════════════════

SYNDROME_KNOWLEDGE = {
    "心气虚证": {
        "organs": ["心"],
        "nature": "虚证",
        "symptoms": ["心悸", "气短", "自汗", "神疲", "乏力", "嗜睡", "面色淡白", "舌淡", "脉虚"],
        "principle": "补益心气",
        "recommended": ["黄芪", "人参", "党参", "茯苓", "红枣", "桂圆", "莲子"],
        "avoid": ["萝卜", "绿豆", "空心菜", "浓茶"],
        "foods": ["黄芪炖鸡", "参苓粥", "桂圆红枣汤", "莲子百合粥"],
    },
    "心血虚证": {
        "organs": ["心"],
        "nature": "虚证",
        "symptoms": ["心悸", "失眠", "多梦", "健忘", "头晕", "面色萎黄", "唇舌色淡", "脉细"],
        "principle": "补血养心",
        "recommended": ["当归", "熟地", "白芍", "阿胶", "红枣", "龙眼肉", "枸杞"],
        "avoid": ["辛辣", "油腻", "浓茶", "咖啡"],
        "foods": ["当归羊肉汤", "红枣桂圆粥", "四物汤", "阿胶糕"],
    },
    "心阴虚证": {
        "organs": ["心"],
        "nature": "虚证",
        "symptoms": ["心悸", "失眠", "心烦", "五心烦热", "盗汗", "口干", "舌红少津", "脉细数"],
        "principle": "滋阴养心",
        "recommended": ["麦冬", "百合", "玉竹", "生地", "沙参", "枸杞", "银耳"],
        "avoid": ["辛辣", "煎炸", "羊肉", "酒"],
        "foods": ["麦冬百合粥", "银耳莲子羹", "生地麦冬饮", "玉竹瘦肉汤"],
    },
    "心阳虚证": {
        "organs": ["心"],
        "nature": "虚证",
        "symptoms": ["心悸", "胸闷", "畏寒", "肢冷", "嗜睡", "面色苍白", "自汗", "舌淡胖", "脉沉迟"],
        "principle": "温补心阳",
        "recommended": ["桂枝", "肉桂", "附子", "干姜", "黄芪", "羊肉", "核桃"],
        "avoid": ["生冷", "寒凉", "西瓜", "苦瓜"],
        "foods": ["桂枝羊肉汤", "黄芪炖鸡", "核桃红枣粥", "姜枣茶"],
    },
    "心火亢盛证": {
        "organs": ["心"],
        "nature": "实证",
        "symptoms": ["心烦", "失眠", "口舌生疮", "面赤", "口渴", "小便短赤", "舌尖红", "脉数"],
        "principle": "清心泻火",
        "recommended": ["黄连", "莲子心", "竹叶", "生地", "栀子", "绿豆", "苦瓜"],
        "avoid": ["辛辣", "羊肉", "酒", "韭菜"],
        "foods": ["莲子心茶", "绿豆汤", "竹叶粥", "苦瓜炒蛋"],
    },
    "肝气郁结证": {
        "organs": ["肝"],
        "nature": "实证",
        "symptoms": ["情绪抑郁", "胁肋胀痛", "善太息", "嗳气", "月经不调", "脉弦"],
        "principle": "疏肝理气",
        "recommended": ["柴胡", "玫瑰花", "薄荷", "香附", "佛手", "橘皮", "金橘"],
        "avoid": ["油腻", "辛辣", "酒"],
        "foods": ["玫瑰花茶", "薄荷粥", "佛手炖汤", "金橘蜂蜜饮"],
    },
    "肝火上炎证": {
        "organs": ["肝"],
        "nature": "实证",
        "symptoms": ["头痛", "目赤", "耳鸣", "口苦", "急躁易怒", "胁痛", "舌红苔黄", "脉弦数"],
        "principle": "清肝泻火",
        "recommended": ["菊花", "决明子", "夏枯草", "龙胆草", "栀子", "芹菜", "苦瓜"],
        "avoid": ["辛辣", "油炸", "酒", "羊肉"],
        "foods": ["菊花决明子茶", "夏枯草瘦肉汤", "芹菜汁", "苦瓜汤"],
    },
    "肝血虚证": {
        "organs": ["肝"],
        "nature": "虚证",
        "symptoms": ["头晕", "目眩", "面色苍白", "爪甲不荣", "肢体麻木", "月经量少", "舌淡", "脉细"],
        "principle": "补肝养血",
        "recommended": ["当归", "白芍", "熟地", "枸杞", "桑椹", "猪肝", "菠菜"],
        "avoid": ["辛辣", "生冷"],
        "foods": ["当归炖猪肝", "枸杞桑椹粥", "菠菜猪肝汤", "首乌炖鸡"],
    },
    "肝阳上亢证": {
        "organs": ["肝"],
        "nature": "本虚标实",
        "symptoms": ["头晕目眩", "头胀痛", "面红目赤", "急躁", "失眠", "腰膝酸软", "舌红", "脉弦有力"],
        "principle": "平肝潜阳",
        "recommended": ["天麻", "钩藤", "石决明", "菊花", "枸杞", "芹菜", "海带"],
        "avoid": ["辛辣", "酒", "咖啡", "煎炸"],
        "foods": ["天麻炖鱼头", "菊花枸杞茶", "芹菜海带汤", "决明子粥"],
    },
    "脾气虚证": {
        "organs": ["脾"],
        "nature": "虚证",
        "symptoms": ["食少", "腹胀", "便溏", "神疲", "乏力", "嗜睡", "面色萎黄", "舌淡苔白", "脉缓弱"],
        "principle": "健脾益气",
        "recommended": ["党参", "白术", "茯苓", "山药", "白扁豆", "莲子", "芡实"],
        "avoid": ["生冷", "油腻", "糯米", "肥肉"],
        "foods": ["四君子汤", "山药莲子粥", "茯苓糕", "白扁豆炖排骨"],
    },
    "脾阳虚证": {
        "organs": ["脾"],
        "nature": "虚证",
        "symptoms": ["腹痛喜按", "便溏", "畏寒", "肢冷", "食少", "腹胀", "嗜睡", "舌淡胖", "脉沉迟"],
        "principle": "温中健脾",
        "recommended": ["干姜", "党参", "白术", "草果", "砂仁", "羊肉", "白扁豆"],
        "avoid": ["生冷", "寒凉", "西瓜", "梨"],
        "foods": ["理中汤", "干姜羊肉汤", "砂仁猪肚汤", "白扁豆粥"],
    },
    "寒湿困脾证": {
        "organs": ["脾"],
        "nature": "实证",
        "symptoms": ["脘腹痞闷", "腹痛", "便溏", "口淡", "头身困重", "苔白腻", "脉濡缓"],
        "principle": "化湿运脾",
        "recommended": ["藿香", "佩兰", "苍术", "厚朴", "陈皮", "白扁豆", "砂仁"],
        "avoid": ["油腻", "生冷", "甜食", "酒"],
        "foods": ["藿香粥", "陈皮砂仁炖汤", "白扁豆薏仁汤", "苍术炖猪肚"],
    },
    "肺气虚证": {
        "organs": ["肺"],
        "nature": "虚证",
        "symptoms": ["咳嗽无力", "气短", "自汗", "易感冒", "神疲", "面色淡白", "舌淡", "脉虚弱"],
        "principle": "补益肺气",
        "recommended": ["黄芪", "党参", "五味子", "百合", "山药", "银耳", "燕窝"],
        "avoid": ["生冷", "辛辣", "烟"],
        "foods": ["黄芪炖鸡", "百合银耳羹", "山药排骨汤", "五味子茶"],
    },
    "肺阴虚证": {
        "organs": ["肺"],
        "nature": "虚证",
        "symptoms": ["干咳少痰", "咽干", "声音嘶哑", "盗汗", "五心烦热", "舌红少津", "脉细数"],
        "principle": "滋阴润肺",
        "recommended": ["沙参", "麦冬", "玉竹", "百合", "银耳", "梨", "蜂蜜"],
        "avoid": ["辛辣", "油炸", "烟酒"],
        "foods": ["沙参麦冬汤", "冰糖炖雪梨", "百合银耳羹", "玉竹瘦肉汤"],
    },
    "风寒束肺证": {
        "organs": ["肺"],
        "nature": "实证",
        "symptoms": ["咳嗽", "咳痰清稀", "鼻塞", "流清涕", "恶寒", "发热", "苔薄白", "脉浮紧"],
        "principle": "疏风散寒",
        "recommended": ["生姜", "葱白", "紫苏", "桂枝", "防风", "红糖", "大蒜"],
        "avoid": ["生冷", "寒凉", "西瓜"],
        "foods": ["生姜红糖水", "葱白粥", "紫苏叶汤", "大蒜红糖饮"],
    },
    "肾阴虚证": {
        "organs": ["肾"],
        "nature": "虚证",
        "symptoms": ["腰膝酸软", "头晕耳鸣", "失眠多梦", "五心烦热", "盗汗", "舌红少苔", "脉细数"],
        "principle": "滋补肾阴",
        "recommended": ["熟地", "山茱萸", "枸杞", "女贞子", "旱莲草", "黑芝麻", "桑椹"],
        "avoid": ["辛辣", "油炸", "羊肉"],
        "foods": ["六味地黄乌鸡汤", "枸杞桑椹粥", "黑芝麻糊", "女贞子茶"],
    },
    "肾阳虚证": {
        "organs": ["肾"],
        "nature": "虚证",
        "symptoms": ["腰膝酸冷", "畏寒", "肢冷", "夜尿多", "性欲减退", "舌淡胖", "脉沉迟"],
        "principle": "温补肾阳",
        "recommended": ["附子", "肉桂", "鹿茸", "仙灵脾", "杜仲", "韭菜", "羊肉"],
        "avoid": ["生冷", "寒凉", "绿豆"],
        "foods": ["金匮肾气羊肉汤", "韭菜炒虾仁", "杜仲炖猪腰", "核桃黑豆粥"],
    },
    "肾精不足证": {
        "organs": ["肾"],
        "nature": "虚证",
        "symptoms": ["腰膝酸软", "头晕", "耳鸣", "健忘", "发脱", "齿摇", "舌淡", "脉沉细"],
        "principle": "补肾填精",
        "recommended": ["熟地", "枸杞", "黄精", "制首乌", "菟丝子", "核桃", "黑芝麻"],
        "avoid": ["辛辣", "油炸"],
        "foods": ["首乌核桃粥", "枸杞黄精炖鸡", "黑芝麻糊", "菟丝子粥"],
    },
    "风寒束表": {
        "organs": ["肺"],
        "nature": "表证",
        "symptoms": ["恶寒", "发热", "头痛", "身痛", "无汗", "鼻塞", "流清涕", "咳嗽", "舌淡苔白", "脉浮紧"],
        "principle": "辛温解表，宣肺散寒",
        "recommended": ["生姜", "葱白", "紫苏", "桂枝", "防风", "羌活"],
        "avoid": ["生冷", "寒凉", "油腻", "水果"],
        "foods": ["生姜红糖水", "葱白豆豉汤", "紫苏粥"],
    },
    "风热犯肺": {
        "organs": ["肺"],
        "nature": "表证",
        "symptoms": ["发热", "咽痛", "口干", "咳嗽", "黄痰", "舌尖红", "苔薄黄", "脉浮数"],
        "principle": "辛凉解表，疏风清热",
        "recommended": ["菊花", "桑叶", "薄荷", "金银花", "连翘", "牛蒡子"],
        "avoid": ["辛辣", "羊肉", "酒", "煎炸"],
        "foods": ["菊花薄荷茶", "桑叶粥", "金银花甘草茶", "冰糖雪梨"],
    },
    "暑湿困脾": {
        "organs": ["脾"],
        "nature": "实证",
        "symptoms": ["身热不扬", "头重如裹", "胸闷", "脘痞", "恶心", "纳呆", "便溏", "苔白腻", "脉濡"],
        "principle": "清暑化湿，健脾和中",
        "recommended": ["藿香", "佩兰", "白扁豆", "薏仁", "荷叶", "绿豆"],
        "avoid": ["油腻", "甜食", "生冷", "酒"],
        "foods": ["藿香粥", "荷叶薏仁汤", "绿豆百合汤"],
    },
    "湿热蕴脾": {
        "organs": ["脾", "肝"],
        "nature": "实证",
        "symptoms": ["脘腹胀闷", "口苦", "纳呆", "便溏不爽", "舌红苔黄腻", "脉滑数"],
        "principle": "清热利湿，化浊和中",
        "recommended": ["茵陈", "栀子", "薏仁", "赤小豆", "冬瓜", "苦瓜"],
        "avoid": ["辛辣", "油炸", "羊肉", "酒", "甜食"],
        "foods": ["赤小豆薏仁汤", "冬瓜汤", "苦瓜炒蛋"],
    },
    "燥邪伤肺": {
        "organs": ["肺"],
        "nature": "实证",
        "symptoms": ["干咳", "咽干", "鼻燥", "口渴", "舌红少津", "脉数"],
        "principle": "清肺润燥，养阴生津",
        "recommended": ["沙参", "麦冬", "百合", "玉竹", "梨", "银耳"],
        "avoid": ["辛辣", "煎炸", "羊肉", "酒"],
        "foods": ["川贝雪梨羹", "沙参麦冬粥", "银耳百合汤"],
    },
    "风寒袭肺": {
        "organs": ["肺"],
        "nature": "表证",
        "symptoms": ["咳嗽", "痰白稀", "鼻塞", "流清涕", "恶寒", "舌淡苔白", "脉浮紧"],
        "principle": "宣肺散寒，化痰止咳",
        "recommended": ["紫苏", "杏仁", "桔梗", "陈皮", "生姜", "葱白"],
        "avoid": ["生冷", "寒凉", "油腻", "甜食"],
        "foods": ["杏仁粥", "陈皮生姜汤", "紫苏叶粥"],
    },
    "表寒证": {
        "organs": ["肺"],
        "nature": "表证",
        "symptoms": ["恶寒", "发热", "无汗", "头痛", "身痛", "舌淡苔白", "脉浮紧"],
        "principle": "辛温解表",
        "recommended": ["生姜", "葱白", "桂枝", "紫苏"],
        "avoid": ["生冷", "寒凉"],
        "foods": ["生姜红糖水", "葱白粥"],
    },
    "表热证": {
        "organs": ["肺"],
        "nature": "表证",
        "symptoms": ["发热", "咽痛", "口渴", "舌尖红", "脉浮数"],
        "principle": "辛凉解表",
        "recommended": ["金银花", "连翘", "薄荷", "桑叶", "菊花"],
        "avoid": ["辛辣", "羊肉", "酒"],
        "foods": ["金银花茶", "桑菊饮", "薄荷粥"],
    },
    "里热证": {
        "organs": ["胃", "大肠"],
        "nature": "实证",
        "symptoms": ["高热", "口渴饮冷", "暴食", "面红", "便秘", "尿黄", "舌红苔黄", "脉洪数"],
        "principle": "清热泻火",
        "recommended": ["石膏", "知母", "黄连", "黄芩", "栀子", "绿豆"],
        "avoid": ["辛辣", "羊肉", "油炸", "酒"],
        "foods": ["绿豆汤", "黄连茶"],
    },
    "里寒证": {
        "organs": ["脾", "胃"],
        "nature": "实证",
        "symptoms": ["畏寒", "肢冷", "腹痛", "喜温喜按", "便溏", "舌淡苔白", "脉沉迟"],
        "principle": "温中散寒",
        "recommended": ["干姜", "肉桂", "小茴香", "花椒", "羊肉", "韭菜"],
        "avoid": ["生冷", "寒凉", "西瓜", "梨"],
        "foods": ["干姜羊肉汤", "肉桂粥"],
    },
    "上热下寒": {
        "organs": ["心", "肾"],
        "nature": "虚实夹杂",
        "symptoms": ["心烦", "失眠", "口舌生疮", "下肢冷", "便溏", "舌红苔白"],
        "principle": "交通心肾，清上温下",
        "recommended": ["黄连", "肉桂", "莲子心"],
        "avoid": ["辛辣", "生冷"],
        "foods": ["交泰茶", "肉桂莲子心茶"],
    },
    "阴虚火旺": {
        "organs": ["肾", "心"],
        "nature": "虚证",
        "symptoms": ["五心烦热", "颧红", "盗汗", "口干", "咽干", "舌红少苔", "脉细数"],
        "principle": "滋阴降火",
        "recommended": ["知母", "黄柏", "生地", "麦冬", "玄参"],
        "avoid": ["辛辣", "煎炸", "羊肉", "酒"],
        "foods": ["知柏地黄汤", "生地麦冬饮"],
    },
}

# 九种体质
CONSTITUTION_KNOWLEDGE = {
    "平和质": {"desc": "阴阳平衡，气血充沛", "principle": "保持均衡", "recommended": ["五谷杂粮", "时令蔬果"], "avoid": ["暴饮暴食"]},
    "气虚质": {"desc": "气短懒言，易疲劳", "principle": "培补元气", "recommended": ["山药", "黄芪", "大枣"], "avoid": ["生冷"]},
    "阳虚质": {"desc": "畏寒怕冷，手足不温", "principle": "温阳散寒", "recommended": ["羊肉", "韭菜", "核桃"], "avoid": ["寒凉生冷"]},
    "阴虚质": {"desc": "口燥咽干，手足心热", "principle": "滋阴降火", "recommended": ["百合", "银耳", "鸭肉"], "avoid": ["辛辣"]},
    "痰湿质": {"desc": "形体肥胖，口黏苔腻", "principle": "健脾化痰", "recommended": ["薏仁", "白扁豆", "陈皮"], "avoid": ["油腻"]},
    "湿热质": {"desc": "面垢油光，易生痤疮", "principle": "清热利湿", "recommended": ["绿豆", "苦瓜", "冬瓜"], "avoid": ["辛辣"]},
    "血瘀质": {"desc": "肤色晦暗，舌有瘀斑", "principle": "活血化瘀", "recommended": ["山楂", "黑豆", "玫瑰花"], "avoid": ["寒凉"]},
    "气郁质": {"desc": "神情抑郁，烦闷不乐", "principle": "疏肝理气", "recommended": ["玫瑰花", "薄荷", "佛手"], "avoid": ["辛辣"]},
    "特禀质": {"desc": "过敏体质，易喷嚏", "principle": "益气固表", "recommended": ["黄芪", "防风", "白术"], "avoid": ["海鲜"]},
}
# ═══════════════════════════════════════════
# 第二部分：辨证引擎
# ═══════════════════════════════════════════

def differentiate(symptoms: List[str], tongue: str = "", pulse: str = "") -> Dict:
    """辨证引擎"""
    if not symptoms:
        return {"error": "至少提供一个症状"}

    symptom_set = set()
    for s in symptoms:
        s = s.strip().lower()
        symptom_set.add(s)
        for ch in ["、", "，", ",", ";", "；", "。"]:
            if ch in s:
                for part in s.split(ch):
                    part = part.strip()
                    if len(part) >= 2:
                        symptom_set.add(part)

    char_features = set()
    for s in list(symptom_set):
        for char in ["烦", "躁", "惊", "恐", "忧", "郁", "怒", "急"]:
            if char in s and len(s) <= 6:
                char_features.add(char)
    symptom_set.update(char_features)

    PULSE_HEAT_KEYWORDS = {"脉数": "热", "一息六七致": "热", "脉洪": "热", "脉滑数": "热", "脉弦数": "热"}
    PULSE_COLD_KEYWORDS = {"脉迟": "寒", "脉沉迟": "寒", "脉微弱": "寒"}
    additional_symptoms = set()
    for s in list(symptom_set):
        for pk, pv in {**PULSE_HEAT_KEYWORDS, **PULSE_COLD_KEYWORDS}.items():
            if pk in s or s in pk:
                additional_symptoms.add("热象" if pv == "热" else "寒象")
        if "溏" in s or "便" in s:
            additional_symptoms.add("脾虚线索")
    symptom_set.update(additional_symptoms)

    scores = []
    for syndrome_name, info in SYNDROME_KNOWLEDGE.items():
        match_count = 0
        matched_symptoms = []
        for symptom in symptom_set:
            for ref in info["symptoms"]:
                if symptom in ref or ref in symptom:
                    match_count += 1
                    matched_symptoms.append(ref)
                    break
                if len(symptom) == 1 and len(ref) >= 2 and symptom in ref:
                    match_count += 0.5
                    matched_symptoms.append(ref)
                    break
                if len(symptom) >= 2 and len(ref) >= 2:
                    common = set(symptom) & set(ref)
                    if len(common) >= 2:
                        match_count += 0.6
                        matched_symptoms.append(ref)
                        break
        if match_count > 0:
            score = match_count / len(info["symptoms"])
            scores.append({
                "syndrome": syndrome_name,
                "organ": info["organs"][0],
                "nature": info["nature"],
                "score": round(score, 3),
                "match_count": match_count,
                "total_ref": len(info["symptoms"]),
                "matched_symptoms": matched_symptoms,
                "principle": info["principle"],
            })

    if not scores:
        return {"syndrome": "无法确定", "confidence": 0, "message": "症状描述不充分"}

    if tongue or pulse:
        scores = apply_four_diag_bonus(scores, tongue, pulse)

    scores.sort(key=lambda x: x["score"], reverse=True)
    top = scores[0]
    top_score = top["score"]

    if top_score >= 0.4:
        confidence = "高"
    elif top_score >= 0.2:
        confidence = "中"
    else:
        confidence = "低"

    result = {
        "syndrome": top["syndrome"],
        "organ": top["organ"],
        "nature": top["nature"],
        "confidence": confidence,
        "match_score": top_score,
        "match_detail": f"匹配 {top['match_count']}/{top['total_ref']} 项症状",
        "matched_symptoms": top["matched_symptoms"],
        "principle": top["principle"],
    }

    if len(scores) > 1 and scores[1]["score"] >= 0.3:
        if scores[1]["organ"] != top["organ"]:
            result["兼夹证"] = {
                "syndrome": scores[1]["syndrome"],
                "organ": scores[1]["organ"],
                "match_detail": f"匹配 {scores[1]['match_count']}/{scores[1]['total_ref']} 项症状",
            }

    result["phase_state"] = nature_to_phase(top["nature"])
    result["organs"] = list(set([top["organ"]]))
    if len(scores) > 1 and scores[1]["score"] >= 0.25:
        result["organs"].append(scores[1]["organ"])

    # 心肾不交检测
    if top["organ"] in ("心", "肾"):
        has_heart = has_kidney = False
        for s in scores[:3]:
            if s["organ"] == "心": has_heart = True
            if s["organ"] == "肾": has_kidney = True
        if has_heart and has_kidney:
            result["special_pattern"] = "心肾不交"
            result["special_desc"] = "水火不济——心火亢于上，肾阴亏于下"

    trace = []
    for s in scores[:5]:
        trace.append({
            "证型": s["syndrome"],
            "病位": s["organ"],
            "病性": s["nature"],
            "匹配度": s["score"],
            "匹配详情": f"{s['match_count']}/{s['total_ref']}",
            "匹配症状": s["matched_symptoms"],
            "治则": s["principle"],
        })
    result["reasoning_trace"] = trace
    return result


def nature_to_phase(nature: str) -> Dict:
    """证型性质 → 相变语言映射"""
    mapping = {
        "虚证": {"phase": "冰/水", "desc": "能量衰减态，需要外部热源输入", "action": "温补滋养"},
        "实证": {"phase": "汽/火", "desc": "能量亢进态，需要降压降温", "action": "清泻疏解"},
        "本虚标实": {"phase": "超临界/湍流", "desc": "核心不足但表面压力大", "action": "标本兼治"},
    }
    return mapping.get(nature, {"phase": "水", "desc": "日常流动态", "action": "观察维持"})


def get_dietary_plan(syndrome_result: Dict) -> Dict:
    """根据辨证结果生成食疗方案"""
    syndrome_name = syndrome_result.get("syndrome")
    if syndrome_name == "无法确定":
        return {"recommended_foods": [], "foods_to_avoid": [], "recipes": [], "note": "证型不明确"}
    info = SYNDROME_KNOWLEDGE.get(syndrome_name, {})
    if not info:
        return {"recommended_foods": [], "foods_to_avoid": [], "recipes": []}
    return {
        "syndrome": syndrome_name,
        "principle": info.get("principle", ""),
        "recommended_ingredients": info.get("recommended", []),
        "foods_to_avoid": info.get("avoid", []),
        "recipes": [{"name": r, "适用证型": syndrome_name} for r in info.get("foods", [])],
    }


def get_constitution_advice(constitution: str) -> Dict:
    """体质调理建议"""
    info = CONSTITUTION_KNOWLEDGE.get(constitution)
    return info if info else {"error": f"未知体质: {constitution}"}
# ═══════════════════════════════════════════
# 第三部分：综合治疗方案
# ═══════════════════════════════════════════

TREATMENT_KNOWLEDGE = {
    "心气虚证": {
        "acupoints": ["内关", "神门", "心俞", "膻中", "足三里", "气海"],
        "moxibustion": ["足三里", "气海", "心俞", "关元"],
        "massage": ["按揉内关穴3分钟", "按揉神门穴2分钟", "叩击心俞穴"],
        "daily_care": ["作息规律，避免熬夜，午间小憩30分钟", "适度运动以不感疲劳为度（散步/八段锦）", "避免剧烈运动和大量出汗", "室温保持温暖"],
        "emotional_care": ["避免过度思虑和精神紧张", "听舒缓音乐（宫调/羽调）", "练习深呼吸：吸气4秒→屏气4秒→呼气6秒"],
        "sleep_advice": "睡前温水泡脚15分钟，按揉涌泉穴",
    },
    "心血虚证": {
        "acupoints": ["血海", "膈俞", "心俞", "脾俞", "足三里", "三阴交"],
        "moxibustion": ["足三里", "血海", "脾俞", "关元"],
        "massage": ["按揉血海穴3分钟", "推按心俞穴", "摩腹顺时针50圈"],
        "daily_care": ["保证睡眠时间，子时（23:00）前入睡", "避免长时间用眼", "经期后适当增加补血食材摄入"],
        "emotional_care": ["避免过度悲伤", "多接触温暖色调环境", "与亲友交流，避免独处时反复回想"],
        "sleep_advice": "睡前温红枣桂圆水，按摩神门穴",
    },
    "心阴虚证": {
        "acupoints": ["神门", "内关", "心俞", "肾俞", "太溪", "三阴交"],
        "moxibustion": ["不宜艾灸"],
        "massage": ["按揉神门穴2分钟", "推太溪穴", "搓涌泉穴至发热"],
        "daily_care": ["忌熬夜，21:00后减少活动", "避免桑拿/汗蒸", "保持居室湿度", "多食滋阴食材"],
        "emotional_care": ["避免急躁和暴怒", "练习书法/绘画等静心活动", "听自然白噪音"],
        "sleep_advice": "睡前百合麦冬水小半杯",
    },
    "心阳虚证": {
        "acupoints": ["心俞", "厥阴俞", "神门", "内关", "关元", "命门"],
        "moxibustion": ["关元", "气海", "命门", "心俞（温灸）"],
        "massage": ["掌擦命门穴至发热", "按揉关元穴", "搓热手掌捂心前区"],
        "daily_care": ["注意保暖，夏日避免冷气直吹", "上午8-10点适度锻炼", "忌生冷饮食和冰镇饮料"],
        "emotional_care": ["主动寻求社交支持", "参与集体活动", "阅读振奋人心的内容"],
        "sleep_advice": "睡前艾草泡脚20分钟，喝姜枣茶",
    },
    "心火亢盛证": {
        "acupoints": ["少冲", "中冲", "劳宫", "曲泽", "大陵", "内关"],
        "moxibustion": ["不宜艾灸"],
        "massage": ["掐按少冲穴", "按揉劳宫穴3分钟", "推天河水"],
        "daily_care": ["忌辛辣/油炸/烧烤", "保持大便通畅", "多饮淡竹叶水"],
        "emotional_care": ["练习冥想/正念呼吸", "避免过度兴奋活动"],
        "sleep_advice": "睡前莲子心泡水（量不宜多）",
    },
    "肝气郁结证": {
        "acupoints": ["太冲", "行间", "期门", "肝俞", "膻中", "阳陵泉"],
        "moxibustion": ["太冲", "期门", "阳陵泉"],
        "massage": ["按揉太冲穴3分钟（向行间推）", "搓两胁肋部", "开四关"],
        "daily_care": ["春季多户外活动", "常做伸展运动/瑜伽", "衣着宽松"],
        "emotional_care": ["主动表达情绪，不要压抑", "与信任的人倾诉", "听角调音乐"],
        "sleep_advice": "睡前玫瑰花茶一杯",
    },
    "肝火上炎证": {
        "acupoints": ["太冲", "行间", "风池", "太阳", "肝俞", "胆俞"],
        "moxibustion": ["不宜艾灸"],
        "massage": ["按揉太冲→行间推压", "按揉太阳穴", "刮痧肝俞/胆俞"],
        "daily_care": ["忌辛辣/油炸/羊肉/狗肉", "忌酒", "可饮菊花/决明子茶"],
        "emotional_care": ["发火前先深呼吸10次", "避免与人争执", "练习冷色调冥想"],
        "sleep_advice": "睡前菊花决明子茶",
    },
    "肝血虚证": {
        "acupoints": ["肝俞", "血海", "足三里", "三阴交", "关元", "太冲"],
        "moxibustion": ["足三里", "关元", "肝俞"],
        "massage": ["按揉血海穴3分钟", "按揉三阴交", "搓热手掌捂眼睛"],
        "daily_care": ["避免长时间看屏幕", "月经后注意补血", "保证睡眠质量"],
        "emotional_care": ["避免突然改变体位", "多观赏绿色植物", "避免强光刺激"],
        "sleep_advice": "睡前热水泡脚，按摩三阴交",
    },
    "肝阳上亢证": {
        "acupoints": ["太冲", "行间", "风池", "百会", "太溪", "涌泉"],
        "moxibustion": ["不宜艾灸头部"],
        "massage": ["推太冲→行间方向", "按揉风池穴3分钟", "涌泉穴搓热"],
        "daily_care": ["低盐饮食", "避免突然剧烈运动", "保持大便通畅", "定期测量血压"],
        "emotional_care": ["做决定前冷静24小时", "练习太极/站桩", "避免激烈辩论"],
        "sleep_advice": "睡前温水泡脚引火下行",
    },
    "脾气虚证": {
        "acupoints": ["足三里", "脾俞", "胃俞", "中脘", "三阴交", "太白"],
        "moxibustion": ["足三里", "中脘", "脾俞", "气海"],
        "massage": ["按揉足三里3分钟", "摩腹顺时针50圈", "叩击脾俞穴"],
        "daily_care": ["少食多餐，细嚼慢咽", "忌生冷寒凉食物", "忌甜食和油腻", "饭后散步15分钟"],
        "emotional_care": ["减少过度分析/担心未来", "专注当下", "听宫调音乐"],
        "sleep_advice": "睡前摩腹100圈，晚餐宜早清淡",
    },
    "脾阳虚证": {
        "acupoints": ["足三里", "脾俞", "胃俞", "中脘", "关元", "命门"],
        "moxibustion": ["关元", "气海", "足三里", "中脘（温灸20分钟）"],
        "massage": ["掌擦命门至发热", "热敷中脘", "按揉足三里"],
        "daily_care": ["全年忌生冷，水果蒸熟吃", "晨起姜枣茶", "上午晒背15分钟"],
        "emotional_care": ["需要温暖的人际互动", "常与人共餐", "避免独居独食"],
        "sleep_advice": "睡前热敷腹部20分钟",
    },
    "寒湿困脾证": {
        "acupoints": ["阴陵泉", "足三里", "脾俞", "水分", "中脘", "丰隆"],
        "moxibustion": ["中脘", "足三里", "阴陵泉", "水分"],
        "massage": ["按揉阴陵泉3分钟", "推丰隆穴", "掌擦脾俞"],
        "daily_care": ["忌油腻/甜食/乳制品", "忌生冷冰镇", "适当辛辣化湿", "梅雨季除湿"],
        "emotional_care": ["不要强迫做高强度脑力工作", "午后站立办公", "保持居住环境干燥"],
        "sleep_advice": "睡前艾草+生姜煮水泡脚",
    },
    "肺气虚证": {
        "acupoints": ["肺俞", "太渊", "足三里", "气海", "膏肓", "膻中"],
        "moxibustion": ["足三里", "气海", "肺俞", "膏肓"],
        "massage": ["叩击肺俞穴", "按揉太渊穴", "搓热手掌捂前胸"],
        "daily_care": ["避风寒，秋冬季戴口罩", "练习腹式呼吸", "多吃白色食物"],
        "emotional_care": ["多听欢快音乐", "唱唱歌锻炼肺气", "避免独处悲伤"],
        "sleep_advice": "睡前腹式呼吸10分钟",
    },
    "肺阴虚证": {
        "acupoints": ["肺俞", "太渊", "尺泽", "孔最", "三阴交", "太溪"],
        "moxibustion": ["不宜艾灸"],
        "massage": ["推尺泽穴", "按揉太渊穴", "搓涌泉穴"],
        "daily_care": ["保持室内湿度", "忌辛辣煎炸烟酒", "多食润肺食材"],
        "emotional_care": ["保持心情平和", "避免长时间说话", "练习轻柔瑜伽"],
        "sleep_advice": "睡前冰糖炖雪梨",
    },
    "风寒束肺证": {
        "acupoints": ["列缺", "风门", "肺俞", "大椎", "合谷", "迎香"],
        "moxibustion": ["大椎（温灸）", "风门", "肺俞"],
        "massage": ["按揉合谷穴", "搓大椎穴至发热", "推鼻翼两侧"],
        "daily_care": ["多饮温热生姜红糖水", "发汗后避风", "忌生冷水果", "热水泡脚至微汗"],
        "emotional_care": ["外感期间让身体休息", "保持心情舒畅"],
        "sleep_advice": "睡前生姜红糖水热饮，盖被取微汗",
    },
    "肾阴虚证": {
        "acupoints": ["太溪", "涌泉", "肾俞", "三阴交", "关元", "复溜"],
        "moxibustion": ["不宜艾灸"],
        "massage": ["搓涌泉穴至发热", "按揉太溪穴3分钟", "擦肾俞至温热"],
        "daily_care": ["忌熬夜", "避免过度出汗运动", "忌辛辣油炸"],
        "emotional_care": ["减少恐惧类娱乐", "建立安全感", "冥想温暖泉水"],
        "sleep_advice": "睡前温水泡脚按揉涌泉",
    },
    "肾阳虚证": {
        "acupoints": ["肾俞", "命门", "关元", "气海", "足三里", "太溪"],
        "moxibustion": ["命门", "关元", "肾俞", "足三里（温灸20-30分钟）"],
        "massage": ["掌擦命门+肾俞", "按揉关元穴", "双手搓后腰"],
        "daily_care": ["全年保暖尤其腰足", "上午晒太阳晒后腰", "节制房事"],
        "emotional_care": ["需要稳定的人际支持", "参与群体活动", "避免长期孤独"],
        "sleep_advice": "睡前艾草花椒泡脚至微汗",
    },
    "肾精不足证": {
        "acupoints": ["肾俞", "命门", "关元", "太溪", "涌泉", "绝骨"],
        "moxibustion": ["命门", "关元", "肾俞", "涌泉（温灸）"],
        "massage": ["搓涌泉穴5分钟", "擦肾俞至发热", "叩齿36次/日"],
        "daily_care": ["保证充足睡眠", "脑力工作每1小时起身", "减少熬夜和过度用脑"],
        "emotional_care": ["记忆力下降不必焦虑", "使用备忘录辅助记忆", "练习八段锦"],
        "sleep_advice": "睡前不思考工作问题",
    },
}


def get_treatment_plan(syndrome_name: str) -> Dict:
    """获取证型的完整治疗方案"""
    return TREATMENT_KNOWLEDGE.get(syndrome_name, {})


# ═══════════════════════════════════════════
# 第四部分：四诊合参 + 经典方剂
# ═══════════════════════════════════════════

FOUR_DIAG_KNOWLEDGE = {
    "心气虚证": {"tongue": {"body": "舌淡", "coat": "苔白"}, "pulse": "脉虚弱/脉沉弱",
        "classic_formulas": [
            {"name": "养心汤", "source": "《证治准绳》", "ingredients": "黄芪·人参·茯苓·茯神·当归·川芎·五味子·柏子仁·酸枣仁·远志·半夏·肉桂·甘草"},
            {"name": "四君子汤加减", "source": "《太平惠民和剂局方》", "ingredients": "人参·白术·茯苓·甘草"},
        ]},
    "心血虚证": {"tongue": {"body": "舌淡", "coat": "苔薄白"}, "pulse": "脉细弱",
        "classic_formulas": [
            {"name": "四物汤", "source": "《太平惠民和剂局方》", "ingredients": "当归·熟地黄·白芍·川芎"},
            {"name": "归脾汤", "source": "《济生方》", "ingredients": "白术·人参·黄芪·当归·茯神·远志·酸枣仁·龙眼肉·木香·甘草"},
        ]},
    "心阴虚证": {"tongue": {"body": "舌红", "coat": "少苔或无苔"}, "pulse": "脉细数",
        "classic_formulas": [
            {"name": "天王补心丹", "source": "《校注妇人良方》", "ingredients": "生地黄·人参·玄参·天冬·麦冬·丹参·当归·柏子仁·酸枣仁·五味子"},
            {"name": "黄连阿胶汤", "source": "《伤寒论》", "ingredients": "黄连·黄芩·芍药·阿胶·鸡子黄"},
        ]},
    "心阳虚证": {"tongue": {"body": "舌淡胖", "coat": "苔白滑"}, "pulse": "脉沉迟/脉微细",
        "classic_formulas": [
            {"name": "保元汤", "source": "《博爱心鉴》", "ingredients": "黄芪·人参·肉桂·甘草"},
            {"name": "桂枝甘草汤", "source": "《伤寒论》", "ingredients": "桂枝·甘草"},
        ]},
    "心火亢盛证": {"tongue": {"body": "舌尖红", "coat": "苔黄"}, "pulse": "脉数/脉滑数",
        "classic_formulas": [
            {"name": "导赤散", "source": "《小儿药证直诀》", "ingredients": "生地黄·木通·竹叶·甘草梢"},
            {"name": "泻心汤", "source": "《金匮要略》", "ingredients": "大黄·黄连·黄芩"},
        ]},
    "肝气郁结证": {"tongue": {"body": "舌淡红", "coat": "苔薄白"}, "pulse": "脉弦",
        "classic_formulas": [
            {"name": "逍遥散", "source": "《太平惠民和剂局方》", "ingredients": "柴胡·当归·白芍·白术·茯苓·甘草·薄荷·煨姜"},
            {"name": "柴胡疏肝散", "source": "《景岳全书》", "ingredients": "柴胡·陈皮·川芎·香附·枳壳·芍药·甘草"},
        ]},
    "肝火上炎证": {"tongue": {"body": "舌红", "coat": "苔黄燥"}, "pulse": "脉弦数",
        "classic_formulas": [
            {"name": "龙胆泻肝汤", "source": "《医方集解》", "ingredients": "龙胆草·黄芩·栀子·泽泻·木通·车前子·当归·生地黄·柴胡·甘草"},
        ]},
    "肝血虚证": {"tongue": {"body": "舌淡", "coat": "苔薄白"}, "pulse": "脉细/脉弦细",
        "classic_formulas": [
            {"name": "补肝汤", "source": "《医宗金鉴》", "ingredients": "当归·白芍·川芎·熟地黄·酸枣仁·木瓜·麦冬·甘草"},
        ]},
    "肝阳上亢证": {"tongue": {"body": "舌红", "coat": "苔黄"}, "pulse": "脉弦有力",
        "classic_formulas": [
            {"name": "天麻钩藤饮", "source": "《中医内科杂病证治新义》", "ingredients": "天麻·钩藤·石决明·栀子·黄芩·川牛膝·杜仲·益母草·桑寄生·夜交藤"},
            {"name": "镇肝熄风汤", "source": "《医学衷中参西录》", "ingredients": "怀牛膝·生赭石·生龙骨·生牡蛎·生龟板·生白芍·玄参·天冬"},
        ]},
    "脾气虚证": {"tongue": {"body": "舌淡", "coat": "苔白"}, "pulse": "脉缓弱",
        "classic_formulas": [
            {"name": "四君子汤", "source": "《太平惠民和剂局方》", "ingredients": "人参·白术·茯苓·甘草"},
            {"name": "参苓白术散", "source": "《太平惠民和剂局方》", "ingredients": "莲子肉·薏苡仁·砂仁·桔梗·白扁豆·茯苓·人参·白术·山药·甘草"},
        ]},
    "脾阳虚证": {"tongue": {"body": "舌淡胖", "coat": "苔白滑"}, "pulse": "脉沉迟",
        "classic_formulas": [
            {"name": "理中汤", "source": "《伤寒论》", "ingredients": "人参·干姜·白术·甘草"},
            {"name": "附子理中汤", "source": "《太平惠民和剂局方》", "ingredients": "附子·人参·干姜·白术·甘草"},
        ]},
    "寒湿困脾证": {"tongue": {"body": "舌淡胖", "coat": "苔白腻"}, "pulse": "脉濡缓",
        "classic_formulas": [
            {"name": "藿香正气散", "source": "《太平惠民和剂局方》", "ingredients": "藿香·紫苏·白芷·桔梗·陈皮·厚朴·白术·茯苓·甘草"},
            {"name": "平胃散", "source": "《太平惠民和剂局方》", "ingredients": "苍术·厚朴·陈皮·甘草"},
        ]},
    "肺气虚证": {"tongue": {"body": "舌淡", "coat": "苔白"}, "pulse": "脉虚弱",
        "classic_formulas": [
            {"name": "补肺汤", "source": "《永类钤方》", "ingredients": "人参·黄芪·熟地·五味子·紫菀·桑白皮"},
            {"name": "玉屏风散", "source": "《医方类聚》", "ingredients": "防风·黄芪·白术"},
        ]},
    "肺阴虚证": {"tongue": {"body": "舌红", "coat": "少苔"}, "pulse": "脉细数",
        "classic_formulas": [
            {"name": "沙参麦冬汤", "source": "《温病条辨》", "ingredients": "沙参·麦冬·玉竹·天花粉·生扁豆·桑叶·甘草"},
        ]},
    "风寒束肺证": {"tongue": {"body": "舌淡红", "coat": "苔薄白"}, "pulse": "脉浮紧",
        "classic_formulas": [
            {"name": "三拗汤", "source": "《太平惠民和剂局方》", "ingredients": "麻黄·杏仁·甘草"},
        ]},
    "肾阴虚证": {"tongue": {"body": "舌红", "coat": "少苔或无苔"}, "pulse": "脉细数",
        "classic_formulas": [
            {"name": "六味地黄丸", "source": "《小儿药证直诀》", "ingredients": "熟地黄·山茱萸·山药·泽泻·牡丹皮·茯苓"},
            {"name": "左归丸", "source": "《景岳全书》", "ingredients": "熟地·山药·枸杞·山茱萸·川牛膝·菟丝子·鹿胶·龟胶"},
        ]},
    "肾阳虚证": {"tongue": {"body": "舌淡胖", "coat": "苔白"}, "pulse": "脉沉迟",
        "classic_formulas": [
            {"name": "金匮肾气丸", "source": "《金匮要略》", "ingredients": "干地黄·山药·山茱萸·泽泻·茯苓·牡丹皮·桂枝·附子"},
            {"name": "右归丸", "source": "《景岳全书》", "ingredients": "熟地·山药·枸杞·山茱萸·鹿角胶·杜仲·肉桂·当归·制附子"},
        ]},
    "肾精不足证": {"tongue": {"body": "舌淡", "coat": "苔白"}, "pulse": "脉沉细",
        "classic_formulas": [
            {"name": "河车大造丸", "source": "《诸证辨疑》", "ingredients": "紫河车·龟板·熟地·杜仲·天冬·麦冬·牛膝·黄柏"},
        ]},
}


def get_four_diag(syndrome_name: str) -> Dict:
    """获取证型的四诊合参信息"""
    return FOUR_DIAG_KNOWLEDGE.get(syndrome_name, {})


def apply_four_diag_bonus(scores: List[Dict], tongue_input: str, pulse_input: str) -> List[Dict]:
    """舌象/脉象加权"""
    if not tongue_input and not pulse_input:
        return scores
    for s in scores:
        bonus = 0.0
        diag = FOUR_DIAG_KNOWLEDGE.get(s["syndrome"], {})
        if tongue_input and diag.get("tongue"):
            t = diag["tongue"]
            if t.get("body") and t["body"] in tongue_input:
                bonus += 0.15
            if t.get("coat") and t["coat"] in tongue_input:
                bonus += 0.1
        if pulse_input and diag.get("pulse"):
            if pulse_input in diag["pulse"] or diag["pulse"] in pulse_input:
                bonus += 0.15
            pulse_names = re.findall(r'[^\s/]+', pulse_input)
            for pn in pulse_names:
                if pn in diag["pulse"]:
                    bonus += 0.1
        s["score"] = round(min(s["score"] + bonus, 1.0), 3)
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores
# ═══════════════════════════════════════════
# 第五部分：风险预警 + 西医建议
# ═══════════════════════════════════════════

HIGH_RISK_PATTERNS = [
    {
        "id": "cardiac_emergency",
        "label": "🚨 高危: 心血管急症风险",
        "keywords": ["胸痛", "胸闷", "压榨感", "心前区", "左肩放射", "背痛", "冷汗", "濒死感"],
        "require_count": 2,
        "require_pairs": [[["胸痛", "胸闷", "心前区"], ["冷汗", "气短", "恶心", "左肩", "背痛"]]],
        "advice": "您描述的症状提示可能存在急性心血管事件风险（心绞痛/心肌梗死）。\n🚑 请立即停止活动，拨打120或由他人陪同前往急诊科就医！\n⚠ 不要自行驾车。如有硝酸甘油可舌下含服一片。",
        "department": "急诊科 / 心血管内科",
        "urgency": "emergency",
    },
    {
        "id": "stroke_risk",
        "label": "🚨 高危: 脑血管意外风险（中风）",
        "keywords": ["突发头痛", "剧烈头痛", "偏瘫", "口眼歪斜", "言语不清", "面部麻木", "肢体无力", "视物模糊", "平衡障碍"],
        "require_count": 2,
        "advice": "您描述的症状与脑血管意外（中风/脑卒中）的前兆高度吻合。\n🚑 请立即前往最近医院急诊科！切勿等待症状自行缓解！\n🔍 快速自测（FAST）: Face面瘫→Arm臂力→Speech语言→Time时间",
        "department": "急诊科 / 神经内科",
        "urgency": "emergency",
    },
    {
        "id": "hypertensive_crisis",
        "label": "🚨 高危: 高血压危象风险",
        "keywords": ["剧烈头痛", "眩晕", "视物模糊", "恶心呕吐", "面红", "耳鸣", "鼻出血"],
        "require_count": 2,
        "require_risk_factors": {"age_range": [40, 120], "has_history": ["高血压", "高血压病史", "高血脂", "冠心病"]},
        "advice": "您描述的症状结合年龄/病史，提示高血压危象可能。\n⚠ 请立即休息，安静状态下15分钟后复测血压。\n🏥 如血压持续>180/110mmHg或症状加重，请立即就医。",
        "department": "急诊科 / 心血管内科",
        "urgency": "emergency",
    },
    {
        "id": "gi_bleeding",
        "label": "🚨 高危: 消化道出血风险",
        "keywords": ["黑便", "呕血", "便血", "柏油样", "咖啡色呕吐", "血便", "暗红色", "面色苍白"],
        "require_count": 2,
        "advice": "您描述的症状提示可能存在消化道出血。\n🚑 请立即空腹前往消化内科或急诊科就诊！\n⚠ 就诊前禁食禁水，不要自行服用止血药。",
        "department": "消化内科 / 急诊科",
        "urgency": "emergency",
    },
    {
        "id": "meningitis",
        "label": "🚨 高危: 颅内感染风险",
        "keywords": ["剧烈头痛", "发热", "颈项强直", "恶心呕吐", "畏光", "意识模糊", "抽搐"],
        "require_count": 3,
        "advice": "您描述的症状（头痛+发热+颈项强直）高度提示中枢神经系统感染可能。\n🚑 请立即前往急诊科就诊！",
        "department": "急诊科 / 神经内科",
        "urgency": "emergency",
    },
    {
        "id": "pulmonary_embolism",
        "label": "🚨 高危: 肺栓塞风险",
        "keywords": ["突发胸痛", "呼吸困难", "咯血", "晕厥", "单侧腿肿", "下肢疼痛"],
        "require_count": 2,
        "require_risk_factors": {"age_range": [40, 120], "has_history": ["静脉曲张", "血栓", "手术后", "长期卧床", "肿瘤", "癌症"]},
        "advice": "您描述的症状（突发胸痛+呼吸困难）结合病史提示肺栓塞可能。\n🚑 这是急症！请立即拨打120或前往急诊科！",
        "department": "急诊科 / 呼吸内科",
        "urgency": "emergency",
    },
    {
        "id": "heart_failure",
        "label": "⚠️ 中高危: 心力衰竭风险",
        "keywords": ["呼吸困难", "夜间憋醒", "端坐呼吸", "下肢水肿", "乏力", "气短", "泡沫痰"],
        "require_count": 2,
        "require_risk_factors": {"age_range": [50, 120], "has_history": ["心脏病", "冠心病", "高血压", "心衰", "心脏"]},
        "advice": "您描述的症状（呼吸困难+下肢水肿+乏力）结合年龄/病史，提示心力衰竭可能。\n⚠ 请尽快到心内科就诊，避免剧烈活动和情绪激动。\n🌙 如夜间突发呼吸困难无法平卧，请立即拨打120。",
        "department": "心血管内科",
        "urgency": "urgent",
    },
    {
        "id": "diabetes_ketoacidosis",
        "label": "⚠️ 中高危: 糖尿病酮症酸中毒风险",
        "keywords": ["多饮", "多尿", "体重下降", "乏力", "恶心呕吐", "腹痛", "呼气有烂苹果味"],
        "require_count": 3,
        "require_risk_factors": {"has_history": ["糖尿病", "糖尿病史", "血糖"]},
        "advice": "您描述的症状结合糖尿病病史，提示糖尿病酮症酸中毒可能。\n⚠ 请立即检测血糖和尿酮体！\n🚑 如血糖>16.7mmol/L且尿酮阳性，请立即前往急诊科。",
        "department": "内分泌科 / 急诊科",
        "urgency": "urgent",
    },
    {
        "id": "thyroid_storm",
        "label": "⚠️ 中高危: 甲亢危象风险",
        "keywords": ["心慌", "手抖", "消瘦", "多汗", "烦躁", "失眠", "突眼", "腹泻", "发热"],
        "require_count": 3,
        "require_risk_factors": {"has_history": ["甲亢", "甲状腺功能亢进", "甲状腺"]},
        "advice": "您描述的症状结合甲亢病史，提示甲亢危象可能。\n⚠ 请立即到内分泌科就诊！避免精神刺激和剧烈运动。",
        "department": "内分泌科 / 急诊科",
        "urgency": "urgent",
    },
    {
        "id": "icterus_liver",
        "label": "⚠️ 中高危: 肝胆系统异常风险",
        "keywords": ["面色发黄", "眼白发黄", "黄疸", "尿黄", "乏力", "恶心", "厌油", "右上腹痛"],
        "require_count": 2,
        "advice": "您描述的黄疸相关症状提示肝胆系统可能存在问题。\n🏥 请尽快到消化内科或肝病科就诊，做肝功能+腹部B超检查。\n⚠ 如伴随剧烈腹痛或高热，请直接去急诊科。",
        "department": "消化内科 / 肝病科",
        "urgency": "urgent",
    },
    {
        "id": "hemoptysis",
        "label": "⚠️ 中高危: 咯血风险",
        "keywords": ["咳血", "咯血", "痰中带血", "血丝痰", "铁锈色痰"],
        "require_count": 1,
        "advice": "咯血（痰中带血）是呼吸系统的重要警示信号。\n🏥 请尽快到呼吸内科就诊，做胸部CT检查。咯血量多时直接去急诊科。",
        "department": "呼吸内科 / 急诊科",
        "urgency": "urgent",
    },
    {
        "id": "hematochezia_urine",
        "label": "⚠️ 中高危: 血尿风险",
        "keywords": ["血尿", "尿血", "肉眼血尿", "尿中带血", "小便红色"],
        "require_count": 1,
        "advice": "肉眼血尿提示泌尿系统可能存在器质性病变。\n🏥 请尽快到泌尿外科或肾内科就诊，做尿常规+泌尿系统B超。",
        "department": "泌尿外科 / 肾内科",
        "urgency": "urgent",
    },
    {
        "id": "renal_failure",
        "label": "💡 注意: 肾功能损害风险",
        "keywords": ["浮肿", "水肿", "泡沫尿", "少尿", "乏力", "恶心", "瘙痒"],
        "require_count": 2,
        "require_risk_factors": {"has_history": ["肾炎", "肾病史", "糖尿病", "高血压", "痛风", "尿酸"]},
        "advice": "您描述的症状（浮肿+泡沫尿+乏力）结合病史，建议尽快到肾内科做尿常规+肾功能检查。\n📋 早期发现对预后至关重要。",
        "department": "肾内科",
        "urgency": "non_urgent",
    },
    {
        "id": "anemia_severe",
        "label": "💡 注意: 严重贫血风险",
        "keywords": ["面色苍白", "头晕", "乏力", "心悸", "气短", "指甲苍白", "口唇淡白"],
        "require_count": 3,
        "require_risk_factors": {"sex": "女", "age_range": [15, 50], "has_history": ["月经量大", "月经过多", "贫血", "缺铁"]},
        "advice": "您描述的症状（面色苍白+头晕+心悸）提示可能存在中重度贫血。\n🩸 请到血液内科做血常规检查，明确贫血类型和原因。",
        "department": "血液内科",
        "urgency": "non_urgent",
    },
    {
        "id": "bmi_obesity_highrisk",
        "label": "💡 注意: 重度肥胖相关代谢风险",
        "keywords": [],
        "use_bmi": True,
        "bmi_threshold": 32,
        "advice": "您的BMI已进入重度肥胖范围，相关代谢风险显著升高。\n🏥 建议到内分泌科或减重门诊做全面代谢评估。",
        "department": "内分泌科 / 减重门诊",
        "urgency": "non_urgent",
    },
    {
        "id": "bmi_underweight",
        "label": "💡 注意: 体重过轻",
        "keywords": [],
        "use_bmi": True,
        "bmi_threshold_under": 18.5,
        "advice": "您的BMI低于正常范围（<18.5），可能提示：\n• 营养摄入不足或吸收障碍\n• 甲状腺功能亢进\n• 慢性消耗性疾病\n🏥 建议到营养科或消化内科排查原因。",
        "department": "营养科 / 消化内科",
        "urgency": "non_urgent",
    },
    {
        "id": "smoking_lung_risk",
        "label": "💡 注意: 长期吸烟相关风险（肺癌/COPD）",
        "keywords": ["咳嗽", "咳血", "气短", "胸痛", "痰多", "声音嘶哑"],
        "require_count": 1,
        "require_risk_factors": {"age_range": [40, 120], "has_history": ["吸烟"]},
        "advice": "您有长期吸烟史，叠加呼吸系统症状，建议：\n• 做低剂量螺旋CT筛查肺部病变（高危人群每年一次）\n• 做肺功能检查排除COPD\n• 戒烟并定期随访\n🏥 就诊呼吸内科。",
        "department": "呼吸内科",
        "urgency": "non_urgent",
    },
    {
        "id": "alcohol_liver_risk",
        "label": "💡 注意: 长期饮酒相关风险（肝损伤）",
        "keywords": ["乏力", "恶心", "厌油", "面色发黄", "眼白发黄", "右上腹痛", "腹胀"],
        "require_count": 2,
        "require_risk_factors": {"age_range": [30, 120], "has_history": ["饮酒"]},
        "advice": "您有长期饮酒史，叠加消化/肝区症状，建议：\n• 做肝功能+腹部B超排除酒精性肝病\n• 检测乙肝五项（饮酒+乙肝=肝癌高发组合）\n• 戒酒或严格限酒\n🏥 就诊消化内科/肝病科。",
        "department": "消化内科 / 肝病科",
        "urgency": "non_urgent",
    },
    {
        "id": "sex_excess_kidney",
        "label": "💡 注意: 房事过度相关肾虚风险",
        "keywords": ["腰膝酸软", "乏力", "耳鸣", "头晕", "盗汗", "畏寒", "夜尿多", "健忘", "阳痿", "早泄"],
        "require_count": 2,
        "require_risk_factors": {"has_history": ["纵欲"]},
        "advice": "您的生活节律（房事偏频繁）与症状（腰膝酸软+乏力）结合，提示可能存在肾精耗损。\n建议：\n• 节制房事，给身体恢复时间\n• 保证充足睡眠（肾精化生于睡眠）\n• 多食补肾食物（核桃/黑芝麻/桑椹/山药）\n• 如症状持续或加重，就诊中医科调理\n🏥 中医科 / 男科。",
        "department": "中医科 / 男科",
        "urgency": "non_urgent",
    },
    {
        "id": "unexplained_weight_loss",
        "label": "💡 注意: 不明原因体重下降",
        "keywords": ["消瘦", "体重下降", "瘦了很多", "暴瘦"],
        "require_count": 1,
        "require_risk_factors": {"age_range": [45, 120]},
        "advice": "中老年不明原因体重下降（6-12个月内下降>5%）需要引起重视。\n🏥 建议到内科进行全面体检，排查器质性病因。",
        "department": "内科 / 体检中心",
        "urgency": "non_urgent",
    },
]

WESTERN_MEDICINE_ADVICE = {
    "失眠": ["建议改善睡眠卫生（固定作息、避免睡前蓝光）", "如持续>2周，可就诊神经内科/睡眠门诊", "短期使用褪黑素（1-3mg）辅助", "排除焦虑/抑郁等心理因素"],
    "头痛": ["区分紧张型头痛/偏头痛/丛集性头痛", "建议记录头痛日记（时间/部位/性质/诱因）", "频繁发作者可就诊神经内科", "避免长期自行服用止痛药（药物过量头痛）"],
    "心悸": ["建议做24小时动态心电图检查", "排除心律失常（房颤/早搏/室上速）", "查甲状腺功能排除甲亢", "避免咖啡/浓茶/酒精等诱发因素"],
    "胸闷": ["建议做心电图+心脏超声初步筛查", "如与活动相关需做运动平板或冠脉CTA", "排除焦虑性胸痛（心脏神经症）", "⚠ 突发剧烈胸痛请立即去急诊"],
    "头晕": ["区分眩晕（前庭性）和头昏（非前庭性）", "测血压排除高血压/低血压", "查颈椎排除颈源性眩晕", "如旋转感明显可就诊耳鼻喉科（耳石症）"],
    "高血压": ["非同日三次测量≥140/90mmHg可诊断", "建议购买上臂式电子血压计家庭监测", "低盐饮食（每日<5g盐）", "规律复查，按医嘱服药，不可自行停药"],
    "便秘": ["增加膳食纤维（25-35g/日）和水分", "乳果糖/聚乙二醇为安全通便药", "避免长期使用刺激性泻药（番泻叶/大黄）", "如>3个月无缓解，就诊消化内科"],
    "腹泻": ["急性腹泻<2周:注意补液+口服补液盐", "慢性腹泻>4周:需做肠镜检查", "注意排除乳糖不耐受/肠易激综合征", "⚠ 伴发热/血便/剧烈腹痛请就医"],
    "腹痛": ["按部位判断:右上腹(胆)/中上腹(胃)/右下腹(阑尾)/左下腹(结肠)", "⚠ 剧烈腹痛+腹肌紧张=急腹症需立即就医", "慢性腹痛可做腹部B超排查", "避免自行服用止痛药掩盖病情"],
    "消化不良": ["少食多餐，避免高脂/辛辣食物", "可试用质子泵抑制剂（奥美拉唑）短期治疗", "根除幽门螺杆菌（查C13/C14呼气试验）", "如伴体重下降/黑便/吞咽困难，需做胃镜"],
    "月经不调": ["建议做性激素六项+甲状腺功能+妇科B超", "记录月经周期2-3个月经周期", "排除多囊卵巢综合征/高泌乳素血症", "就诊妇科或生殖内分泌科"],
    "腰痛": ["急性腰痛:48h内冷敷→后热敷，避免弯腰负重", "慢性>3个月:需做腰椎影像学检查", "排除肾结石（腰痛+血尿）和妇科疾病", "适当核心肌群训练预防复发"],
    "关节痛": ["区分炎性（类风湿）和退行性（骨关节炎）", "查血沉/CRP/类风湿因子/RF", "骨关节炎：减重+护膝+氨基葡萄糖", "⚠ 单关节红肿热痛需排除痛风/感染"],
    "咳嗽": ["急性咳嗽<3周:多为感染后咳嗽，对症治疗", "亚急性咳嗽3-8周:排查百日咳/鼻后滴漏", "慢性咳嗽>8周:需做胸片+肺功能", "咳嗽变异性哮喘是慢性咳嗽常见原因"],
    "发热": ["低热<38.5°C:多喝水、物理降温", "高热≥38.5°C:可用退热药（布洛芬/对乙酰氨基酚）", "发热>3天:需查血常规+CRP+病原学检查", "⚠ 伴意识模糊/呼吸困难/皮疹=重症，立即就医"],
    "皮肤问题": ["皮疹:记录部位/形态/诱因（药物/食物/接触物）", "湿疹:保湿为先，外用激素药膏有效", "荨麻疹:抗组胺药（氯雷他定/西替利嗪）", "⚠ 皮疹+呼吸困难=过敏急症，立即就医"],
    "情绪问题": ["焦虑/抑郁是常见心理障碍，可治疗", "PHQ-9/GAD-7自评量表可初步筛查", "心理治疗+药物治疗联合效果最佳", "就诊精神科或心理科，不要独自硬扛"],
    "贫血": ["查血常规+铁蛋白+维生素B12+叶酸", "缺铁性贫血最常见:补铁+寻找失血原因", "平均红细胞体积(MCV)有助于分型", "⚠ 不明原因贫血需排查消化道肿瘤"],
    "甲状腺": ["查甲状腺功能（TSH/FT3/FT4）+甲状腺B超", "甲亢:抗甲状腺药物/碘131/手术", "甲减:优甲乐替代治疗", "甲状腺结节>1cm建议细针穿刺"],
    "糖尿病": ["空腹血糖≥7.0mmol/L或餐后2h≥11.1mmol/L可诊断", "糖化血红蛋白(HbA1c)反映3个月平均血糖", "饮食控制+规律运动+药物（二甲双胍一线）", "每年检查眼底+肾功能+足部"],
    "高血脂": ["查血脂四项（TC/TG/HDL/LDL）", "LDL-C是主要干预目标", "他汀类药物是一线降脂药", "饮食控制:少饱和脂肪+多不饱和脂肪酸"],
    "痛风": ["急性期:秋水仙碱/NSAIDs/糖皮质激素", "间歇期:降尿酸治疗（别嘌醇/非布司他）", "急性期禁用降尿酸药（会加重疼痛）", "饮食:低嘌呤+多饮水（>2000ml/日）"],
    "骨质疏松": ["双能X线吸收法（DXA）是金标准", "T值≤-2.5诊断骨质疏松", "补充钙（1000mg/日）+维生素D（800IU/日）", "抗骨松药物包括双膦酸盐/地舒单抗等"],
    "视力下降": ["突然视力下降=眼科急症，立即就医", "渐进性下降:查屈光+眼底+眼压", "飞蚊症突然增多需查眼底排除视网膜脱离", "糖尿病/高血压患者每年查眼底"],
    "耳鸣": ["区分搏动性（血管性）和非搏动性", "突聋伴耳鸣=耳鼻喉科急症", "避免噪声暴露，减少耳机使用", "耳鸣认知行为疗法有效"],
    "颈椎": ["颈痛+上肢麻木=神经根型颈椎病", "颈痛+头晕=椎动脉型颈椎病", "MRI是诊断金标准", "避免长时间低头，做颈部操"],
    "高血压病史": ["规律监测血压，推荐家庭自测", "低盐低脂饮食，控制体重", "按医嘱服药，不可自行停药", "每3-6个月复查血脂/血糖/肾功能"],
    "糖尿病史": ["定期监测空腹和餐后血糖", "控制糖化血红蛋白<7%", "每年检查眼底/尿微量白蛋白/足部", "饮食+运动+药物三驾马车"],
    "心脏病史": ["定期心内科随访，不可自行停药", "避免剧烈运动和情绪激动", "随身携带急救药物（硝酸甘油）", "低盐低脂饮食，控制体重"],
    "胃病史": ["根除幽门螺杆菌（如阳性）", "避免NSAIDs类药物损伤胃黏膜", "少食多餐，忌辛辣刺激性食物", "定期复查胃镜"],
}


def assess_risk(symptoms: List[str], bio: dict = None) -> List[Dict]:
    """根据症状+生物信息评估高危风险"""
    if bio is None:
        bio = {}

    age = bio.get("age", 0)
    sex = bio.get("sex", "")
    weight = bio.get("weight", 0)
    height = bio.get("height", 0)
    medical_history = bio.get("medical_history", "").lower()
    family_history = bio.get("family_history", "").lower()
    smoking = bio.get("smoking", "")
    smoking_years = bio.get("smoking_years", 0) or 0
    alcohol = bio.get("alcohol", "")
    alcohol_years = bio.get("alcohol_years", 0) or 0
    sex_life = bio.get("sex_life", "")

    bmi = 0
    if weight > 0 and height > 0:
        bmi = round(weight / ((height / 100) ** 2), 1)

    full_history = " ".join([medical_history, family_history])
    is_heavy_smoker = any(k in smoking for k in [">", "每日"]) and smoking_years >= 5
    is_very_heavy_smoker = any(k in smoking for k in [">", "每日10-20支", "每日>20支"]) and smoking_years >= 20
    is_heavy_drinker = any(k in alcohol for k in ["每周>3次", "每日饮", "每日"]) and alcohol_years >= 5
    is_very_heavy_drinker = any(k in alcohol for k in ["每日饮", "每日"]) and alcohol_years >= 15
    is_sex_excess = any(k in sex_life for k in ["频繁", "过度"])

    # 柔性匹配函数
    def symptom_contains(kw: str) -> bool:
        if kw in symptom_text:
            return True
        words = [w for w in re.findall(r'[\u4e00-\u9fff]{2,}', kw) if len(w) >= 2]
        if len(words) > 1:
            for w in words:
                if w in symptom_text:
                    return True
        for sym in symptoms:
            if sym in kw:
                return True
        return False

    hits = []
    symptom_text = " ".join(symptoms).lower()

    for pattern in HIGH_RISK_PATTERNS:
        if pattern.get("use_bmi"):
            if bmi > 0:
                th = pattern.get("bmi_threshold", 0)
                th_u = pattern.get("bmi_threshold_under", 0)
                if th and bmi >= th:
                    hits.append(pattern)
                elif th_u and bmi <= th_u:
                    hits.append(pattern)
            continue

        keywords = pattern.get("keywords", [])
        req = pattern.get("require_count", 2)
        matched_kws = [kw for kw in keywords if symptom_contains(kw)]
        if len(matched_kws) < req:
            continue

        pairs = pattern.get("require_pairs", [])
        if pairs:
            pair_matched = False
            for group_a, group_b in pairs:
                has_a = any(symptom_contains(k) for k in group_a)
                has_b = any(symptom_contains(k) for k in group_b)
                if has_a and has_b:
                    pair_matched = True
                    break
            if not pair_matched:
                continue

        rf = pattern.get("require_risk_factors", {})
        if rf:
            age_range = rf.get("age_range", [])
            if age_range and (age < age_range[0] or age > age_range[1]):
                continue
            rf_sex = rf.get("sex", "")
            if rf_sex and sex != rf_sex:
                continue
            has_history = rf.get("has_history", [])
            if has_history:
                hm = any(h in full_history for h in has_history)
                if not hm:
                    if "吸烟" in has_history and is_heavy_smoker:
                        hm = True
                    elif "饮酒" in has_history and is_heavy_drinker:
                        hm = True
                    elif "纵欲" in has_history and is_sex_excess:
                        hm = True
                if not hm:
                    continue

        hits.append(pattern)

    urgency_order = {"emergency": 0, "urgent": 1, "non_urgent": 2}
    hits.sort(key=lambda x: urgency_order.get(x.get("urgency", "non_urgent"), 3))
    return hits


def get_western_advice(symptoms: List[str]) -> List[Dict]:
    """基于症状提供西医参考建议"""
    matched = []
    seen = set()
    for symptom in symptoms:
        if symptom in WESTERN_MEDICINE_ADVICE and symptom not in seen:
            seen.add(symptom)
            matched.append({"symptom": symptom, "advice": WESTERN_MEDICINE_ADVICE[symptom]})
            continue
        for key, advice_list in WESTERN_MEDICINE_ADVICE.items():
            if key not in seen and (key in symptom or symptom in key):
                seen.add(key)
                matched.append({"symptom": key, "advice": advice_list})
    return matched
