#!/bin/bash
NUM=5
IMAGE="simulator-image"
BASE_NAME="sim"
OUTPUT_BASE="$HOME/simulator_output"

mkdir -p $OUTPUT_BASE

for i in $(seq 1 $NUM); do
    CONTAINER_NAME="${BASE_NAME}${i}"
    OUTPUT_DIR="${OUTPUT_BASE}/${CONTAINER_NAME}"
    mkdir -p $OUTPUT_DIR
    echo "Starting $CONTAINER_NAME ..."
    # 修改点：将 docker 替换为 /usr/bin/docker
    /usr/bin/docker run -d \
        --name $CONTAINER_NAME \
        -v $OUTPUT_DIR:/app/output \
        $IMAGE \
        python air_detector.py --output /app/output/simulated_air_data.json
done

echo "All containers started."