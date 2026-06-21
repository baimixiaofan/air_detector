#!/bin/bash

# ==========================================
# 变量定义
# ==========================================
WORKSPACE="/var/lib/jenkins/workspace/test"
SERVER_DIR="$WORKSPACE/server"
SIMULATOR_DIR="$WORKSPACE/simulator"
TARGET_API_DIR="/home/flask_app"
TARGET_SIM_DIR="/home/air_detector"
VENV_DIR="$WORKSPACE/venv"
REQ_FILE="$SERVER_DIR/requirements.txt"
HASH_FILE="$WORKSPACE/.req_hash"

echo "============================"
echo "开始部署 Flask API 服务"
echo "============================"

# ----- 1. 处理依赖（虚拟环境 + 缓存）-----
if [ ! -f "$REQ_FILE" ]; then
    echo "警告: 未找到 requirements.txt，跳过依赖安装"
else
    CURRENT_HASH=$(md5sum "$REQ_FILE" | cut -d' ' -f1)
    if [ -f "$HASH_FILE" ] && [ "$(cat $HASH_FILE)" = "$CURRENT_HASH" ]; then
        echo "依赖未变化，跳过安装，复用已有虚拟环境"
    else
        echo "依赖已变化，正在重新安装..."
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        pip install --upgrade pip
        pip install -r "$REQ_FILE"
        deactivate
        echo "$CURRENT_HASH" > "$HASH_FILE"
        echo "依赖安装完成"
    fi
fi

# ----- 2. 部署 Flask API 代码 -----
mkdir -p $TARGET_API_DIR
cp -f $SERVER_DIR/flask_api_server.py $TARGET_API_DIR/
cp -f $SERVER_DIR/miniprogram_api.py $TARGET_API_DIR/
cp -f $SERVER_DIR/consumer.py $TARGET_API_DIR/
cp -f $SERVER_DIR/web.html $TARGET_API_DIR/
cp -f $REQ_FILE $TARGET_API_DIR/ 2>/dev/null || true
cp -f $SERVER_DIR/config.py $TARGET_API_DIR/
cp -f $SERVER_DIR/device_config.json $TARGET_API_DIR/
cp -f $SERVER_DIR/daily_stats_job.py $TARGET_API_DIR/
cp -f $SERVER_DIR/admin_api.py $TARGET_API_DIR/
cp -f $SERVER_DIR/alert_checker.py $TARGET_API_DIR/
cp -f $SERVER_DIR/db_migrate.py $TARGET_API_DIR/

# ----- 3. 重启所有服务（nohup 方式）-----
echo ">>> 重启服务..."
# 停旧进程
pkill -f 'flask_api_server.py' 2>/dev/null || true
pkill -f 'consumer.py' 2>/dev/null || true
pkill -f 'daily_stats_job.py' 2>/dev/null || true
sleep 2

cd $TARGET_API_DIR

# 启动 Flask
nohup python3 flask_api_server.py > flask_output.log 2>&1 &
sleep 3
if pgrep -f flask_api_server.py > /dev/null; then
    echo "✅ Flask API 启动成功"
else
    echo "❌ Flask API 启动失败，请检查 /home/flask_app/flask_output.log"
    exit 1
fi

# 启动 Consumer
nohup python3 consumer.py > consumer.log 2>&1 &
echo "✅ Consumer 已启动"

# 启动日统计
nohup python3 daily_stats_job.py > daily_stats.log 2>&1 &
echo "✅ 日统计任务已启动"

# ----- 4. 同步模拟器代码（仅同步，不重启容器）-----
echo "============================"
echo "同步模拟器代码到 $TARGET_SIM_DIR"
echo "============================"
mkdir -p $TARGET_SIM_DIR
rsync -av --delete $SIMULATOR_DIR/ $TARGET_SIM_DIR/

# ----- 5. 重新构建模拟器镜像并重启容器（可选）-----
echo "============================"
echo "重新构建 simulator-image 并重启容器"
echo "============================"
cd $TARGET_SIM_DIR
docker build -t simulator-image .
docker stop sim1 sim2 sim3 sim4 sim5 2>/dev/null || true
docker rm sim1 sim2 sim3 sim4 sim5 2>/dev/null || true

# ----- 6. 构建并部署前端 web-admin -----
echo "============================"
echo "构建并部署 web-admin 前端"
echo "============================"
cd $WORKSPACE/web-admin
npm install
npm run build
rm -rf /home/flask_app/web-admin/dist
cp -r dist /home/flask_app/web-admin/dist
echo "✅ web-admin 前端部署完成"

echo "✅ 模拟器容器已更新并重启"
echo "✅ 模拟器代码同步完成（容器未重启）"
echo "✅ 全部部署完成"
