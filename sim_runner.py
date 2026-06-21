"""
空气质量模拟器 — 本地版（型号驱动）
- 读取 sim_config.json（设备型号 + 设备列表 + 服务器配置）
- 每台设备按其型号的参数范围生成数据
- 命令行参数可覆盖配置
"""
import json, time, hashlib, random, sys, os, argparse, requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    '重庆大渡口': ('重庆市','重庆市','大渡口区'), '重庆巴南': ('重庆市','重庆市','巴南区'),
    '重庆北碚': ('重庆市','重庆市','北碚区'),
}

SENSOR_FIELD_MAP = {
    'AQI':   'AQI',
    'PM2.5': 'PM₂.₅',
    'PM10':  'PM₁₀',
    'NO2':   'NO₂',
    'SO2':   'SO₂',
    'O3':    'O₃',
    'CO':    'CO',
}

DEFAULT_CONFIG = {
    "server": {
        "url": "https://47.109.191.13/api/air-quality",
        "api_key": "111",
        "verify_ssl": False,
        "timeout": 5
    },
    "device_models": {},
    "devices": [],
    "interval_seconds": 10,
    "max_rounds": 0,
    "show_per_device": True,
    "show_round_summary": True,
    "aqi_offset": 0,
    "model_filter": "",
    "city_filter": "",
}


def load_config(path):
    if not os.path.exists(path):
        print(f'找不到配置文件 {path}')
        print('请用 --init 生成示例配置，或使用 --list-models / --example 命令')
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_args(cfg, args):
    if args.url: cfg['server']['url'] = args.url
    if args.api_key: cfg['server']['api_key'] = args.api_key
    if args.interval is not None: cfg['interval_seconds'] = args.interval
    if args.rounds is not None: cfg['max_rounds'] = args.rounds
    if args.aqi_offset is not None: cfg['aqi_offset'] = args.aqi_offset
    if args.model: cfg['model_filter'] = args.model
    if args.city: cfg['city_filter'] = args.city
    if args.no_per_device: cfg['show_per_device'] = False
    if args.no_summary: cfg['show_round_summary'] = False
    return cfg


def filter_devices(devices, model_filter, city_filter):
    out = []
    for d in devices:
        if model_filter and d.get('model') != model_filter:
            continue
        if city_filter and city_filter not in d.get('city', ''):
            continue
        out.append(d)
    return out


def gen_value(rng, jitter, offset=0):
    lo, hi = rng
    base = random.uniform(lo, hi)
    base += offset
    if jitter:
        base += random.uniform(-jitter, jitter)
    return max(0, round(base, 1))


def build_data(model, aqi_offset):
    data = {}
    jitter = model.get('jitter', 15)
    for sensor, rng in model.get('ranges', {}).items():
        offset = aqi_offset if sensor == 'AQI' else 0
        value = gen_value(rng, jitter, offset)
        data[SENSOR_FIELD_MAP.get(sensor, sensor)] = value
    return data


def send_one(session, server, device_id, city, data):
    loc = CITY_LOC.get(city, ('', '', ''))
    payload = {
        "device_id": device_id,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "data": data,
        "location": {"province": loc[0], "city": loc[1], "district": loc[2]},
        "user": {"name": "演示用户", "industry": "办公"}
    }
    md5 = hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    headers = {
        'X-API-Key': server['api_key'],
        'X-Content-MD5': md5,
        'Content-Type': 'application/json',
    }
    r = session.post(server['url'], json=payload, headers=headers,
                     timeout=server.get('timeout', 5), verify=server.get('verify_ssl', False))
    return r.status_code, md5, payload


def cmd_list_models(cfg):
    print('设备型号：')
    for name, m in cfg.get('device_models', {}).items():
        sensors = ', '.join(m.get('sensors', []))
        print(f'  · {name:24s} {m.get("description", ""):30s}  [{sensors}]')
    print(f'\n设备总数：{len(cfg.get("devices", []))}')
    cities = {d.get("city") for d in cfg.get("devices", [])}
    print(f'城市数：{len(cities)}')


def main():
    parser = argparse.ArgumentParser(description='本地空气质量模拟器（型号驱动）')
    parser.add_argument('--config', default='sim_config.json', help='配置文件路径')
    parser.add_argument('--url', help='API 地址')
    parser.add_argument('--api-key', help='API Key')
    parser.add_argument('--interval', type=int, help='每轮间隔秒数')
    parser.add_argument('--rounds', type=int, help='最大轮数（0=无限）')
    parser.add_argument('--aqi-offset', type=int, help='AQI 偏移量（演示污染用）')
    parser.add_argument('--model', help='只跑指定型号的设备，如 AQ-Pro-2000')
    parser.add_argument('--city', help='只跑指定城市的设备（包含匹配），如 重庆')
    parser.add_argument('--no-per-device', action='store_true')
    parser.add_argument('--no-summary', action='store_true')
    parser.add_argument('--list-models', action='store_true', help='列出所有型号和设备并退出')
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.list_models:
        cmd_list_models(cfg)
        return

    cfg = merge_args(cfg, args)
    models = cfg.get('device_models', {})
    devices = cfg.get('devices', [])

    if not models or not devices:
        print('配置中缺少 device_models 或 devices 字段')
        return

    filtered = filter_devices(devices, cfg.get('model_filter', ''), cfg.get('city_filter', ''))
    if not filtered:
        print('筛选后没有设备')
        return

    print('=' * 70)
    print(f'  设备数: {len(filtered)}    型号数: {len(set(d["model"] for d in filtered))}')
    print(f'  服务器: {cfg["server"]["url"]}')
    print(f'  间隔:   {cfg["interval_seconds"]}s    最大轮次: {cfg["max_rounds"] or "无限"}')
    if cfg.get('aqi_offset'):
        print(f'  AQI 偏移: {cfg["aqi_offset"]:+d}')
    if cfg.get('model_filter'):
        print(f'  筛选型号: {cfg["model_filter"]}')
    if cfg.get('city_filter'):
        print(f'  筛选城市: {cfg["city_filter"]}')
    print('=' * 70)
    print('按 Ctrl+C 停止\n')

    session = requests.Session()
    session.headers.update({'User-Agent': 'sim-runner/3.0'})

    round_no = 0
    try:
        while True:
            round_no += 1
            ok = fail = 0
            for d in filtered:
                model = models.get(d['model'])
                if not model:
                    fail += 1
                    continue
                data = build_data(model, cfg.get('aqi_offset', 0))
                try:
                    code, md5, payload = send_one(session, cfg['server'], d['id'], d.get('city', ''), data)
                    if cfg['show_per_device']:
                        aqi = data.get('AQI', '--')
                        pm25 = data.get('PM₂.₅', '--')
                        mark = 'OK' if code == 200 else f'ERR{code}'
                        print(f"[{d['id']:12s}] {d['model']:22s} AQI={aqi:>5} PM2.5={pm25:>5} → {mark}  MD5={md5[:16]}...")
                    if code == 200: ok += 1
                    else: fail += 1
                except Exception as e:
                    fail += 1
                    if cfg['show_per_device']:
                        print(f"[{d['id']:12s}] 异常: {e}")

            if cfg['show_round_summary']:
                print(f'--- 第 {round_no} 轮：成功 {ok} / 失败 {fail} / 间隔 {cfg["interval_seconds"]}s ---\n')

            if cfg['max_rounds'] and round_no >= cfg['max_rounds']:
                print(f'已完成 {cfg["max_rounds"]} 轮，自动退出')
                break
            time.sleep(cfg['interval_seconds'])
    except KeyboardInterrupt:
        print('\n已停止')


if __name__ == '__main__':
    main()
