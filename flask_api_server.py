# api_server.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/air-quality', methods=['POST'])
def receive_air_quality_data():
    try:
        # 获取POST请求中的JSON数据
        data = request.json
        print("接收到空气质量数据：")
        print(f"时间戳: {data['timestamp']}")
        print(f"数据: {data['data']}")
        
        # 这里可以添加数据处理逻辑，比如保存到数据库
        # ...
        
        # 返回成功响应
        return jsonify({
            "status": "success",
            "message": "数据接收成功",
            "data": data
        }), 200
    except Exception as e:
        print(f"处理数据时出错：{e}")
        return jsonify({
            "status": "error",
            "message": f"处理数据时出错：{str(e)}"
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
