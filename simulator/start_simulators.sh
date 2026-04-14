#!/bin/bash
# 获取传入的数量参数，默认为5
NUM=${1:-5}
IMAGE="simulator-image"
BASE_NAME="sim"
OUTPUT_BASE="$HOME/simulator_output"
# Flask API 端点地址（使用 host 网络模式，所以可以用 127.0.0.1）
API_ENDPOINT="http://127.0.0.1:5000/api/air-quality"

# 使用 docker 绝对路径
DOCKER_CMD="/usr/bin/docker"

echo "将启动 $NUM 个模拟器容器"

# 检查 docker 是否可用
if [ ! -x "$DOCKER_CMD" ]; then
    echo "错误: 找不到 docker 命令: $DOCKER_CMD"
    exit 1
fi

mkdir -p $OUTPUT_BASE

for i in $(seq 1 $NUM); do
    CONTAINER_NAME="${BASE_NAME}${i}"
    OUTPUT_DIR="${OUTPUT_BASE}/${CONTAINER_NAME}"
    mkdir -p $OUTPUT_DIR
    echo "Starting $CONTAINER_NAME ..."
    $DOCKER_CMD run -d \
        --name $CONTAINER_NAME \
        --network host \
        -e SIMULATOR_ID=$CONTAINER_NAME \
        -e REDIS_HOST=127.0.0.1 \
        -v $OUTPUT_DIR:/app/output \
        $IMAGE \
        python air_detector.py --output /app/output/simulated_air_data.json --api-endpoint $API_ENDPOINT
done

echo "All containers started."