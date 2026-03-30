# api_server.py
import json
import logging
from datetime import datetime
import os
from flask import Flask, request, jsonify

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

def save_data_to_file(data):
    """保存数据到JSON文件"""
    filename = f"air_quality_data_{datetime.now().strftime('%Y%m%d')}.json"
    
    # 准备保存的数据格式
    record = {
        "timestamp": datetime.now().isoformat(),
        "received_at": data.get('timestamp'),
        "data": data.get('data'),
        "client_ip": request.remote_addr
    }
    
    # 读取现有数据或创建新列表
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []
    else:
        records = []
    
    # 添加新记录
    records.append(record)
    
    # 写回文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    
    return filename

@app.route('/api/air-quality', methods=['POST'])
def receive_air_quality_data():
    try:
        # 获取POST请求中的JSON数据
        data = request.json
        client_ip = request.remote_addr
        
        logger.info(f"接收到空气质量数据，客户端IP: {client_ip}")
        logger.info(f"时间戳: {data.get('timestamp', 'N/A')}")
        logger.info(f"数据: {data.get('data', {})})")
        
        # 保存数据到文件
        filename = save_data_to_file(data)
        
        logger.info(f"数据已保存到文件: {filename}")
        
        # 返回成功响应
        response_data = {
            "status": "success",
            "message": "数据接收并保存成功",
            "received_at": datetime.now().isoformat(),
            "saved_to": filename,
            "data": data
        }
        
        logger.info(f"向客户端 {client_ip} 返回成功响应")
        return jsonify(response_data), 200
        
    except Exception as e:
        client_ip = request.remote_addr
        logger.error(f"处理来自 {client_ip} 的数据时出错: {str(e)}")
        error_response = {
            "status": "error",
            "message": f"处理数据时出错：{str(e)}"
        }
        
        logger.info(f"向客户端 {client_ip} 返回错误响应: {str(e)}")
        return jsonify(error_response), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)