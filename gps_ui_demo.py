import tkinter as tk
from tkinter import ttk, font
import math

class GPSMonitorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GPS 定位监控")
        self.root.geometry("400x600")
        self.root.configure(bg='#1a1a2e')
        
        # 设置字体
        self.title_font = font.Font(family="Microsoft YaHei", size=20, weight="bold")
        self.label_font = font.Font(family="Microsoft YaHei", size=12)
        self.value_font = font.Font(family="Courier New", size=18, weight="bold")
        self.btn_font = font.Font(family="Microsoft YaHei", size=14, weight="bold")
        
        # 创建 UI
        self.create_widgets()
        
    def create_widgets(self):
        # 标题
        title_label = tk.Label(
            self.root, 
            text="📍 GPS 定位监控", 
            font=self.title_font,
            bg='#1a1a2e',
            fg='#ffffff'
        )
        title_label.pack(pady=20)
        
        # 状态指示
        self.status_label = tk.Label(
            self.root,
            text="● 未定位",
            font=self.label_font,
            bg='#1a1a2e',
            fg='#ff6b6b'
        )
        self.status_label.pack(pady=5)
        
        # 坐标显示框
        coord_frame = tk.Frame(self.root, bg='#16213e', padx=20, pady=20)
        coord_frame.pack(pady=10, fill=tk.X, padx=20)
        
        # 纬度
        tk.Label(
            coord_frame, 
            text="纬度 (Latitude)", 
            font=self.label_font,
            bg='#16213e',
            fg='#a0a0a0'
        ).pack(anchor=tk.W)
        
        self.lat_label = tk.Label(
            coord_frame,
            text="--",
            font=self.value_font,
            bg='#16213e',
            fg='#4ecdc4'
        )
        self.lat_label.pack(pady=5, anchor=tk.W)
        
        # 经度
        tk.Label(
            coord_frame, 
            text="经度 (Longitude)", 
            font=self.label_font,
            bg='#16213e',
            fg='#a0a0a0'
        ).pack(anchor=tk.W, pady=(15, 0))
        
        self.lon_label = tk.Label(
            coord_frame,
            text="--",
            font=self.value_font,
            bg='#16213e',
            fg='#4ecdc4'
        )
        self.lon_label.pack(pady=5, anchor=tk.W)
        
        # 精度
        tk.Label(
            coord_frame, 
            text="精度 (Accuracy)", 
            font=self.label_font,
            bg='#16213e',
            fg='#a0a0a0'
        ).pack(anchor=tk.W, pady=(15, 0))
        
        self.acc_label = tk.Label(
            coord_frame,
            text="--",
            font=self.value_font,
            bg='#16213e',
            fg='#4ecdc4'
        )
        self.acc_label.pack(pady=5, anchor=tk.W)
        
        # 按钮区
        btn_frame = tk.Frame(self.root, bg='#1a1a2e')
        btn_frame.pack(pady=30)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="🚀 开始定位",
            font=self.btn_font,
            bg='#667eea',
            fg='white',
            activebackground='#5568d3',
            activeforeground='white',
            width=12,
            height=2,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.start_gps
        )
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹️ 停止",
            font=self.btn_font,
            bg='#ff6b6b',
            fg='white',
            activebackground='#ee5a5a',
            activeforeground='white',
            width=12,
            height=2,
            relief=tk.FLAT,
            cursor='hand2',
            command=self.stop_gps,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
    def start_gps(self):
        self.status_label.config(text="● 正在定位...", fg='#ffd93d')
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        # 模拟获取位置
        self.simulate_location()
        
    def stop_gps(self):
        self.status_label.config(text="● 已停止", fg='#ff6b6b')
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
    def simulate_location(self):
        # 模拟更新经纬度（实际应从 GPS 模块获取）
        import random
        lat = 39.9042 + random.uniform(-0.01, 0.01)
        lon = 116.4074 + random.uniform(-0.01, 0.01)
        acc = random.uniform(5, 50)
        
        self.lat_label.config(text=f"{lat:.6f}°")
        self.lon_label.config(text=f"{lon:.6f}°")
        self.acc_label.config(text=f"{acc:.1f} 米")
        self.status_label.config(text="● GPS 定位成功", fg='#6bcb77')
        
        # 每 2 秒更新一次
        self.root.after(2000, self.simulate_location)

if __name__ == "__main__":
    root = tk.Tk()
    app = GPSMonitorUI(root)
    root.mainloop()
