# GPS NMEA 解析工具

一个用于解析 GPS NMEA 数据、计算两点间距离和方位角，并在地图上可视化 GPS 轨迹的工具。

## 功能特性

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

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行模式

解析单个 NMEA 文件：

```bash
python cli.py parse sample_data/sample.nmea
```

计算两个坐标点之间的距离：

```bash
python cli.py distance --lat1 39.9042 --lon1 116.4074 --lat2 31.2304 --lon2 121.4737
```

计算方位角：

```bash
python cli.py bearing --lat1 39.9042 --lon1 116.4074 --lat2 31.2304 --lon2 121.4737
```

将 NMEA 轨迹导出为 KML：

```bash
python cli.py export sample_data/sample.nmea output/trajectory.kml
```

查看帮助：

```bash
python cli.py --help
```

### 作为模块使用

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

## 项目结构

```
gps/
├── README.md              # 项目文档
├── nmea_parser.py         # NMEA 语句解析器
├── gps_calculator.py      # GPS 坐标计算工具
├── kml_exporter.py        # KML 文件导出器
├── cli.py                 # 命令行接口
├── requirements.txt       # Python 依赖
├── sample_data/
│   └── sample.nmea        # 示例 NMEA 数据
├── output/                # 输出目录
└── tests/
    └── test_gps_parser.py # 单元测试
```

## 支持的 NMEA 语句

### GPGGA - 全球定位系统固定数据
```
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
```
包含时间、位置、质量、卫星数量、海拔等信息。

### GPRMC - 推荐定位数据
```
$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
```
包含时间、状态、位置、速度、日期、磁偏角等信息。

## 算法说明

### Haversine 公式
用于计算两个经纬度坐标点之间的大圆距离：

```
a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
c = 2 ⋅ atan2(√a, √(1−a))
d = R ⋅ c
```

其中 φ 是纬度，λ 是经度，R 是地球半径（平均 6371 km）。

### 方位角计算
使用正切公式计算从点 1 到点 2 的初始方位角：

```
θ = atan2(sin Δλ ⋅ cos φ2, cos φ1 ⋅ sin φ2 − sin φ1 ⋅ cos φ2 ⋅ cos Δλ)
```

## 测试

运行单元测试：

```bash
python -m pytest tests/test_gps_parser.py -v
```

## 许可证

MIT License
