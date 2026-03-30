import json
import logging
import redis
from datetime import datetime
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('consumer.log'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

def validate_data(data):
    """
    验证数据是否包含必需字段
    
    Args:
        data (dict): 待验证的数据字典
    
    Returns:
        bool: 验证是否通过
    """
    required_fields = ["timestamp", "data"]
    for field in required_fields:
        if field not in data:
            return False
    return True

def write_data_to_file(parsed_data):
    """
    将验证通过的数据写入按日期分片的文件
    
    Args:
        parsed_data (dict): 解析后的数据字典
    """
    try:
        # 从时间戳中提取日期部分（前10个字符，如 "2025-03-30"）
        timestamp_str = parsed_data.get("timestamp", "")
        if len(timestamp_str) >= 10:
            date_part = timestamp_str[:10]  # 提取 YYYY-MM-DD 部分
        else:
            # 如果时间戳格式不符合预期，使用当前日期
            date_part = datetime.now().strftime("%Y-%m-%d")
        
        # 生成文件名
        filename = f"data_{date_part}.log"
        
        # 将数据转换为紧凑的JSON字符串
        json_line = json.dumps(parsed_data, separators=(',', ':'))
        
        # 写入文件
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(json_line + '\n')
        
        logger.info(f"数据已写入文件 {filename}: {parsed_data.get('timestamp', 'N/A')}")
        
    except Exception as e:
        logger.error(f"写入文件时出错: {str(e)}, 原始数据: {parsed_data}")

def main():
    """主函数，启动消费者程序"""
    logger.info("Redis 消费者程序启动")
    
    try:
        # 连接到 Redis 服务器
        redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
        logger.info("成功连接到 Redis 服务器")
        
        # 持续从队列中获取数据
        while True:
            try:
                # 阻塞式获取数据，超时时间为0表示永久阻塞直到有数据
                result = redis_client.blpop(['data_queue'], timeout=0)
                
                if result:
                    # 获取键值对，result[0] 是键名，result[1] 是值
                    key, json_data = result
                    
                    # 解析 JSON 数据
                    try:
                        parsed_data = json.loads(json_data)
                        
                        # 验证数据
                        if validate_data(parsed_data):
                            # 数据验证通过，写入文件
                            write_data_to_file(parsed_data)
                        else:
                            # 数据验证失败，记录错误日志
                            logger.error(f"数据验证失败，缺少必需字段: {json_data}")
                            
                    except json.JSONDecodeError as e:
                        # JSON 解析失败
                        logger.error(f"JSON 解析失败: {str(e)}, 原始数据: {json_data}")
                        
            except KeyboardInterrupt:
                logger.info("收到键盘中断信号，程序退出")
                break
            except Exception as e:
                # 捕获其他异常，记录错误日志，但不退出程序
                logger.error(f"处理消息时出现异常: {str(e)}")
                
    except redis.ConnectionError:
        logger.error("无法连接到 Redis 服务器，请确保 Redis 已在 localhost:6379 上运行")
    except Exception as e:
        logger.error(f"程序出现严重错误: {str(e)}")
    
    logger.info("Redis 消费者程序结束")

if __name__ == "__main__":
    main()
