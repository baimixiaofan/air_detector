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
    docker run -d \
        --name $CONTAINER_NAME \
        --network host \
        -e SIMULATOR_ID=$CONTAINER_NAME \
        -e REDIS_HOST=127.0.0.1 \
        -v $OUTPUT_DIR:/app/output \
        $IMAGE \
        python air_detector.py --output /app/output/simulated_air_data.json
done

echo "All containers started."