"""
空气质量数据模拟器 — 轮播模式 + 地理位置标签 + 用户标签

支持两种模式：
1. 单点模式：模拟一个固定位置的设备（原有功能）
2. 轮播模式：依次模拟多个城市的设备，每个城市运行一段时间后切换

用法示例：
  # 单点模式（模拟重庆渝中区的一个设备）
  python air_detector.py --api-endpoint https://47.109.191.13/api/air-quality --api-header X-API-Key=111

  # 轮播模式（依次模拟全国多个城市，每个城市30分钟）
  python air_detector.py --mode rotate --rotate-minutes 30 --api-endpoint https://47.109.191.13/api/air-quality --api-header X-API-Key=111

  # 轮播模式但只模拟部分城市
  python air_detector.py --mode rotate --cities 北京,上海,广州,深圳 --rotate-minutes 15 --api-endpoint https://47.109.191.13/api/air-quality --api-header X-API-Key=111
"""

import pandas as pd
import numpy as np
import os
import json
import time
import argparse
import threading
import queue
import requests
import socket
import urllib3
import hashlib
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import redis
except ImportError:
    redis = None

DATA_GENERATION_INTERVAL = 5000  # 默认5秒

# ============================================================
#  全国城市配置 — 每个城市有不同的 AQI 基准和特征
# ============================================================
CITY_PROFILES = {
    # 华北
    '北京': {'province': '北京市', 'city': '北京市', 'district': '朝阳区', 'lat': 39.92, 'lng': 116.46,
            'aqi_base': 75, 'pm25_base': 40, 'no2_base': 35, 'so2_base': 10, 'o3_base': 45, 'industry': '办公'},
    '天津': {'province': '天津市', 'city': '天津市', 'district': '滨海新区', 'lat': 39.08, 'lng': 117.20,
            'aqi_base': 70, 'pm25_base': 38, 'no2_base': 32, 'so2_base': 9, 'o3_base': 42, 'industry': '办公'},
    '石家庄': {'province': '河北省', 'city': '石家庄市', 'district': '长安区', 'lat': 38.04, 'lng': 114.51,
              'aqi_base': 85, 'pm25_base': 48, 'no2_base': 38, 'so2_base': 12, 'o3_base': 40, 'industry': '工厂'},
    '太原': {'province': '山西省', 'city': '太原市', 'district': '迎泽区', 'lat': 37.87, 'lng': 112.55,
            'aqi_base': 80, 'pm25_base': 45, 'no2_base': 36, 'so2_base': 11, 'o3_base': 38, 'industry': '工厂'},
    # 华东
    '上海': {'province': '上海市', 'city': '上海市', 'district': '浦东新区', 'lat': 31.23, 'lng': 121.47,
            'aqi_base': 55, 'pm25_base': 28, 'no2_base': 25, 'so2_base': 6, 'o3_base': 40, 'industry': '办公'},
    '南京': {'province': '江苏省', 'city': '南京市', 'district': '鼓楼区', 'lat': 32.06, 'lng': 118.80,
            'aqi_base': 60, 'pm25_base': 32, 'no2_base': 28, 'so2_base': 7, 'o3_base': 42, 'industry': '办公'},
    '杭州': {'province': '浙江省', 'city': '杭州市', 'district': '西湖区', 'lat': 30.27, 'lng': 120.15,
            'aqi_base': 50, 'pm25_base': 25, 'no2_base': 22, 'so2_base': 6, 'o3_base': 45, 'industry': '办公'},
    '合肥': {'province': '安徽省', 'city': '合肥市', 'district': '蜀山区', 'lat': 31.82, 'lng': 117.23,
            'aqi_base': 62, 'pm25_base': 33, 'no2_base': 26, 'so2_base': 7, 'o3_base': 40, 'industry': '办公'},
    '福州': {'province': '福建省', 'city': '福州市', 'district': '鼓楼区', 'lat': 26.07, 'lng': 119.30,
            'aqi_base': 40, 'pm25_base': 20, 'no2_base': 18, 'so2_base': 5, 'o3_base': 50, 'industry': '办公'},
    '济南': {'province': '山东省', 'city': '济南市', 'district': '历下区', 'lat': 36.65, 'lng': 117.00,
            'aqi_base': 68, 'pm25_base': 36, 'no2_base': 30, 'so2_base': 8, 'o3_base': 44, 'industry': '办公'},
    # 华南
    '广州': {'province': '广东省', 'city': '广州市', 'district': '天河区', 'lat': 23.13, 'lng': 113.26,
            'aqi_base': 48, 'pm25_base': 24, 'no2_base': 22, 'so2_base': 6, 'o3_base': 52, 'industry': '办公'},
    '深圳': {'province': '广东省', 'city': '深圳市', 'district': '南山区', 'lat': 22.54, 'lng': 113.95,
            'aqi_base': 42, 'pm25_base': 22, 'no2_base': 20, 'so2_base': 5, 'o3_base': 50, 'industry': '办公'},
    '南宁': {'province': '广西', 'city': '南宁市', 'district': '青秀区', 'lat': 22.82, 'lng': 108.32,
            'aqi_base': 45, 'pm25_base': 23, 'no2_base': 20, 'so2_base': 5, 'o3_base': 48, 'industry': '办公'},
    '海口': {'province': '海南省', 'city': '海口市', 'district': '美兰区', 'lat': 20.02, 'lng': 110.35,
            'aqi_base': 32, 'pm25_base': 16, 'no2_base': 14, 'so2_base': 4, 'o3_base': 55, 'industry': '酒店'},
    # 华中
    '武汉': {'province': '湖北省', 'city': '武汉市', 'district': '武昌区', 'lat': 30.56, 'lng': 114.34,
            'aqi_base': 62, 'pm25_base': 33, 'no2_base': 27, 'so2_base': 7, 'o3_base': 42, 'industry': '办公'},
    '长沙': {'province': '湖南省', 'city': '长沙市', 'district': '岳麓区', 'lat': 28.23, 'lng': 112.94,
            'aqi_base': 58, 'pm25_base': 30, 'no2_base': 25, 'so2_base': 7, 'o3_base': 42, 'industry': '办公'},
    '郑州': {'province': '河南省', 'city': '郑州市', 'district': '金水区', 'lat': 34.75, 'lng': 113.65,
            'aqi_base': 72, 'pm25_base': 38, 'no2_base': 30, 'so2_base': 9, 'o3_base': 44, 'industry': '办公'},
    # 西南
    '重庆': {'province': '重庆市', 'city': '重庆市', 'district': '渝中区', 'lat': 29.56, 'lng': 106.55,
            'aqi_base': 65, 'pm25_base': 34, 'no2_base': 28, 'so2_base': 8, 'o3_base': 44, 'industry': '办公'},
    '成都': {'province': '四川省', 'city': '成都市', 'district': '武侯区', 'lat': 30.57, 'lng': 104.07,
            'aqi_base': 72, 'pm25_base': 38, 'no2_base': 30, 'so2_base': 9, 'o3_base': 46, 'industry': '办公'},
    '贵阳': {'province': '贵州省', 'city': '贵阳市', 'district': '观山湖区', 'lat': 26.65, 'lng': 106.63,
            'aqi_base': 48, 'pm25_base': 25, 'no2_base': 22, 'so2_base': 5, 'o3_base': 40, 'industry': '办公'},
    '昆明': {'province': '云南省', 'city': '昆明市', 'district': '盘龙区', 'lat': 25.04, 'lng': 102.68,
            'aqi_base': 38, 'pm25_base': 20, 'no2_base': 18, 'so2_base': 5, 'o3_base': 50, 'industry': '酒店'},
    # 西北
    '西安': {'province': '陕西省', 'city': '西安市', 'district': '雁塔区', 'lat': 34.26, 'lng': 108.94,
            'aqi_base': 78, 'pm25_base': 42, 'no2_base': 34, 'so2_base': 11, 'o3_base': 40, 'industry': '办公'},
    '兰州': {'province': '甘肃省', 'city': '兰州市', 'district': '城关区', 'lat': 36.06, 'lng': 103.83,
            'aqi_base': 80, 'pm25_base': 44, 'no2_base': 35, 'so2_base': 11, 'o3_base': 38, 'industry': '工厂'},
    '乌鲁木齐': {'province': '新疆', 'city': '乌鲁木齐市', 'district': '天山区', 'lat': 43.83, 'lng': 87.62,
               'aqi_base': 82, 'pm25_base': 45, 'no2_base': 35, 'so2_base': 12, 'o3_base': 38, 'industry': '工厂'},
    # 东北
    '沈阳': {'province': '辽宁省', 'city': '沈阳市', 'district': '和平区', 'lat': 41.80, 'lng': 123.43,
            'aqi_base': 70, 'pm25_base': 38, 'no2_base': 32, 'so2_base': 10, 'o3_base': 42, 'industry': '工厂'},
    '长春': {'province': '吉林省', 'city': '长春市', 'district': '南关区', 'lat': 43.88, 'lng': 125.35,
            'aqi_base': 68, 'pm25_base': 36, 'no2_base': 30, 'so2_base': 9, 'o3_base': 42, 'industry': '办公'},
    '哈尔滨': {'province': '黑龙江省', 'city': '哈尔滨市', 'district': '南岗区', 'lat': 45.75, 'lng': 126.65,
              'aqi_base': 72, 'pm25_base': 40, 'no2_base': 32, 'so2_base': 10, 'o3_base': 40, 'industry': '办公'},
}

