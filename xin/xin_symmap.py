#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
道归 · SymMap 中西医结合数据查询模块 v1
整合 SymMap 7大实体数据集 → 与 TCM-MKG 交叉关联
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict

CACHE_DIR = Path(__file__).parent / "data" / "symmap_cache"

# ── 加载的缓存数据 ──
_herbs: Dict[str, dict] = {}          # Herb_id → 完整记录
_herbs_by_name: Dict[str, list] = {}  # 中文名 → [记录]
_diseases: Dict[str, dict] = {}       # Disease_id → 完整记录
_diseases_by_name: Dict[str, list] = {}
_tcm_symptoms: Dict[str, dict] = {}   # TCM_symptom_id → 记录
_tcm_symptoms_by_name: Dict[str, list] = {}
_mm_symptoms: Dict[str, dict] = {}    # MM_symptom_id → 记录
_mm_symptoms_by_name: Dict[str, list] = {}
_syndromes: Dict[str, dict] = {}      # Syndrome_id → 记录
_syndromes_by_name: Dict[str, list] = {}
_compounds: Dict[str, dict] = {}      # Mol_id → 记录
_compounds_by_name: Dict[str, list] = {}
_targets: Dict[str, dict] = {}        # Gene_id → 记录
_targets_by_symbol: Dict[str, list] = {}
_loaded = False


def _load_all():
    global _loaded, _herbs, _herbs_by_name, _diseases, _diseases_by_name
    global _tcm_symptoms, _tcm_symptoms_by_name
    global _mm_symptoms, _mm_symptoms_by_name
    global _syndromes, _syndromes_by_name, _compounds, _compounds_by_name
    global _targets, _targets_by_symbol
    if _loaded:
        return

    # ── 中药 SMHB ──
    for fn in ['SMHB file (73 KB).json', 'SMHB file (98 KB).json']:
        p = CACHE_DIR / fn
        if p.exists():
            data = json.loads(p.read_text(encoding='utf-8'))
            for r in data['rows']:
                hid = r.get('Herb_id', '')
                _herbs[hid] = r
                cn = r.get('Chinese_name', '')
                if cn:
                    _herbs_by_name.setdefault(cn, []).append(r)

    # ── 疾病 SMDE ──
    for fn in ['SMDE file (2,261 KB).json', 'SMDE file (416 KB).json']:
        p = CACHE_DIR / fn
        if p.exists():
            data = json.loads(p.read_text(encoding='utf-8'))
            for r in data['rows']:
                did = r.get('Disease_id', '')
                _diseases[did] = r
                dn = r.get('Disease_Name', '')
                if dn:
                    _diseases_by_name.setdefault(dn.lower(), []).append(r)

    # ── TCM症状 SMTS ──
    for fn in ['SMTS file (174 KB).json', 'SMTS file (221 KB).json']:
        p = CACHE_DIR / fn
        if p.exists():
            data = json.loads(p.read_text(encoding='utf-8'))
            for r in data['rows']:
                sid = r.get('TCM_symptom_id', '')
                _tcm_symptoms[sid] = r
                sn = r.get('TCM_symptom_name', '')
                if sn:
                    _tcm_symptoms_by_name.setdefault(sn, []).append(r)

    # ── 西医症状 SMMS ──
    for fn in ['SMMS file (113 KB).json', 'SMMS file (137 KB).json']:
        p = CACHE_DIR / fn
        if p.exists():
            data = json.loads(p.read_text(encoding='utf-8'))
            for r in data['rows']:
                mid = r.get('MM_symptom_id', '')
                _mm_symptoms[mid] = r
                mn = r.get('MM_symptom_name', '')
                if mn:
                    _mm_symptoms_by_name.setdefault(mn.lower(), []).append(r)

    # ── 证型 SMSY ──
    p = CACHE_DIR / 'SMSY file (31 KB).json'
    if p.exists():
        data = json.loads(p.read_text(encoding='utf-8'))
        for r in data['rows']:
            sid = r.get('Syndrome_id', '')
            _syndromes[sid] = r
            sn = r.get('Syndrome_name', '')
            if sn:
                _syndromes_by_name.setdefault(sn, []).append(r)

    # ── 化合物 SMIT ──
    for fn in ['SMIT file (1,846 KB).json', 'SMIT file (1,930 KB).json']:
        p = CACHE_DIR / fn
        if p.exists():
            data = json.loads(p.read_text(encoding='utf-8'))
            for r in data['rows']:
                mid = r.get('MOL_id', '') or r.get('Mol_id', '')
                _compounds[mid] = r
                mn = r.get('Molecule_name', '')
                if mn:
                    _compounds_by_name.setdefault(mn.lower(), []).append(r)

    # ── 基因靶点 SMTT ──
    for fn in ['SMTT file (1,639 KB).json', 'SMTT file (612 KB).json']:
        p = CACHE_DIR / fn
        if p.exists():
            data = json.loads(p.read_text(encoding='utf-8'))
            for r in data['rows']:
                gid = r.get('Gene_id', '')
                _targets[gid] = r
                sym = r.get('Gene_symbol', '')
                if sym:
                    _targets_by_symbol.setdefault(sym.lower(), []).append(r)

    _loaded = True
    print(f"  SymMap 已加载: {len(_herbs)}药 · {len(_diseases)}病 · {len(_tcm_symptoms)}中医症 · "
          f"{len(_mm_symptoms)}西医症 · {len(_syndromes)}证型 · {len(_compounds)}化合物 · {len(_targets)}靶点")


# ═══════════════════════════════════════════
# 查询接口
# ═══════════════════════════════════════════

