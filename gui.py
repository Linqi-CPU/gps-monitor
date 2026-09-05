"""
GPS NMEA 解析工具 - Tkinter GUI 界面

提供图形化界面，支持：
- NMEA 文件解析和轨迹显示
- 坐标点距离计算
- 方位角计算
- KML 文件导出
- 轨迹可视化
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from datetime import datetime

# 导入自定义模块
from nmea_parser import NMEAParser, GGAData, RMCData, GLLData
from gps_calculator import GPSCalculator
from kml_exporter import KMLExporter


class GPSApp:
    """GPS NMEA 解析工具主界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("GPS NMEA 解析工具")
        self.root.geometry("1200x700")
        
        # 设置窗口图标和主题
        self.root.minsize(800, 600)
        
        # 初始化组件
        self.parser = NMEAParser()
        self.calculator = GPSCalculator()
        self.exporter = KMLExporter()
        
        # 存储解析结果
        self.parsed_sentences = []
        self.positions = []
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 文件解析选项卡
        parse_frame = ttk.Frame(notebook, padding="10")
        notebook.add(parse_frame, text="文件解析")
        self._create_parse_tab(parse_frame)
        
        # 坐标计算选项卡
        calc_frame = ttk.Frame(notebook, padding="10")
        notebook.add(calc_frame, text="坐标计算")
        self._create_calc_tab(calc_frame)
        
        # KML 导出选项卡
        export_frame = ttk.Frame(notebook, padding="10")
        notebook.add(export_frame, text="KML导出")
        self._create_export_tab(export_frame)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def _create_parse_tab(self, parent):
        """创建文件解析选项卡"""
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(2, weight=1)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(parent, text="NMEA 文件", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(file_frame, text="文件路径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60)
        file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="浏览", command=self._browse_file)
        browse_btn.grid(row=0, column=2, padx=(0, 5))
        
        parse_btn = ttk.Button(file_frame, text="解析", command=self._parse_file)
        parse_btn.grid(row=0, column=3)
        
        file_frame.columnconfigure(1, weight=1)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(parent, text="统计信息", padding="10")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_var = tk.StringVar(value="请先解析文件")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var)
        stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(parent, text="解析结果", padding="10")
        result_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 使用 Treeview 显示结果
        self.tree = ttk.Treeview(result_frame, columns=('time', 'lat', 'lon', 'alt', 'quality'), 
                                 show='tree headings', height=20)
        self.tree.heading('#0', text='语句类型')
        self.tree.heading('time', text='时间')
        self.tree.heading('lat', text='纬度')
        self.tree.heading('lon', text='经度')
        self.tree.heading('alt', text='海拔(m)')
        self.tree.heading('quality', text='质量')
        
        self.tree.column('#0', width=120)
        self.tree.column('time', width=80)
        self.tree.column('lat', width=100)
        self.tree.column('lon', width=100)
        self.tree.column('alt', width=80)
        self.tree.column('quality', width=60)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 导出按钮
        export_btn = ttk.Button(parent, text="导出到 KML", command=lambda: self._export_to_kml())
        export_btn.grid(row=3, column=0, pady=(10, 0))
        
    def _create_calc_tab(self, parent):
        """创建坐标计算选项卡"""
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        
        # 起点坐标
        start_frame = ttk.LabelFrame(parent, text="起点坐标", padding="10")
        start_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        start_frame.columnconfigure(1, weight=1)
        
        ttk.Label(start_frame, text="纬度:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.start_lat = ttk.Entry(start_frame)
        self.start_lat.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        self.start_lat.insert(0, "39.9042")  # 北京
        
        ttk.Label(start_frame, text="经度:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.start_lon = ttk.Entry(start_frame)
        self.start_lon.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        self.start_lon.insert(0, "116.4074")  # 北京
        
        # 终点坐标
        end_frame = ttk.LabelFrame(parent, text="终点坐标", padding="10")
        end_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        end_frame.columnconfigure(1, weight=1)
        
        ttk.Label(end_frame, text="纬度:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.end_lat = ttk.Entry(end_frame)
        self.end_lat.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        self.end_lat.insert(0, "31.2304")  # 上海
        
        ttk.Label(end_frame, text="经度:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.end_lon = ttk.Entry(end_frame)
        self.end_lon.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        self.end_lon.insert(0, "121.4737")  # 上海
        
        # 计算结果
        calc_frame = ttk.LabelFrame(parent, text="计算结果", padding="10")
        calc_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        calc_frame.columnconfigure(0, weight=1)
        calc_frame.columnconfigure(1, weight=1)
        
        self.distance_var = tk.StringVar(value="距离: --")
        self.bearing_var = tk.StringVar(value="方位角: --")
        
        distance_label = ttk.Label(calc_frame, textvariable=self.distance_var, font=('Arial', 12))
        distance_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        bearing_label = ttk.Label(calc_frame, textvariable=self.bearing_var, font=('Arial', 12))
        bearing_label.grid(row=0, column=1, sticky=tk.W)
        
        # 计算按钮
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        
        calc_btn = ttk.Button(btn_frame, text="计算", command=self._calculate)
        calc_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(btn_frame, text="清除", command=self._clear_calc)
        clear_btn.pack(side=tk.LEFT)
        
    def _create_export_tab(self, parent):
        """创建 KML 导出选项卡"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        
        # 文件信息
        info_frame = ttk.LabelFrame(parent, text="导出信息", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="KML 文件:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.kml_path_var = tk.StringVar()
        kml_entry = ttk.Entry(info_frame, textvariable=self.kml_path_var)
        kml_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(info_frame, text="浏览", command=self._browse_kml)
        browse_btn.grid(row=0, column=2)
        
        ttk.Label(info_frame, text="轨迹名称:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.track_name_var = tk.StringVar(value="GPS Track")
        name_entry = ttk.Entry(info_frame, textvariable=self.track_name_var)
        name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 5), pady=(5, 0))
        
        ttk.Label(info_frame, text="线条颜色:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.color_var = tk.StringVar(value="ff0000ff")
        color_entry = ttk.Entry(info_frame, textvariable=self.color_var, width=15)
        color_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        ttk.Label(info_frame, text="(KML格式: aabbggrr)", font=('Arial', 8)).grid(row=2, column=2, sticky=tk.W, pady=(5, 0))
        
        # 导出按钮
        export_btn = ttk.Button(info_frame, text="导出 KML", command=self._export_kml)
        export_btn.grid(row=3, column=0, columnspan=3, pady=(20, 0))
        
        # 说明文字
        help_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD, height=15, width=80)
        help_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        help_text.insert(tk.END, """KML 文件说明：

KML (Keyhole Markup Language) 是一种 XML 格式的文件，用于在地图应用中显示地理数据。

使用方法：
1. 选择输出文件路径
2. 输入轨迹名称
3. 可选：修改线条颜色（格式：aabbggrr）
   - 前两位：透明度 (ff=不透明, 80=半透明)
   - 后六位：颜色值 (rrggbb)
   - 例如：ff0000ff = 不透明蓝色
   - 例如：ff00ff00 = 不透明绿色
4. 点击"导出 KML"按钮

打开方式：
- Google Earth（推荐）
- Google Maps（上传到 Google Drive）
- 其他支持 KML 的地图应用

提示：
- 从"文件解析"选项卡解析的轨迹可以自动导出
- 导出的文件可以在 Google Earth 中查看 3D 轨迹
""")
        help_text.config(state=tk.DISABLED)
        
    def _browse_file(self):
        """浏览并选择 NMEA 文件"""
        filetypes = [
            ("NMEA 文件", "*.nmea *.log *.txt"),
            ("所有文件", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="选择 NMEA 文件",
            filetypes=filetypes
        )
        if filename:
            self.file_path_var.set(filename)
            
    def _browse_kml(self):
        """浏览并选择 KML 输出文件"""
        filetypes = [("KML 文件", "*.kml"), ("所有文件", "*.*")]
        filename = filedialog.asksaveasfilename(
            title="保存 KML 文件",
            filetypes=filetypes,
            defaultextension=".kml"
        )
        if filename:
            self.kml_path_var.set(filename)
            
    def _parse_file(self):
        """解析 NMEA 文件"""
        filepath = self.file_path_var.get()
        if not filepath:
            messagebox.showwarning("警告", "请先选择 NMEA 文件")
            return
            
        if not os.path.exists(filepath):
            messagebox.showerror("错误", "文件不存在")
            return
            
        # 在新线程中解析文件
        def parse():
            try:
                self.status_var.set("正在解析文件...")
                self.root.update()
                
                sentences = self.parser.parse_file(filepath)
                positions = self.parser.get_positions(sentences)
                
                # 更新界面
                self.parsed_sentences = sentences
                self.positions = positions
                self._update_results(sentences, positions)
                
                # 更新统计信息
                self.stats_var.set(
                    f"共解析 {len(sentences)} 条语句，"
                    f"提取 {len(positions)} 个位置点"
                )
                
                self.status_var.set(f"解析完成，共 {len(sentences)} 条语句")
                messagebox.showinfo("成功", f"解析完成！\n共解析 {len(sentences)} 条语句")
                
            except Exception as e:
                self.status_var.set("解析失败")
                messagebox.showerror("错误", f"解析失败：{str(e)}")
        
        threading.Thread(target=parse, daemon=True).start()
        
    def _update_results(self, sentences, positions):
        """更新结果显示"""
        # 清空树形视图
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 添加位置信息
        type_names = {
            'GPGGA': 'GGA',
            'GPRMC': 'RMC',
            'GPGLL': 'GLL'
        }
        
        for sentence in sentences:
            if isinstance(sentence, (GGAData, RMCData, GLLData)):
                type_name = type_names.get(sentence.sentence_type, sentence.sentence_type)
                
                # 提取时间
                time_str = ""
                if hasattr(sentence, 'fix_time') and sentence.fix_time:
                    time_str = sentence.fix_time.strftime("%H:%M:%S")
                
                # 提取坐标
                lat = f"{sentence.latitude:.6f}" if sentence.latitude else ""
                lon = f"{sentence.longitude:.6f}" if sentence.longitude else ""
                
                # 提取海拔
                alt = ""
                if hasattr(sentence, 'altitude') and sentence.altitude is not None:
                    alt = f"{sentence.altitude:.1f}"
                
                # 提取质量
                quality = ""
                if hasattr(sentence, 'fix_quality'):
                    quality = str(sentence.fix_quality) if sentence.fix_quality else ""
                elif hasattr(sentence, 'status'):
                    quality = sentence.status if sentence.status else ""
                
                self.tree.insert('', tk.END, text=type_name, 
                               values=(time_str, lat, lon, alt, quality))
                               
    def _export_to_kml(self):
        """导出轨迹到 KML 文件"""
        if not self.positions:
            messagebox.showwarning("警告", "请先解析 NMEA 文件")
            return
            
        filepath = filedialog.asksaveasfilename(
            title="保存 KML 文件",
            filetypes=[("KML 文件", "*.kml"), ("所有文件", "*.*")],
            defaultextension=".kml"
        )
        
        if filepath:
            # 提取轨迹点
            points = [(p['latitude'], p['longitude']) for p in self.positions]
            
            exporter = KMLExporter()
            exporter.add_track(points, name="GPS Track")
            
            if exporter.save(filepath):
                messagebox.showinfo("成功", f"KML 文件已保存到:\n{filepath}")
            else:
                messagebox.showerror("错误", "保存 KML 文件失败")
                
    def _calculate(self):
        """计算距离和方位角"""
        try:
            lat1 = float(self.start_lat.get())
            lon1 = float(self.start_lon.get())
            lat2 = float(self.end_lat.get())
            lon2 = float(self.end_lon.get())
            
            # 计算距离
            distance = self.calculator.haversine_distance(lat1, lon1, lat2, lon2, 'km')
            self.distance_var.set(f"距离: {distance:.2f} km")
            
            # 计算方位角
            bearing = self.calculator.bearing(lat1, lon1, lat2, lon2)
            self.bearing_var.set(f"方位角: {bearing:.1f}°")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")
            
    def _clear_calc(self):
        """清除计算结果显示"""
        self.distance_var.set("距离: --")
        self.bearing_var.set("方位角: --")
        
    def _export_kml(self):
        """导出 KML 文件"""
        filepath = self.kml_path_var.get()
        if not filepath:
            messagebox.showwarning("警告", "请选择 KML 文件保存路径")
            return
            
        track_name = self.track_name_var.get()
        color = self.color_var.get()
        
        if not self.positions:
            messagebox.showwarning("警告", "请先解析 NMEA 文件获取轨迹数据")
            return
            
        # 提取轨迹点
        points = [(p['latitude'], p['longitude']) for p in self.positions]
        
        exporter = KMLExporter()
        exporter.add_track(points, name=track_name, color=color)
        
        if exporter.save(filepath):
            messagebox.showinfo("成功", f"KML 文件已保存到:\n{filepath}")
        else:
            messagebox.showerror("错误", "保存 KML 文件失败")


def main():
    """主函数"""
    root = tk.Tk()
    app = GPSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