# 模拟用户名池
USER_POOL = [
    '张先生', '李女士', '王经理', '赵主任', '刘工程师',
    '陈医生', '杨老师', '黄主管', '周总监', '吴校长',
    '郑院长', '孙经理', '马主任', '朱工程师', '胡主管',
    '林女士', '何先生', '高经理', '罗主任', '梁工程师',
]


class AirQualitySimulator:
    def __init__(self, city_profile, output_file, frequency=DATA_GENERATION_INTERVAL,
                 max_records=100, api_endpoint=None, api_headers=None,
                 device_prefix='AQ', user_name=None):
        self.profile = city_profile
        self.output_file = output_file
        self.frequency = frequency
        self.max_records = max_records
        self.api_endpoint = api_endpoint
        self.api_headers = api_headers or {}

        self.cols = ['AQI', 'PM₂.₅', 'NO₂', 'SO₂', 'O₃']

        # 基于城市配置生成均值和协方差
        self.mean_vec = pd.Series([
            city_profile['aqi_base'],
            city_profile['pm25_base'],
            city_profile['no2_base'],
            city_profile['so2_base'],
            city_profile['o3_base']
        ], index=self.cols)
        self.cov_mat = pd.DataFrame(np.eye(5) * 5, index=self.cols, columns=self.cols)

        self.current_values = self.mean_vec.values + np.random.normal(0, 3, size=len(self.cols))

        self.alert_event_active = False
        self.alert_countdown = 0
        self.alert_direction = 1

        self.simulated_data = []
        self.timestamps = []
        self.data_queue = queue.Queue()
        self.running = False
        self.save_running = False
        self.heartbeat_running = False
        self.data_sent = 0
        self.data_sent_lock = threading.Lock()

        self.simulator_id = f"{device_prefix}_{city_profile['city']}_{random.randint(100, 999)}"
        self.user_name = user_name or random.choice(USER_POOL)

        self.redis_client = None
        self.redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))

    def start(self):
        self.running = True
        self.save_running = True
        self.heartbeat_running = True

        threading.Thread(target=self.generate_data, daemon=True).start()
        threading.Thread(target=self.save_data, daemon=True).start()
        threading.Thread(target=self.heartbeat_report, daemon=True).start()

        print(f"✅ 开始模拟 [{self.profile['province']} {self.profile['city']} {self.profile['district']}]")
        print(f"   设备ID: {self.simulator_id} | 用户: {self.user_name}")
        print(f"   AQI基准: {self.profile['aqi_base']} | 频率: {self.frequency}ms")

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        self.save_running = False
        self.heartbeat_running = False
        self.update_heartbeat_status("stopped")
        print("模拟器已停止")

    def generate_data(self):
        while self.running:
            try:
                revert_strength = 0.03
                for i in range(len(self.cols)):
                    self.current_values[i] += (self.mean_vec.values[i] - self.current_values[i]) * revert_strength

                delta = np.random.multivariate_normal(np.zeros(len(self.cols)), self.cov_mat.values * 0.02)
                self.current_values += delta

                if not self.alert_event_active and np.random.random() < 0.015:
                    self.alert_event_active = True
                    self.alert_countdown = np.random.randint(5, 10)
                    self.alert_direction = 1

                if self.alert_event_active:
                    if self.alert_direction == 1:
                        spike = np.array([np.random.uniform(5, 12), np.random.uniform(4, 8),
                                          np.random.uniform(3, 6), np.random.uniform(1, 3), np.random.uniform(2, 5)])
                        self.current_values += spike
                        if self.alert_countdown <= self.alert_countdown // 2:
                            self.alert_direction = -1
                    else:
                        for i in range(len(self.cols)):
                            target = self.mean_vec.values[i]
                            self.current_values[i] += (target - self.current_values[i]) * 0.3
                            self.current_values[i] += np.random.normal(0, 0.5)
                    self.alert_countdown -= 1
                    if self.alert_countdown <= 0:
                        self.alert_event_active = False

                bounds = {'AQI': (10, 250), 'PM₂.₅': (3, 150), 'NO₂': (3, 80), 'SO₂': (1, 40), 'O₃': (3, 100)}
                for i, col in enumerate(self.cols):
                    lo, hi = bounds.get(col, (0, 999))
                    self.current_values[i] = np.clip(self.current_values[i], lo, hi)

                data_point = self.current_values.copy()
                timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')

                with threading.Lock():
                    self.timestamps.append(timestamp)
                    self.simulated_data.append(data_point.tolist())
                    if len(self.simulated_data) > self.max_records:
                        self.simulated_data.pop(0)
                        self.timestamps.pop(0)

                self.data_queue.put(True)
                print(f"[{timestamp}] {self.profile['city']}/{self.profile['district']} | AQI: {data_point[0]:.1f} PM2.5: {data_point[1]:.1f}")
                time.sleep(self.frequency / 1000)
            except Exception as e:
                print(f"生成数据出错: {e}")
                time.sleep(1)

    def save_data(self):
        while self.save_running:
            try:
                self.data_queue.get(block=True, timeout=1)
                self.send_http_request()
                self.data_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"保存数据出错: {e}")
                time.sleep(1)

    def send_http_request(self):
        if not self.api_endpoint:
            return
        with threading.Lock():
            if not self.timestamps or not self.simulated_data:
                return
            latest_timestamp = self.timestamps[-1]
            latest_data = self.simulated_data[-1]

        # 构建带标签的 payload
        payload = {
            "device_id": self.simulator_id,
            "timestamp": latest_timestamp,
            "data": {},
            # --- 地理位置标签 ---
            "location": {
                "province": self.profile['province'],
                "city": self.profile['city'],
                "district": self.profile['district'],
                "latitude": self.profile['lat'],
                "longitude": self.profile['lng']
            },
            # --- 用户标签 ---
            "user": {
                "name": self.user_name,
                "industry": self.profile.get('industry', '办公')
            }
        }
        for i, col in enumerate(self.cols):
            payload["data"][col] = round(latest_data[i], 2)

        payload_str = json.dumps(payload, sort_keys=True)
        md5_hash = hashlib.md5(payload_str.encode('utf-8')).hexdigest()

        headers_with_md5 = self.api_headers.copy()
        headers_with_md5['X-Content-MD5'] = md5_hash

        success = self._send_with_retry(payload, headers_with_md5)
        if success:
            with self.data_sent_lock:
                self.data_sent += 1

    def _send_with_retry(self, payload, headers=None, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_endpoint, json=payload, headers=headers or self.api_headers,
                                         timeout=10, verify=False)
                if response.status_code in [200, 201, 202]:
                    return True
            except Exception:
                pass
            if attempt < max_retries - 1:
                time.sleep(1 + attempt)
        return False

    def init_redis(self):
        if not redis:
            return False
        try:
            if not self.redis_client:
                self.redis_client = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
                self.redis_client.ping()
                return True
            return True
        except Exception:
            self.redis_client = None
            return False

    def update_heartbeat_status(self, status):
        if self.init_redis():
            try:
                key = f"simulator:heartbeat:{self.simulator_id}"
                self.redis_client.hset(key, mapping={
                    'status': status,
                    'last_update': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'data_sent': str(self.data_sent),
                    'city': self.profile['city'],
                    'district': self.profile['district'],
                    'user': self.user_name
                })
                self.redis_client.expire(key, 60)
            except Exception:
                pass

    def heartbeat_report(self):
        while self.heartbeat_running:
            self.update_heartbeat_status("online")
            time.sleep(15)


