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

class AirQualitySimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("空气质量数据模拟器")
        self.root.geometry("1000x700")
        
        # 读取数据并计算统计量
        self.input_file = "重庆市2025空气日报汇总.xlsx"
        self.df = pd.read_excel(self.input_file)
        self.cols = ['AQI', 'PM₂.₅', 'NO₂', 'SO₂', 'O₃']
        self.data = self.df[self.cols]
        self.mean_vec = self.data.mean()
        self.cov_mat = self.data.cov()
        
        # 数据存储
        self.simulated_data = []
        self.timestamps = []
        
        # 控制变量
        self.running = False
        self.frequency = 1000  # 默认1秒生成一次数据（毫秒）
        
        # 创建GUI界面
        self.create_widgets()
        
        # 初始化图表
        self.init_plot()
    
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
        
        # 数据显示区域
        data_frame = ttk.LabelFrame(self.root, text="实时数据")
        data_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # 表格
        self.tree = ttk.Treeview(data_frame)
        self.tree["columns"] = ("timestamp", "AQI", "PM₂.₅", "NO₂", "SO₂", "O₃")
        
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # 图表区域
        chart_frame = ttk.LabelFrame(self.root, text="数据趋势")
        chart_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.fig, self.ax = plt.subplots(figsize=(10, 4))
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
            
            # 启动数据生成线程
            self.thread = threading.Thread(target=self.generate_data)
            self.thread.daemon = True
            self.thread.start()
    
    def stop_generation(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
    
    def generate_data(self):
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
            
            # 限制数据量，保持最新的100条
            if len(self.simulated_data) > 100:
                self.simulated_data.pop(0)
                self.timestamps.pop(0)
            
            # 输出到JSON文件
            self.save_to_json()
            
            # 更新GUI
            self.update_gui(timestamp, data_point)
            
            # 等待指定时间
            time.sleep(self.frequency / 1000)
    
    def save_to_json(self):
        # 构建JSON数据
        json_data = []
        for i, timestamp in enumerate(self.timestamps):
            data_dict = {"timestamp": timestamp}
            for j, col in enumerate(self.cols):
                data_dict[col] = self.simulated_data[i][j]
            json_data.append(data_dict)
        
        # 保存到JSON文件
        with open('simulated_air_data.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    def update_gui(self, timestamp, data_point):
        # 更新表格
        self.root.after(0, self._update_tree, timestamp, data_point)
        
        # 更新图表
        self.root.after(0, self._update_plot)
    
    def _update_tree(self, timestamp, data_point):
        # 插入新数据
        values = [timestamp] + data_point.tolist()
        self.tree.insert("", "end", values=values)
        
        # 保持表格行数限制
        if len(self.tree.get_children()) > 50:
            self.tree.delete(self.tree.get_children()[0])
    
    def _update_plot(self):
        # 更新图表数据
        for col in self.cols:
            col_index = self.cols.index(col)
            data = [point[col_index] for point in self.simulated_data]
            self.lines[col].set_data(range(len(data)), data)
        
        if self.simulated_data:
            self.ax.set_xlim(0, len(self.simulated_data) - 1)
            all_data = [val for point in self.simulated_data for val in point]
            if all_data:
                self.ax.set_ylim(min(all_data) * 0.9, max(all_data) * 1.1)
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = AirQualitySimulator(root)
    root.mainloop()