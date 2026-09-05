[app]

# 应用标题
title = GPS Monitor

# 包名
package.name = gpsmonitor
package.domain = org.gps

# 源目录
source.dir = .

# 包含的文件
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,json,xml

# 版本
version = 1.0

# 依赖
requirements = python3,kivy,matplotlib,numpy,Pillow

# Android 配置
android.api = 34
android.minapi = 21
android.target = 34
android.ndk = 25b
android.sdk = 34

# 权限
android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# 架构
android.archs = arm64-v8a, armeabi-v7a

# 全屏
android.fullscreen = 1

# 方向
android.orientation = portrait

# 图标和启动画面
# android.icon = 
# android.private_storage = True

# 复制资产
android.add_assets = assets/

# 源码排除
source.exclude_exts = spec

[buildozer]
log_level = 2
warn_on_root = 1
