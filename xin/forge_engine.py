"""
锻因缘 · 推演引擎
道归相变玄学 · Daogui实现
"""
import json, os, random, hashlib, time
from datetime import datetime

DATA_FILE = os.path.expanduser("~/.openclaw/workspace/forge_data.json")

# 生肖五行
SHENGXIAO_WUXING = {
    '鼠': '水', '牛': '土', '虎': '木', '兔': '木',
    '龙': '土', '蛇': '火', '马': '火', '羊': '土',
    '猴': '金', '鸡': '金', '狗': '土', '猪': '水'
}

SHENGXIAO_PAIRS = {
    ('鼠','牛'): '六合', ('虎','猪'): '六合', ('兔','狗'): '六合',
    ('龙','鸡'): '六合', ('蛇','猴'): '六合', ('马','羊'): '六合',
}

# 占星元素
STAR_SIGNS_CN = ['白羊','金牛','双子','巨蟹','狮子','处女','天秤','天蝎','射手','摩羯','水瓶','双鱼']
STAR_ELEMENTS = {'火':['白羊','狮子','射手'],'土':['金牛','处女','摩羯'],'风':['双子','天秤','水瓶'],'水':['巨蟹','天蝎','双鱼']}

# 态度词库（从文本中提取特征）
ICE_KEYWORDS = ['冷','冰','冻','封','硬','僵','固','闭','藏','收','默','远','沉','冷漠','距离']
WATER_KEYWORDS = ['暖','流','柔','软','温','动','开','融','化','润','透','渗','包容','理解']

