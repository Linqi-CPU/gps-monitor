# GPS 工具集

一个包含 **NMEA 解析工具**（Python）和 **GPS Monitor APK**（Android）的 GPS 数据处理与监控套件。

---

## 项目概览

| 项目 | 语言/平台 | 用途 | 运行环境 |
|------|----------|------|----------|
| [NMEA 解析工具](#nmea-解析工具) | Python | 解析 NMEA 0183 日志，计算距离/方位角，导出 KML | 桌面/服务器 |
| [GPS Monitor APK](#gps-monitor-apk) | Android (Java) | 手机端实时 GPS 定位，省份识别，离线地图 | Android 7.0+ |

---

## NMEA 解析工具

一个用于解析 GPS NMEA 数据、计算两点间距离和方位角，并在地图上可视化 GPS 轨迹的 Python 工具。

### 功能特性

- 解析标准 NMEA 0183 语句：
  - `$GPGGA` - 全球定位系统固定数据
  - `$GPRMC` - 推荐定位数据
  - `$GPGLL` - 地理定位信息
  - `$GPGSA` - GPS DOP 和活动卫星
  - `$GPGSV` - GPS 可见卫星
- 计算两点间的大圆距离（Haversine 公式）
- 计算两点间的初始方位角
- 将 GPS 轨迹导出为 KML 文件（可在 Google Earth 中查看）
- 命令行界面，支持批处理 NMEA 日志文件
- 单元测试覆盖核心功能

### 安装

```bash
pip install -r requirements.txt
```

### 使用方法

#### 命令行模式

```bash
# 解析单个 NMEA 文件
python cli.py parse sample_data/sample.nmea

# 计算两个坐标点之间的距离
python cli.py distance --lat1 39.9042 --lon1 116.4074 --lat2 31.2304 --lon2 121.4737

# 计算方位角
python cli.py bearing --lat1 39.9042 --lon1 116.4074 --lat2 31.2304 --lon2 121.4737

# 将 NMEA 轨迹导出为 KML
python cli.py export sample_data/sample.nmea output/trajectory.kml

# 查看帮助
python cli.py --help
```

#### 作为模块使用

```python
from nmea_parser import NMEAParser
from gps_calculator import GPSCalculator

# 解析 NMEA 语句
parser = NMEAParser()
with open('sample_data/sample.nmea', 'r') as f:
    for line in f:
        if line.startswith('$'):
            sentence = parser.parse_sentence(line.strip())
            print(sentence)

# 计算距离
calculator = GPSCalculator()
distance = calculator.haversine_distance(
    39.9042, 116.4074,  # 北京
    31.2304, 121.4737   # 上海
)
print(f"距离: {distance:.2f} km")

# 计算方位角
bearing = calculator.bearing(
    39.9042, 116.4074,
    31.2304, 121.4737
)
print(f"方位角: {bearing:.1f}°")

# 导出 KML
from kml_exporter import KMLExporter
exporter = KMLExporter()
exporter.add_point(39.9042, 116.4074, "北京")
exporter.add_track([(39.9042, 116.4074), (31.2304, 121.4737)])
exporter.save('output/trajectory.kml')
```

### 支持的 NMEA 语句

#### GPGGA - 全球定位系统固定数据

```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
```

包含时间、位置、质量、卫星数量、海拔等信息。

#### GPRMC - 推荐定位数据

```
$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
```

包含时间、状态、位置、速度、日期、磁偏角等信息。

### 算法说明

#### Haversine 公式

用于计算两个经纬度坐标点之间的大圆距离：

```
a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
c = 2 ⋅ atan2(√a, √(1−a))
d = R ⋅ c
```

其中 φ 是纬度，λ 是经度，R 是地球半径（平均 6371 km）。

#### 方位角计算

使用正切公式计算从点 1 到点 2 的初始方位角：

```
θ = atan2(sin Δλ ⋅ cos φ2, cos φ1 ⋅ sin φ2 − sin φ1 ⋅ cos φ2 ⋅ cos Δλ)
```

### 测试

运行单元测试：

```bash
python -m pytest tests/test_gps_parser.py -v
```

---

## GPS Monitor APK

纯本地离线 GPS 定位监控 Android 应用，实时显示经纬度、速度、海拔，自动识别所在省份，并提供离线地图可视化。

### 功能特性

- **实时 GPS 定位**：通过 `LocationManager` 获取 GPS/网络定位
- **数据可视化**：纬度、经度、精度、海拔、速度实时更新
- **省份识别**：内置 34 个省级行政区边界数据，智能判断当前位置省份
- **离线地图**：内置中国地图 PNG，无需网络，显示当前位置红点
- **三种算法切换**：
  - **矩形边界**：坐标落在省份矩形框内 → 该省（简单快速）
  - **速度矢量**：10 秒采样计算速度方向 → 过滤方向 ±60° → 取最近距离省份
  - **混合对比**：两种算法同时运行，不一致时取距离边界更近的
- **方向预测**：沿运动方向延伸 50km，预测即将进入的省份（如 "→ 河北省"）
- **定位历史**：最近 50 条记录，含时间戳、坐标、省份、算法标签
- **纯离线运行**：不依赖任何网络服务，完全本地计算

### 下载安装

1. 前往 [Releases](../../releases) 下载最新 `app-debug.apk`
2. 安装到 Android 设备（需要允许"未知来源"）
3. 首次打开授予**位置权限**（精确位置 + 粗略位置）

### 使用说明

1. 点击 **🚀 开始定位** 启动 GPS 追踪
2. 静置或移动，观察省份识别和方向变化
3. 点击 **🔄 切换算法** 对比三种模式效果
4. 点击 **⏹️ 停止** 暂停追踪
5. 点击 **🗑️ 清空** 清除历史记录

#### 算法选择建议

- **静止或低速**（< 5 km/h）：用 **矩形边界**
- **高速移动**（> 18 km/h）：用 **速度矢量** 或 **混合对比**
- **省界附近**：用 **混合对比**，自动对比两种结果

### 技术栈

- **Android 原生**：Java + Gradle + Android SDK
- **最低版本**：Android 7.0（API 24）
- **目标版本**：Android 14（API 34）
- **位置权限**：`ACCESS_FINE_LOCATION` + `ACCESS_COARSE_LOCATION`
- **地图数据**：内置 34 省边界框 + 省会坐标（离线）

### 开发与打包

#### 本地构建

```bash
cd app
./gradlew clean assembleDebug
# APK 输出到 app/build/outputs/apk/debug/app-debug.apk
```

#### GitHub Actions

Push 到 `main` 分支自动触发构建，Artifacts 中下载 `gps-monitor-apk.zip`。

### 项目结构

```
gps/
├── app/                          # Android 模块
│   ├── src/main/
│   │   ├── java/com/gps/monitor/
│   │   │   ├── MainActivity.java       # 主界面（纯原生 UI）
│   │   │   ├── ProvinceMap.java         # 离线地图引擎（绘制省份红点）
│   │   │   └── ProvinceInferencer.java  # 省份推断算法（三种模式）
│   │   ├── res/                         # 资源（布局、颜色、图标）
│   │   └── assets/
│   │       └── china_map.png            # 内置中国地图（1080×700）
│   └── build.gradle
├── .github/workflows/build-apk.yml      # GitHub Actions 自动构建
├── nmea_parser.py                       # NMEA 语句解析器
├── gps_calculator.py                    # GPS 坐标计算工具
├── kml_exporter.py                      # KML 文件导出器
├── cli.py                               # 命令行接口
├── requirements.txt                     # Python 依赖
├── sample_data/
│   └── sample.nmea                      # 示例 NMEA 数据
├── output/                              # 输出目录
└── tests/
    └── test_gps_parser.py              # 单元测试
```

### 算法原理

#### 矩形边界法

```java
if (lon >= p.minLon && lon <= p.maxLon && lat >= p.minLat && lat <= p.maxLat) {
    return p.name;
}
```

#### 速度矢量法

```java
// 1. 10秒采样
// 2. 计算 Haversine 距离和方位角
// 3. 过滤在运动方向 ±60° 内的省份
// 4. 计算到边界的最近距离，取最近省份
// 5. 沿方向延伸 50km，预测目标省份
```

#### 混合对比法

```java
if (!boundsResult.equals(vectorResult)) {
    // 不一致时，取距离边界更近的省份
}
```

### 已知限制

- 省份边界为**简化矩形框**，交界地带可能有误差
- 离线地图为**静态 PNG**，不显示详细地级市边界
- 方向预测基于 10 秒采样，静止或低速时不触发
- Debug APK 签名仅用于测试，安装需手动允许未知来源

### TODO

- [ ] 用真实 GeoJSON 多边形替换矩形边界（精度提升）
- [ ] 支持 OpenStreetMap 离线瓦片（四级缩放）
- [ ] 轨迹导出 KML/GPX
- [ ] 后台持续追踪 + 通知栏常驻
- [ ] 地图上绘制历史轨迹线

---

## 许可证

MIT License
