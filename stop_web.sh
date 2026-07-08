#!/bin/bash
set -e

PID_FILE="/home/pi/ddns-dnshe/data/ddns_web.pid"

if [ -f ${PID_FILE} ]; then
    PID=$(cat ${PID_FILE})
    if ps -p ${PID} > /dev/null 2>&1; then
        kill ${PID}
        # 等待进程结束
        sleep 2
        if ps -p ${PID} > /dev/null 2>&1; then
            kill -9 ${PID} 2>/dev/null || true
        fi
        rm -f ${PID_FILE}
        echo "✅ DNSHE DDNS Web 后台已停止"
    else
        rm -f ${PID_FILE}
        echo "ℹ️ DNSHE DDNS Web 后台未运行（清理残留 PID）"
    fi
else
    echo "ℹ️ DNSHE DDNS Web 后台未运行"
fi