def _load_data():
    if os.path.isfile(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _generate_code():
    return ''.join(random.choices('0123456789', k=6))

def _get_shengxiao(year_str):
    if not year_str:
        return None
    try:
        year = int(year_str[:4])
        animals = list(SHENGXIAO_WUXING.keys())
        return animals[(year - 4) % 12]
    except:
        return None

def _analyze_phase(text):
    """分析文本中的水态/冰态倾向"""
    ice_score = sum(1 for kw in ICE_KEYWORDS if kw in text)
    water_score = sum(1 for kw in WATER_KEYWORDS if kw in text)
    total = ice_score + water_score
    if total == 0:
        return {'phase': '未显', 'score': 0.5, 'detail': '文本温度中性，未检测到明显的相变倾向'}
    
    ratio = water_score / total if total > 0 else 0.5
    if ratio > 0.6:
        return {'phase': '水态', 'score': ratio, 'detail': f'水态倾向明显（{water_score}/{total}），流动、渗透、可适应'}
    elif ratio < 0.4:
        return {'phase': '冰态', 'score': 1 - ratio, 'detail': f'冰态倾向明显（{ice_score}/{total}），固定、维持、谨慎'}
    else:
        return {'phase': '临界', 'score': 0.5, 'detail': '处于相变临界点，温度变化将触发状态切换'}

def _analyze_temp(text):
    """温度分析"""
    temp_words = {'热':0,'暖':0,'温':0,'凉':0,'冷':0,'寒':0,'烫':0,'冰':0}
    for word in temp_words:
        temp_words[word] = text.count(word)
    hot = temp_words['热'] + temp_words['暖'] + temp_words['温'] + temp_words['烫']
    cold = temp_words['凉'] + temp_words['冷'] + temp_words['寒'] + temp_words['冰']
    return hot - cold

def _phase_compatibility(p1, p2):
    """双相兼容性"""
    if p1 == '临界' or p2 == '临界':
        return '波动', '一方处于临界态，关系温度将随环境变化而剧烈波动'
    if p1 == p2:
        if p1 == '水态':
            return '相融', '双水相融，双方都能流动适应，温差小，易共鸣'
        else:
            return '相持', '双冰相持，结构稳定但缺乏流动，需要外部温度才能软化'
    else:
        return '相变', '一水一冰，温差驱动相变——水可结冰，冰可化水，关键在于温度'

def _generate_verdict(name1, name2, comp, phase1, phase2, temp_diff):
    """生成良人箴言"""
    templates_high = [
        f'{name1}与{name2}之间有一座桥。桥不是谁建的，是两人同时向对方走了一步。',
        f'锻因缘不是寻找完美的人，是认出那个愿意和你一起进炉的人。{name2}没有转身。',
        f'温差存在，但方向一致——这是{name1}和{name2}之间最重要的信号。',
        f'情是十三盘的驱动介质。{name2}在盘上的位置，恰好是你需要看见的那一格。',
        f'水遇水则溶，冰遇冰则固。{name1}与{name2}之间，刚好能化开又凝得住。',
    ]
    templates_med = [
        f'{name1}看见了{name2}的一部分轮廓，但不是全部。这不是骗，是温度还不够。',
        f'两人之间有一段沉默的距离。这段距离不是隔阂，是相变需要的空间。',
        f'不需要现在就确认良人。只需要确认：你们在同一个温度场里，方向没有反。',
        f'{name1}的描述里有一种温度，{name2}的描述里有另一种。温差不大，但存在。',
    ]
    templates_low = [
        f'{name1}的描述偏{phase1}，{name2}的描述偏{phase2}。这个温差不会自动消失。',
        f'锻因缘的前提是诚实。如果有一方在描述中回避了温度，那结果也会回避结论。',
        f'不是每一炉都能成器。有时候锻过了，才知道这块料不适合这个炉。',
        f'{name1}和{name2}之间缺的不是缘分，是同一个温度层。人不在同一层，再怎么锻也焊不上。',
    ]
    
    if comp == '相融':
        t = templates_high
    elif comp in ('相持', '波动'):
        t = templates_med
    else:
        if temp_diff > 5 or temp_diff < -5:
            t = templates_low
        else:
            t = templates_med
    
    return random.choice(t)

def generate_analysis(user1, user2, viewer):
    """生成推演分析"""
    p1 = _analyze_phase(user1['impression']) if viewer == 2 else _analyze_phase(user1['impression'])
    p2 = _analyze_phase(user2['impression'])
    
    # 根据视角切换引用方向
    if viewer == 1:
        # 用户一看到：用户一对用户二的印象 + 用户二对用户一的印象
        my_phase = _analyze_phase(user1['impression'])
        their_phase = _analyze_phase(user2['impression'])
        my_name = user1['name']
        their_name = user2['name']
        my_impression = user1['impression']
        their_impression = user2['impression']
    else:
        my_phase = _analyze_phase(user2['impression'])
        their_phase = _analyze_phase(user1['impression'])
        my_name = user2['name']
        their_name = user1['name']
        my_impression = user2['impression']
        their_impression = user1['impression']
    
    comp, comp_detail = _phase_compatibility(my_phase['phase'], their_phase['phase'])
    
    temp_diff = _analyze_temp(my_impression) - _analyze_temp(their_impression)
    
    # 生肖
    sx1 = _get_shengxiao(user1.get('birth', ''))
    sx2 = _get_shengxiao(user2.get('birth', ''))
    sx_info = ''
    if sx1 and sx2:
        pair = (sx1, sx2)
        if pair in SHENGXIAO_PAIRS:
            sx_info = f'生肖{sx1}与{sx2}为{SHENGXIAO_PAIRS[pair]}。'
        elif (sx2, sx1) in SHENGXIAO_PAIRS:
            sx_info = f'生肖{sx2}与{sx1}为{SHENGXIAO_PAIRS[(sx2,sx1)]}。'
        else:
            sx_info = f'生肖{sx1}（{SHENGXIAO_WUXING[sx1]}）与{sx2}（{SHENGXIAO_WUXING[sx2]}）。'
    
    return {
        'viewer_name': my_name,
        'temp_analysis': f'<p><strong>你描述{their_name}时的体温：</strong>{_temp_desc(_analyze_temp(my_impression))}</p><p><strong>{their_name}描述你时的体温：</strong>{_temp_desc(_analyze_temp(their_impression))}</p><p><strong>温差：</strong>{abs(temp_diff)}度{" · 你偏暖" if temp_diff > 0 else " · 你偏凉" if temp_diff < 0 else " · 温度均衡"}</p>',
        'phase_analysis': f'<p><strong>你在{their_name}面前：</strong>{my_phase["phase"]}（{my_phase["detail"]}）</p><p><strong>{their_name}在你面前：</strong>{their_phase["phase"]}（{their_phase["detail"]}）</p><p><strong>相态关系：</strong>{comp} — {comp_detail}</p>',
        'thread_analysis': f'<p>{sx_info}</p><p>你在描述中用了"{_key_phrase(my_impression)}"，{their_name}在描述中用了"{_key_phrase(their_impression)}"。这两个词之间的张力，就是缘线的质地。</p>',
        'verdict': f'<p style="font-size:15px;line-height:1.9;color:#d8ccb0;">{_generate_verdict(my_name, their_name, comp, my_phase["phase"], their_phase["phase"], temp_diff)}</p>',
    }

def _temp_desc(score):
    if score > 5: return '🔥🔥🔥 高温 · 热烈'
    if score > 2: return '🔥 温热 · 有温度'
    if score > -2: return '🌡️ 常温 · 平稳'
    if score > -5: return '❄️ 微凉 · 有距离'
    return '❄️❄️❄️ 低温 · 冷静'

def _key_phrase(text):
    """提取关键短语"""
    words = [w for w in text if len(w) > 1 and w in '冷暖热凉温柔刚硬明亮暗淡远近深浅长短宽窄粗细轻重缓急动静虚实浓淡清浊明暗']
    return random.sample(words, min(2, len(words))) if len(words) >= 2 else ['温度', '形状']

# ── API 接口 ──

def handle_create(user1_data):
    """用户一创建锻因缘"""
    data = _load_data()
    code = _generate_code()
    while code in data:
        code = _generate_code()
    data[code] = {
        'user1': {
            'name': user1_data.get('name', '无名氏'),
            'birth': user1_data.get('birth', ''),
            'impression': user1_data.get('impression', ''),
        },
        'user2': None,
        'created_at': time.time(),
    }
    _save_data(data)
    return {'success': True, 'code': code}

def handle_join(code, user2_data):
    """用户二接入"""
    data = _load_data()
    if code not in data:
        return {'success': False, 'error': '邀请码无效'}
    if data[code]['user2'] is not None:
        return {'success': False, 'error': '该锻因缘已有第二人入局'}
    data[code]['user2'] = {
        'name': user2_data.get('name', '无名氏'),
        'birth': user2_data.get('birth', ''),
        'impression': user2_data.get('impression', ''),
    }
    _save_data(data)
    return {'success': True}

def handle_result(code, user):
    """获取评审结果"""
    data = _load_data()
    if code not in data:
        return {'success': False, 'error': '锻因缘不存在'}
    d = data[code]
    if d['user2'] is None:
        return {'success': False, 'user1_ready': True, 'user2_ready': False}
    
    user1 = d['user1']
    user2 = d['user2']
    
    view1 = generate_analysis(user1, user2, viewer=1)
    view2 = generate_analysis(user1, user2, viewer=2)
    
    return {
        'success': True,
        'user1_ready': True,
        'user2_ready': True,
        'view1': view1,
        'view2': view2,
    }

def cleanup_old():
    """清理24小时前的旧数据"""
    data = _load_data()
    now = time.time()
    expired = [k for k, v in data.items() if now - v.get('created_at', 0) > 86400]
    for k in expired:
        del data[k]
    if expired:
        _save_data(data)
    return len(expired)
