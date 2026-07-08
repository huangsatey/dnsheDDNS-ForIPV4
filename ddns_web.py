#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DNSHE DDNS 后台管理系统
提供 Web 界面进行配置管理、日志查看和服务控制
"""

from flask import Flask, render_template_string, request, jsonify, Response
import os
import subprocess
import configparser
import time
from datetime import datetime
from pathlib import Path
import threading
import signal

app = Flask(__name__)

# 路径配置 - 使用正确的路径（指向 IPv4 版本）
CONFIG_PATH = '/home/pi/ddns-dnshe/app/ddns-dnshe/app/ddns_config.ini'
LOG_FILE = '/home/pi/ddns-dnshe/data/logs/ddns.log'
PID_FILE = '/home/pi/ddns-dnshe/data/ddns.pid'  # 改到家目录
START_SCRIPT = '/home/pi/ddns-dnshe/start.sh'
STOP_SCRIPT = '/home/pi/ddns-dnshe/stop.sh'

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DNSHE DDNS 后台管理 (IPv4)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        header h1 { font-size: 2em; margin-bottom: 15px; }
        .ip-version-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            margin-bottom: 10px;
        }
        #status-bar {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            font-size: 1.1em;
        }
        .status-label { margin-right: 10px; }
        .status-indicator {
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
        }
        .status-running {
            background: #4CAF50;
            animation: pulse 2s infinite;
        }
        .status-stopped { background: #f44336; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .pid-info { margin-left: 15px; opacity: 0.9; }
        .control-panel {
            padding: 30px;
            background: #f5f5f5;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .btn-success { background: #4CAF50; color: white; }
        .btn-danger { background: #f44336; color: white; }
        .btn-warning { background: #ff9800; color: white; }
        .btn-info { background: #2196F3; color: white; }
        .btn-secondary { background: #757575; color: white; }
        .btn-primary { background: #667eea; color: white; }
        .btn-sm { padding: 8px 15px; font-size: 0.9em; }
        section { padding: 30px; border-bottom: 1px solid #e0e0e0; }
        h2 { color: #333; margin-bottom: 20px; font-size: 1.5em; }
        h3 { color: #555; margin-bottom: 15px; font-size: 1.2em; }
        .config-group {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .form-group { margin-bottom: 15px; }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: bold;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
        }
        .form-group input:focus, .form-group select:focus { outline: none; border-color: #667eea; }
        .form-group input[readonly] { background: #e0e0e0; cursor: not-allowed; }
        .form-actions { display: flex; gap: 10px; flex-wrap: wrap; }
        .logs-section { background: #fafafa; }
        .log-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .auto-refresh-label {
            display: flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
        }
        #log-container {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 15px;
            max-height: 500px;
            overflow-y: auto;
        }
        #log-content {
            color: #d4d4d4;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        footer {
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            color: #757575;
        }
        .message {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            animation: slideIn 0.3s;
        }
        .message.success { background: #4CAF50; }
        .message.error { background: #f44336; }
        .message.info { background: #2196F3; }
        @keyframes slideIn {
            from { transform: translateX(400px); }
            to { transform: translateX(0); }
        }
        @media (max-width: 768px) {
            body { padding: 10px; }
            header h1 { font-size: 1.5em; }
            .control-panel { flex-direction: column; }
            .btn { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="ip-version-badge">📍 IPv4 DDNS</div>
            <h1>🌐 DNSHE DDNS 后台管理系统</h1>
            <div id="status-bar">
                <span class="status-label">服务状态：</span>
                <span id="service-status" class="status-indicator">加载中...</span>
                <span id="pid-info" class="pid-info"></span>
            </div>
        </header>
        <section class="control-panel">
            <button class="btn btn-success" onclick="startService()">▶️ 启动</button>
            <button class="btn btn-danger" onclick="stopService()">⏹️ 停止</button>
            <button class="btn btn-warning" onclick="restartService()">🔄 重启</button>
            <button class="btn btn-info" onclick="checkStatus()">🔄 刷新状态</button>
        </section>
        <section class="config-section">
            <h2>⚙️ 配置管理</h2>
            <form id="config-form">
                <div class="config-group">
                    <h3>DNSHE API 配置</h3>
                    <div class="form-group">
                        <label for="api-key">API Key:</label>
                        <input type="text" id="api-key" name="api_key" required>
                    </div>
                    <div class="form-group">
                        <label for="api-secret">API Secret:</label>
                        <input type="text" id="api-secret" name="api_secret" required>
                    </div>
                    <div class="form-group">
                        <label for="subdomain-id">子域名 ID (Subdomain ID):</label>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <input type="number" id="subdomain-id" name="subdomain_id" required style="flex: 1;">
                            <button type="button" class="btn btn-info" onclick="autoFetchSubdomains()" style="padding: 10px 20px; white-space: nowrap;">🔍 自动获取</button>
                        </div>
                        <small style="color: #757575; display: block; margin-top: 5px;">点击"自动获取"按钮，根据 API Key 和 API Secret 自动获取子域名列表</small>
                    </div>
                    <div class="form-group">
                        <label for="record-type">DNS 记录类型:</label>
                        <select id="record-type" name="record_type" style="width:100%;padding:10px;border:1px solid #ddd;border-radius:5px;font-size:1em;">
                            <option value="A">A (IPv4)</option>
                            <option value="AAAA">AAAA (IPv6)</option>
                        </select>
                        <small style="color: #757575; display: block; margin-top: 5px;">当前版本仅支持 A 记录 (IPv4)</small>
                    </div>
                </div>
                <div class="config-group">
                    <h3>系统设置</h3>
                    <div class="form-group">
                        <label for="check-interval">检查间隔 (秒):</label>
                        <input type="number" id="check-interval" name="check_interval" value="600" required>
                    </div>
                    <div class="form-group">
                        <label for="dns-ttl">DNS TTL (秒):</label>
                        <input type="number" id="dns-ttl" name="dns_ttl" value="600" required>
                    </div>
                    <div class="form-group">
                        <label for="log-file">日志路径:</label>
                        <input type="text" id="log-file" name="log_file" readonly>
                    </div>
                </div>
                <div class="form-actions">
                    <button type="submit" class="btn btn-primary">💾 保存配置</button>
                    <button type="button" class="btn btn-secondary" onclick="loadConfig()">重新加载</button>
                </div>
            </form>
        </section>
        <section class="logs-section">
            <h2>📋 实时日志 <span id="log-lines-count">(0 行)</span></h2>
            <div class="log-controls">
                <button class="btn btn-sm btn-info" onclick="loadLogs()">🔄 刷新日志</button>
                <button class="btn btn-sm btn-danger" onclick="clearLogs()">🗑️ 清空日志</button>
                <label class="auto-refresh-label">
                    <input type="checkbox" id="auto-refresh" checked> 自动刷新
                </label>
            </div>
            <div id="log-container">
                <pre id="log-content">加载中...</pre>
            </div>
        </section>
        <footer><p>DNSHE DDNS 后台管理系统 (IPv4) &copy; 2026</p></footer>
    </div>
    <script>
        // 页面加载完成后获取状态
        window.addEventListener('load', function() {
            checkStatus();
            loadConfig();
            loadLogs();
            // 自动刷新日志
            setInterval(function() {
                if (document.getElementById('auto-refresh').checked) {
                    loadLogs();
                }
            }, 3000);
        });

        function showMessage(message, type) {
            var msg = document.createElement('div');
            msg.className = 'message ' + type;
            msg.textContent = message;
            document.body.appendChild(msg);
            setTimeout(function() {
                msg.remove();
            }, 5000);
        }

        function checkStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    var statusEl = document.getElementById('service-status');
                    var pidEl = document.getElementById('pid-info');
                    if (data.status === 'running') {
                        statusEl.textContent = '🟢 运行中';
                        statusEl.className = 'status-indicator status-running';
                        pidEl.textContent = 'PID: ' + data.pid;
                    } else if (data.status === 'stopped') {
                        statusEl.textContent = '🔴 已停止';
                        statusEl.className = 'status-indicator status-stopped';
                        pidEl.textContent = '';
                    } else {
                        statusEl.textContent = '⚠️ ' + data.status;
                        statusEl.className = 'status-indicator';
                        pidEl.textContent = '';
                    }
                })
                .catch(error => {
                    console.error('状态检查失败:', error);
                });
        }

        function startService() {
            fetch('/api/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('✅ 服务启动成功', 'success');
                    } else {
                        showMessage('❌ 启动失败: ' + data.message, 'error');
                    }
                    checkStatus();
                })
                .catch(error => {
                    showMessage('❌ 请求失败: ' + error, 'error');
                });
        }

        function stopService() {
            fetch('/api/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('✅ 服务已停止', 'success');
                    } else {
                        showMessage('❌ 停止失败: ' + data.message, 'error');
                    }
                    checkStatus();
                })
                .catch(error => {
                    showMessage('❌ 请求失败: ' + error, 'error');
                });
        }

        function restartService() {
            fetch('/api/restart', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('✅ 服务重启成功', 'success');
                    } else {
                        showMessage('❌ 重启失败: ' + data.message, 'error');
                    }
                    checkStatus();
                })
                .catch(error => {
                    showMessage('❌ 请求失败: ' + error, 'error');
                });
        }

        function loadConfig() {
            fetch('/api/config')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        var dnshe = data.config.dnshe || {};
                        var settings = data.config.settings || {};
                        document.getElementById('api-key').value = dnshe.api_key || '';
                        document.getElementById('api-secret').value = dnshe.api_secret || '';
                        document.getElementById('subdomain-id').value = dnshe.subdomain_id || '';
                        document.getElementById('check-interval').value = settings.check_interval || 600;
                        document.getElementById('dns-ttl').value = settings.dns_ttl || 600;
                        document.getElementById('log-file').value = '{{ log_file }}';
                    } else {
                        showMessage('加载配置失败: ' + data.message, 'error');
                    }
                })
                .catch(error => {
                    showMessage('加载配置失败: ' + error, 'error');
                });
        }

        // 配置表单提交
        document.getElementById('config-form').addEventListener('submit', function(e) {
            e.preventDefault();
            var formData = new FormData(this);
            var data = {
                dnshe: {
                    api_key: formData.get('api_key'),
                    api_secret: formData.get('api_secret'),
                    subdomain_id: formData.get('subdomain_id')
                },
                settings: {
                    check_interval: formData.get('check_interval'),
                    dns_ttl: formData.get('dns_ttl')
                }
            };
            fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('✅ 配置保存成功' + (data.need_restart ? '，请重启服务生效' : ''), 'success');
                } else {
                    showMessage('❌ 保存失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showMessage('❌ 保存失败: ' + error, 'error');
            });
        });

        function loadLogs() {
            fetch('/api/logs?lines=100')
                .then(response => response.json())
                .then(data => {
                    var content = document.getElementById('log-content');
                    if (data.success) {
                        content.textContent = data.logs || '暂无日志';
                        var lines = (data.logs || '').split('\\n').length - 1;
                        document.getElementById('log-lines-count').textContent = '(' + lines + ' 行)';
                    } else {
                        content.textContent = '加载日志失败: ' + data.message;
                    }
                })
                .catch(error => {
                    document.getElementById('log-content').textContent = '加载日志失败: ' + error;
                });
        }

        function clearLogs() {
            if (confirm('确定要清空日志吗？')) {
                fetch('/api/logs/clear', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showMessage('✅ 日志已清空', 'success');
                            loadLogs();
                        } else {
                            showMessage('❌ 清空失败: ' + data.message, 'error');
                        }
                    })
                    .catch(error => {
                        showMessage('❌ 清空失败: ' + error, 'error');
                    });
            }
        }

        function autoFetchSubdomains() {
            var apiKey = document.getElementById('api-key').value;
            var apiSecret = document.getElementById('api-secret').value;
            
            if (!apiKey || !apiSecret) {
                showMessage('⚠️ 请先填写 API Key 和 API Secret', 'error');
                return;
            }
            
            showMessage('🔍 正在获取子域名列表...', 'info');
            
            fetch('/api/auto_fetch_subdomains', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    var subdomains = data.subdomains || [];
                    if (subdomains.length === 0) {
                        showMessage('⚠️ 未找到子域名，请检查 API 配置', 'error');
                        return;
                    }
                    // 显示子域名列表供选择
                    var msg = '找到 ' + subdomains.length + ' 个子域名：\\n\\n';
                    subdomains.forEach(function(s, i) {
                        msg += (i+1) + '. ' + s.full_domain + ' (ID: ' + s.id + ')\\n';
                    });
                    msg += '\\n请输入要使用的子域名 ID：';
                    var selectedId = prompt(msg);
                    if (selectedId) {
                        document.getElementById('subdomain-id').value = selectedId;
                        showMessage('✅ 已选择子域名 ID: ' + selectedId, 'success');
                    }
                } else {
                    showMessage('❌ 获取失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showMessage('❌ 请求失败: ' + error, 'error');
            });
        }
    </script>
</body>
</html>'''

def fix_config():
    # 注意：实际使用时需要手动创建配置文件
    # 不要在代码中硬编码 API 密钥
    pass

def load_config():
    """加载配置文件"""
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        config.read(CONFIG_PATH, encoding='utf-8')
    return config

def save_config(config):
    """保存配置文件"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        config.write(f)

