#!/bin/bash
set -e

WEB_SCRIPT="/home/pi/ddns-dnshe/ddns_web.py"
PID_FILE="/home/pi/ddns-dnshe/data/ddns_web.pid"
LOG_FILE="/home/pi/ddns-dnshe/data/logs/ddns_web.log"

mkdir -p /home/pi/ddns-dnshe/data/logs

if [ -f ${PID_FILE} ]; then
    PID=$(cat ${PID_FILE})
    if ps -p ${PID} > /dev/null 2>&1; then
        echo "ℹ️ Web 后台已运行（PID：${PID}）"
        echo "🌐 http://$(hostname -I | awk '{print $1}'):5000"
        exit 0
    else
        rm -f ${PID_FILE}
    fi
fi

if [ ! -f ${WEB_SCRIPT} ]; then
    echo "❌ 错误：找不到 Web 脚本 ${WEB_SCRIPT}"
    exit 1
fi

nohup python3 ${WEB_SCRIPT} >> ${LOG_FILE} 2>&1 &
echo $! > ${PID_FILE}

sleep 1
if ps -p $(cat ${PID_FILE}) > /dev/null 2>&1; then
    echo "✅ Web 后台启动成功！"
    echo "🌐 http://$(hostname -I | awk '{print $1}'):5000"
    echo "📄 日志：${LOG_FILE}"
else
    echo "❌ 启动失败，请检查日志"
    rm -f ${PID_FILE}
    exit 1
fi
