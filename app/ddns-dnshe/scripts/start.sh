#!/bin/bash

set -e

# 树莓派实际路径
APP_ROOT="/home/pi/ddns-dnshe/app/ddns-dnshe"
DATA_DIR="/home/pi/ddns-dnshe/data"
LOG_FILE="${DATA_DIR}/logs/ddns.log"
PID_FILE="${DATA_DIR}/ddns.pid"

# 检查是否已运行
if [ -f ${PID_FILE} ]; then
    PID=$(cat ${PID_FILE})
    if ps -p ${PID} > /dev/null 2>&1; then
        echo "ℹ️ DNSHE DDNS已运行（PID：${PID}）"
        exit 0
    else
        rm -f ${PID_FILE}
    fi
fi

# 确保日志目录存在
mkdir -p ${DATA_DIR}/logs

# 后台启动程序
nohup python3 ${APP_ROOT}/app/ddns_dnshe.py >> ${LOG_FILE} 2>&1 &
echo $! > ${PID_FILE}

# 等待一秒确认启动
sleep 1
if ps -p $(cat ${PID_FILE}) > /dev/null 2>&1; then
    echo "✅ DNSHE DDNS启动成功！"
    echo "📄 日志路径：${LOG_FILE}"
    echo "📌 PID: $(cat ${PID_FILE})"
else
    echo "❌ 启动失败，请检查日志：${LOG_FILE}"
    rm -f ${PID_FILE}
    exit 1
fi