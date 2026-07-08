#!/bin/bash

set -e

# 修改为实际路径
APP_ROOT="/home/pi/ddns-dnshe/app/ddns-dnshe"

# 创建数据目录（日志/运行状态）
mkdir -p /home/pi/ddns-dnshe/data/logs
chmod 755 /home/pi/ddns-dnshe/data/logs

# 赋予脚本执行权限
chmod +x ${APP_ROOT}/scripts/*.sh
chmod 600 ${APP_ROOT}/app/ddns_config.ini

# 安装Python依赖
if command -v pip3 &>/dev/null; then
    pip3 install requests flask -i https://pypi.tuna.tsinghua.edu.cn/simple --user
else
    sudo apt update && sudo apt install python3-pip -y
    pip3 install requests flask -i https://pypi.tuna.tsinghua.edu.cn/simple --user
fi

echo "✅ DNSHE DDNS (IPv4) 安装成功！"
echo ""
echo "📌 下一步操作："
echo "1. 编辑配置文件：vi ${APP_ROOT}/app/ddns_config.ini"
echo "   填写你的 API Key、API Secret 和子域名 ID"
echo ""
echo "2. 启动 DDNS 服务：${APP_ROOT}/scripts/start.sh"
echo ""
echo "3. 启动 Web 管理后台：python3 ${APP_ROOT}/app/ddns_web.py"
echo "   访问 http://你的IP:5000"