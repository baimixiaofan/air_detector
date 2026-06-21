"""
空气质量模拟器 — 本地版，全国58个设备同时模拟
"""
import json, time, hashlib, random, requests

API_URL = 'https://47.109.191.13/api/air-quality'
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

CITY_LOC = {
    '北京朝阳': ('北京市','北京市','朝阳区'), '北京海淀': ('北京市','北京市','海淀区'),
    '天津滨海': ('天津市','天津市','滨海新区'), '上海浦东': ('上海市','上海市','浦东新区'),
    '石家庄': ('河北省','石家庄市','石家庄市'), '南京': ('江苏省','南京市','南京市'),
    '杭州': ('浙江省','杭州市','杭州市'), '合肥': ('安徽省','合肥市','合肥市'),
    '福州': ('福建省','福州市','福州市'), '济南': ('山东省','济南市','济南市'),
    '广州': ('广东省','广州市','广州市'), '深圳': ('广东省','深圳市','深圳市'),
    '南宁': ('广西','南宁市','南宁市'), '海口': ('海南省','海口市','海口市'),
    '武汉': ('湖北省','武汉市','武汉市'), '长沙': ('湖南省','长沙市','长沙市'),
    '郑州': ('河南省','郑州市','郑州市'), '成都': ('四川省','成都市','成都市'),
    '贵阳': ('贵州省','贵阳市','贵阳市'), '昆明': ('云南省','昆明市','昆明市'),
    '西安': ('陕西省','西安市','西安市'), '兰州': ('甘肃省','兰州市','兰州市'),
    '沈阳': ('辽宁省','沈阳市','沈阳市'),
    '重庆渝中': ('重庆市','重庆市','渝中区'), '重庆江北': ('重庆市','重庆市','江北区'),
    '重庆南岸': ('重庆市','重庆市','南岸区'), '重庆渝北': ('重庆市','重庆市','渝北区'),
    '重庆九龙坡': ('重庆市','重庆市','九龙坡区'), '重庆沙坪坝': ('重庆市','重庆市','沙坪坝区'),
}

# 生成全部设备ID
DEVICES = []
for city in CITY_AQI:
    for i in (1, 2):
        DEVICES.append((f"SIM_{city}_{i}", city))

print(f"启动 {len(DEVICES)} 个模拟设备，每轮约 {len(DEVICES) * 5} 秒")
print(f"目标: {API_URL}")
print("按 Ctrl+C 停止\n")

while True:
    for device_id, city_name in DEVICES:
        base = CITY_AQI.get(city_name, (60, 30))
        loc = CITY_LOC.get(city_name, ('','',''))
        
        aqi = max(10, min(250, base[0] + random.randint(-20, 30)))
        pm25 = max(3, min(150, base[1] + random.randint(-10, 15)))
        no2 = max(3, min(80, int(aqi * 0.4 + random.randint(-5, 10))))
        so2 = max(1, min(40, int(aqi * 0.12 + random.randint(-2, 5))))
        o3 = max(3, min(100, int(aqi * 0.6 + random.randint(-5, 15))))

        payload = {
            "device_id": device_id,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "data": {"AQI": aqi, "PM₂.₅": pm25, "NO₂": no2, "SO₂": so2, "O₃": o3},
            "location": {"province": loc[0], "city": loc[1], "district": loc[2]},
            "user": {"name": "监控用户", "industry": "办公"}
        }

        md5 = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        headers = {'X-API-Key': API_KEY, 'X-Content-MD5': md5, 'Content-Type': 'application/json'}

        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=5, verify=False)
            print(f"[{device_id:22s}] AQI={aqi:3d} PM2.5={pm25:2d} → {r.status_code}")
        except Exception as e:
            print(f"[{device_id:22s}] 失败: {e}")

    print(f"--- 一轮完成（{len(DEVICES)} 台），10 秒后下一轮 ---\n")
    time.sleep(10)