def run_rotate_mode(api_endpoint, api_headers, rotate_minutes, frequency, city_names=None):
    """轮播模式：依次模拟多个城市"""
    available = list(CITY_PROFILES.keys())
    if city_names:
        available = [c for c in city_names if c in CITY_PROFILES]
    if not available:
        available = list(CITY_PROFILES.keys())

    print(f"🔄 轮播模式启动，共 {len(available)} 个城市，每个城市 {rotate_minutes} 分钟")
    print(f"   城市列表: {', '.join(available)}")
    print(f"   总时长: {len(available) * rotate_minutes} 分钟")
    print()

    city_index = 0
    while True:
        city_name = available[city_index % len(available)]
        profile = CITY_PROFILES[city_name]
        user_name = random.choice(USER_POOL)

        print(f"\n{'='*60}")
        print(f"🏙️  切换到: {profile['province']} {profile['city']} {profile['district']}")
        print(f"   用户: {user_name} | 行业: {profile.get('industry', '办公')}")
        print(f"   运行时间: {rotate_minutes} 分钟")
        print(f"{'='*60}\n")

        simulator = AirQualitySimulator(
            city_profile=profile,
            output_file=f'data_{city_name}.json',
            frequency=frequency,
            api_endpoint=api_endpoint,
            api_headers=api_headers,
            user_name=user_name
        )

        # 启动模拟器（在子线程中运行）
        sim_thread = threading.Thread(target=simulator.start, daemon=True)
        sim_thread.start()

        # 运行指定时间
        try:
            time.sleep(rotate_minutes * 60)
        except KeyboardInterrupt:
            print("\n轮播模式停止")
            simulator.stop()
            return

        simulator.stop()
        print(f"\n✅ {city_name} 模拟完成，已发送 {simulator.data_sent} 条数据\n")
        city_index += 1


