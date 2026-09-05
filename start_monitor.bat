@echo off
chcp 65001 >nul
echo ========================================
echo   GPS 定位监控系统 - 启动服务器
echo ========================================
echo.
echo 正在启动 HTTP 服务器...
echo 请在手机浏览器中访问: http://[你的电脑IP]:8080/gps_monitor.html
echo.
echo 查看本机 IP 地址:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    echo   %%a
)
echo.
echo 按 Ctrl+C 停止服务器
echo.

cd /d "%~dp0"

REM 使用 Python 启动简单 HTTP 服务器
python -m http.server 8080

pause
