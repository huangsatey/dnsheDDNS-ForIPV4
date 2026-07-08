#!/usr/bin/env python3
import requests
import json
import time
import configparser
import os
import socket
import fcntl
import struct
from datetime import datetime

# 禁用SSL警告
requests.packages.urllib3.disable_warnings()

CONFIG_PATH = '/home/pi/ddns-dnshe/app/ddns-dnshe/app/ddns_config.ini'
LOG_FILE = '/home/pi/ddns-dnshe/data/logs/ddns.log'

def load_config():
    """加载配置文件"""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_PATH):
        config['DNSHE'] = {
            'api_key': 'YOUR_API_KEY_HERE',
            'api_secret': 'YOUR_API_SECRET_HERE',
            'subdomain_id': '229726',
            'ttl': '600'
        }
        config['SETTINGS'] = {
            'check_interval': '30',
            'log_file': LOG_FILE
        }
        # 确保目录存在
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            config.write(f)
        print(f"✅ 已创建默认配置文件: {CONFIG_PATH}")
    config.read(CONFIG_PATH, encoding='utf-8')
    return config

def log(message, level="INFO"):
    """统一日志输出"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    try:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"⚠️ 写入日志失败: {e}")

def is_private_ip(ip):
    """判断是否为私有IP或Tailscale IP"""
    if not ip:
        return True
    
    # 过滤Tailscale IP段 (100.64.0.0/10)
    if ip.startswith('100.'):
        parts = ip.split('.')
        if len(parts) >= 2:
            second = int(parts[1])
            if 64 <= second <= 127:  # 100.64.0.0 - 100.127.255.255
                return True
    
    # 过滤标准私有IP段
    if ip.startswith(('192.168.', '10.', '127.')):
        return True
    
    # 过滤172.16-172.31内网段
    if ip.startswith('172.'):
        parts = ip.split('.')
        if len(parts) >= 2:
            second = int(parts[1])
            if 16 <= second <= 31:
                return True
    
    return False

def get_local_ipv4():
    """从本地网卡获取公网IPv4（排除内网和Tailscale）"""
    try:
        # 获取所有网络接口，排除loopback、docker和Tailscale接口
        exclude_interfaces = ['lo', 'docker0', 'tailscale0', 'ts']  # Tailscale接口通常以tailscale或ts开头
        interfaces = []
        
        for ifname_tuple in socket.if_nameindex():
            ifname = ifname_tuple[1]
            # 检查是否应该排除此接口
            should_exclude = False
            for exclude in exclude_interfaces:
                if ifname.startswith(exclude):
                    should_exclude = True
                    break
            if not should_exclude:
                interfaces.append(ifname)
        
        log(f"📡 扫描网络接口: {interfaces}", "DEBUG")
        
        for ifname in interfaces:
            try:
                # 创建IPv4套接字
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # 获取接口的IPv4地址
                addr = socket.inet_ntoa(fcntl.ioctl(
                    s.fileno(),
                    0x8915,  # SIOCGIFADDR
                    struct.pack('256s', ifname.encode('utf-8'))
                )[20:24])
                
                # 检查是否为有效的公网IP
                if not is_private_ip(addr):
                    log(f"✅ 从接口 {ifname} 获取到公网IPv4: {addr}", "INFO")
                    return addr
                else:
                    log(f"ℹ️ 接口 {ifname} 的IP {addr} 是私有IP，已跳过", "DEBUG")
            except Exception as e:
                log(f"⚠️ 读取接口 {ifname} 失败: {str(e)}", "DEBUG")
                continue
                
    except Exception as e:
        log(f"本地获取IPv4失败: {str(e)}", "DEBUG")
    return None

def get_public_ipv4():
    """混合方式获取IPv4（先本地，后外部）"""
    # 1. 先从本地网卡获取（已排除Tailscale）
    local_ipv4 = get_local_ipv4()
    if local_ipv4:
        log(f"✅ 本地网卡获取IPv4: {local_ipv4}", "INFO")
        return local_ipv4
    
    # 2. 外部接口获取（缩短超时到5秒）
    ipv4_urls = [
        "https://api.ipify.org",
        "https://ipv4.icanhazip.com",
        "https://ifconfig.me/ip",
        "https://api64.ipify.org"
    ]
    log("🔍 本地获取失败，尝试外部接口获取IPv4...", "INFO")
    for url in ipv4_urls:
        try:
            response = requests.get(
                url, 
                timeout=5,  # 缩短超时到5秒
                headers={'User-Agent': 'Mozilla/5.0'},
                verify=False
            )
            ipv4 = response.text.strip()
            # IPv4格式验证：包含点且不包含冒号
            if "." in ipv4 and ":" not in ipv4 and not is_private_ip(ipv4):
                log(f"✅ 外部接口{url}获取IPv4: {ipv4}", "INFO")
                return ipv4
        except Exception as e:
            log(f"❌ 外部接口{url}失败: {str(e)}", "DEBUG")
            continue
    
    log("❌ 所有方式都无法获取IPv4", "ERROR")
    return None

def get_a_record(subdomain_id, config):
    """获取现有A记录"""
    log(f"🔍 检查ID={subdomain_id}的A记录...", "INFO")
    api_key = config['DNSHE']['api_key']
    api_secret = config['DNSHE']['api_secret']
    api_url = "https://api005.dnshe.com/index.php"
    params = {
        'm': 'domain_hub',
        'endpoint': 'dns_records',
        'action': 'list',
        'subdomain_id': subdomain_id
    }
    headers = {
        'X-API-Key': api_key,
        'X-API-Secret': api_secret,
        'User-Agent': 'Mozilla/5.0'
    }
    
    try:
        response = requests.get(
            api_url, 
            params=params, 
            headers=headers, 
            timeout=10,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', data.get('data', []))
            for rec in records:
                if rec.get('type') == 'A' and rec.get('name') == '@':
                    log(f"✅ 找到现有A记录: {rec['content']}", "INFO")
                    return rec
        log(f"❌ 未找到A记录", "DEBUG")
    except Exception as e:
        log(f"❌ 获取A记录失败: {str(e)}", "ERROR")
    return None

def update_a_record(record_id, new_ipv4, config):
    """更新A记录"""
    log(f"🔄 尝试更新A记录(ID={record_id})到{new_ipv4}...", "INFO")
    api_key = config['DNSHE']['api_key']
    api_secret = config['DNSHE']['api_secret']
    ttl = int(config['DNSHE']['ttl'])
    api_url = "https://api005.dnshe.com/index.php"
    params = {
        'm': 'domain_hub',
        'endpoint': 'dns_records',
        'action': 'update',
        'id': record_id
    }
    headers = {
        'X-API-Key': api_key,
        'X-API-Secret': api_secret,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    payload = {
        'content': new_ipv4,
        'ttl': ttl
    }
    
    try:
        response = requests.post(
            api_url, 
            params=params, 
            headers=headers, 
            json=payload, 
            timeout=10,
            verify=False
        )
        result = response.json()
        if result.get('code') == 0 or result.get('success'):
            log(f"✅ IPv4更新成功: {new_ipv4}", "INFO")
            return True
        else:
            log(f"❌ IPv4更新失败: {result}", "ERROR")
    except Exception as e:
        log(f"❌ 更新A记录异常: {str(e)}", "ERROR")
    return False

def create_a_record(subdomain_id, new_ipv4, config):
    """创建A记录"""
    log(f"➕ 尝试创建A记录(ID={subdomain_id})为{new_ipv4}...", "INFO")
    api_key = config['DNSHE']['api_key']
    api_secret = config['DNSHE']['api_secret']
    ttl = int(config['DNSHE']['ttl'])
    api_url = "https://api005.dnshe.com/index.php"
    params = {
        'm': 'domain_hub',
        'endpoint': 'dns_records',
        'action': 'create'
    }
    headers = {
        'X-API-Key': api_key,
        'X-API-Secret': api_secret,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    payload = {
        'subdomain_id': subdomain_id,
        'type': 'A',
        'content': new_ipv4,
        'ttl': ttl,
        'name': '@'
    }
    
    try:
        response = requests.post(
            api_url, 
            params=params, 
            headers=headers, 
            json=payload, 
            timeout=10,
            verify=False
        )
        result = response.json()
        if result.get('code') == 0 or result.get('success'):
            log(f"✅ IPv4记录创建成功: {new_ipv4}", "INFO")
            return True
        else:
            log(f"❌ IPv4创建失败: {result}", "ERROR")
    except Exception as e:
        log(f"❌ 创建A记录异常: {str(e)}", "ERROR")
    return False

def main():
    """主程序"""
    # 先加载配置
    config = load_config()
    
    # 从配置读取参数
    check_interval = int(config['SETTINGS']['check_interval'])
    subdomain_id = int(config['DNSHE']['subdomain_id'])
    last_ipv4 = ""
    
    log("=== DDNS服务启动（IPv4）===", "INFO")
    log(f"🔧 配置信息：ID={subdomain_id}，检查间隔={check_interval}秒", "INFO")
    
    while True:
        log("========================================", "INFO")
        log("🔍 开始新一轮IPv4检查...", "INFO")
        
        # 1. 获取公网IPv4
        current_ipv4 = get_public_ipv4()
        if not current_ipv4:
            log("❌ 无法获取公网IPv4，10秒后重试", "ERROR")
            time.sleep(10)
            continue
        
        # 2. IPv4未变化则跳过
        if current_ipv4 == last_ipv4:
            log(f"ℹ️ IPv4未变化: {current_ipv4}", "INFO")
            time.sleep(check_interval)
            continue
        
        log(f"✅ 检测到新IPv4: {current_ipv4}（上次: {last_ipv4}）", "INFO")
        
        # 3. 检查现有A记录
        a_record = get_a_record(subdomain_id, config)
        
        # 4. 更新/创建IPv4记录
        success = False
        if a_record:
            success = update_a_record(a_record['id'], current_ipv4, config)
        else:
            success = create_a_record(subdomain_id, current_ipv4, config)
        
        # 5. 记录成功的IPv4
        if success:
            last_ipv4 = current_ipv4
        
        # 6. 间隔等待
        log(f"⏳ 等待{check_interval}秒后再次检查...", "INFO")
        time.sleep(check_interval)

if __name__ == "__main__":
    main()