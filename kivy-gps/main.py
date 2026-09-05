"""
GPS Monitor - Kivy + Matplotlib Map
纯本地实现，支持真实 GPS 定位、轨迹记录、KML 导出
打包: buildozer android debug
"""

import os
import json
import math
import random
import platform
import threading
from datetime import datetime
from pathlib import Path

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.core.window import Window
from kivy.utils import platform as kivy_platform

# Matplotlib for map
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import numpy as np
import io

# ============================================
# GPS 数据模型
# ============================================

class GPSData:
    """GPS 数据管理：实时数据 + 轨迹历史"""
    def __init__(self, max_history=1000):
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.speed = 0.0
        self.accuracy = 0.0
        self.timestamp = None
        self.is_fixed = False
        self.history = []  # [(lat, lon, alt, speed, timestamp), ...]
        self.max_history = max_history

    def update(self, lat, lon, alt=0, speed=0, accuracy=0, timestamp=None):
        self.latitude = lat
        self.longitude = lon
        self.altitude = alt
        self.speed = speed
        self.accuracy = accuracy
        self.timestamp = timestamp or datetime.now()
        self.is_fixed = True
        self.history.append((lat, lon, alt, speed, self.timestamp))
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def clear_history(self):
        self.history.clear()

    def to_kml(self, filename):
        """导出轨迹为 KML 文件"""
        if not self.history:
            return False
        kml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>GPS Track</name>
  <Placemark>
    <name>Track</name>
    <LineString>
      <coordinates>
'''
        kml_footer = '''      </coordinates>
    </LineString>
  </Placemark>
