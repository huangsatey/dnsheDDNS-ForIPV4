
#!/bin/bash

set -e

# 树莓派实际路径
APP_ROOT="/home/pi/ddns-dnshe/app/ddns-dnshe"
DATA_ROOT="/home/pi/ddns-dnshe/data"

echo "⚠️ 即将卸载 DNSHE DDNS"
echo "这将停止服务并删除所有相关文件"
echo ""
read -p "确认卸载？(y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消卸载"
    exit 1
fi

# 停止服务
if [ -f ${APP_ROOT}/scripts/stop.sh ]; then
    ${APP_ROOT}/scripts/stop.sh
else
    # 直接停止
    PID_FILE="${DATA_ROOT}/ddns.pid"
    if [ -f ${PID_FILE} ]; then
        PID=$(cat ${PID_FILE})
        kill ${PID} 2>/dev/null || true
        rm -f ${PID_FILE}
    fi
fi

# 删除安装目录
echo "🗑️ 删除应用文件..."
rm -rf ${APP_ROOT}

# 询问是否删除数据（日志等）
read -p "是否删除数据文件（日志、PID等）？(y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ${DATA_ROOT}
    echo "✅ 已删除数据文件"
fi

echo "✅ DNSHE DDNS卸载成功！"