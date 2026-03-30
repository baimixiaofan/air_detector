# 使用 Python 官方轻量镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --timeout 120 -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir -r requirements.txt

# 复制所有代码和数据文件
COPY . .

# 创建输出目录（容器内）
RUN mkdir /app/out

# 容器启动命令（默认不带API参数，可通过docker run命令行覆盖）
CMD ["python", "air_detector.py", "--output", "/app/output/simulated_air_data.json"
