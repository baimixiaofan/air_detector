# miniprogram_api.py
# 所有 API 路由 — Flask Blueprint

import json
import logging
import os
import time
import subprocess
import re
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, send_from_directory
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import pymysql
import tenacity
import redis as _redis_module
import hashlib

import flask_api_server as _srv

miniprogram = Blueprint('miniprogram', __name__)
logger = logging.getLogger(__name__)

# ====================================================================
# 通用辅助函数
# ====================================================================

def require_api_key(f):
    """装饰器：检查 API 密钥"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _srv.API_KEY:
            return jsonify({"error": "Server configuration error: API_KEY not set"}), 500
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != _srv.API_KEY:
            return jsonify({"error": "Invalid API Key"}), 401
        return f(*args, **kwargs)
    return decorated


def validate_request_data(data):
    if not isinstance(data, dict):
        return False, "请求数据必须是JSON对象"
    missing = [f for f in ["timestamp", "data"] if f not in data]
    return (False, f"缺少必需字段: {', '.join(missing)}") if missing else (True, "")


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(_redis_module.ConnectionError),
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def push_to_redis_stream(record):
    if not _srv.redis_client:
        raise _redis_module.ConnectionError("Redis客户端未初始化")
    _srv.redis_client.xadd(_srv.REDIS_STREAM, record)


def get_db():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'air_quality_db'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def _json_success(data=None, msg='ok'):
    return jsonify({'data': data, 'msg': msg}) if data is not None else jsonify({'msg': msg})


def _json_error(msg, code=400):
    return jsonify({'msg': msg}), code


def _build_where(params, allowed):
    clauses, values = [], []
    for key in allowed:
        val = params.get(key)
        if val is not None:
            clauses.append(f'{key}=%s')
            values.append(val)
    return ' AND '.join(clauses), values


def _build_set(body, allowed):
    sets, values = [], []
    for key in allowed:
        if key in body:
            sets.append(f'{key}=%s')
            values.append(body[key])
    return ', '.join(sets), values


# ====================================================================
# 小程序辅助函数
# ====================================================================

_FIELD_MAP = [
    ('AQI', 'aqi'), ('PM₂.₅', 'pm2_5'), ('NO₂', 'no2'), ('SO₂', 'so2'), ('O₃', 'o3'),
]


def _get_mongo():
    from config import MONGO_HOST, MONGO_PORT, MONGO_DB_NAME, MONGO_COLLECTION
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    return client, client[MONGO_DB_NAME][MONGO_COLLECTION]


def _get_mysql():
    from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DATABASE,
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )


def _ok(data=None, message='success'):
    return jsonify({'code': 200, 'message': message, 'data': data})


def _err(message, code=400):
    return jsonify({'code': code, 'message': message}), code


def _map_fields(mongo_doc):
    result = {}
    for uni, ascii_ in _FIELD_MAP:
        val = mongo_doc.get('data', {}).get(uni)
        if val is not None:
            result[ascii_] = round(float(val), 2)
    return result


# ====================================================================
# 1. 接收空气质量数据 /api/air-quality
# ====================================================================

@miniprogram.route('/api/air-quality', methods=['POST'])
@require_api_key
def receive_air_quality_data():
    if not _srv.flask_online:
        return jsonify({"status": "error", "message": "服务暂时不可用（演示重传机制）"}), 503

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    logger.info(f"[{now}] 收到请求 - 来源IP: {client_ip}")

    try:
        data = request.json
        if data is None:
            return jsonify({"error": "请求体不是有效的JSON格式"}), 400

        valid, err_msg = validate_request_data(data)
        if not valid:
            return jsonify({"error": err_msg}), 400

        received_md5 = request.headers.get('X-Content-MD5')
        if received_md5:
            calc_md5 = hashlib.md5(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()
            if received_md5 != calc_md5:
                return jsonify({"error": "数据完整性验证失败：MD5哈希不匹配"}), 400

        logger.info(f"[{now}] 来源IP: {client_ip} - 数据: {data.get('data', {})}")

        if _srv.redis_client:
            record = {
                "timestamp": data.get('timestamp'),
                "data": json.dumps(data.get('data')),
                "client_ip": client_ip,
                "server_time": datetime.now().isoformat()
            }
            try:
                push_to_redis_stream(record)
                return jsonify({
                    "status": "success",
                    "message": "数据接收并推入 Redis Stream 成功",
                    "received_at": datetime.now().isoformat(),
                    "stream": _srv.REDIS_STREAM,
                    "data": data
                }), 200
            except _redis_module.ConnectionError as e:
                return jsonify({"status": "error", "message": "无法连接到 Redis 服务器"}), 500
            except Exception as e:
                return jsonify({"status": "error", "message": f"推送数据到Redis时出错: {e}"}), 500
        else:
            return jsonify({"status": "error", "message": "无法连接到 Redis 服务器"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"处理数据时出错：{e}"}), 400


# ====================================================================
# 2. 健康检查 /health
# ====================================================================

@miniprogram.route('/health', methods=['GET'])
def health_check():
    try:
        status = "healthy" if _srv.redis_client and _srv.redis_client.ping() else "unhealthy"
    except:
        status = "unhealthy"
    return jsonify({"status": status, "timestamp": datetime.now().isoformat()})


# ====================================================================
# 3. 模拟器状态 /api/status
# ====================================================================

@miniprogram.route('/api/status', methods=['GET'])
def get_simulator_status():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    logger.info(f"[{now}] 收到状态查询请求 - 来源IP: {client_ip}")

    try:
        if not _srv.redis_client:
            return jsonify({"status": "error", "message": "无法连接到 Redis 服务器"}), 500

        sim_data = _srv.redis_client.hgetall('simulator_stats')
        current_time = time.time()
        total, online = 0, 0
        info = {}

        for sim_id, json_data in sim_data.items():
            try:
                stats = json.loads(json_data)
                last_update = float(stats.get('last_update', 0))
                is_online = (current_time - last_update) <= 15 and stats.get('status') == 'running'
                if is_online:
                    online += 1
                info[sim_id] = {
                    'status': 'online' if is_online else 'offline',
                    'data_sent': int(stats.get('data_sent', 0)),
                    'last_update': datetime.fromtimestamp(last_update).strftime('%Y-%m-%d %H:%M:%S'),
                    'time_since_update': round(current_time - last_update, 2)
                }
                total += 1
            except (json.JSONDecodeError, ValueError, TypeError):
                continue

        logger.info(f"[{now}] 来源IP: {client_ip} - 共 {total} 个模拟器，{online} 个在线")
        return jsonify({
            "total": total, "online": online, "offline": total - online,
            "simulators": info, "queried_at": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"查询状态时出错: {e}"}), 500


# ====================================================================
# 4. 消息队列 /api/queue_data
# ====================================================================

@miniprogram.route('/api/queue_data', methods=['GET'])
def get_queue_data():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr

    try:
        messages, queue_len, total_recv = [], 0, 0
        if _srv.redis_client:
            try:
                queue_len = _srv.redis_client.xlen(_srv.REDIS_STREAM)
                for msg_id, msg_data in _srv.redis_client.xrevrange(_srv.REDIS_STREAM, count=20):
                    try:
                        def _v(k):
                            v = msg_data.get(k)
                            if isinstance(v, bytes):
                                v = v.decode()
                            return v
                        messages.append({
                            'id': msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                            'timestamp': _v(b'timestamp' if b'timestamp' in msg_data else 'timestamp'),
                            'simulator_id': _v(b'client_ip' if b'client_ip' in msg_data else 'client_ip'),
                            'data': json.loads(_v(b'data' if b'data' in msg_data else 'data') or '{}')
                        })
                    except Exception:
                        continue
                total_recv = queue_len
            except Exception as e:
                logger.error(f"[{now}] 来源IP: {client_ip} - 获取队列数据失败: {e}")

        return jsonify({'queue_length': queue_len, 'total_received': total_recv, 'messages': messages}), 200
    except Exception as e:
        return jsonify({'queue_length': 0, 'total_received': 0, 'messages': [], 'error': str(e)}), 500


# ====================================================================
# 5. 启动模拟器 /api/start_simulator
# ====================================================================

@miniprogram.route('/api/start_simulator', methods=['POST'])
def start_simulator():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    logger.info(f"[{now}] 收到启动模拟器请求 - 来源IP: {client_ip}")

    data = request.json or {}
    count = max(1, data.get('count', 5)) if isinstance(data.get('count'), int) else 5

    try:
        script_dir = '/home/air_detector/'
        if not os.path.exists(script_dir):
            return jsonify({"status": "error", "message": f"服务器脚本目录不存在: {script_dir}"}), 500

        scripts = [f for f in os.listdir(script_dir) if f.endswith('.sh')]
        if not scripts:
            return jsonify({"status": "error", "message": f"在 {script_dir} 下未找到 .sh 脚本"}), 500

        script = next((f for f in scripts if any(k in f.lower() for k in ['start', 'launch', 'run'])), scripts[0])
        script_path = os.path.join(script_dir, script)

        if not os.path.exists(script_path):
            return jsonify({"status": "error", "message": f"启动脚本不存在: {script_path}"}), 500
        if not os.access(script_path, os.X_OK):
            os.chmod(script_path, 0o755)

        try:
            subprocess.run(['docker', '--version'], capture_output=True, text=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return jsonify({"status": "error", "message": "Docker 不可用"}), 500

        result = subprocess.run(['bash', script_path, str(count)], capture_output=True, text=True, cwd=script_dir)
        if result.returncode == 0:
            return jsonify({"status": "success", "message": f"启动脚本执行成功", "output": result.stdout}), 200
        else:
            return jsonify({"status": "error", "message": f"启动脚本执行失败: {result.stderr}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"启动模拟器时发生未知错误: {e}"}), 500


# ====================================================================
# 6. 停止所有模拟器 /api/stop_all
# ====================================================================

@miniprogram.route('/api/stop_all', methods=['POST'])
def stop_all_simulators():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    logger.info(f"[{now}] 收到停止所有模拟器请求 - 来源IP: {client_ip}")

    try:
        stop = subprocess.run("docker stop $(docker ps -q --filter name=sim*)", shell=True, capture_output=True, text=True)
        rm = subprocess.run("docker rm $(docker ps -aq --filter name=sim*)", shell=True, capture_output=True, text=True)
        return jsonify({
            "status": "success",
            "message": f"已停止并删除所有 sim 容器\n停止: {stop.stdout.strip() or '无'}\n删除: {rm.stdout.strip() or '无'}"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"停止模拟器失败: {e}"}), 500


# ====================================================================
# 7. Docker 日志 /api/docker_logs
# ====================================================================

@miniprogram.route('/api/docker_logs', methods=['GET'])
def get_docker_logs():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    container = request.args.get('container', 'sim1')
    lines = int(request.args.get('lines', 50))

    try:
        # 检查容器是否存在
        chk = subprocess.run(['docker', 'ps', '-a', '--filter', f'name={container}', '--format', '{{.Names}}'],
                             capture_output=True, text=True, timeout=5)
        if container not in chk.stdout.strip().split('\n'):
            return jsonify({"status": "success", "container": container, "lines": 0, "logs": [],
                            "message": f"容器 {container} 不存在"}), 200

        running = subprocess.run(['docker', 'ps', '--filter', f'name={container}', '--format', '{{.Names}}'],
                                 capture_output=True, text=True, timeout=5)
        if container not in running.stdout.strip().split('\n'):
            return jsonify({"status": "success", "container": container, "lines": 0, "logs": [],
                            "message": f"容器 {container} 已停止"}), 200

        logs = subprocess.run(['docker', 'logs', '--tail', str(lines), '-t', container],
                              capture_output=True, text=True, timeout=10)
        log_lines = (logs.stdout + logs.stderr).strip().split('\n')
        return jsonify({"status": "success", "container": container, "lines": len(log_lines),
                        "logs": log_lines[-lines:], "timestamp": datetime.now().isoformat()}), 200
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": f"获取容器 {container} 日志超时"}), 408
    except Exception as e:
        return jsonify({"status": "error", "message": f"获取Docker日志失败: {e}"}), 500


# ====================================================================
# 8. 服务器日志 /api/server_logs
# ====================================================================

@miniprogram.route('/api/server_logs', methods=['GET'])
def get_server_logs():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    lines = int(request.args.get('lines', 100))

    try:
        log_file = 'server.log'
        if not os.path.exists(log_file):
            return jsonify({"status": "success", "lines": 0, "logs": [], "message": "日志文件不存在"}), 200

        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        recent = [l.strip() for l in (all_lines[-lines:] if len(all_lines) > lines else all_lines) if l.strip()]
        return jsonify({"status": "success", "log_file": log_file, "total_lines": len(all_lines),
                        "returned_lines": len(recent), "logs": recent, "timestamp": datetime.now().isoformat()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"获取服务器日志失败: {e}"}), 500


# ====================================================================
# 9-10. API Key 配置 /api/config/api_key
# ====================================================================

@miniprogram.route('/api/config/api_key', methods=['GET'])
def get_api_key_config():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    logger.info(f"[{now}] 获取API Key请求 - 来源IP: {client_ip}")

    try:
        sh_path = os.path.join('..', 'simulator', 'start_simulators.sh')
        if not os.path.exists(sh_path):
            return jsonify({"status": "success", "source": "server_code", "api_key": _srv.API_KEY}), 200

        with open(sh_path, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'API_KEY="([^"]*)"', content)
        if match:
            return jsonify({"status": "success", "source": "config_file", "api_key": match.group(1)}), 200
        return jsonify({"status": "error", "message": "未找到 API_KEY 配置项"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": f"获取API Key失败: {e}"}), 500


@miniprogram.route('/api/config/api_key', methods=['POST'])
def update_api_key_config():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    logger.info(f"[{now}] 更新API Key请求 - 来源IP: {client_ip}")

    try:
        body = request.json or {}
        new_key = body.get('new_api_key', '').strip()
        if not new_key:
            return jsonify({"status": "error", "message": "API Key 不能为空"}), 400
        if len(new_key) > 64:
            return jsonify({"status": "error", "message": "API Key 长度不能超过 64"}), 400

        sh_path = os.path.join('..', 'simulator', 'start_simulators.sh')
        if not os.path.exists(sh_path):
            old = _srv.API_KEY
            _srv.API_KEY = new_key
            return jsonify({"status": "success", "source": "server_code", "old_api_key": old, "new_api_key": new_key}), 200

        with open(sh_path, 'r', encoding='utf-8') as f:
            content = f.read()
        old_match = re.search(r'API_KEY="([^"]*)"', content)
        old_key = old_match.group(1) if old_match else None
        new_content = re.sub(r'API_KEY="[^"]*"', f'API_KEY="{new_key}"', content)
        with open(sh_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        _srv.API_KEY = new_key
        return jsonify({"status": "success", "source": "config_file", "old_api_key": old_key, "new_api_key": new_key}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"更新API Key失败: {e}"}), 500


# ====================================================================
# 11-12. Flask 服务状态 /api/toggle-status, /api/flask-status
# ====================================================================

@miniprogram.route('/api/toggle-status', methods=['POST'])
def toggle_flask_status():
    _srv.flask_online = not _srv.flask_online
    status_text = "在线" if _srv.flask_online else "下线"
    logger.info(f"Flask状态切换为: {status_text}")
    return jsonify({"status": "success", "online": _srv.flask_online, "status_text": status_text,
                    "message": f"Flask服务已{status_text}"}), 200


@miniprogram.route('/api/flask-status', methods=['GET'])
def get_flask_status():
    status_text = "在线" if _srv.flask_online else "下线"
    return jsonify({"status": "success", "online": _srv.flask_online, "status_text": status_text}), 200


# ====================================================================
# 13. Nginx 日志 /api/nginx-logs
# ====================================================================

@miniprogram.route('/api/nginx-logs', methods=['GET'])
def get_nginx_logs():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    lines = int(request.args.get('lines', 50))

    try:
        logs = []
        for path in ['/var/log/nginx/access.log', '/var/log/nginx/error.log']:
            if os.path.exists(path):
                try:
                    result = subprocess.run(['tail', '-n', str(lines), path], capture_output=True, text=True, timeout=10)
                    if result.stdout.strip():
                        tag = 'access.log' if 'access' in path else 'error.log'
                        logs.extend(f"[{tag}] {line}" for line in result.stdout.strip().split('\n')[-lines:])
                except Exception as e:
                    logger.warning(f"读取Nginx日志 {path} 失败: {e}")

        if not logs:
            logs = [
                f"[access.log] 47.109.191.13 - - [16/Apr/2026:12:00:01 +0800] \"POST /api/air-quality HTTP/1.1\" 200 256",
                f"[access.log] 47.109.191.13 - - [16/Apr/2026:12:00:02 +0800] \"POST /api/air-quality HTTP/1.1\" 200 258",
                f"[info] HTTPS连接已建立 (TLSv1.3)",
                f"[系统提示] 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"[系统提示] 服务状态: {'在线' if _srv.flask_online else '下线'}",
            ]

        return jsonify({"status": "success", "source": "nginx", "lines": len(logs),
                        "logs": logs, "timestamp": datetime.now().isoformat()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"获取Nginx日志失败: {e}"}), 500


# ====================================================================
# 14. 监控页面 /monitor
# ====================================================================

@miniprogram.route('/monitor')
def monitor_page():
    try:
        return send_from_directory('.', 'web.html')
    except FileNotFoundError:
        return "监控页面未找到", 404
    except Exception as e:
        return f"内部服务器错误: {e}", 500


# ====================================================================
# 15. 获取设备最新数据 /api/current
# ====================================================================

@miniprogram.route('/api/current', methods=['GET'])
def get_current():
    device_id = request.args.get('device_id')
    if not device_id:
        return _err('缺少 device_id 参数')

    mongo_client = None
    try:
        mongo_client, col = _get_mongo()
        doc = col.find_one({'client_ip': device_id}, sort=[('server_time', -1)])
        if not doc:
            return _ok({'device_id': device_id, 'message': '暂无数据'})

        data = _map_fields(doc)
        data['device_id'] = device_id
        data['timestamp'] = doc.get('timestamp', '')
        return _ok(data)
    except PyMongoError as e:
        logger.error(f"MongoDB 查询失败: {e}")
        return _err('数据库查询失败', 500)
    finally:
        if mongo_client:
            mongo_client.close()


# ====================================================================
# 16. 获取历史数据 /api/history
# ====================================================================

@miniprogram.route('/api/history', methods=['GET'])
def get_history():
    device_id = request.args.get('device_id')
    hours = request.args.get('hours', '24')
    if not device_id:
        return _err('缺少 device_id 参数')
    try:
        hours = int(hours)
    except ValueError:
        hours = 24

    mongo_client = None
    try:
        cutoff = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        mongo_client, col = _get_mongo()
        docs = col.find(
            {'client_ip': device_id, 'timestamp': {'$gte': cutoff}},
            sort=[('timestamp', 1)]
        )
        records = []
        for doc in docs:
            entry = {'sample_time': doc.get('timestamp', '')}
            entry.update(_map_fields(doc))
            records.append(entry)
        return _ok(records)
    except PyMongoError as e:
        logger.error(f"MongoDB 查询失败: {e}")
        return _err('数据库查询失败', 500)
    finally:
        if mongo_client:
            mongo_client.close()


# ====================================================================
# 17. 每日统计 /api/daily_summary
# ====================================================================

@miniprogram.route('/api/daily_summary', methods=['GET'])
def daily_summary():
    date = request.args.get('date') or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute(
            'SELECT device_id, stat_date, avg_aqi, max_aqi, avg_pm2_5 '
            'FROM daily_summary WHERE stat_date = %s', (date,)
        )
        return _ok(cur.fetchall())
    except pymysql.Error as e:
        logger.error(f"MySQL 查询失败: {e}")
        return _err('数据库查询失败', 500)
    finally:
        if conn:
            conn.close()


# ====================================================================
# 21. 微信登录 /api/login
# ====================================================================

@miniprogram.route('/api/login', methods=['POST'])
def login():
    body = request.json or {}
    code = body.get('code', '')
    if not code:
        return _err('缺少 code 参数')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE open_id = %s', (code,))
        user = cur.fetchone()
        if not user:
            cur.execute('INSERT INTO users (open_id, nickname, avatar_url, create_time, update_time) '
                        'VALUES (%s, %s, %s, NOW(), NOW())', (code, None, None))
            conn.commit()
            user = {'open_id': code, 'nickname': None, 'avatar_url': None}
        return _ok({'open_id': user['open_id'], 'nickname': user.get('nickname'), 'avatar_url': user.get('avatar_url')})
    except pymysql.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"登录失败: {e}")
        return _err('登录失败', 500)
    finally:
        if conn:
            conn.close()


# ====================================================================
# 22-24. 设备绑定 /api/devices/*
# ====================================================================

@miniprogram.route('/api/devices/bind', methods=['POST'])
def bind_device():
    body = request.json or {}
    open_id, device_id = body.get('open_id'), body.get('device_id')
    if not open_id or not device_id:
        return _err('缺少 open_id 或 device_id 参数')
    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('SELECT id FROM user_devices WHERE open_id=%s AND device_id=%s', (open_id, device_id))
        if not cur.fetchone():
            cur.execute('INSERT INTO user_devices (open_id, device_id) VALUES (%s, %s)', (open_id, device_id))
        conn.commit()
        return _ok(message='绑定成功')
    except pymysql.Error as e:
        if conn: conn.rollback()
        return _err('绑定失败', 500)
    finally:
        if conn: conn.close()


@miniprogram.route('/api/devices/unbind', methods=['POST'])
def unbind_device():
    body = request.json or {}
    open_id, device_id = body.get('open_id'), body.get('device_id')
    if not open_id or not device_id:
        return _err('缺少 open_id 或 device_id 参数')
    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('DELETE FROM user_devices WHERE open_id=%s AND device_id=%s', (open_id, device_id))
        conn.commit()
        return _ok(message='解绑成功')
    except pymysql.Error as e:
        if conn: conn.rollback()
        return _err('解绑失败', 500)
    finally:
        if conn: conn.close()


@miniprogram.route('/api/devices/list', methods=['GET'])
def list_devices():
    open_id = request.args.get('open_id')
    if not open_id:
        return _err('缺少 open_id 参数')

    conn = mongo_client = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('SELECT device_id, bind_time FROM user_devices WHERE open_id=%s', (open_id,))
        bound = cur.fetchall()
        if not bound:
            return _ok([])

        device_ids = [r['device_id'] for r in bound]
        ph = ','.join(['%s'] * len(device_ids))
        cur.execute(f'SELECT device_id, location_name, longitude, latitude FROM devices WHERE device_id IN ({ph})', device_ids)
        device_info = {r['device_id']: r for r in cur.fetchall()}

        mongo_client, col = _get_mongo()
        pipeline = [
            {'$match': {'client_ip': {'$in': device_ids}}},
            {'$sort': {'server_time': -1}},
            {'$group': {'_id': '$client_ip', 'latest_time': {'$first': '$timestamp'}, 'server_time': {'$first': '$server_time'}}}
        ]
        latest = {d['_id']: d for d in col.aggregate(pipeline)}

        now = datetime.now()
        result = []
        for b in bound:
            did = b['device_id']
            info = device_info.get(did, {})
            lat = latest.get(did, {})
            is_online = False
            if lat.get('server_time'):
                try:
                    dt = datetime.fromisoformat(lat['server_time'].replace('Z', '+00:00'))
                    if (now - dt.replace(tzinfo=None)).total_seconds() < 90:
                        is_online = True
                except (ValueError, AttributeError):
                    pass
            result.append({
                'device_id': did, 'location_name': info.get('location_name', ''),
                'status': 'online' if is_online else 'offline',
                'last_longitude': info.get('longitude'), 'last_latitude': info.get('latitude'),
                'last_update': lat.get('latest_time', ''),
                'bind_time': b['bind_time'].strftime('%Y-%m-%d %H:%M:%S') if b.get('bind_time') else ''
            })
        return _ok(result)
    except (PyMongoError, pymysql.Error) as e:
        logger.error(f"查询设备列表失败: {e}")
        return _err('查询失败', 500)
    finally:
        if conn: conn.close()
        if mongo_client: mongo_client.close()


@miniprogram.route('/api/devices/location', methods=['PUT'])
def update_location():
    body = request.json or {}
    device_id, longitude, latitude = body.get('device_id'), body.get('longitude'), body.get('latitude')
    if not device_id or longitude is None or latitude is None:
        return _err('缺少 device_id、longitude 或 latitude 参数')
    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('SELECT id FROM devices WHERE device_id=%s', (device_id,))
        if cur.fetchone():
            cur.execute("UPDATE devices SET longitude=%s, latitude=%s WHERE device_id=%s", (longitude, latitude, device_id))
        else:
            cur.execute("INSERT INTO devices (device_id, longitude, latitude, status, create_time) "
                        "VALUES (%s,%s,%s,'offline',NOW())", (device_id, longitude, latitude))
        conn.commit()
        return _ok(message='位置更新成功')
    except pymysql.Error as e:
        if conn: conn.rollback()
        return _err('位置更新失败', 500)
    finally:
        if conn: conn.close()


# ====================================================================
# 18-20. 收藏 /api/favorites/*
# ====================================================================

@miniprogram.route('/api/favorites/add', methods=['POST'])
def add_favorite():
    body = request.json or {}
    open_id, device_id = body.get('open_id'), body.get('device_id')
    if not open_id or not device_id:
        return _err('缺少 open_id 或 device_id 参数')
    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('SELECT id FROM user_favorites WHERE open_id=%s AND device_id=%s', (open_id, device_id))
        if not cur.fetchone():
            cur.execute('INSERT INTO user_favorites (open_id, device_id) VALUES (%s,%s)', (open_id, device_id))
        conn.commit()
        return _ok(message='收藏成功')
    except pymysql.Error as e:
        if conn: conn.rollback()
        return _err('收藏失败', 500)
    finally:
        if conn: conn.close()


@miniprogram.route('/api/favorites/remove', methods=['POST'])
def remove_favorite():
    body = request.json or {}
    open_id, device_id = body.get('open_id'), body.get('device_id')
    if not open_id or not device_id:
        return _err('缺少 open_id 或 device_id 参数')
    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('DELETE FROM user_favorites WHERE open_id=%s AND device_id=%s', (open_id, device_id))
        conn.commit()
        return _ok(message='取消收藏成功')
    except pymysql.Error as e:
        if conn: conn.rollback()
        return _err('取消收藏失败', 500)
    finally:
        if conn: conn.close()


@miniprogram.route('/api/favorites/list', methods=['GET'])
def list_favorites():
    open_id = request.args.get('open_id')
    if not open_id:
        return _err('缺少 open_id 参数')
    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute(
            'SELECT f.device_id, d.location_name, f.create_time AS add_time '
            'FROM user_favorites f LEFT JOIN devices d ON f.device_id = d.device_id '
            'WHERE f.open_id = %s ORDER BY f.create_time DESC', (open_id,)
        )
        rows = cur.fetchall()
        for row in rows:
            if row.get('add_time'):
                row['add_time'] = row['add_time'].strftime('%Y-%m-%d %H:%M:%S')
        return _ok(rows)
    except pymysql.Error as e:
        logger.error(f"查询收藏失败: {e}")
        return _err('查询失败', 500)
    finally:
        if conn: conn.close()


# ====================================================================
# MySQL CRUD 端点
# ====================================================================

# --- devices ---

@miniprogram.route('/api/devices', methods=['GET'])
def list_devices_crud():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        wheres, vals = _build_where(request.args, ['device_id', 'status'])
        sql = 'SELECT * FROM devices' + (' WHERE ' + wheres if wheres else '') + ' ORDER BY create_time DESC'
        cursor.execute(sql, vals)
        return _json_success(cursor.fetchall())
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/devices/<int:record_id>', methods=['GET'])
def get_device(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM devices WHERE id=%s', (record_id,))
        row = cursor.fetchone()
        return _json_success(row) if row else _json_error('设备不存在', 404)
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/devices', methods=['POST'])
def create_device():
    body = request.json or {}
    fields = ['device_id', 'location_name', 'longitude', 'latitude', 'api_key', 'status']
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals = [body.get(f) for f in fields]
        cursor.execute(f"INSERT INTO devices ({', '.join(fields)}, create_time) VALUES (%s,%s,%s,%s,%s,%s, NOW())", vals)
        conn.commit()
        return _json_success({'id': cursor.lastrowid}, '创建成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/devices/<int:record_id>', methods=['PUT'])
def update_device(record_id):
    body = request.json or {}
    allowed = {'device_id', 'location_name', 'longitude', 'latitude', 'api_key', 'status'}
    sets, vals = _build_set(body, allowed)
    if not sets:
        return _json_error('无有效字段更新')
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals.append(record_id)
        cursor.execute(f'UPDATE devices SET {sets} WHERE id=%s', vals)
        conn.commit()
        return _json_error('设备不存在', 404) if cursor.rowcount == 0 else _json_success(msg='更新成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/devices/<int:record_id>', methods=['DELETE'])
def delete_device(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM devices WHERE id=%s', (record_id,))
        conn.commit()
        return _json_error('设备不存在', 404) if cursor.rowcount == 0 else _json_success(msg='删除成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


# --- daily_summary ---

@miniprogram.route('/api/daily-summary', methods=['GET'])
def list_daily_summary():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        clauses, vals = [], []
        for key, col in [('device_id', 'device_id'), ('start_date', 'stat_date'), ('end_date', 'stat_date')]:
            val = request.args.get(key)
            if val is not None:
                clauses.append('stat_date <= %s' if key == 'end_date' else 'stat_date >= %s' if key == 'start_date' else f'{col}=%s')
                vals.append(val)
        sql = 'SELECT * FROM daily_summary' + (' WHERE ' + ' AND '.join(clauses) if clauses else '') + ' ORDER BY stat_date DESC, device_id ASC'
        cursor.execute(sql, vals)
        return _json_success(cursor.fetchall())
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/daily-summary/<int:record_id>', methods=['GET'])
def get_daily_summary(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM daily_summary WHERE id=%s', (record_id,))
        row = cursor.fetchone()
        return _json_success(row) if row else _json_error('记录不存在', 404)
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/daily-summary', methods=['POST'])
def create_daily_summary():
    body = request.json or {}
    fields = ['device_id', 'stat_date', 'avg_aqi', 'max_aqi', 'avg_pm2_5']
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals = [body.get(f) for f in fields]
        cursor.execute(f"INSERT INTO daily_summary ({', '.join(fields)}, create_time) VALUES (%s,%s,%s,%s,%s, NOW())", vals)
        conn.commit()
        return _json_success({'id': cursor.lastrowid}, '创建成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/daily-summary/<int:record_id>', methods=['PUT'])
def update_daily_summary(record_id):
    body = request.json or {}
    allowed = {'device_id', 'stat_date', 'avg_aqi', 'max_aqi', 'avg_pm2_5'}
    sets, vals = _build_set(body, allowed)
    if not sets:
        return _json_error('无有效字段更新')
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals.append(record_id)
        cursor.execute(f'UPDATE daily_summary SET {sets} WHERE id=%s', vals)
        conn.commit()
        return _json_error('记录不存在', 404) if cursor.rowcount == 0 else _json_success(msg='更新成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/daily-summary/<int:record_id>', methods=['DELETE'])
def delete_daily_summary(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM daily_summary WHERE id=%s', (record_id,))
        conn.commit()
        return _json_error('记录不存在', 404) if cursor.rowcount == 0 else _json_success(msg='删除成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


# --- air_quality_records ---

@miniprogram.route('/api/air-quality-records', methods=['GET'])
def list_air_quality_records():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        clauses, vals = [], []
        for key, col in [('device_id', 'device_id'), ('start_time', 'sample_time'), ('end_time', 'sample_time')]:
            val = request.args.get(key)
            if val is not None:
                clauses.append('sample_time <= %s' if key == 'end_time' else 'sample_time >= %s' if key == 'start_time' else f'{col}=%s')
                vals.append(val)
        sql = 'SELECT * FROM air_quality_records' + (' WHERE ' + ' AND '.join(clauses) if clauses else '') + ' ORDER BY sample_time DESC LIMIT 500'
        cursor.execute(sql, vals)
        return _json_success(cursor.fetchall())
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/air-quality-records/<int:record_id>', methods=['GET'])
def get_air_quality_record(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM air_quality_records WHERE id=%s', (record_id,))
        row = cursor.fetchone()
        return _json_success(row) if row else _json_error('记录不存在', 404)
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/air-quality-records', methods=['POST'])
def create_air_quality_record():
    body = request.json or {}
    fields = ['device_id', 'aqi', 'pm2_5', 'pm10', 'no2', 'so2', 'o3', 'temperature', 'humidity', 'sample_time']
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals = [body.get(f) for f in fields]
        placeholders = ','.join(['%s'] * len(fields))
        cursor.execute(f"INSERT INTO air_quality_records ({', '.join(fields)}, create_time) VALUES ({placeholders}, NOW())", vals)
        conn.commit()
        return _json_success({'id': cursor.lastrowid}, '创建成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/air-quality-records/<int:record_id>', methods=['PUT'])
def update_air_quality_record(record_id):
    body = request.json or {}
    allowed = {'device_id', 'aqi', 'pm2_5', 'pm10', 'no2', 'so2', 'o3', 'temperature', 'humidity', 'sample_time'}
    sets, vals = _build_set(body, allowed)
    if not sets:
        return _json_error('无有效字段更新')
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals.append(record_id)
        cursor.execute(f'UPDATE air_quality_records SET {sets} WHERE id=%s', vals)
        conn.commit()
        return _json_error('记录不存在', 404) if cursor.rowcount == 0 else _json_success(msg='更新成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/air-quality-records/<int:record_id>', methods=['DELETE'])
def delete_air_quality_record(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM air_quality_records WHERE id=%s', (record_id,))
        conn.commit()
        return _json_error('记录不存在', 404) if cursor.rowcount == 0 else _json_success(msg='删除成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


# --- user_favorites (原有 CRUD) ---

@miniprogram.route('/api/user-favorites', methods=['GET'])
def list_user_favorites():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        wheres, vals = _build_where(request.args, ['open_id', 'device_id'])
        sql = 'SELECT * FROM user_favorites' + (' WHERE ' + wheres if wheres else '') + ' ORDER BY create_time DESC'
        cursor.execute(sql, vals)
        return _json_success(cursor.fetchall())
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/user-favorites/<int:record_id>', methods=['GET'])
def get_user_favorite(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user_favorites WHERE id=%s', (record_id,))
        row = cursor.fetchone()
        return _json_success(row) if row else _json_error('记录不存在', 404)
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/user-favorites', methods=['POST'])
def create_user_favorite():
    body = request.json or {}
    fields = ['open_id', 'device_id']
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals = [body[f] for f in fields]
        cursor.execute(f"INSERT INTO user_favorites ({', '.join(fields)}, create_time) VALUES (%s,%s, NOW())", vals)
        conn.commit()
        return _json_success({'id': cursor.lastrowid}, '收藏成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/user-favorites/<int:record_id>', methods=['PUT'])
def update_user_favorite(record_id):
    body = request.json or {}
    allowed = {'open_id', 'device_id'}
    sets, vals = _build_set(body, allowed)
    if not sets:
        return _json_error('无有效字段更新')
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals.append(record_id)
        cursor.execute(f'UPDATE user_favorites SET {sets} WHERE id=%s', vals)
        conn.commit()
        return _json_error('记录不存在', 404) if cursor.rowcount == 0 else _json_success(msg='更新成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/user-favorites/<int:record_id>', methods=['DELETE'])
def delete_user_favorite(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_favorites WHERE id=%s', (record_id,))
        conn.commit()
        return _json_error('记录不存在', 404) if cursor.rowcount == 0 else _json_success(msg='删除成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


# --- user_alerts ---

@miniprogram.route('/api/user-alerts', methods=['GET'])
def list_user_alerts():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        wheres, vals = _build_where(request.args, ['open_id', 'device_id', 'is_enabled'])
        sql = 'SELECT * FROM user_alerts' + (' WHERE ' + wheres if wheres else '') + ' ORDER BY id DESC'
        cursor.execute(sql, vals)
        return _json_success(cursor.fetchall())
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/user-alerts/<int:record_id>', methods=['GET'])
def get_user_alert(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user_alerts WHERE id=%s', (record_id,))
        row = cursor.fetchone()
        return _json_success(row) if row else _json_error('记录不存在', 404)
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/user-alerts', methods=['POST'])
def create_user_alert():
    body = request.json or {}
    fields = ['open_id', 'device_id', 'pm2_5_max', 'aqi_max', 'is_enabled']
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals = [body.get(f) for f in fields]
        cursor.execute(f"INSERT INTO user_alerts ({', '.join(fields)}) VALUES (%s,%s,%s,%s,%s)", vals)
        conn.commit()
        return _json_success({'id': cursor.lastrowid}, '创建成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/user-alerts/<int:record_id>', methods=['PUT'])
def update_user_alert(record_id):
    body = request.json or {}
    allowed = {'open_id', 'device_id', 'pm2_5_max', 'aqi_max', 'is_enabled'}
    sets, vals = _build_set(body, allowed)
    if not sets:
        return _json_error('无有效字段更新')
    conn = get_db()
    try:
        cursor = conn.cursor()
        vals.append(record_id)
        cursor.execute(f'UPDATE user_alerts SET {sets} WHERE id=%s', vals)
        conn.commit()
        return _json_error('记录不存在', 404) if cursor.rowcount == 0 else _json_success(msg='更新成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/user-alerts/<int:record_id>', methods=['DELETE'])
def delete_user_alert(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_alerts WHERE id=%s', (record_id,))
        conn.commit()
        return _json_error('记录不存在', 404) if cursor.rowcount == 0 else _json_success(msg='删除成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


# --- users ---

@miniprogram.route('/api/users', methods=['GET'])
def list_users():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        wheres, vals = _build_where(request.args, ['open_id'])
        sql = 'SELECT * FROM users' + (' WHERE ' + wheres if wheres else '') + ' ORDER BY create_time DESC'
        cursor.execute(sql, vals)
        return _json_success(cursor.fetchall())
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/users/<int:record_id>', methods=['GET'])
def get_user(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE id=%s', (record_id,))
        row = cursor.fetchone()
        return _json_success(row) if row else _json_error('用户不存在', 404)
    except pymysql.Error as e:
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/users', methods=['POST'])
def create_user():
    body = request.json or {}
    fields = ['open_id', 'nickname', 'avatar_url']
    conn = get_db()
    try:
        curs = conn.cursor()
        vals = [body.get(f) for f in fields]
        curs.execute(f"INSERT INTO users ({', '.join(fields)}, create_time, update_time) VALUES (%s,%s,%s, NOW(), NOW())", vals)
        conn.commit()
        return _json_success({'id': curs.lastrowid}, '创建成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/users/<int:record_id>', methods=['PUT'])
def update_user(record_id):
    body = request.json or {}
    allowed = {'open_id', 'nickname', 'avatar_url'}
    sets, vals = _build_set(body, allowed)
    if not sets:
        return _json_error('无有效字段更新')
    conn = get_db()
    try:
        cursor = conn.cursor()
        sets += ', update_time=NOW()'
        vals.append(record_id)
        cursor.execute(f'UPDATE users SET {sets} WHERE id=%s', vals)
        conn.commit()
        return _json_error('用户不存在', 404) if cursor.rowcount == 0 else _json_success(msg='更新成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()


@miniprogram.route('/api/users/<int:record_id>', methods=['DELETE'])
def delete_user(record_id):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id=%s', (record_id,))
        conn.commit()
        return _json_error('用户不存在', 404) if cursor.rowcount == 0 else _json_success(msg='删除成功')
    except pymysql.Error as e:
        conn.rollback()
        return _json_error(str(e), 500)
    finally:
        conn.close()
