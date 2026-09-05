#!/data/data/com.termux/files/usr/bin/bash
# GPS 定位监控 - Termux 一键启动脚本
# 使用方法：在 Termux 中进入项目目录后运行 ./start_gps.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "   GPS 定位监控 - 手机端启动"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python &> /dev/null; then
    echo -e "${RED}错误：未安装 Python${NC}"
    echo "请先在 Termux 中运行：pkg install python"
    exit 1
fi

# 检查定位权限
echo -e "${YELLOW}检查权限...${NC}"
if [ ! -d "$PREFIX/var/lib/proot" ]; then
    echo -e "${YELLOW}提示：请确保已授予 Termux 位置权限${NC}"
fi

# 唤醒锁（防止手机休眠导致定位中断）
echo -e "${GREEN}申请唤醒锁...${NC}"
termux-wake-lock 2>/dev/null || true

# 获取本机 IP
LOCAL_IP=$(ifconfig wlan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1)
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="localhost"
fi

# 启动 HTTP 服务器
echo -e "${GREEN}启动 GPS 监控服务...${NC}"
echo ""
echo "========================================"
echo "   访问地址："
echo "   手机浏览器打开：http://localhost:8080/gps_monitor.html"
echo "   电脑浏览器打开：http://$LOCAL_IP:8080/gps_monitor.html"
echo "========================================"
echo ""
echo -e "${YELLOW}提示：${NC}"
echo "1. 手机浏览器需允许定位权限"
echo "2. MIUI 用户：请在最近任务页锁定 Termux，并关闭电池优化"
echo "3. 按 Ctrl+C 停止服务"
echo ""

# 启动服务器
python -m http.server 8080

# 清理
termux-wake-unlock 2>/dev/null || true
echo ""
echo "服务已停止"
