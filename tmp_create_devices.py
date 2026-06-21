"""批量创建模拟设备，匹配 CITY_PROFILES，每个城市2台"""
import json, os

CITY_PROFILES = {
    '北京朝阳': {'province': '北京市', 'city': '北京市', 'district': '朝阳区', 'lat': 39.92, 'lng': 116.46},
    '北京海淀': {'province': '北京市', 'city': '北京市', 'district': '海淀区', 'lat': 39.96, 'lng': 116.33},
    '天津滨海': {'province': '天津市', 'city': '天津市', 'district': '滨海新区', 'lat': 39.08, 'lng': 117.20},
    '上海浦东': {'province': '上海市', 'city': '上海市', 'district': '浦东新区', 'lat': 31.23, 'lng': 121.47},
    '石家庄': {'province': '河北省', 'city': '石家庄市', 'district': '石家庄市', 'lat': 38.04, 'lng': 114.51},
    '南京': {'province': '江苏省', 'city': '南京市', 'district': '南京市', 'lat': 32.06, 'lng': 118.80},
    '杭州': {'province': '浙江省', 'city': '杭州市', 'district': '杭州市', 'lat': 30.27, 'lng': 120.15},
    '合肥': {'province': '安徽省', 'city': '合肥市', 'district': '合肥市', 'lat': 31.82, 'lng': 117.23},
    '福州': {'province': '福建省', 'city': '福州市', 'district': '福州市', 'lat': 26.07, 'lng': 119.30},
    '济南': {'province': '山东省', 'city': '济南市', 'district': '济南市', 'lat': 36.65, 'lng': 117.00},
    '广州': {'province': '广东省', 'city': '广州市', 'district': '广州市', 'lat': 23.13, 'lng': 113.26},
    '深圳': {'province': '广东省', 'city': '深圳市', 'district': '深圳市', 'lat': 22.54, 'lng': 113.95},
    '南宁': {'province': '广西', 'city': '南宁市', 'district': '南宁市', 'lat': 22.82, 'lng': 108.32},
    '海口': {'province': '海南省', 'city': '海口市', 'district': '海口市', 'lat': 20.02, 'lng': 110.35},
    '武汉': {'province': '湖北省', 'city': '武汉市', 'district': '武汉市', 'lat': 30.56, 'lng': 114.34},
    '长沙': {'province': '湖南省', 'city': '长沙市', 'district': '长沙市', 'lat': 28.23, 'lng': 112.94},
    '郑州': {'province': '河南省', 'city': '郑州市', 'district': '郑州市', 'lat': 34.75, 'lng': 113.65},
    '成都': {'province': '四川省', 'city': '成都市', 'district': '成都市', 'lat': 30.57, 'lng': 104.07},
    '贵阳': {'province': '贵州省', 'city': '贵阳市', 'district': '贵阳市', 'lat': 26.65, 'lng': 106.63},
    '昆明': {'province': '云南省', 'city': '昆明市', 'district': '昆明市', 'lat': 25.04, 'lng': 102.68},
    '西安': {'province': '陕西省', 'city': '西安市', 'district': '西安市', 'lat': 34.26, 'lng': 108.94},
    '兰州': {'province': '甘肃省', 'city': '兰州市', 'district': '兰州市', 'lat': 36.06, 'lng': 103.83},
    '沈阳': {'province': '辽宁省', 'city': '沈阳市', 'district': '沈阳市', 'lat': 41.80, 'lng': 123.43},
    # 重庆市各区
    '重庆渝中': {'province': '重庆市', 'city': '重庆市', 'district': '渝中区', 'lat': 29.56, 'lng': 106.55},
    '重庆江北': {'province': '重庆市', 'city': '重庆市', 'district': '江北区', 'lat': 29.61, 'lng': 106.57},
    '重庆南岸': {'province': '重庆市', 'city': '重庆市', 'district': '南岸区', 'lat': 29.52, 'lng': 106.66},
    '重庆渝北': {'province': '重庆市', 'city': '重庆市', 'district': '渝北区', 'lat': 29.72, 'lng': 106.63},
    '重庆九龙坡': {'province': '重庆市', 'city': '重庆市', 'district': '九龙坡区', 'lat': 29.50, 'lng': 106.51},
    '重庆沙坪坝': {'province': '重庆市', 'city': '重庆市', 'district': '沙坪坝区', 'lat': 29.54, 'lng': 106.46},
}

def main():
    config_path = '/home/flask_app/device_config.json'
    
    # 读取现有配置
    with open(config_path) as f:
        cfg = json.load(f)
    
    devices = cfg.get('devices', [])
    existing_codes = {d['code'] for d in devices}
    
    count = 0
    for city_name, profile in CITY_PROFILES.items():
        for i in (1, 2):
            code = f"SIM_{city_name}_{i}"
            if code in existing_codes:
                print(f" 跳过 {code}（已存在）")
                continue
            devices.append({
                'code': code,
                'name': city_name,
                'province': profile['province'],
                'city': profile['city'],
                'district': profile['district'],
                'latitude': profile['lat'],
                'longitude': profile['lng']
            })
            count += 1
            print(f"  + {code} ({profile['province']} {profile['city']} {profile['district']})")
    
    cfg['devices'] = devices
    with open(config_path, 'w') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成！新增 {count} 个设备，共 {len(devices)} 个设备")
    print(f"\nMini-program 可绑定的新设备 ID：")
    for city_name, profile in list(CITY_PROFILES.items())[:5]:
        print(f"  SIM_{city_name}_1, SIM_{city_name}_2")
    print(f"  ... 共 {len(CITY_PROFILES) * 2} 个设备")

if __name__ == '__main__':
    main()
