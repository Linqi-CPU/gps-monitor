# GPS 工具集 — 技术文档

## 1. 项目概述

GPS 工具集包含两个独立子项目，共享 GPS 计算核心算法：

- **NMEA 解析工具**：Python 实现的 NMEA 0183 语句解析、距离/方位角计算、KML 导出
- **GPS Monitor APK**：Android 原生 APK，实时 GPS 定位、省份识别、离线地图

---

## 2. NMEA 解析工具

### 2.1 模块结构

```
nmea_parser.py      — NMEA 语句词法/语法解析
gps_calculator.py   — Haversine 距离、方位角计算
kml_exporter.py     — KML 文件生成（Google Earth 可视化）
cli.py              — 命令行入口
tests/
└── test_gps_parser.py  — 单元测试
```

### 2.2 核心算法

#### 2.2.1 Haversine 公式

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # 地球半径（米）
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat/2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
```

精度：对短距离（< 100 km）误差 < 0.5%。

#### 2.2.2 方位角计算

```python
def calculate_bearing(lat1, lon1, lat2, lon2):
    d_lon = math.radians(lon2 - lon1)
    y = math.sin(d_lon) * math.cos(math.radians(lat2))
    x = (math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) -
         math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(d_lon))
    return (math.degrees(math.atan2(y, x)) + 360) % 360
```

返回值：0–360°，0° 为正北，90° 为正东。

#### 2.2.3 NMEA 解析

- `$GPGGA` → 解析时间、纬度、经度、定位质量、卫星数、海拔
- `$GPRMC` → 解析时间、状态、位置、速度、日期
- 采用正则表达式 `\$([A-Z]{2}G[GLS][A-Z]{2}),([^*]+)\*([0-9A-F]{2})` 提取字段

### 2.3 KML 导出

```python
class KMLExporter:
    def add_point(self, lat, lon, name=""): ...
    def add_track(self, points, name=""): ...
    def save(self, path): ...
```

生成标准 KML，可在 Google Earth 中直接打开。

---

## 3. GPS Monitor APK

### 3.1 架构

```
MainActivity（AppCompatActivity）
├── ProvinceMap              — 离线地图渲染
├── ProvinceInferencer       — 省份推断引擎
└── LocationListener         — GPS 回调
```

### 3.2 界面布局（纯代码构建）

- `LinearLayout` 根节点（垂直）
- 数据卡片：纬度 / 经度 / 精度 / 海拔 / 速度 / 省份 / 移动方向 / 算法模式
- 按钮行：开始定位 / 停止 / 清空 / 切换算法
- `ImageView`：离线地图（`china_map.png`）
- `LinearLayout`：历史记录列表（最多 50 条）

### 3.3 定位流程

```
onCreate
  └── LocationManager.getSystemService(LocationManager.GPS_PROVIDER)
      └── 按钮触发 startTracking()
          └── requestLocationUpdates(GPS_PROVIDER + NETWORK_PROVIDER, 1000ms, 0m, this)
              └── onLocationChanged(Location)
                  ├── 更新 UI（latValue/lonValue/...）
                  ├── ProvinceInferencer.update(lat, lon, timestamp)
                  ├── ProvinceMap.getMapBitmap(lat, lon) → mapView
                  └── 添加到历史列表
```

### 3.4 省份推断算法

#### 3.4.1 矩形边界法（BOUNDS）

```java
if (lon >= p.minLon && lon <= p.maxLon && lat >= p.minLat && lat <= p.maxLat) {
    return p.name;  // 落在矩形框内
}
```

- 优点：速度快，无状态
- 缺点：省界交界处可能误判

#### 3.4.2 速度矢量法（VECTOR）

```java
// 1. 10秒采样间隔（lastSampleTime 控制）
// 2. 计算 Haversine 距离 → 速度 = 距离 / 时间
// 3. 计算方位角 bearing
// 4. 速度 > 5m/s 时，过滤在方向 ±60° 内的候选省份
// 5. 计算到边界的最近距离（简化：到最近边的 Haversine 距离）
// 6. 取最近的候选省份
// 7. 沿 bearing 延伸 50km，预测目标省份 → 显示 "→ 省份名"
```

- 优点：动态跟踪，可预测方向
- 缺点：静止/低速时不触发，需要 10 秒采样

#### 3.4.3 混合对比法（HYBRID）

```java
Province boundsResult = findProvinceByBounds(lat, lon);
Province vectorResult = findNearestByVector(...);

if (!boundsResult.equals(vectorResult)) {
    // 不一致时：
    //   boundsDistance < 10km → 信矩形（可能在省界附近静止）
    //  否则 → 信矢量（正在穿越省界）
}
```

### 3.5 离线地图

- 资源：`assets/china_map.png`（1080×700 像素，深色主题）
- 绘制逻辑：
  1. 加载 Bitmap → copy ARGB 8888
  2. 遍历省份数据，坐标转像素（线性映射：73–135°E → 0–1080px，54–18°N → 0–700px）
  3. 高亮当前省份（半透明矩形，`highlightPaint`）
  4. 绘制当前位置红点（半径 8px）
  5. 绘制省份名称标签

---

## 4. 省份数据

34 个省级行政区的边界框（minLon, maxLon, minLat, maxLat）和中心点（省会坐标）。数据来源：公开地理信息整理，精度为省界简化矩形。

---

## 5. 构建与打包

### 5.1 APK

```bash
cd app
gradlew clean assembleDebug
# 输出：app/build/outputs/apk/debug/app-debug.apk
```

### 5.2 GitHub Actions

- 触发：push 到 `main`
- 步骤：
  1. `setup-java`（JDK 17）
  2. `setup-android`（SDK + Build Tools 34.0.0）
  3. `gradlew assembleDebug --stacktrace --info`
  4. `upload-artifact`（`gps-monitor-apk.zip`）

---

## 6. 已知问题与限制

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 省界交界误判 | 矩形框简化 | 改用 GeoJSON 多边形 |
| 地图无缩放 | 静态 PNG | 改用离线瓦片或放大图 |
| 方向预测不准 | 10秒采样 + GPS 漂移 | 增加滤波（卡尔曼） |
| Debug APK 未签名 | buildozer 已移除 Android 支持 | 当前用 Gradle debug 签名 |
| 定位更新频率高耗电 | 1000ms 间隔 | 可改为 3000ms 或动态调整 |

---

## 7. 依赖与版本

- **Android SDK**：compileSdk 34，minSdk 24，targetSdk 34
- **Gradle**：8.2
- **Java**：JDK 17
- **AppCompat**：1.6.1（`Theme.AppCompat.Light.NoActionBar`）

---

## 8. 许可证

MIT License
