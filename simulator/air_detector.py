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

# 尝试导入 Redis 模块
try:
    import redis
except ImportError:
    print("警告: 未安装 redis 模块，心跳上报功能将不可用")
    redis = None

# 时间间隔变量（毫秒）
# 可以直接修改这个值来调整默认的生成数据时间间隔
DATA_GENERATION_INTERVAL = 1000  # 默认1秒生成一次数据

class AirQualitySimulator:
    def __init__(self, input_file, output_file, frequency=DATA_GENERATION_INTERVAL, max_records=100, api_endpoint=None, api_headers=None):
        """
        空气质量数据模拟器
        
        Args:
            input_file: 输入Excel文件路径
            output_file: 输出JSON文件路径
            frequency: 数据生成频率（毫秒）
            max_records: 保存的最大记录数
            api_endpoint: API端点URL，用于发送HTTP请求
            api_headers: API请求头
        """
        self.input_file = input_file
        self.output_file = output_file
        self.frequency = frequency
        self.max_records = max_records
        self.api_endpoint = api_endpoint
        self.api_headers = api_headers or {}
        
        # 读取数据并计算统计量
        try:
            self.df = pd.read_excel(input_file)
            self.cols = ['AQI', 'PM₂.₅', 'NO₂', 'SO₂', 'O₃']
            self.data = self.df[self.cols]
            self.mean_vec = self.data.mean()
            self.cov_mat = self.data.cov()
            print("成功读取Excel文件并计算统计量")
        except Exception as e:
            print(f"读取Excel文件时出错：{e}")
            raise
        
        # 数据存储
        self.simulated_data = []
        self.timestamps = []
        
        # 线程安全的数据队列
        self.data_queue = queue.Queue()
        
        # 控制变量
        self.running = False
        self.save_running = False
        self.heartbeat_running = False
        
        # 线程
        self.generate_thread = None
        self.save_thread = None
        self.heartbeat_thread = None
        
        # 数据发送计数器
        self.data_sent = 0
        self.data_sent_lock = threading.Lock()
        
        # 心跳相关
        self.simulator_id = os.getenv('SIMULATOR_ID', socket.gethostname() or 'unknown')
        self.redis_client = None
        # 使用 127.0.0.1 作为默认值，连接到宿主机
        self.redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
    
    def start(self):
        """开始生成数据"""
        self.running = True
        self.save_running = True
        
        # 创建并启动数据生成线程
        self.generate_thread = threading.Thread(target=self.generate_data)
        self.generate_thread.daemon = True
        self.generate_thread.start()
        
        # 创建并启动数据保存线程
        self.save_thread = threading.Thread(target=self.save_data)
        self.save_thread.daemon = True
        self.save_thread.start()
        
        # 创建并启动心跳线程
        self.heartbeat_running = True
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_report)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        print(f"开始生成空气质量数据，频率：{self.frequency}ms")
        print(f"输出文件：{self.output_file}")
        print(f"模拟器ID：{self.simulator_id}")
        print("按 Ctrl+C 停止生成")
        
        try:
            # 主线程等待
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n停止生成数据")
            self.stop()
        except Exception as e:
            print(f"运行时出错：{e}")
            self.stop()
    
    def generate_data(self):
        """数据生成线程"""
        while self.running:
            try:
                # 生成单个数据点
                data_point = np.random.multivariate_normal(self.mean_vec.values, self.cov_mat.values, size=1)[0]
                
                # 处理非负约束
                for i, col in enumerate(self.cols):
                    if col in ['PM₂.₅', 'NO₂', 'SO₂', 'O₃', 'AQI']:
                        data_point[i] = max(0, data_point[i])
                
                # 添加时间戳
                timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 存储数据
                with threading.Lock():
                    self.timestamps.append(timestamp)
                    self.simulated_data.append(data_point.tolist())
                    
                    # 限制数据量
                    if len(self.simulated_data) > self.max_records:
                        self.simulated_data.pop(0)
                        self.timestamps.pop(0)
                
                # 通知保存线程
                self.data_queue.put(True)
                
                # 打印生成的数据
                print(f"[{timestamp}] AQI: {data_point[0]:.2f}, PM₂.₅: {data_point[1]:.2f}, NO₂: {data_point[2]:.2f}, SO₂: {data_point[3]:.2f}, O₃: {data_point[4]:.2f}")
                
                # 等待指定时间
                time.sleep(self.frequency / 1000)
            except Exception as e:
                print(f"生成数据时出错：{e}")
                time.sleep(1)
    
    def save_data(self):
        """数据保存线程"""
        while self.save_running:
            try:
                # 等待数据生成
                self.data_queue.get(block=True, timeout=1)
                
                # 保存数据
                self.save_to_json()
                
                # 发送HTTP请求
                self.send_http_request()
                
                # 标记任务完成
                self.data_queue.task_done()
            except queue.Empty:
                # 超时，继续等待
                continue
            except Exception as e:
                print(f"保存数据时出错：{e}")
                time.sleep(1)
    
    def stop(self):
        """停止生成数据"""
        self.running = False
        self.save_running = False
        self.heartbeat_running = False
        
        # 等待线程结束
        if self.generate_thread:
            self.generate_thread.join(timeout=2)
        if self.save_thread:
            self.save_thread.join(timeout=2)
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        
        # 退出时更新状态
        self.update_heartbeat_status("stopped")
        
        print("所有线程已停止")
    
    def send_http_request(self):
        """发送HTTP请求"""
        if not self.api_endpoint:
            return  # 如果没有设置API端点，则不发送请求
        
        try:
            # 获取最新数据
            with threading.Lock():
                if not self.timestamps or not self.simulated_data:
                    return
                
                # 获取最新的数据点
                latest_timestamp = self.timestamps[-1]
                latest_data = self.simulated_data[-1]
            
            # 构建要发送的数据
            payload = {
                "timestamp": latest_timestamp,
                "data": {}
            }
            for i, col in enumerate(self.cols):
                payload["data"][col] = latest_data[i]
            
            # 发送POST请求
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=self.api_headers,
                timeout=10  # 设置超时时间为10秒
            )
            
            # 检查响应状态
            if response.status_code in [200, 201, 202]:
                print(f"HTTP请求发送成功，状态码：{response.status_code}")
                # 增加数据发送计数器
                with self.data_sent_lock:
                    self.data_sent += 1
            else:
                print(f"HTTP请求发送失败，状态码：{response.status_code}，响应：{response.text}")
        
        except requests.exceptions.Timeout:
            print(f"HTTP请求超时，端点：{self.api_endpoint}")
        except requests.exceptions.ConnectionError:
            print(f"连接错误，无法连接到API端点：{self.api_endpoint}")
        except requests.exceptions.RequestException as e:
            print(f"发送HTTP请求时发生错误：{e}")
        except Exception as e:
            print(f"发送HTTP请求时发生未知错误：{e}")
    
    def save_to_json(self):
        """保存数据到JSON文件"""
        try:
            # 线程安全地获取数据副本
            with threading.Lock():
                timestamps_copy = self.timestamps.copy()
                simulated_data_copy = self.simulated_data.copy()
            
            # 构建JSON数据
            json_data = []
            for i, timestamp in enumerate(timestamps_copy):
                data_dict = {"timestamp": timestamp}
                for j, col in enumerate(self.cols):
                    data_dict[col] = simulated_data_copy[i][j]
                json_data.append(data_dict)
            
            # 保存到JSON文件
            with open(self.output_file, 'w') as f:
                json.dump(json_data, f)
        except Exception as e:
            print(f"保存JSON文件时出错：{e}")
    
    def init_redis(self):
        """初始化Redis连接"""
        if not redis:
            print("Redis模块未安装，跳过Redis初始化")
            return False
        
        try:
            if not self.redis_client:
                self.redis_client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    decode_responses=True
                )
                # 测试连接
                self.redis_client.ping()
                print(f"成功连接到Redis: {self.redis_host}:{self.redis_port}")
                return True
            return True
        except Exception as e:
            print(f"连接Redis失败: {e}")
            self.redis_client = None
            return False
    
    def update_heartbeat_status(self, status):
        """更新心跳状态"""
        if not self.init_redis():
            return
        
        try:
            with self.data_sent_lock:
                data_sent = self.data_sent
            
            heartbeat_data = {
                "last_update": time.time(),
                "data_sent": data_sent,
                "status": status
            }
            
            # 将数据保存到Redis的Hash键中
            self.redis_client.hset("simulator_stats", self.simulator_id, json.dumps(heartbeat_data))
            if status == "stopped":
                print(f"更新模拟器状态为：{status}")
        except Exception as e:
            print(f"更新心跳状态失败: {e}")
    
    def heartbeat_report(self):
        """心跳上报线程"""
        while self.heartbeat_running:
            try:
                self.update_heartbeat_status("running")
                # 每5秒上报一次
                time.sleep(5)
            except Exception as e:
                print(f"心跳上报出错: {e}")
                # 出错后等待1秒再重试
                time.sleep(1)

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='空气质量数据模拟器')
    parser.add_argument('--input', default='重庆市2025空气日报汇总.xlsx', help='输入Excel文件路径')
    parser.add_argument('--output', default='simulated_air_data.json', help='输出JSON文件路径')
    parser.add_argument('--frequency', type=int, default=DATA_GENERATION_INTERVAL, help='数据生成频率（毫秒）')
    parser.add_argument('--max-records', type=int, default=100, help='保存的最大记录数')
    parser.add_argument('--api-endpoint', help='API端点URL，用于发送HTTP请求')
    parser.add_argument('--api-header', action='append', help='API请求头，格式：key=value')
    
    args = parser.parse_args()
    
    # 解析API请求头
    api_headers = {}
    if args.api_header:
        for header in args.api_header:
            key, value = header.split('=', 1)
            api_headers[key.strip()] = value.strip()
    
    # 创建模拟器实例并开始生成数据
    simulator = AirQualitySimulator(
        input_file=args.input,
        output_file=args.output,
        frequency=args.frequency,
        max_records=args.max_records,
        api_endpoint=args.api_endpoint,
        api_headers=api_headers
    )
    
    try:
        simulator.start()
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在停止...")
        simulator.stop()
    except Exception as e:
        print(f"运行时出错：{e}")
        simulator.stop()