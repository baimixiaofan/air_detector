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

# 从环境变量读取配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_STREAM = os.getenv('REDIS_STREAM', 'data_stream')
API_KEY = os.getenv('API_KEY')  # 可选的API密钥
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
except redis.ConnectionError:
    print(f"无法连接到 Redis 服务器，请确保 Redis 已在 {REDIS_HOST}:{REDIS_PORT} 上运行")
    redis_client = None

app = Flask(__name__)

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
    """装饰器：检查API密钥（如果设置了API_KEY环境变量）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if API_KEY:  # 只有设置了API_KEY才进行验证
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
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到请求 - 来源IP: {client_ip}")
    
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

@app.route('/api/start_simulator', methods=['POST'])
def start_simulator():
    """
    启动一个新的模拟器容器（通过调用服务器上 /root/air_detector/ 目录下的.sh脚本）
    """
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到启动模拟器请求 - 来源IP: {client_ip}")
    
    try:
        # 指定服务器上 .sh 文件的路径
        server_scripts_dir = '/root/air_detector/'
        
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
        
        logger.info(f"找到启动脚本: {script_path}")
        
        # 执行 .sh 脚本
        result = subprocess.run(
            ['bash', script_path],
            capture_output=True,
            text=True,
            cwd=server_scripts_dir  # 设置工作目录为脚本目录
        )
        
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
    logger.info("空气质量数据API服务器启动")
    app.run(host='0.0.0.0', port=5000, debug=(os.getenv('FLASK_DEBUG', 'False').lower() == 'true'))