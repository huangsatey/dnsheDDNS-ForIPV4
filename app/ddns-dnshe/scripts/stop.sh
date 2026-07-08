#!/bin/bash

set -e

DATA_DIR="/home/pi/ddns-dnshe/data"
PID_FILE="${DATA_DIR}/ddns.pid"

if [ -f ${PID_FILE} ]; then
    PID=$(cat ${PID_FILE})
    if ps -p ${PID} > /dev/null 2>&1; then
        echo "🟢 运行中（PID：${PID}）"
        # 显示进程运行时间
        ps -p ${PID} -o etime= 2>/dev/null | xargs echo "⏱️ 运行时间:"
        exit 0
    else
        rm -f ${PID_FILE}
        echo "🔴 已停止（清理残留PID）"
        exit 1
    fi
else
    echo "🔴 已停止"
    exit 1
fi