"""
演示数据种子 — 创建客户、设备、工单、告警、报告
用法：PYTHONIOENCODING=utf-8 python seed_data.py
"""
import json, random, ssl, urllib.request, urllib.error, sys
ssl._create_default_https_context = ssl._create_unverified_context

BASE = 'https://47.109.191.13/api/admin'
DEVICE_API = 'https://47.109.191.13/api/air-quality'

def api(method, path, data=None, token=''):
    url = f'{BASE}{path}'
    hdr = {'Content-Type': 'application/json'}
    if token: hdr['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=hdr, method=method)
    try: return json.loads(urllib.request.urlopen(req, timeout=15).read())
    except Exception as e: print(f'  !! {path}: {e}'); return None

# 登录
print('>>> Login')
r = api('POST', '/login', {'username': 'admin', 'password': 'admin123'})
assert r and r.get('code') == 200, 'Login failed!'
token = r['data']['token']
print(f'OK')

# ── 清除旧设备，从头来 ──
print('\n>>> Clean old devices')
old = api('GET', '/devices', token=token)
if old and old.get('code') == 200:
    for d in old.get('data', []):
        if isinstance(d, dict) and d.get('id'):
            api('DELETE', f'/devices/{d["device_id"]}', token=token)

# ── 城市坐标映射 ──
CT = {
    '北京朝阳': (39.92, 116.46, '北京市', '北京市', '朝阳区'),
    '上海浦东': (31.22, 121.54, '上海市', '上海市', '浦东新区'),
    '成都武侯': (30.60, 104.06, '四川省', '成都市', '武侯区'),
    '深圳南山': (22.54, 113.95, '广东省', '深圳市', '南山区'),
    '杭州西湖': (30.26, 120.15, '浙江省', '杭州市', '西湖区'),
    '武汉武昌': (30.55, 114.32, '湖北省', '武汉市', '武昌区'),
    '南京鼓楼': (32.06, 118.78, '江苏省', '南京市', '鼓楼区'),
    # 重庆各区县
    '重庆渝中': (29.56, 106.57, '重庆市', '重庆市', '渝中区'),
    '重庆江北': (29.61, 106.54, '重庆市', '重庆市', '江北区'),
    '重庆沙坪坝': (29.56, 106.46, '重庆市', '重庆市', '沙坪坝区'),
    '重庆南岸': (29.52, 106.56, '重庆市', '重庆市', '南岸区'),
    '重庆渝北': (29.72, 106.63, '重庆市', '重庆市', '渝北区'),
    '重庆九龙坡': (29.50, 106.51, '重庆市', '重庆市', '九龙坡区'),
    '重庆大渡口': (29.48, 106.48, '重庆市', '重庆市', '大渡口区'),
    '重庆巴南': (29.38, 106.52, '重庆市', '重庆市', '巴南区'),
    '重庆北碚': (29.83, 106.40, '重庆市', '重庆市', '北碚区'),
}

customer_map = {}

# ── 创建客户（先删旧的）──
print('\n>>> Customers')
customers_plan = [
    # (名称, 类型, 行业, 城市键)
    ('万科地产集团', 'enterprise', '地产', '深圳南山'),
    ('华润物业', 'enterprise', '地产', '上海浦东'),
    ('希尔顿酒店', 'enterprise', '酒店', '北京朝阳'),
    ('锦江之星', 'enterprise', '酒店', '重庆渝中'),
    ('华西医院', 'enterprise', '医院', '成都武侯'),
    ('北大附中', 'enterprise', '学校', '北京朝阳'),
    ('字节跳动', 'enterprise', '办公', '北京朝阳'),
    ('顺丰速运', 'enterprise', '工厂', '深圳南山'),
    ('阿里巴巴', 'enterprise', '办公', '杭州西湖'),
    ('光谷科技', 'enterprise', '办公', '武汉武昌'),
    ('苏宁置业', 'enterprise', '地产', '南京鼓楼'),
    # 重庆本地企业（重点）
    ('渝中地产集团', 'enterprise', '地产', '重庆渝中'),
    ('南滨酒店管理', 'enterprise', '酒店', '重庆南岸'),
    ('山城物流公司', 'enterprise', '工厂', '重庆渝北'),
    ('巴南教育局', 'enterprise', '学校', '重庆巴南'),
    # 个人客户
    ('吴先生', 'individual', '办公', '上海浦东'),
    ('郑女士', 'individual', '办公', '北京朝阳'),
    ('黄同学', 'individual', '学校', '杭州西湖'),
]

for name, ctype, industry, city_key in customers_plan:
    r = api('POST', '/customers', {
        'name': name, 'type': ctype, 'industry': industry,
        'contact_name': f'{name[:2]}负责人', 'phone': f'138{random.randint(10000000,99999999)}'
    }, token)
    if r and r.get('code') == 200:
        customer_map[name] = r['data']['id']
        print(f'  OK {name} ({ctype}/{industry}) ')
    else:
        print(f'  SKIP {name}')

# ── 按客户创建设备（企业多台，重庆重点）──
print('\n>>> Devices')
all_devices_for_config = []

def make_device(name, cid, city_key, dev_name):
    """创建设备并返回真实 device_id"""
    lat, lng, prov, city, district = CT[city_key]
    lat += random.uniform(-0.01, 0.01)
    lng += random.uniform(-0.01, 0.01)
    r = api('POST', '/devices', {
        'name': dev_name, 'product_model': 'AirInsight Pro 2025',
        'district': district, 'customer_id': cid,
        'latitude': round(lat, 4), 'longitude': round(lng, 4)
    }, token)
    if r and r.get('code') == 200:
        real_id = r['data'].get('device_id', '')
        # 激活
        all_devs = api('GET', '/devices', token=token)
        if all_devs and all_devs.get('code') == 200:
            for d in all_devs.get('data', []):
                if isinstance(d, dict) and d.get('device_id') == real_id:
                    api('PUT', f'/devices/{d["id"]}', {'activation_status': 'activated'}, token)
                    break
        return real_id, lat, lng, prov, city, district
    return None, lat, lng, prov, city, district

# 企业设备方案：{客户名: (城市键, [设备名列表])}
plan = {
    '万科地产集团': ('深圳南山', ['总部监测仪A', '总部监测仪B', '花园监测仪', '新城监测仪', '会所监测仪']),
    '华润物业': ('上海浦东', ['华润大厦', '万象城', '华润广场', '华润中心', '生活馆']),
    '希尔顿酒店': ('北京朝阳', ['大堂监测仪', '客房楼层A', '健身房', '会议室', '餐厅']),
    '锦江之星': ('重庆渝中', ['大堂监测仪', '客房A区', '客房B区', '餐厅', '大厅']),
    '华西医院': ('成都武侯', ['门诊楼', '住院部A', '住院部B', '急诊中心', '行政楼']),
    '北大附中': ('北京朝阳', ['教学楼A', '体育馆', '图书馆', '实验室', '食堂']),
    '字节跳动': ('北京朝阳', ['总部1层', '总部5层', '总部10层', '总部15层', '健身房']),
    '顺丰速运': ('深圳南山', ['仓储中心', '分拣中心A', '分拣中心B', '办公区', '调度室']),
    '阿里巴巴': ('杭州西湖', ['西溪园区A', '西溪园区B', '滨江园区', '云谷校区', '访客中心']),
    '光谷科技': ('武汉武昌', ['研发中心A', '研发中心B', '测试中心', '数据中心', '办公区']),
    '苏宁置业': ('南京鼓楼', ['总部办公楼', '苏宁广场A', '苏宁广场B', '售后中心', '体验店']),
    # 重庆重点
    '渝中地产集团': ('重庆渝中', ['解放碑监测仪', '洪崖洞监测仪', '朝天门监测仪', '大坪监测仪', '上清寺监测仪']),
    '南滨酒店管理': ('重庆南岸', ['南滨路A', '南滨路B', '南坪监测仪', '弹子石监测仪', '茶园监测仪']),
    '山城物流公司': ('重庆渝北', ['物流园区A', '物流园区B', '空港监测仪', '龙头寺监测仪', '保税区监测仪']),
    '巴南教育局': ('重庆巴南', ['巴南中学', '鱼洞小学', '龙洲湾校区', '李家沱校区', '花溪校区']),
    # 个人
    '吴先生': ('上海浦东', ['客厅检测仪']),
    '郑女士': ('北京朝阳', ['卧室检测仪']),
    '黄同学': ('杭州西湖', ['书房检测仪']),
}

# 给重庆没在客户列表里的区也各补5台(挂在已有重庆客户名下)
extra_cq = {
    '重庆江北': '渝中地产集团',
    '重庆沙坪坝': '渝中地产集团',
    '重庆九龙坡': '南滨酒店管理',
    '重庆大渡口': '南滨酒店管理',
    '重庆北碚': '山城物流公司',
}
for city_key, cn in extra_cq.items():
    plan.setdefault(cn, (city_key, []))[1].extend([f'{city_key}监测点{i+1}' for i in range(5)])

for name, (city_key, dev_names) in plan.items():
    cid = customer_map.get(name)
    if not cid: continue
    for dn in dev_names:
        rid, lat, lng, prov, city, district = make_device(name, cid, city_key, dn)
        if rid:
            print(f'  OK {rid} {dn} ({district}) -> {name}')
            all_devices_for_config.append({
                'code': rid, 'name': dn,
                'longitude': lng, 'latitude': lat,
                'customer_id': str(cid), 'company_name': name,
                'province': prov, 'city': city, 'district': district
            })

print(f'\n  Total devices: {len(all_devices_for_config)}')

# ── 工单 ──
print('\n>>> Work orders')
for i, (title, wtype, priority) in enumerate([
    ('AQI数据异常升高', 'fault', 'urgent'),
    ('传感器需要校准', 'repair', 'high'),
    ('设备离线超过2小时', 'fault', 'urgent'),
    ('定期巡检维护', 'inspection', 'medium'),
    ('用户投诉空气有异味', 'complaint', 'high'),
    ('设备更换滤网', 'repair', 'medium'),
    ('数据上报延迟', 'fault', 'low'),
    ('PM2.5传感器故障', 'fault', 'high'),
    ('季度预防性维护', 'inspection', 'low'),
    ('设备安装位置调整', 'repair', 'medium'),
]):
    d = all_devices_for_config[i % len(all_devices_for_config)] if all_devices_for_config else {}
    cid = int(d.get('customer_id', '')) if d.get('customer_id') else None
    r = api('POST', '/workorders', {
        'title': title, 'type': wtype, 'priority': priority,
        'description': f'自动生成: {title}',
        'device_id': d.get('code', ''), 'customer_id': cid
    }, token)
    if r and r.get('code') == 200: print(f'  OK {title}')

# ── 告警规则 ──
print('\n>>> Alert rules')
for name, metric, op, thresh, sev in [
    ('AQI严重超标', 'aqi', '>', 150, 'critical'),
    ('AQI警告', 'aqi', '>', 100, 'warning'),
    ('PM2.5偏高', 'pm25', '>', 75, 'warning'),
    ('O3超标', 'o3', '>', 100, 'info'),
]:
    r = api('POST', '/alerts/rules', {'name': name, 'metric': metric, 'operator': op, 'threshold': thresh, 'severity': sev, 'enabled': 1}, token)
    print(f'  {"OK" if r and r.get("code")==200 else "SKIP"} {name}')

# ── 企业报告 ──
print('\n>>> Enterprise reports')
for cname in ['万科地产集团', '华西医院', '字节跳动', '渝中地产集团', '华润物业']:
    cid = customer_map.get(cname)
    if not cid: continue
    r = api('POST', '/reports/enterprise', {
        'customer_id': cid, 'report_title': f'{cname}2026年6月空气质量月报',
        'report_type': 'monthly', 'style': 'formal', 'highlights': ['设备运行稳定', '达标率良好']
    }, token)
    if r and r.get('code') == 200: print(f'  OK {cname} (report_id={r["data"]["id"]})')
    else: print(f'  FAIL {cname}: {r.get("msg","?") if r else "error"}')

# ── 企业信息 ──
print('\n>>> Company info')
api('PUT', '/company-info', {
    'name': 'AirInsight 智能空气监测平台', 'address': '北京市朝阳区科技园A座',
    'contact_name': '运营团队', 'contact_phone': '400-888-8888',
    'contact_email': 'support@airinsight.com',
    'description': '企业级空气质量监测与数据分析平台，提供实时监测、智能告警、大数据分析、AI报告等一站式服务'
}, token)
print('  OK')

# ── 导出 device_config.json ──
with open('d:/软件设计/server/device_config.json', 'w', encoding='utf-8') as f:
    json.dump({'devices': all_devices_for_config}, f, ensure_ascii=False, indent=2)

print('\n' + '='*60)
print(f'SEED COMPLETE: {len(customer_map)} customers, {len(all_devices_for_config)} devices')
print('Now run: PYTHONIOENCODING=utf-8 python simulator/air_detector.py --enterprise --api-endpoint https://47.109.191.13/api/air-quality --api-header X-API-Key=111 --frequency 3000')
print('='*60)
