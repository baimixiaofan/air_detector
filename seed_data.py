"""
数据种子脚本 — 通过 API 填充业务数据
用法：python seed_data.py
"""
import requests
import json
import random
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

requests.packages.urllib3.disable_warnings()

API_BASE = 'https://baimeixiaofan.xyz/api/admin'

def get_token():
    r = requests.post(f'{API_BASE}/login', json={'username': 'admin', 'password': 'admin123'}, verify=False)
    return r.json()['data']['token']

def api(method, path, token, data=None):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    r = getattr(requests, method)(f'{API_BASE}{path}', json=data, headers=headers, verify=False, timeout=15)
    return r.json()

def seed_products(token):
    products = [
        {'name': 'AirMonitor Pro 2025', 'product_line': 'Pro系列', 'sensor_types': 'PM2.5,PM10,NO2,SO2,O3,CO', 'description': '高端室内空气质量监测仪，支持6项指标实时监测', 'status': 1},
        {'name': 'AirMonitor Lite', 'product_line': 'Lite系列', 'sensor_types': 'PM2.5,NO2,O3', 'description': '入门级空气检测仪，3项核心指标', 'status': 1},
        {'name': 'AirMonitor Outdoor', 'product_line': 'Pro系列', 'sensor_types': 'PM2.5,PM10,NO2,SO2,O3,CO,CO2', 'description': '户外环境监测站，7项全指标', 'status': 1},
        {'name': 'AirSense Mini', 'product_line': '基础系列', 'sensor_types': 'PM2.5,AQI', 'description': '迷你便携式，适合个人用户', 'status': 1},
        {'name': 'AirGuard Enterprise', 'product_line': 'Pro系列', 'sensor_types': 'PM2.5,PM10,NO2,SO2,O3,CO,CO2,TVOC', 'description': '企业级8项全指标监测', 'status': 1},
    ]
    count = 0
    for p in products:
        try:
            r = api('post', '/products', token, p)
            if r.get('code') == 200: count += 1
        except: pass
    print(f'  [OK] 产品型号: {count}/{len(products)}')

def seed_customers(token):
    customers = [
        {'name': '万科地产集团', 'type': 'enterprise', 'contact_name': '张经理', 'phone': '13800138001', 'industry': '地产', 'address': '深圳市盐田区'},
        {'name': '碧桂园集团', 'type': 'enterprise', 'contact_name': '李总监', 'phone': '13900139002', 'industry': '地产', 'address': '佛山市顺德区'},
        {'name': '希尔顿酒店', 'type': 'enterprise', 'contact_name': '王经理', 'phone': '13700137003', 'industry': '酒店', 'address': '上海市浦东新区'},
        {'name': '清华附中', 'type': 'enterprise', 'contact_name': '赵校长', 'phone': '13600136004', 'industry': '学校', 'address': '北京市海淀区'},
        {'name': '协和医院', 'type': 'enterprise', 'contact_name': '陈主任', 'phone': '13500135005', 'industry': '医院', 'address': '北京市东城区'},
        {'name': '字节跳动', 'type': 'enterprise', 'contact_name': '刘HR', 'phone': '13400134006', 'industry': '办公', 'address': '北京市海淀区'},
        {'name': '阿里巴巴', 'type': 'enterprise', 'contact_name': '黄经理', 'phone': '13300133007', 'industry': '办公', 'address': '杭州市余杭区'},
        {'name': '重庆市政府', 'type': 'enterprise', 'contact_name': '周处长', 'phone': '13200132008', 'industry': '办公', 'address': '重庆市渝中区'},
        {'name': '成都七中', 'type': 'enterprise', 'contact_name': '吴校长', 'phone': '13100131009', 'industry': '学校', 'address': '成都市武侯区'},
        {'name': '华西医院', 'type': 'enterprise', 'contact_name': '郑主任', 'phone': '13000130010', 'industry': '医院', 'address': '成都市武侯区'},
    ]
    count = 0
    for c in customers:
        try:
            r = api('post', '/customers', token, c)
            if r.get('code') == 200: count += 1
        except: pass
    print(f'  [OK] 客户数据: {count}/{len(customers)}')

