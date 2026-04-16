# api_server.py
import json
import logging
import os
import time
import subprocess
from datetime import datetime
import redis
from flask import Flask, request, jsonify, send_from_directory
import tenacity
from functools import wraps
import hashlib

# 从环境变量读取配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_STREAM = os.getenv('REDIS_STREAM', 'data_stream')
API_KEY = '111'  # API密钥（写死）
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# 建立 Redis 连接
try:
    redis_client = redis.StrictRedis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        db=REDIS_DB, 
        decode_responses=True
    )
    # 测试连接
    redis_client.ping()
    print(f"成功连接到 Redis 服务器: {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError as e:
    print(f"无法连接到 Redis 服务器，请确保 Redis 已在 {REDIS_HOST}:{REDIS_PORT} 上运行: {str(e)}")
    redis_client = None
except Exception as e:
    print(f"连接 Redis 时发生未知错误: {str(e)}")
    redis_client = None

app = Flask(__name__)

# 服务器状态控制（用于演示重传机制）
server_online = True
server_offline_reason = ""

# 配置日志
numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

def require_api_key(f):
    """装饰器：检查API密钥（必须设置API_KEY环境变量）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not API_KEY:
            logger.error("未设置API_KEY环境变量，拒绝请求")
            return jsonify({"error": "Server configuration error: API_KEY not set"}), 500
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            logger.warning(f"无效的API密钥: {api_key}")
            return jsonify({"error": "Invalid API Key"}), 401
        return f(*args, **kwargs)
    return decorated_function

def validate_request_data(data):
    """
    验证请求数据是否包含必需字段
    
    Args:
        data (dict): 待验证的数据字典
    
    Returns:
        tuple: (是否有效, 错误信息)
    """
    if not isinstance(data, dict):
        return False, "请求数据必须是JSON对象"
    
    required_fields = ["timestamp", "data"]
    missing_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"缺少必需字段: {', '.join(missing_fields)}"
    
    return True, ""

@tenacity.retry(
    retry=tenacity.retry_if_exception_type(redis.ConnectionError),
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def push_to_redis_stream(record):
    """
    将数据推送到Redis Stream，带重试机制
    
    Args:
        record (dict): 要推送的数据记录
    """
    global redis_client
    if not redis_client:
        raise redis.ConnectionError("Redis客户端未初始化")
    
    redis_client.xadd(REDIS_STREAM, record)

@app.route('/api/air-quality', methods=['POST'])
@require_api_key
def receive_air_quality_data():
    """
    接收空气质量数据的API端点
    """
    global server_online, server_offline_reason
    
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到请求 - 来源IP: {client_ip}")
    
    # 检查服务器是否在线（用于演示重传机制）
    if not server_online:
        logger.warning(f"[{request_time}] 来源IP: {client_ip} - 服务器已下线，拒绝接收数据")
        return jsonify({
            "status": "error",
            "message": f"服务器暂时不可用：{server_offline_reason}",
            "code": "SERVER_OFFLINE"
        }), 503
    
    try:
        # 获取POST请求中的JSON数据
        data = request.json
        
        if data is None:
            error_msg = "请求体不是有效的JSON格式"
            logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
            return jsonify({"error": error_msg}), 400
        
        # 验证数据
        is_valid, error_msg = validate_request_data(data)
        if not is_valid:
            logger.error(f"[{request_time}] 来源IP: {client_ip} - 数据验证失败: {error_msg}")
            return jsonify({"error": error_msg}), 400
        
        # 验证MD5哈希
        received_md5 = request.headers.get('X-Content-MD5')
        if received_md5:
            # 计算接收到的数据的MD5哈希
            payload_str = json.dumps(data, sort_keys=True)
            calculated_md5 = hashlib.md5(payload_str.encode('utf-8')).hexdigest()
            
            if received_md5 != calculated_md5:
                error_msg = "数据完整性验证失败：MD5哈希不匹配"
                logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
                logger.error(f"[{request_time}] 来源IP: {client_ip} - 接收的MD5: {received_md5}")
                logger.error(f"[{request_time}] 来源IP: {client_ip} - 计算的MD5: {calculated_md5}")
                return jsonify({"error": error_msg}), 400
            logger.info(f"[{request_time}] 来源IP: {client_ip} - MD5验证成功")
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 接收到空气质量数据")
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 时间戳: {data.get('timestamp', 'N/A')}")
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 数据: {data.get('data', {})})")
        
        # 将数据推入 Redis Stream
        if redis_client:
            # 准备要推送的数据格式
            record = {
                "timestamp": data.get('timestamp'),
                "data": json.dumps(data.get('data')),
                "client_ip": client_ip,
                "server_time": datetime.now().isoformat()
            }
            
            try:
                # 推送数据到 Redis Stream，带重试机制
                push_to_redis_stream(record)
                logger.info(f"[{request_time}] 来源IP: {client_ip} - 数据已推入 Redis Stream: {REDIS_STREAM}")
                
                # 返回成功响应
                response_data = {
                    "status": "success",
                    "message": "数据接收并推入 Redis Stream 成功",
                    "received_at": datetime.now().isoformat(),
                    "stream": REDIS_STREAM,
                    "data": data
                }
                
                logger.info(f"[{request_time}] 来源IP: {client_ip} - 请求处理成功")
                return jsonify(response_data), 200
                
            except redis.ConnectionError as e:
                logger.error(f"[{request_time}] 来源IP: {client_ip} - Redis 连接失败: {str(e)}")
                error_response = {
                    "status": "error",
                    "message": "无法连接到 Redis 服务器"
                }
                return jsonify(error_response), 500
            except Exception as e:
                logger.error(f"[{request_time}] 来源IP: {client_ip} - 推送数据到Redis时出错: {str(e)}")
                error_response = {
                    "status": "error",
                    "message": f"推送数据到Redis时出错: {str(e)}"
                }
                return jsonify(error_response), 500
        else:
            # 如果无法连接 Redis，返回错误
            error_response = {
                "status": "error",
                "message": "无法连接到 Redis 服务器"
            }
            logger.error(f"[{request_time}] 来源IP: {client_ip} - Redis 连接失败，请求处理失败")
            return jsonify(error_response), 500
        
    except Exception as e:
        # 记录错误情况
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.error(f"[{error_time}] 来源IP: {client_ip} - 请求处理失败: {str(e)}")
        
        error_response = {
            "status": "error",
            "message": f"处理数据时出错：{str(e)}"
        }
        
        logger.info(f"[{error_time}] 来源IP: {client_ip} - 返回错误响应")
        return jsonify(error_response), 400

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点
    """
    try:
        if redis_client:
            redis_client.ping()
            status = "healthy"
        else:
            status = "unhealthy"
    except:
        status = "unhealthy"
    
    return jsonify({
        "status": status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/status', methods=['GET'])
def get_simulator_status():
    """
    获取所有模拟器的运行状态
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到状态查询请求 - 来源IP: {client_ip}")
    
    try:
        if not redis_client:
            error_response = {
                "status": "error",
                "message": "无法连接到 Redis 服务器"
            }
            logger.error(f"[{request_time}] 来源IP: {client_ip} - Redis 连接失败")
            return jsonify(error_response), 500
        
        # 从 Redis 读取所有模拟器统计数据
        simulator_data = redis_client.hgetall('simulator_stats')
        
        current_time = time.time()
        timeout_threshold = 15  # 15秒超时
        
        total_count = 0
        online_count = 0
        simulators_info = {}
        
        for sim_id, json_data in simulator_data.items():
            try:
                # 解析JSON数据
                stats = json.loads(json_data)
                
                last_update = float(stats.get('last_update', 0))
                data_sent = int(stats.get('data_sent', 0))
                status = stats.get('status', 'unknown')
                
                # 检查是否超时
                time_diff = current_time - last_update
                if time_diff > timeout_threshold:
                    effective_status = 'offline'
                else:
                    effective_status = status
                    if status == 'running':
                        online_count += 1
                
                # 转换时间戳为可读格式
                readable_time = datetime.fromtimestamp(last_update).strftime('%Y-%m-%d %H:%M:%S')
                
                simulators_info[sim_id] = {
                    'status': effective_status,
                    'data_sent': data_sent,
                    'last_update': readable_time,
                    'time_since_update': round(time_diff, 2)
                }
                
                total_count += 1
                
            except json.JSONDecodeError as e:
                logger.error(f"解析模拟器 {sim_id} 的统计数据时出错: {str(e)}, 原始数据: {json_data}")
                continue
            except (ValueError, TypeError) as e:
                logger.error(f"处理模拟器 {sim_id} 的统计数据时出错: {str(e)}, 数据: {json_data}")
                continue
        
        response_data = {
            "total": total_count,
            "online": online_count,
            "offline": total_count - online_count,
            "simulators": simulators_info,
            "queried_at": datetime.now().isoformat()
        }
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 状态查询成功，共 {total_count} 个模拟器，{online_count} 个在线")
        return jsonify(response_data), 200
        
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.error(f"[{error_time}] 来源IP: {client_ip} - 查询状态时出错: {str(e)}")
        
        error_response = {
            "status": "error",
            "message": f"查询状态时出错: {str(e)}"
        }
        
        logger.info(f"[{error_time}] 来源IP: {client_ip} - 返回错误响应")
        return jsonify(error_response), 500

@app.route('/api/queue_data', methods=['GET'])
def get_queue_data():
    """
    获取消息队列数据和最近的消息
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    try:
        messages = []
        queue_length = 0
        total_received = 0
        
        if redis_client:
            try:
                queue_length = redis_client.xlen(REDIS_STREAM)
                
                recent_messages = redis_client.xrevrange(REDIS_STREAM, count=20)
                
                for msg_id, msg_data in recent_messages:
                    try:
                        message = {
                            'id': msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                            'timestamp': msg_data.get(b'timestamp', msg_data.get('timestamp', b'')).decode() if isinstance(msg_data.get(b'timestamp', msg_data.get('timestamp')), bytes) else msg_data.get('timestamp', ''),
                            'simulator_id': msg_data.get(b'client_ip', msg_data.get('client_ip', b'')).decode() if isinstance(msg_data.get(b'client_ip', msg_data.get('client_ip')), bytes) else msg_data.get('client_ip', ''),
                            'data': json.loads(msg_data.get(b'data', msg_data.get('data', b'{}')).decode() if isinstance(msg_data.get(b'data', msg_data.get('data')), bytes) else msg_data.get('data', '{}'))
                        }
                        messages.append(message)
                    except Exception as e:
                        continue
                
                total_received = queue_length
                
            except Exception as e:
                logger.error(f"[{request_time}] 来源IP: {client_ip} - 获取队列数据失败: {str(e)}")
        
        response_data = {
            'queue_length': queue_length,
            'total_received': total_received,
            'messages': messages
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.error(f"[{error_time}] 来源IP: {client_ip} - 获取队列数据时出错: {str(e)}")
        return jsonify({
            'queue_length': 0,
            'total_received': 0,
            'messages': [],
            'error': str(e)
        }), 500

@app.route('/api/start_simulator', methods=['POST'])
def start_simulator():
    """
    启动一个新的模拟器容器（通过调用服务器上 /home/air_detector/ 目录下的.sh脚本）
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到启动模拟器请求 - 来源IP: {client_ip}")
    
    # 获取请求中的启动数量，默认为5
    data = request.json or {}
    num_simulators = data.get('count', 5)
    
    # 确保数量是正整数
    if not isinstance(num_simulators, int) or num_simulators < 1:
        num_simulators = 5
    
    logger.info(f"[{request_time}] 来源IP: {client_ip} - 请求启动 {num_simulators} 个模拟器")
    
    try:
        # 指定服务器上 .sh 文件的路径
        server_scripts_dir = '/home/air_detector/'
        
        # 检查目录是否存在
        if not os.path.exists(server_scripts_dir):
            error_msg = f"服务器脚本目录不存在: {server_scripts_dir}"
            logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 500
        
        # 搜索 /root/air_detector/ 目录下的所有 .sh 文件
        sh_files = []
        for file in os.listdir(server_scripts_dir):
            if file.endswith('.sh'):
                sh_files.append(file)
        
        if not sh_files:
            error_msg = f"在 {server_scripts_dir} 目录下未找到 .sh 脚本文件"
            logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 500
        
        # 默认使用第一个找到的 .sh 文件，或查找特定的启动脚本
        script_name = None
        for file_name in sh_files:
            if 'start' in file_name.lower() or 'launch' in file_name.lower() or 'run' in file_name.lower():
                script_name = file_name
                break
        
        # 如果没找到特定名称的脚本，使用第一个找到的
        if not script_name:
            script_name = sh_files[0]
        
        script_path = os.path.join(server_scripts_dir, script_name)
        
        # 检查脚本文件是否存在
        if not os.path.exists(script_path):
            error_msg = f"启动脚本不存在: {script_path}"
            logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 500
        
        # 检查脚本文件是否有执行权限
        if not os.access(script_path, os.X_OK):
            logger.warning(f"[{request_time}] 来源IP: {client_ip} - 脚本文件没有执行权限，尝试添加执行权限")
            try:
                os.chmod(script_path, 0o755)
                logger.info(f"[{request_time}] 来源IP: {client_ip} - 成功添加执行权限")
            except Exception as e:
                error_msg = f"无法添加执行权限: {str(e)}"
                logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
                return jsonify({
                    "status": "error",
                    "message": error_msg
                }), 500
        
        logger.info(f"找到启动脚本: {script_path}")
        
        # 检查Docker是否可用
        try:
            docker_check = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True
            )
            if docker_check.returncode != 0:
                error_msg = f"Docker不可用: {docker_check.stderr}"
                logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
                return jsonify({
                    "status": "error",
                    "message": error_msg
                }), 500
        except FileNotFoundError:
            error_msg = "未找到 docker 命令，请确保 Docker 已安装并添加到 PATH"
            logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 500
        
        # 执行 .sh 脚本，传递数量参数
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 开始执行启动脚本: {script_name}，数量: {num_simulators}")
        result = subprocess.run(
            ['bash', script_path, str(num_simulators)],
            capture_output=True,
            text=True,
            cwd=server_scripts_dir  # 设置工作目录为脚本目录
        )
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 脚本执行返回码: {result.returncode}")
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 脚本标准输出: {result.stdout}")
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 脚本标准错误: {result.stderr}")
        
        if result.returncode == 0:
            logger.info(f"[{request_time}] 来源IP: {client_ip} - 模拟器启动脚本执行成功")
            return jsonify({
                "status": "success",
                "message": f"模拟器启动脚本 {script_name} 执行成功",
                "output": result.stdout
            }), 200
        else:
            error_msg = f"启动脚本执行失败: {result.stderr}"
            logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 500
        
    except subprocess.CalledProcessError as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"启动模拟器脚本失败: {e.stderr if e.stderr else str(e)}"
        logger.error(f"[{error_time}] 来源IP: {client_ip} - {error_msg}")
        
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500
    
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"启动模拟器时发生未知错误: {str(e)}"
        logger.error(f"[{error_time}] 来源IP: {client_ip} - {error_msg}")
        
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500

@app.route('/api/stop_all', methods=['POST'])
def stop_all_simulators():
    """
    停止并删除所有以 "sim" 开头的容器
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到停止所有模拟器请求 - 来源IP: {client_ip}")
    
    try:
        # 停止所有以 sim 开头的容器
        stop_cmd = "docker stop $(docker ps -q --filter name=sim*)"
        stop_result = subprocess.run(
            stop_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        # 删除所有以 sim 开头的容器（包括已停止的）
        remove_cmd = "docker rm $(docker ps -aq --filter name=sim*)"
        remove_result = subprocess.run(
            remove_cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        # 记录操作结果
        stop_output = stop_result.stdout.strip() if stop_result.stdout.strip() else "无容器需要停止"
        remove_output = remove_result.stdout.strip() if remove_result.stdout.strip() else "无容器需要删除"
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 停止容器结果: {stop_output}")
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 删除容器结果: {remove_output}")
        
        return jsonify({
            "status": "success",
            "message": f"已停止并删除所有以 'sim' 开头的容器\n停止结果: {stop_output}\n删除结果: {remove_output}"
        }), 200
        
    except subprocess.CalledProcessError as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"停止或删除模拟器容器失败: {e.stderr if e.stderr else str(e)}"
        logger.error(f"[{error_time}] 来源IP: {client_ip} - {error_msg}")
        
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500
    
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"停止模拟器时发生未知错误: {str(e)}"
        logger.error(f"[{error_time}] 来源IP: {client_ip} - {error_msg}")
        
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500

@app.route('/api/docker_logs', methods=['GET'])
def get_docker_logs():
    """
    获取指定 Docker 容器的实时日志
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    container_name = request.args.get('container', 'sim1')
    lines = int(request.args.get('lines', 50))
    
    logger.info(f"[{request_time}] 收到获取Docker日志请求 - 来源IP: {client_ip}, 容器: {container_name}")
    
    try:
        # 首先检查容器是否存在
        check_cmd = ['docker', 'ps', '-a', '--filter', f'name={container_name}', '--format', '{{.Names}}']
        check_result = subprocess.run(
            check_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        existing_containers = check_result.stdout.strip().split('\n') if check_result.stdout.strip() else []
        
        if container_name not in existing_containers:
            response_data = {
                "status": "success",
                "container": container_name,
                "lines": 0,
                "logs": [],
                "message": f"容器 {container_name} 不存在或未运行",
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"[{request_time}] 来源IP: {client_ip} - 容器 {container_name} 不存在")
            return jsonify(response_data), 200
        
        # 检查容器是否运行
        running_cmd = ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}']
        running_result = subprocess.run(
            running_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        running_containers = running_result.stdout.strip().split('\n') if running_result.stdout.strip() else []
        
        if container_name not in running_containers:
            response_data = {
                "status": "success",
                "container": container_name,
                "lines": 0,
                "logs": [],
                "message": f"容器 {container_name} 已停止运行",
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"[{request_time}] 来源IP: {client_ip} - 容器 {container_name} 已停止")
            return jsonify(response_data), 200
        
        # 使用 docker logs 命令获取容器日志
        cmd = ['docker', 'logs', '--tail', str(lines), '-t', container_name]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # 解析日志内容（合并stdout和stderr）
        log_output = result.stdout + result.stderr
        log_lines = log_output.strip().split('\n') if log_output.strip() else []
        
        # 取最后N行
        final_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        response_data = {
            "status": "success",
            "container": container_name,
            "lines": len(final_lines),
            "logs": final_lines,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 成功获取容器 {container_name} 的 {len(final_lines)} 条日志")
        return jsonify(response_data), 200
        
    except subprocess.TimeoutExpired:
        error_msg = f"获取容器 {container_name} 日志超时"
        logger.error(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 408
        
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"获取Docker日志时发生未知错误: {str(e)}"
        logger.error(f"[{error_time}] 来源IP: {client_ip} - {error_msg}")
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500


@app.route('/api/server_logs', methods=['GET'])
def get_server_logs():
    """
    获取服务器端的实时日志
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    lines = int(request.args.get('lines', 100))
    
    logger.info(f"[{request_time}] 收到获取服务器日志请求 - 来源IP: {client_ip}")
    
    try:
        log_file_path = 'server.log'
        
        if not os.path.exists(log_file_path):
            error_msg = f"服务器日志文件不存在: {log_file_path}"
            logger.warning(f"[{request_time}] 来源IP: {client_ip} - {error_msg}")
            return jsonify({
                "status": "success",
                "message": error_msg,
                "lines": 0,
                "logs": [],
                "timestamp": datetime.now().isoformat()
            }), 200
        
        # 读取日志文件的最后N行
        with open(log_file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
        # 获取最后N行
        recent_logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # 清理换行符并过滤空行
        cleaned_logs = [line.strip() for line in recent_logs if line.strip()]
        
        response_data = {
            "status": "success",
            "log_file": log_file_path,
            "total_lines": len(all_lines),
            "returned_lines": len(cleaned_logs),
            "logs": cleaned_logs,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 成功获取 {len(cleaned_logs)} 条服务器日志")
        return jsonify(response_data), 200
        
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"获取服务器日志时发生未知错误: {str(e)}"
        logger.error(f"[{error_time}] 来源IP: {client_ip} - {error_msg}")
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500


@app.route('/api/config/api_key', methods=['GET'])
def get_api_key_config():
    """
    获取当前配置的 API Key（从 .sh 文件读取）
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到获取API Key配置请求 - 来源IP: {client_ip}")
    
    try:
        # 尝试从 .sh 文件中读取 API_KEY
        sh_file_path = os.path.join('..', 'simulator', 'start_simulators.sh')
        
        if not os.path.exists(sh_file_path):
            # 如果 .sh 文件不存在，返回服务器端硬编码的 API_KEY
            return jsonify({
                "status": "success",
                "source": "server_code",
                "api_key": API_KEY,
                "message": "未找到 .sh 配置文件，使用服务器端配置"
            }), 200
        
        # 读取 .sh 文件内容
        with open(sh_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式提取 API_KEY 的值
        import re
        match = re.search(r'API_KEY="([^"]*)"', content)
        
        if match:
            api_key_value = match.group(1)
            response_data = {
                "status": "success",
                "source": "config_file",
                "sh_file": sh_file_path,
                "api_key": api_key_value,
                "message": f"成功从配置文件读取 API Key"
            }
            
            logger.info(f"[{request_time}] 来源IP: {client_ip} - 成功获取API Key配置")
            return jsonify(response_data), 200
        else:
            return jsonify({
                "status": "error",
                "message": "在 .sh 文件中未找到 API_KEY 配置项",
                "sh_file": sh_file_path
            }), 404
            
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"获取API Key配置时发生错误: {str(e)}"
        logger.error(f"[{error_time}] 来源IP: {client_ip} - {error_msg}")
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500


@app.route('/api/config/api_key', methods=['POST'])
def update_api_key_config():
    """
    更新 .sh 文件中的 API Key 配置
    """
    global API_KEY
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到更新API Key请求 - 来源IP: {client_ip}")
    
    try:
        # 获取请求数据
        data = request.json
        
        if not data or 'new_api_key' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少必需参数: new_api_key"
            }), 400
        
        new_api_key = str(data['new_api_key']).strip()
        
        if not new_api_key:
            return jsonify({
                "status": "error",
                "message": "API Key 不能为空"
            }), 400
        
        # 验证 API Key 格式（简单验证）
        if len(new_api_key) > 64:
            return jsonify({
                "status": "error",
                "message": "API Key 长度不能超过 64 个字符"
            }), 400
        
        # 更新 .sh 文件中的 API_KEY
        sh_file_path = os.path.join('..', 'simulator', 'start_simulators.sh')
        
        if not os.path.exists(sh_file_path):
            # 如果 .sh 文件不存在，更新服务器端的 API_KEY
            global API_KEY
            old_api_key = API_KEY
            API_KEY = new_api_key
            
            logger.info(f"[{request_time}] 来源IP: {client_ip} - 已更新服务器端API Key: {old_api_key} -> {new_api_key}")
            return jsonify({
                "status": "success",
                "source": "server_code",
                "old_api_key": old_api_key,
                "new_api_key": new_api_key,
                "message": "已更新服务器端 API Key（未找到 .sh 配置文件）"
            }), 200
        
        # 读取并修改 .sh 文件
        with open(sh_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取旧的 API_KEY
        import re
        match = re.search(r'API_KEY="([^"]*)"', content)
        old_api_key = match.group(1) if match else None
        
        # 替换 API_KEY 值
        new_content = re.sub(
            r'API_KEY="[^"]*"',
            f'API_KEY="{new_api_key}"',
            content
        )
        
        # 写回文件
        with open(sh_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 同时更新服务器端的 API_KEY
        API_KEY = new_api_key
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 成功更新API Key: {old_api_key} -> {new_api_key}")
        
        return jsonify({
            "status": "success",
            "source": "config_file",
            "sh_file": sh_file_path,
            "old_api_key": old_api_key,
            "new_api_key": new_api_key,
            "message": f"成功更新 API Key: {old_api_key} -> {new_api_key}"
        }), 200
        
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"更新API Key时发生错误: {str(e)}"
        logger.error(f"[{error_time}] 来源IP: {client_ip} - {error_msg}")
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 500

@app.route('/api/server/control', methods=['POST'])
def control_server_status():
    """
    控制服务器上线/下线状态（用于演示重传机制）
    """
    global server_online, server_offline_reason
    
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "请求体不是有效的JSON格式"}), 400
        
        action = data.get('action')
        
        if action == 'offline':
            # 服务器下线
            reason = data.get('reason', '维护中')
            server_online = False
            server_offline_reason = reason
            logger.warning(f"[{request_time}] 来源IP: {client_ip} - 服务器已下线，原因：{reason}")
            
            return jsonify({
                "status": "success",
                "message": f"服务器已下线，原因：{reason}",
                "server_online": False,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }), 200
            
        elif action == 'online':
            # 服务器上线
            server_online = True
            server_offline_reason = ""
            logger.info(f"[{request_time}] 来源IP: {client_ip} - 服务器已上线")
            
            return jsonify({
                "status": "success",
                "message": "服务器已上线",
                "server_online": True,
                "timestamp": datetime.now().isoformat()
            }), 200
            
        else:
            return jsonify({"error": "无效的操作，支持的操作：online, offline"}), 400
            
    except Exception as e:
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.error(f"[{error_time}] 来源IP: {client_ip} - 控制服务器状态时出错: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"控制服务器状态时出错: {str(e)}"
        }), 500

@app.route('/api/server/status', methods=['GET'])
def get_server_status():
    """
    获取服务器当前状态
    """
    return jsonify({
        "server_online": server_online,
        "server_offline_reason": server_offline_reason if not server_online else "",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/nginx_logs', methods=['GET'])
def get_nginx_logs():
    """
    获取 Nginx 访问日志（用于证明 HTTPS 传输）
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到获取Nginx日志请求 - 来源IP: {client_ip}")
    
    lines = int(request.args.get('lines', 50))
    
    try:
        # 尝试读取 Nginx 访问日志
        nginx_log_paths = [
            '/var/log/nginx/access.log',
            '/var/log/nginx/error.log'
        ]
        
        logs_data = []
        
        for log_path in nginx_log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        all_lines = f.readlines()
                        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                        
                        for line in recent_lines:
                            log_entry = {
                                "source": os.path.basename(log_path),
                                "content": line.strip(),
                                "is_https": '443' in line or 'HTTPS' in line.upper()
                            }
                            logs_data.append(log_entry)
                            
                except Exception as e:
                    logger.error(f"读取Nginx日志文件 {log_path} 时出错: {str(e)}")
                    
        response_data = {
            "status": "success",
            "total_lines": len(logs_data),
            "logs": logs_data[-100:],  # 返回最近100条
            "log_files": [path for path in nginx_log_paths if os.path.exists(path)],
            "timestamp": datetime.now().isoformat(),
            "message": "Nginx日志（包含HTTP和HTTPS请求记录）"
        }
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 成功获取 {len(logs_data)} 条Nginx日志")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"[{request_time}] 来源IP: {client_ip} - 获取Nginx日志时出错: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"获取Nginx日志时出错: {str(e)}"
        }), 500


@app.route('/monitor')
def monitor_page():
    """
    监控页面路由，返回 web.html 文件
    """
    try:
        # 从与 flask_api_server.py 同级的目录返回 web.html
        return send_from_directory('.', 'web.html')
    except FileNotFoundError:
        logger.error("web.html 文件未找到")
        return "监控页面未找到", 404
    except Exception as e:
        logger.error(f"返回监控页面时出错: {str(e)}")
        return "内部服务器错误", 500


if __name__ == '__main__':
    print("正在启动空气质量数据API服务器...")
    print(f"Redis连接状态: {'已连接' if redis_client else '未连接'}")
    logger.info("空气质量数据API服务器启动")
    app.run(host='0.0.0.0', port=5000, debug=(os.getenv('FLASK_DEBUG', 'False').lower() == 'true'))