</Document>
</kml>'''
        coords = "\n".join([f"{lon},{lat},{alt}" for lat, lon, alt, spd, ts in self.history])
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(kml_header + coords + kml_footer)
        return True

    def to_json(self, filename):
        """导出为 JSON"""
        data = [{"lat": lat, "lon": lon, "alt": alt, "speed": spd, "time": ts.isoformat()}
                for lat, lon, alt, spd, ts in self.history]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

# ============================================
# 地图组件（Matplotlib 静态图）
# ============================================

class MapWidget(Widget):
    """显示 GPS 轨迹的静态地图"""
    def __init__(self, gps_data=None, **kwargs):
        super().__init__(**kwargs)
        self.gps_data = gps_data
        self._texture = None
        self._rect = None
        self._update_map()

    def _update_map(self):
        if not self.gps_data or len(self.gps_data.history) < 2:
            # 空地图
            self.figure = Figure(figsize=(4, 4), dpi=100, facecolor='#16213e')
            self.ax = self.figure.add_subplot(111)
            self.ax.set_facecolor('#16213e')
            self.ax.text(0.5, 0.5, '暂无轨迹\n请点击"开始定位"', 
                        ha='center', va='center', transform=self.ax.transAxes,
                        color='#666', fontsize=12)
            self.ax.axis('off')
        else:
            # 绘制轨迹
            lats = [p[0] for p in self.gps_data.history]
            lons = [p[1] for p in self.gps_data.history]
            lats_last = lats[-1]
            lons_last = lons[-1]

            self.figure = Figure(figsize=(4, 4), dpi=100, facecolor='#16213e')
            self.ax = self.figure.add_subplot(111)
            self.ax.set_facecolor('#16213e')

            # 轨迹线
            self.ax.plot(lons, lats, color='#4ecdc4', linewidth=2, alpha=0.7, label='轨迹')
            # 起点
            self.ax.scatter(lons[0], lats[0], c='#667eea', s=60, marker='o', label='起点', zorder=5)
            # 当前位置
            self.ax.scatter(lons_last, lats_last, c='#ff6b6b', s=100, marker='*', label='当前位置', zorder=6)

            # 自动调整视图
            margin = 0.001
            self.ax.set_xlim(min(lons)-margin, max(lons)+margin)
            self.ax.set_ylim(min(lats)-margin, max(lats)+margin)

            self.ax.set_xlabel('经度', color='white', fontsize=8)
            self.ax.set_ylabel('纬度', color='white', fontsize=8)
            self.ax.tick_params(colors='white', labelsize=6)
            for spine in self.ax.spines.values():
                spine.set_edgecolor('#444')
            self.ax.grid(True, color='#333', linewidth=0.5)
            self.ax.legend(loc='upper right', fontsize=8, labelcolor='white')

        self.figure.tight_layout()

        # 渲染到纹理
        canvas = FigureCanvasAgg(self.figure)
        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)

        from kivy.graphics.texture import Texture
        from kivy.core.image import Image as CoreImage

        img = CoreImage(buf, ext='png')
        self._texture = img.texture
        with self.canvas:
            if self._rect is None:
                self._rect = Rectangle(texture=self._texture, pos=self.pos, size=self.size)
            else:
                self._rect.texture = self._texture
                self._rect.pos = self.pos
                self._rect.size = self.size

    def update(self):
        self._update_map()

    def on_size(self, *args):
        if self._rect:
            self._rect.size = self.size
            self._rect.pos = self.pos

    def on_pos(self, *args):
        if self._rect:
            self._rect.pos = self.pos

# ============================================
# GPS 定位源（模拟 / 真实）
# ============================================

class GPSLocationSource:
    """GPS 数据源：支持模拟模式和真实定位"""
    def __init__(self, gps_data, on_update=None):
        self.gps_data = gps_data
        self.on_update = on_update
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1)
            self._thread = None

    def _run(self):
        while self.running:
            if kivy_platform == 'android':
                self._get_android_location()
            else:
                self._get_mock_location()
            # 更新频率 1 秒
            import time; time.sleep(1)

    def _get_mock_location(self):
        """模拟位置（北京附近随机漂移）"""
        lat = 39.9042 + random.uniform(-0.001, 0.001)
        lon = 116.4074 + random.uniform(-0.001, 0.001)
        alt = random.uniform(40, 60)
        speed = random.uniform(0, 15)
        acc = random.uniform(3, 15)
        self.gps_data.update(lat, lon, alt, speed, acc)
        if self.on_update:
            self.on_update(self.gps_data)

    def _get_android_location(self):
        """真实 Android GPS（需要 plyer 或 pyjnius）"""
        try:
            from android.permissions import request_permissions, Permission
            from jnius import autoclass, cast
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
            
            LocationManager = autoclass('android.location.LocationManager')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity.getApplicationContext()
            lm = cast(android.location.LocationManager, context.getSystemService(PythonActivity.LOCATION_SERVICE))
            
            if lm.isProviderEnabled(LocationManager.GPS_PROVIDER):
                location = lm.getLastKnownLocation(LocationManager.GPS_PROVIDER)
                if location:
                    lat = location.getLatitude()
                    lon = location.getLongitude()
                    alt = location.getAltitude()
                    speed = location.getSpeed()
                    acc = location.getAccuracy()
                    self.gps_data.update(lat, lon, alt, speed, acc)
                    if self.on_update:
                        self.on_update(self.gps_data)
        except Exception as e:
            print(f"Android GPS error: {e}")

# ============================================
# 主界面
# ============================================

class GPSMonitorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gps_data = GPSData()
        self.gps_source = None
        self.running = False
        self.build_ui()

    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 标题栏
        title_box = BoxLayout(size_hint_y=None, height=50)
        title = Label(text="📍 GPS 定位监控", font_size=24, color=(1, 1, 1, 1), bold=True)
        title_box.add_widget(title)
        root.add_widget(title_box)

        # 状态栏
        self.status_label = Label(
            text="● 未定位",
            font_size=16,
            color=(1, 0.42, 0.42, 1),
            size_hint_y=None,
            height=30
        )
        root.add_widget(self.status_label)

        # Tab 面板
        tabs = TabbedPanel(do_default_tab=False, tab_pos='top_mid')

        # === Tab 1: 数据 ===
        data_tab = TabbedPanelItem(text="数据")
        data_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # 数据卡片
        card = BoxLayout(orientation='vertical', padding=15, spacing=10)
        with card.canvas.before:
            Color(0.09, 0.13, 0.23, 1)
            self._card_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[10])

        self.lat_label = self._make_value_label("纬度", "--")
        card.add_widget(self.lat_label)

        self.lon_label = self._make_value_label("经度", "--")
        card.add_widget(self.lon_label)

        self.acc_label = self._make_value_label("精度", "--")
        card.add_widget(self.acc_label)

        self.alt_label = self._make_value_label("海拔", "--")
        card.add_widget(self.alt_label)

        self.spd_label = self._make_value_label("速度", "--")
        card.add_widget(self.spd_label)

        data_layout.add_widget(card)

        # 按钮区
        btn_box = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.start_btn = Button(
            text="🚀 开始定位",
            font_size=18,
            background_color=(0.4, 0.49, 0.72, 1),
            background_normal='',
            on_press=self.start_gps
        )
        self.stop_btn = Button(
            text="⏹️ 停止",
            font_size=18,
            background_color=(1, 0.42, 0.42, 1),
            background_normal='',
            on_press=self.stop_gps,
            disabled=True
        )
        btn_box.add_widget(self.start_btn)
        btn_box.add_widget(self.stop_btn)
        data_layout.add_widget(btn_box)

        # 导出按钮
        export_box = BoxLayout(size_hint_y=None, height=60, spacing=10)
        self.export_kml_btn = Button(
            text="📤 导出 KML",
            font_size=16,
            background_color=(0.31, 0.8, 0.78, 1),
            background_normal='',
            on_press=self.export_kml
        )
        self.export_json_btn = Button(
            text="📄 导出 JSON",
            font_size=16,
            background_color=(0.31, 0.8, 0.78, 1),
            background_normal='',
            on_press=self.export_json
        )
        self.clear_btn = Button(
            text="🗑️ 清空轨迹",
            font_size=16,
            background_color=(1, 0.42, 0.42, 1),
            background_normal='',
            on_press=self.clear_history
        )
        export_box.add_widget(self.export_kml_btn)
        export_box.add_widget(self.export_json_btn)
        export_box.add_widget(self.clear_btn)
        data_layout.add_widget(export_box)

        data_tab.add_widget(data_layout)
        tabs.add_widget(data_tab)

        # === Tab 2: 地图 ===
        map_tab = TabbedPanelItem(text="地图")
        self.map_widget = MapWidget(gps_data=self.gps_data)
        map_tab.add_widget(self.map_widget)
        tabs.add_widget(map_tab)

        # === Tab 3: 历史记录 ===
        history_tab = TabbedPanelItem(text="历史")
        history_layout = BoxLayout(orientation='vertical', padding=10)
        self.history_label = Label(
            text="暂无记录",
            font_size=12,
            color=(0.8, 0.8, 0.8, 1),
            halign='left',
            valign='top'
        )
        scroll = ScrollView()
        scroll.add_widget(self.history_label)
        history_layout.add_widget(scroll)
        history_tab.add_widget(history_layout)
        tabs.add_widget(history_tab)

        root.add_widget(tabs)
        self.add_widget(root)

        self._card_rect.bind(pos=self._update_card_rect, size=self._update_card_rect)

    def _make_value_label(self, label_text, value_text):
        box = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        lbl = Label(
            text=label_text,
            font_size=12,
            color=(0.63, 0.63, 0.63, 1),
            size_hint_y=None,
            height=20
        )
        val = Label(
            text=value_text,
            font_size=24,
            color=(0.31, 0.8, 0.78, 1),
            bold=True,
            font_name='Courier'
        )
        box.add_widget(lbl)
        box.add_widget(val)
        return box

    def _update_card_rect(self, instance, value):
        self._card_rect.pos = instance.pos
        self._card_rect.size = instance.size

    def start_gps(self, *args):
        self.running = True
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.status_label.text = "● 正在定位..."
        self.status_label.color = (1, 0.85, 0.24, 1)
        self.gps_source = GPSLocationSource(
            self.gps_data,
            on_update=self._on_gps_update
        )
        self.gps_source.start()

    def stop_gps(self, *args):
        self.running = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.status_label.text = "● 已停止"
        self.status_label.color = (1, 0.42, 0.42, 1)
        if self.gps_source:
            self.gps_source.stop()
            self.gps_source = None

    def _on_gps_update(self, gps_data):
        """在主线程更新 UI"""
        def update_ui(dt):
            if not self.running:
                return
            # 更新坐标
            self.lat_label.children[0].text = f"{gps_data.latitude:.6f}°"
            self.lon_label.children[0].text = f"{gps_data.longitude:.6f}°"
            self.acc_label.children[0].text = f"{gps_data.accuracy:.1f} 米"
            self.alt_label.children[0].text = f"{gps_data.altitude:.1f} 米"
            self.spd_label.children[0].text = f"{gps_data.speed * 3.6:.1f} km/h"
            self.status_label.text = "● GPS 定位成功"
            self.status_label.color = (0.42, 0.8, 0.47, 1)
            # 更新地图
            self.map_widget.update()
            # 更新历史记录
            self._update_history()
        Clock.schedule_once(update_ui, 0)

    def _update_history(self):
        """显示最近 20 条历史记录"""
        recent = self.gps_data.history[-20:]
        lines = []
        for i, (lat, lon, alt, spd, ts) in enumerate(reversed(recent)):
            time_str = ts.strftime("%H:%M:%S")
            lines.append(f"{i+1}. {lat:.6f}, {lon:.6f} | {time_str}")
        self.history_label.text = "\n".join(lines) if lines else "暂无记录"

    def export_kml(self, *args):
        if not self.gps_data.history:
            self._show_popup("提示", "暂无轨迹数据可导出")
            return
        # 弹出文件选择器（简化：直接保存到默认路径）
        path = Path.home() / "gps_track.kml"
        if self.gps_data.to_kml(str(path)):
            self._show_popup("导出成功", f"KML 文件已保存到:\n{path}")
        else:
            self._show_popup("导出失败", "无法保存 KML 文件")

    def export_json(self, *args):
        if not self.gps_data.history:
            self._show_popup("提示", "暂无轨迹数据可导出")
            return
        path = Path.home() / "gps_track.json"
        if self.gps_data.to_json(str(path)):
            self._show_popup("导出成功", f"JSON 文件已保存到:\n{path}")
        else:
            self._show_popup("导出失败", "无法保存 JSON 文件")

    def clear_history(self, *args):
        self.gps_data.clear_history()
        self.map_widget.update()
        self.history_label.text = "暂无记录"
        self._show_popup("已清空", "轨迹历史已清空")

    def _show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, halign='center', valign='center'),
            size_hint=(0.8, 0.4),
            auto_dismiss=True
        )
        popup.open()

# ============================================
# App Entry
# ============================================

class GPSMonitorApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.18, 1)
        sm = ScreenManager()
        sm.add_widget(GPSMonitorScreen(name='gps'))
        return sm

if __name__ == '__main__':
    GPSMonitorApp().run()
