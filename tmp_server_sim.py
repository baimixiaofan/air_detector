"""
模拟数据生成器（服务器端版）
从 device_config.json 读取 SIM_ 设备，循环发数据
"""
import json, time, hashlib, random, requests

CONFIG_PATH = '/home/flask_app/device_config.json'
API_URL = 'http://127.0.0.1:5000/api/air-quality'
API_KEY = '111'

CITY_AQI = {
    '北京朝阳': (75, 40), '北京海淀': (72, 38), '天津滨海': (70, 38),
    '上海浦东': (55, 28), '石家庄': (85, 48), '南京': (60, 32),
    '杭州': (50, 25), '合肥': (62, 33), '福州': (40, 20),
    '济南': (68, 36), '广州': (48, 24), '深圳': (42, 22),
    '南宁': (45, 23), '海口': (32, 16), '武汉': (62, 33),
    '长沙': (58, 30), '郑州': (72, 38), '成都': (72, 38),
    '贵阳': (48, 25), '昆明': (38, 20), '西安': (78, 42),
    '兰州': (80, 44), '沈阳': (70, 38),
    '重庆渝中': (65, 34), '重庆江北': (62, 32), '重庆南岸': (60, 31),
    '重庆渝北': (58, 30), '重庆九龙坡': (68, 36), '重庆沙坪坝': (63, 33),
}

with open(CONFIG_PATH) as f:
    devices = json.load(f).get('devices', [])

sim_devices = [d for d in devices if d.get('code', '').startswith('SIM_')]
print(f"找到 {len(sim_devices)} 个模拟设备")
print("开始发送数据，按 Ctrl+C 停止\n")

while True:
    for d in sim_devices:
        code = d['code']
        city_name = d['name']  # e.g. 北京朝阳
        base = CITY_AQI.get(city_name, (60, 30))
        aqi = max(10, min(250, base[0] + random.randint(-20, 30)))
        pm25 = max(3, min(150, base[1] + random.randint(-10, 15)))
        no2 = max(3, min(80, int(aqi * 0.4 + random.randint(-5, 10))))
        so2 = max(1, min(40, int(aqi * 0.12 + random.randint(-2, 5))))
        o3 = max(3, min(100, int(aqi * 0.6 + random.randint(-5, 15))))

        payload = {
            "device_id": code,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "data": {"AQI": aqi, "PM₂.₅": pm25, "NO₂": no2, "SO₂": so2, "O₃": o3},
            "location": {
                "province": d.get('province', ''),
                "city": d.get('city', ''),
                "district": d.get('district', '')
            },
            "user": {"name": "监控用户", "industry": "办公"}
        }

        md5 = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        headers = {'X-API-Key': API_KEY, 'X-Content-MD5': md5, 'Content-Type': 'application/json'}

        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=5, verify=False)
            print(f"[{code:22s}] AQI={aqi:3d} PM2.5={pm25:2d} → {r.status_code}")
        except Exception as e:
            print(f"[{code:22s}] 失败: {e}")

    print(f"--- 一轮完成，等待 10 秒 ---")
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print("\n停止")
        break