def main():
    parser = argparse.ArgumentParser(description='空气质量数据模拟器（支持轮播模式）')
    parser.add_argument('--mode', choices=['single', 'rotate'], default='single', help='运行模式')
    parser.add_argument('--city', default='重庆', help='单点模式：城市名')
    parser.add_argument('--cities', default='', help='轮播模式：城市列表，逗号分隔（留空=全部）')
    parser.add_argument('--rotate-minutes', type=int, default=30, help='轮播模式：每个城市运行分钟数')
    parser.add_argument('--frequency', type=int, default=DATA_GENERATION_INTERVAL, help='数据生成频率(ms)')
    parser.add_argument('--output', default='air_quality_data.json', help='输出文件')
    parser.add_argument('--max-records', type=int, default=100, help='最大记录数')
    parser.add_argument('--api-endpoint', default='', help='API端点URL')
    parser.add_argument('--api-header', action='append', help='API请求头 key=value')

    args = parser.parse_args()

    api_headers = {}
    if args.api_header:
        for header in args.api_header:
            key, value = header.split('=', 1)
            api_headers[key.strip()] = value.strip()

    if args.mode == 'rotate':
        city_names = [c.strip() for c in args.cities.split(',') if c.strip()] if args.cities else None
        run_rotate_mode(args.api_endpoint, api_headers, args.rotate_minutes, args.frequency, city_names)
    else:
        if args.city not in CITY_PROFILES:
            print(f"未知城市: {args.city}，可选: {', '.join(CITY_PROFILES.keys())}")
            return
        simulator = AirQualitySimulator(
            city_profile=CITY_PROFILES[args.city],
            output_file=args.output,
            frequency=args.frequency,
            max_records=args.max_records,
            api_endpoint=args.api_endpoint,
            api_headers=api_headers
        )
        try:
            simulator.start()
        except KeyboardInterrupt:
            simulator.stop()


if __name__ == '__main__':
    main()