def seed_work_orders(token):
    orders = [
        {'title': '万科渝中花园设备离线', 'type': 'fault', 'priority': 'urgent', 'device_id': 'AQ_重庆市_100', 'description': '设备持续离线超过24小时', 'assignee': '张工'},
        {'title': '碧桂园设备传感器校准', 'type': 'repair', 'priority': 'high', 'device_id': 'AQ_广州市_200', 'description': 'PM2.5读数偏高', 'assignee': '李工'},
        {'title': '重庆市政府季度巡检', 'type': 'inspection', 'priority': 'medium', 'description': '季度例行巡检', 'assignee': ''},
        {'title': '成都七中设备数据异常', 'type': 'fault', 'priority': 'high', 'device_id': 'AQ_成都市_300', 'description': 'AQI数据波动异常', 'assignee': '王工'},
        {'title': '希尔顿酒店报告延迟', 'type': 'complaint', 'priority': 'medium', 'description': '客户反馈月度报告延迟'},
        {'title': '阿里园区设备外壳更换', 'type': 'repair', 'priority': 'low', 'device_id': 'AQ_杭州市_400', 'description': '设备外壳老化', 'assignee': '赵工'},
        {'title': '希尔顿浦东设备重启', 'type': 'fault', 'priority': 'urgent', 'device_id': 'AQ_上海市_500', 'description': '设备频繁自动重启', 'assignee': '张工'},
    ]
    count = 0
    for o in orders:
        try:
            r = api('post', '/workorders', token, o)
            if r.get('code') == 200: count += 1
        except: pass
    print(f'  [OK] 售后工单: {count}/{len(orders)}')

def seed_enterprise_reports(token):
    reports = [
        {'company_name': '万科地产集团', 'report_title': '2026年5月空气质量月度报告', 'report_type': 'monthly', 'metrics': ['AQI', 'PM2.5'], 'highlights': ['PM2.5同比下降12%', '达标率提升至95%'], 'style': 'formal'},
        {'company_name': '清华附中', 'report_title': '2026年春季学期教室空气质量报告', 'report_type': 'monthly', 'metrics': ['AQI', 'PM2.5'], 'highlights': ['教室空气质量优秀率92%'], 'style': 'formal'},
        {'company_name': '希尔顿酒店', 'report_title': '2026年Q2客房空气质量分析', 'report_type': 'quarterly', 'metrics': ['AQI', 'PM2.5'], 'highlights': ['客户满意度提升8%'], 'style': 'casual'},
    ]
    count = 0
    for r in reports:
        try:
            resp = api('post', '/reports/enterprise', token, r)
            if resp.get('code') == 200: count += 1
        except: pass
    print(f'  [OK] 企业报告: {count}/{len(reports)}')

def seed_smart_reports(token):
    count = 0
    for rtype in ['daily', 'weekly', 'monthly']:
        try:
            resp = api('post', '/reports/generate', token, {'type': rtype})
            if resp.get('code') == 200: count += 1
        except: pass
    print(f'  [OK] 智能报告: {count}/3')

if __name__ == '__main__':
    print('=' * 50)
    print('[SEED] 开始填充业务数据...')
    print('=' * 50)

    token = get_token()
    print(f'[OK] 登录成功')

    print('\n[1/6] 产品型号...')
    seed_products(token)

    print('\n[2/6] 客户数据...')
    seed_customers(token)

    print('\n[3/6] 售后工单...')
    seed_work_orders(token)

    print('\n[4/6] 智能报告...')
    seed_smart_reports(token)

    print('\n[5/6] 企业报告...')
    seed_enterprise_reports(token)

    print('\n' + '=' * 50)
    print('[DONE] 业务数据填充完成！')
    print('=' * 50)
