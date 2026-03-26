import pandas as pd
import numpy as np
import os
import json
import time
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import queue
import logging

# 配置日志文件
logging.basicConfig(
    filename='air_quality_simulator.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 宏定义：模拟程序数量
SIMULATOR_COUNT = 10  # 可以修改此值来更改模拟程序数量

class BackgroundSimulator:
    """后台模拟类，负责实际的数据生成"""
    def __init__(self, simulator_id, mean_vec, cov_mat, cols, output_file):
        self.simulator_id = simulator_id
        self.mean_vec = mean_vec
        self.cov_mat = cov_mat
        self.cols = cols
        self.output_file = output_file
        
        # 数据存储
        self.simulated_data = []
        self.timestamps = []
        
        # 控制变量
        self.running = False
        self.frequency = 1000  # 默认1秒生成一次数据（毫秒）
        
        # 数据队列，用于向GUI传递数据
        self.data_queue = queue.Queue()
        
        # 线程
        self.thread = None
    
    def start(self, frequency=1000):
        """开始生成数据"""
        self.running = True
        self.frequency = frequency
        
        # 启动数据生成线程
        self.thread = threading.Thread(target=self.generate_data)
        self.thread.daemon = True
        self.thread.start()
        
        message = f"模拟器 {self.simulator_id} 已启动，频率：{self.frequency}ms"
        print(message)
        logging.info(message)
    
    def stop(self):
        """停止生成数据"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        message = f"模拟器 {self.simulator_id} 已停止"
        print(message)
        logging.info(message)
    
    def generate_data(self):
        """生成数据的线程函数"""
        logging.info(f"模拟器 {self.simulator_id} 开始生成数据")
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
                self.timestamps.append(timestamp)
                self.simulated_data.append(data_point.tolist())
                
                # 限制数据量，保持最新的100条
                if len(self.simulated_data) > 100:
                    self.simulated_data.pop(0)
                    self.timestamps.pop(0)
                
                # 输出到JSON文件
                self.save_to_json()
                
                # 向GUI传递数据
                self.data_queue.put((timestamp, data_point.tolist()))
                
                # 每10次生成记录一次日志
                if len(self.simulated_data) % 10 == 0:
                    logging.info(f"模拟器 {self.simulator_id} 正常生成数据，已生成 {len(self.simulated_data)} 条")
                
                # 等待指定时间
                time.sleep(self.frequency / 1000)
            except Exception as e:
                error_message = f"模拟器 {self.simulator_id} 生成数据时出错：{e}"
                print(error_message)
                logging.error(error_message)
                time.sleep(1)
        logging.info(f"模拟器 {self.simulator_id} 停止生成数据")
    
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
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            # 每20次保存记录一次日志
            if len(self.simulated_data) % 20 == 0:
                logging.info(f"模拟器 {self.simulator_id} 数据已保存到 {self.output_file}")
        except Exception as e:
            error_message = f"模拟器 {self.simulator_id} 保存JSON文件时出错：{e}"
            print(error_message)
            logging.error(error_message)

class AirQualitySimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("空气质量数据模拟器")
        self.root.geometry("1200x800")
        
        # 记录程序开始时间
        self.start_time = time.time()
        logging.info("空气质量数据模拟器启动")
        
        # 读取数据并计算统计量
        try:
            self.input_file = "重庆市2025空气日报汇总.xlsx"
            self.df = pd.read_excel(self.input_file)
            self.cols = ['AQI', 'PM₂.₅', 'NO₂', 'SO₂', 'O₃']
            self.data = self.df[self.cols]
            self.mean_vec = self.data.mean()
            self.cov_mat = self.data.cov()
            logging.info(f"成功读取Excel文件并计算统计量，指标列：{self.cols}")
        except Exception as e:
            logging.error(f"读取Excel文件时出错：{e}")
            raise
        
        # 存储所有模拟器实例
        self.simulators = []
        
        # 控制变量
        self.running = False
        self.frequency = 1000  # 默认1秒生成一次数据（毫秒）
        
        # 创建GUI界面
        self.create_widgets()
        
        # 初始化图表
        self.init_plot()
        
        # 初始化模拟器实例
        self.init_simulators()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def init_simulators(self):
        """初始化模拟器实例"""
        for i in range(SIMULATOR_COUNT):
            output_file = f'simulated_air_data_{i+1}.json'
            simulator = BackgroundSimulator(
                simulator_id=i+1,
                mean_vec=self.mean_vec,
                cov_mat=self.cov_mat,
                cols=self.cols,
                output_file=output_file
            )
            self.simulators.append(simulator)
        print(f"已初始化 {SIMULATOR_COUNT} 个模拟器实例")
    
    def create_widgets(self):
        # 控制面板
        control_frame = ttk.LabelFrame(self.root, text="控制面板")
        control_frame.pack(padx=10, pady=10, fill="x")
        
        # 频率调整
        ttk.Label(control_frame, text="生成频率（毫秒）：").grid(row=0, column=0, padx=5, pady=5)
        self.freq_var = tk.StringVar(value="1000")
        freq_entry = ttk.Entry(control_frame, textvariable=self.freq_var, width=10)
        freq_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 开始按钮
        self.start_btn = ttk.Button(control_frame, text="开始生成", command=self.start_generation)
        self.start_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 结束按钮
        self.stop_btn = ttk.Button(control_frame, text="结束生成", command=self.stop_generation, state="disabled")
        self.stop_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # 模拟器数量显示
        ttk.Label(control_frame, text=f"模拟器数量：{SIMULATOR_COUNT}").grid(row=0, column=4, padx=5, pady=5)
        
        # 数据显示区域
        data_frame = ttk.LabelFrame(self.root, text="实时数据")
        data_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # 表格
        self.tree = ttk.Treeview(data_frame)
        self.tree["columns"] = ("simulator", "timestamp", "AQI", "PM₂.₅", "NO₂", "SO₂", "O₃")
        
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # 图表区域
        chart_frame = ttk.LabelFrame(self.root, text="数据趋势")
        chart_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(12, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def init_plot(self):
        self.lines = {}
        colors = ['blue', 'green', 'red', 'purple', 'orange']
        for i, col in enumerate(self.cols):
            line, = self.ax.plot([], [], label=col, color=colors[i % len(colors)])
            self.lines[col] = line
        self.ax.legend()
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('数值')
        self.ax.set_title('空气质量数据趋势')
    
    def start_generation(self):
        if not self.running:
            # 更新频率
            try:
                self.frequency = int(self.freq_var.get())
            except ValueError:
                self.frequency = 1000
            
            self.running = True
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            
            # 启动所有模拟器实例
            logging.info(f"开始生成数据，频率：{self.frequency}ms，模拟器数量：{SIMULATOR_COUNT}")
            for simulator in self.simulators:
                simulator.start(self.frequency)
            
            # 启动数据监听线程
            self.monitor_thread = threading.Thread(target=self.monitor_data)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logging.info("数据监听线程已启动")
    
    def stop_generation(self):
        self.running = False
        
        # 停止所有模拟器实例
        logging.info("停止生成数据")
        for simulator in self.simulators:
            simulator.stop()
        
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        logging.info("所有模拟器已停止")
    
    def on_closing(self):
        """处理窗口关闭事件"""
        if self.running:
            self.stop_generation()
        
        # 计算运行时间
        run_time = time.time() - self.start_time
        logging.info(f"空气质量数据模拟器关闭，运行时间：{run_time:.2f}秒")
        
        self.root.destroy()
    
    def monitor_data(self):
        """监听所有模拟器的数据"""
        while self.running:
            for i, simulator in enumerate(self.simulators):
                try:
                    # 尝试从队列获取数据
                    timestamp, data_point = simulator.data_queue.get(block=False)
                    # 更新GUI
                    self.update_gui(i+1, timestamp, data_point)
                except queue.Empty:
                    # 队列为空，继续检查下一个模拟器
                    continue
                except Exception as e:
                    print(f"监听数据时出错：{e}")
            # 短暂休眠，避免占用过多CPU
            time.sleep(0.1)
    
    def update_gui(self, simulator_id, timestamp, data_point):
        # 更新表格
        self.root.after(0, self._update_tree, simulator_id, timestamp, data_point)
        
        # 更新图表
        self.root.after(0, self._update_plot)
    
    def _update_tree(self, simulator_id, timestamp, data_point):
        # 插入新数据
        values = [simulator_id, timestamp] + data_point
        self.tree.insert("", "end", values=values)
        
        # 保持表格行数限制
        if len(self.tree.get_children()) > 100:
            self.tree.delete(self.tree.get_children()[0])
    
    def _update_plot(self):
        # 清空图表
        self.ax.clear()
        
        # 为每个模拟器绘制数据
        colors = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        for i, simulator in enumerate(self.simulators):
            if simulator.simulated_data:
                # 为每个指标绘制一条线
                for j, col in enumerate(self.cols):
                    color = colors[(i * len(self.cols) + j) % len(colors)]
                    data = [point[j] for point in simulator.simulated_data]
                    self.ax.plot(range(len(data)), data, label=f'Sim{i+1}_{col}', color=color, alpha=0.7)
        
        self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('数值')
        self.ax.set_title('空气质量数据趋势（多模拟器）')
        
        # 调整布局
        self.fig.tight_layout()
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = AirQualitySimulator(root)
    root.mainloop()