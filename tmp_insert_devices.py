"""将 SIM_ 设备插入 MySQL devices 表"""
import json, pymysql

config_path = '/home/flask_app/device_config.json'
with open(config_path) as f:
    cfg = json.load(f)

sim_devices = [d for d in cfg.get('devices', []) if d.get('code', '').startswith('SIM_')]
print(f"找到 {len(sim_devices)} 个 SIM_ 设备")

conn = pymysql.connect(host='127.0.0.1', user='air_user', password='',
                       database='air_quality', charset='utf8mb4')
cur = conn.cursor()

inserted = 0
for d in sim_devices:
    code = d['code']
    name = d.get('name', code)
    province = d.get('province', '')
    city = d.get('city', '')
    district = d.get('district', '')
    lat = d.get('latitude')
    lng = d.get('longitude')

    cur.execute('SELECT id FROM devices WHERE device_id=%s', (code,))
    if cur.fetchone():
        print(f"  跳过 {code}（已存在）")
        continue

    cur.execute('''INSERT INTO devices
        (device_id, name, location_name, longitude, latitude, activation_status, district, province, city, status, create_time)
        VALUES (%s, %s, %s, %s, %s, 'activated', %s, %s, %s, 1, NOW())''',
        (code, name, f"{province} {city} {district}", lng, lat, district, province, city))
    inserted += 1
    print(f"  + {code} ({province} {city} {district})")

conn.commit()
cur.close()
conn.close()
print(f"\n完成！新增 {inserted} 条，跳过 {len(sim_devices) - inserted} 条")
