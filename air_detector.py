import pandas as pd
import numpy as np
import os
import json
import time
import argparse
import threading
import queue

# 时间间隔变量（毫秒）
# 可以直接修改这个值来调整默认的生成数据时间间隔
DATA_GENERATION_INTERVAL = 1000  # 默认1秒生成一次数据

class AirQualitySimulator:
    def __init__(self, input_file, output_file, frequency=DATA_GENERATION_INTERVAL, max_records=100):
        """
        空气质量数据模拟器
        
        Args:
            input_file: 输入Excel文件路径
            output_file: 输出JSON文件路径
            frequency: 数据生成频率（毫秒）
            max_records: 保存的最大记录数
        """
        self.input_file = input_file
        self.output_file = output_file
        self.frequency = frequency
        self.max_records = max_records
        
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
        
        # 线程
        self.generate_thread = None
        self.save_thread = None
    
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
        
        print(f"开始生成空气质量数据，频率：{self.frequency}ms")
        print(f"输出文件：{self.output_file}")
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
        
        # 等待线程结束
        if self.generate_thread:
            self.generate_thread.join(timeout=2)
        if self.save_thread:
            self.save_thread.join(timeout=2)
        
        print("所有线程已停止")
    
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

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='空气质量数据模拟器')
    parser.add_argument('--input', default='重庆市2025空气日报汇总.xlsx', help='输入Excel文件路径')
    parser.add_argument('--output', default='simulated_air_data.json', help='输出JSON文件路径')
    parser.add_argument('--frequency', type=int, default=DATA_GENERATION_INTERVAL, help='数据生成频率（毫秒）')
    parser.add_argument('--max-records', type=int, default=100, help='保存的最大记录数')
    
    args = parser.parse_args()
    
    # 创建模拟器实例并开始生成数据
    simulator = AirQualitySimulator(
        input_file=args.input,
        output_file=args.output,
        frequency=args.frequency,
        max_records=args.max_records
    )
    
    try:
        simulator.start()
    except KeyboardInterrupt:
        print("\n接收到中断信号，正在停止...")
        simulator.stop()
    except Exception as e:
        print(f"运行时出错：{e}")
        simulator.stop()