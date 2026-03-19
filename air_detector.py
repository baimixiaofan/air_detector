import pandas as pd
import numpy as np
import os
import json
import time
import argparse

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
        
        # 控制变量
        self.running = False
    
    def start(self):
        """开始生成数据"""
        self.running = True
        print(f"开始生成空气质量数据，频率：{self.frequency}ms")
        print(f"输出文件：{self.output_file}")
        print("按 Ctrl+C 停止生成")
        
        try:
            while self.running:
                # 生成单个数据点
                data_point = np.random.multivariate_normal(self.mean_vec.values, self.cov_mat.values, size=1)[0]
                
                # 处理非负约束
                for i, col in enumerate(self.cols):
                    if col in ['PM₂.₅', 'NO₂', 'SO₂', 'O₃', 'AQI']:
                        data_point[i] = max(0, data_point[i])
                
                # 添加时间戳
                timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 存储数据
                self.timestamps.append(timestamp)
                self.simulated_data.append(data_point.tolist())
                
                # 限制数据量
                if len(self.simulated_data) > self.max_records:
                    self.simulated_data.pop(0)
                    self.timestamps.pop(0)
                
                # 输出到JSON文件
                self.save_to_json()
                
                # 打印生成的数据
                print(f"[{timestamp}] AQI: {data_point[0]:.2f}, PM₂.₅: {data_point[1]:.2f}, NO₂: {data_point[2]:.2f}, SO₂: {data_point[3]:.2f}, O₃: {data_point[4]:.2f}")
                
                # 等待指定时间
                time.sleep(self.frequency / 1000)
        except KeyboardInterrupt:
            print("\n停止生成数据")
            self.running = False
        except Exception as e:
            print(f"生成数据时出错：{e}")
            self.running = False
    
    def stop(self):
        """停止生成数据"""
        self.running = False
    
    def save_to_json(self):
        """保存数据到JSON文件"""
        try:
            # 构建JSON数据
            json_data = []
            for i, timestamp in enumerate(self.timestamps):
                data_dict = {"timestamp": timestamp}
                for j, col in enumerate(self.cols):
                    data_dict[col] = self.simulated_data[i][j]
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
    
    simulator.start()