# GPS Monitor APK

纯本地离线 GPS 定位监控 Android 应用，实时显示经纬度、速度、海拔，自动识别所在省份，并提供离线地图可视化。

## 功能特性

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

## 下载安装

1. 前往 [Releases](../../releases) 下载最新 `app-debug.apk`
2. 安装到 Android 设备（需要允许"未知来源"）
3. 首次打开授予**位置权限**（精确位置 + 粗略位置）

## 使用说明

1. 点击 **🚀 开始定位** 启动 GPS 追踪
2. 静置或移动，观察省份识别和方向变化
3. 点击 **🔄 切换算法** 对比三种模式效果
4. 点击 **⏹️ 停止** 暂停追踪
5. 点击 **🗑️ 清空** 清除历史记录

### 算法选择建议

- **静止或低速**（< 5 km/h）：用 **矩形边界**
- **高速移动**（> 18 km/h）：用 **速度矢量** 或 **混合对比**
- **省界附近**：用 **混合对比**，自动对比两种结果

## 项目结构

```
gps/
├── app/
│   ├── src/main/
│   │   ├── java/com/gps/monitor/
│   │   │   ├── MainActivity.java       # 主界面（纯原生 UI）
│   │   │   ├── ProvinceMap.java         # 离线地图引擎（绘制省份红点）
│   │   │   └── ProvinceInferencer.java  # 省份推断算法（三种模式）
│   │   ├── res/                         # 资源（布局、颜色、图标）
│   │   └── assets/
│   │       └── china_map.png            # 内置中国地图（1080×700）
│   ├── build.gradle                     # 模块级构建配置
│   └── proguard-rules.pro
├── .github/workflows/build-apk.yml      # GitHub Actions 自动构建
└── README.md                            # 项目文档

```

## 技术栈

- **Android 原生**：Java + Gradle + Android SDK
- **最低版本**：Android 7.0（API 24）
- **目标版本**：Android 14（API 34）
- **位置权限**：`ACCESS_FINE_LOCATION` + `ACCESS_COARSE_LOCATION`
- **地图数据**：内置 34 省边界框 + 省会坐标（离线）
- **自动构建**：GitHub Actions（每次 push 自动打包 Debug APK）

## 开发与打包

### 本地构建

```bash
./gradlew clean assembleDebug
# APK 输出到 app/build/outputs/apk/debug/app-debug.apk
```

### GitHub Actions

Push 到 `main` 分支自动触发构建，Artifacts 中下载 `gps-monitor-apk.zip`。

## 算法原理

### 矩形边界法

```java
if (lon >= p.minLon && lon <= p.maxLon && lat >= p.minLat && lat <= p.maxLat) {
    return p.name; // 落在省份矩形框内
}
```

### 速度矢量法

```java
// 1. 10秒采样
// 2. 计算 Haversine 距离和方位角
// 3. 过滤在运动方向 ±60° 内的省份
// 4. 计算到边界的最近距离，取最近省份
// 5. 沿方向延伸 50km，预测目标省份
```

### 混合对比法

```java
if (!boundsResult.equals(vectorResult)) {
    // 不一致时，取距离边界更近的省份
    // 矩形距离 < 10km → 信矩形，否则信矢量
}
```

## 已知限制

- 省份边界为**简化矩形框**，交界地带可能有误差（如河北/山西边界）
- 离线地图为**静态 PNG**，不显示详细地级市边界
- 方向预测基于 10 秒采样，静止或低速时不触发
- Debug APK 签名仅用于测试，安装需手动允许未知来源

## TODO

- [ ] 用真实 GeoJSON 多边形替换矩形边界（精度提升）
- [ ] 支持 OpenStreetMap 离线瓦片（四级缩放）
- [ ] 轨迹导出 KML/GPX
- [ ] 后台持续追踪 + 通知栏常驻
- [ ] 地图上绘制历史轨迹线

## 许可证

MIT License