def lookup_herb(name: str) -> Optional[dict]:
    """按中文名查 SymMap 中药"""
    _load_all()
    results = _herbs_by_name.get(name, [])
    return results[0] if results else None


def lookup_herb_by_id(hid: str) -> Optional[dict]:
    _load_all()
    return _herbs.get(hid)


def search_herbs(keyword: str) -> List[dict]:
    """模糊搜索中药名"""
    _load_all()
    results = []
    for name, herbs in _herbs_by_name.items():
        if keyword in name:
            results.extend(herbs)
    return results[:20]


def lookup_disease(name: str) -> List[dict]:
    """按名称查疾病（中文/英文）"""
    _load_all()
    return _diseases_by_name.get(name.lower(), [])


def search_diseases(keyword: str) -> List[dict]:
    """模糊搜索疾病"""
    _load_all()
    results = []
    for name, ds in _diseases_by_name.items():
        if keyword.lower() in name:
            results.extend(ds)
    return results[:20]


def lookup_tcm_symptom(name: str) -> Optional[dict]:
    _load_all()
    results = _tcm_symptoms_by_name.get(name, [])
    return results[0] if results else None


def search_tcm_symptoms(keyword: str) -> List[dict]:
    _load_all()
    results = []
    for name, syms in _tcm_symptoms_by_name.items():
        if keyword in name:
            results.extend(syms)
    return results[:20]


def lookup_mm_symptom(name: str) -> Optional[dict]:
    _load_all()
    results = _mm_symptoms_by_name.get(name.lower(), [])
    return results[0] if results else None


def search_syndromes(keyword: str) -> List[dict]:
    _load_all()
    results = []
    for name, syms in _syndromes_by_name.items():
        if keyword in name:
            results.extend(syms)
    return results[:10]


def lookup_compound(name: str) -> Optional[dict]:
    _load_all()
    results = _compounds_by_name.get(name.lower(), [])
    return results[0] if results else None


def search_compounds(keyword: str) -> List[dict]:
    _load_all()
    results = []
    for name, cs in _compounds_by_name.items():
        if keyword in name:
            results.extend(cs)
    return results[:20]


def lookup_gene(symbol: str) -> Optional[dict]:
    _load_all()
    results = _targets_by_symbol.get(symbol.lower(), [])
    return results[0] if results else None


def get_herb_relation(herb_id: str) -> dict:
    """查中药的跨库关联（TCMID/TCMSP等）"""
    herb = lookup_herb_by_id(herb_id) if not herb_id.isdigit() else _herbs.get(herb_id)
    if not herb:
        return {}
    return {
        'tcmid': herb.get('TCMID_id', ''),
        'tcms_id': herb.get('TCM-ID_id', ''),
        'tcms_sp': herb.get('TCMSP_id', ''),
        'herbdb': herb.get('HERBDB_ID', ''),
    }


def get_disease_codes(disease_id: str) -> dict:
    """查疾病的现代医学编码"""
    disease = _diseases.get(disease_id)
    if not disease:
        return {}
    return {
        'umls': disease.get('UMLS_id', ''),
        'mesh': disease.get('MeSH_id', ''),
        'omim': disease.get('OMIM_id', ''),
        'icd10': disease.get('ICD10CM_id', ''),
    }


def status() -> dict:
    _load_all()
    return {
        'herbs': len(_herbs),
        'diseases': len(_diseases),
        'tcm_symptoms': len(_tcm_symptoms),
        'mm_symptoms': len(_mm_symptoms),
        'syndromes': len(_syndromes),
        'compounds': len(_compounds),
        'targets': len(_targets),
    }


def tcm_mkg_crossref() -> dict:
    """交叉验证 TCM-MKG 和 SymMap 的中药重合度"""
    _load_all()
    try:
        from xin_knowledge import lookup_herb as tcm_lookup
    except ImportError:
        return {'error': 'xin_knowledge not loaded'}
    
    sym_herb_names = set()
    for name in _herbs_by_name:
        sym_herb_names.add(name)
    
    found = 0
    for name in sym_herb_names:
        if tcm_lookup(name):
            found += 1
    
    return {
        'symmap_herbs': len(sym_herb_names),
        'tcm_mkg_herbs': 6398,
        'cross_found': found,
        'cross_rate': f"{found/len(sym_herb_names)*100:.1f}%" if sym_herb_names else "0%",
    }


if __name__ == '__main__':
    import time
    t0 = time.time()
    s = status()
    t = time.time() - t0
    print(f"⏱ 加载 {t:.2f}s")
    print(f"📊 SymMap 状态:")
    for k, v in s.items():
        print(f"  {k}: {v:,}")
    
    print(f"\n🔗 TCM-MKG 交叉关联:")
    cr = tcm_mkg_crossref()
    if 'error' not in cr:
        print(f"  SymMap有药: {cr['symmap_herbs']} 味")
        print(f"  TCM-MKG有药: {cr['tcm_mkg_herbs']} 味")
        print(f"  互相覆盖: {cr['cross_found']} 味 ({cr['cross_rate']})")
    
    print(f"\n🔍 测试查询:")
    tests = [
        ('lookup_herb("枸杞")', lookup_herb("枸杞")),
        ('search_diseases("失眠")', search_diseases("失眠")[:3]),
        ('search_tcm_symptoms("失眠")', search_tcm_symptoms("失眠")[:3]),
        ('lookup_compound("berberine")', lookup_compound("berberine")),
    ]
    for name, result in tests:
        if result:
            if isinstance(result, list):
                print(f"  ✅ {name}: {len(result)} 条")
            else:
                print(f"  ✅ {name}: {str(dict(list(result.items())[:4]))[:80]}...")
        else:
            print(f"  ⚠️ {name}: 未找到")
