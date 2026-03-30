# api_server.py
import json
import logging
from datetime import datetime
import os
import redis
from flask import Flask, request, jsonify

# 建立 Redis 连接
try:
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    # 测试连接
    redis_client.ping()
    print("成功连接到 Redis 服务器")
except redis.ConnectionError:
    print("无法连接到 Redis 服务器，请确保 Redis 已在 localhost:6379 上运行")
    redis_client = None

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

@app.route('/api/air-quality', methods=['POST'])
def receive_air_quality_data():
    # 记录请求开始时间和来源IP
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    client_ip = request.remote_addr
    
    logger.info(f"[{request_time}] 收到请求 - 来源IP: {client_ip}")
    
    try:
        # 获取POST请求中的JSON数据
        data = request.json
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 接收到空气质量数据")
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 时间戳: {data.get('timestamp', 'N/A')}")
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 数据: {data.get('data', {})})")
        
        # 将数据推入 Redis 消息队列
        if redis_client:
            # 准备要推送的数据格式
            record = {
                "timestamp": datetime.now().isoformat(),
                "received_at": data.get('timestamp'),
                "data": data.get('data'),
                "client_ip": request.remote_addr
            }
            # 推送数据到 Redis 列表
            redis_client.lpush('data_queue', json.dumps(record))
            logger.info(f"[{request_time}] 来源IP: {client_ip} - 数据已推入 Redis 队列: data_queue")
            
            # 返回成功响应
            response_data = {
                "status": "success",
                "message": "数据接收并推入 Redis 队列成功",
                "received_at": datetime.now().isoformat(),
                "queued_to": "data_queue",
                "data": data
            }
        else:
            # 如果无法连接 Redis，返回错误
            error_response = {
                "status": "error",
                "message": "无法连接到 Redis 服务器"
            }
            logger.error(f"[{request_time}] 来源IP: {client_ip} - Redis 连接失败，请求处理失败")
            return jsonify(error_response), 500
        
        logger.info(f"[{request_time}] 来源IP: {client_ip} - 请求处理成功")
        return jsonify(response_data), 200
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)