def get_service_status():
    """获取服务状态 - 通过 ps 命令查找"""
    try:
        # 使用 ps 查找 ddns_dnshe 进程（排除 ddns_web）
        result = subprocess.run(
            ['ps', 'aux'], 
            capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'ddns' in line and 'ddns_web' not in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = int(parts[1])
                        return {'status': 'running', 'pid': pid}
        return {'status': 'stopped', 'pid': None}
    except Exception as e:
        return {'status': 'error', 'pid': None, 'message': str(e)}

def execute_script(script_path):
    """执行脚本"""
    try:
        result = subprocess.run(['bash', script_path], capture_output=True, text=True, timeout=30)
        return {'success': result.returncode == 0, 'output': result.stdout, 'error': result.stderr}
    except subprocess.TimeoutExpired:
        return {'success': False, 'output': '', 'error': '脚本执行超时'}
    except Exception as e:
        return {'success': False, 'output': '', 'error': str(e)}

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE, log_file=LOG_FILE)

@app.route('/api/status')
def api_status():
    """获取服务状态"""
    status = get_service_status()
    return jsonify(status)

@app.route('/api/start', methods=['POST'])
def api_start():
    """启动服务 - 直接启动 Python 脚本"""
    status = get_service_status()
    if status['status'] == 'running':
        return jsonify({'success': False, 'message': '服务已在运行中'})
    
    # 查找 IPv4 版本的脚本
    script_paths = [
        '/home/pi/ddns-dnshe/app/ddns-dnshe/app/ddns_dnshe.py',  # 替换后的 IPv4 版本
        '/tmp/ddns_dnshe.py',
        '/home/pi/ddns-dnshe/app/ddns-dnshe/app/ddns_dnshe.py',
        '/home/pi/ddns-dnshe/app/ddns-dnshe/app/ddns_dnshe.py'
    ]
    
    script_path = None
    for path in script_paths:
        if os.path.exists(path):
            script_path = path
            break
    
    if not script_path:
        return jsonify({'success': False, 'message': '找不到 DDNS 脚本文件'})
    
    try:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        
        # 后台启动
        with open(LOG_FILE, 'a') as log:
            process = subprocess.Popen(
                ['python3', script_path],
                stdout=log,
                stderr=log,
                start_new_session=True
            )
        
        time.sleep(2)
        new_status = get_service_status()
        if new_status['status'] == 'running':
            return jsonify({'success': True, 'message': '服务启动成功', 'new_status': new_status})
        else:
            return jsonify({'success': False, 'message': '服务启动失败，请检查日志'})
    except Exception as e:
        return jsonify({'success': False, 'message': f"启动失败：{str(e)}"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """停止服务 - 直接 kill 进程"""
    status = get_service_status()
    if status['status'] == 'stopped':
        return jsonify({'success': False, 'message': '服务已停止'})
    
    try:
        # 使用 pkill 停止进程
        # 精确停止 DDNS 进程（不影响 Web 后台）
        result = subprocess.run(
            ['bash', '-c', "ps aux | grep '[d]dns' | grep -v 'web' | awk '{print $2}' | xargs kill 2>/dev/null"],
            capture_output=True, text=True
        )
        time.sleep(1)
        new_status = get_service_status()
        if new_status['status'] == 'stopped':
            return jsonify({'success': True, 'message': '服务停止成功', 'new_status': {'status': 'stopped', 'pid': None}})
        else:
            return jsonify({'success': False, 'message': '停止失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f"停止失败：{str(e)}"})

@app.route('/api/restart', methods=['POST'])
def api_restart():
    """重启服务"""
    # 先停止
    stop_result = api_stop()
    time.sleep(1)
    
    # 再启动
    start_result = api_start()
    return start_result

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """获取配置"""
    try:
        config = load_config()
        dnshe_config = dict(config['DNSHE']) if 'DNSHE' in config else {}
        settings_config = dict(config['DDNS']) if 'DDNS' in config else {}
        return jsonify({'success': True, 'config': {'dnshe': dnshe_config, 'settings': settings_config}})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/config', methods=['POST'])
def api_save_config():
    """保存配置"""
    try:
        data = request.get_json()
        config = load_config()
        if 'dnshe' in data:
            if 'DNSHE' not in config:
                config['DNSHE'] = {}
            for key, value in data['dnshe'].items():
                config['DNSHE'][key] = str(value)
        if 'settings' in data:
            if 'DDNS' not in config:
                config['DDNS'] = {}
            for key, value in data['settings'].items():
                config['DDNS'][key] = str(value)
        save_config(config)
        status = get_service_status()
        need_restart = status['status'] == 'running'
        return jsonify({'success': True, 'message': '配置保存成功' + ('（需重启服务才能生效）' if need_restart else ''), 'need_restart': need_restart})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    """获取日志"""
    try:
        lines = int(request.args.get('lines', 100))
        if not os.path.exists(LOG_FILE):
            return jsonify({'success': True, 'logs': '', 'message': '日志文件不存在'})
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
        return jsonify({'success': True, 'logs': ''.join(logs)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auto_fetch_subdomains', methods=['POST'])
def api_auto_fetch_subdomains():
    """自动获取子域名列表"""
    import requests
    
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        api_secret = data.get('api_secret', '').strip()
        
        if not api_key or not api_secret:
            return jsonify({
                'success': False,
                'message': 'API Key 和 API Secret 不能为空'
            })
        
        # 调用 DNSHE API 获取子域名列表
        url = "https://api005.dnshe.com/index.php"
        params = {
            'm': 'domain_hub',
            'endpoint': 'subdomains',
            'action': 'list'
        }
        headers = {
            'X-API-Key': api_key,
            'X-API-Secret': api_secret,
            'User-Agent': 'Mozilla/5.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('success'):
            subdomains = result.get('subdomains', [])
            
            # 格式化返回数据
            subdomain_list = []
            for sub in subdomains:
                subdomain_list.append({
                    'id': sub['id'],
                    'name': sub['subdomain'],
                    'rootdomain': sub['rootdomain'],
                    'full_domain': sub['full_domain'],
                    'status': sub['status']
                })
            
            return jsonify({
                'success': True,
                'message': f'成功获取 {len(subdomain_list)} 个子域名',
                'subdomains': subdomain_list
            })
        else:
            return jsonify({
                'success': False,
                'message': f'API 请求失败：{result}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'请求异常：{str(e)}'
        })

@app.route('/api/logs/clear', methods=['POST'])
def api_clear_logs():
    """清空日志"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                f.write('')
            return jsonify({'success': True, 'message': '日志已清空'})
        else:
            return jsonify({'success': True, 'message': '日志文件不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)