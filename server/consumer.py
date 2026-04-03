# consumer.py
import json
import logging
import os
import redis
import signal
import sys
import time
from datetime import datetime
from collections import defaultdict
import threading

# 从环境变量读取配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_STREAM = os.getenv('REDIS_STREAM', 'data_stream')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'air_quality_group')
CONSUMER_NAME = os.getenv('CONSUMER_NAME', 'consumer_1')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 100))
FLUSH_INTERVAL = int(os.getenv('FLUSH_INTERVAL', 5))  # 批处理间隔秒数
LOG_DIR = os.getenv('LOG_DIR', '.')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEAD_LETTER_STREAM = os.getenv('DEAD_LETTER_STREAM', 'dead_letter_stream')

# 配置日志
numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'consumer.log')),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)

class RedisStreamConsumer:
    def __init__(self):
        self.redis_client = None
        self.running = True
        self.batch_buffer = []
        self.last_flush_time = time.time()
        self.lock = threading.Lock()
        
    def connect_redis(self):
        """连接到Redis服务器"""
        try:
            self.redis_client = redis.StrictRedis(
                host=REDIS_HOST, 
                port=REDIS_PORT, 
                db=REDIS_DB, 
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info(f"成功连接到 Redis 服务器: {REDIS_HOST}:{REDIS_PORT}")
            
            # 尝试创建消费者组，如果不存在的话
            try:
                self.redis_client.xgroup_create(REDIS_STREAM, CONSUMER_GROUP, id='0', mkstream=True)
                logger.info(f"消费者组 {CONSUMER_GROUP} 创建成功或已存在")
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.info(f"消费者组 {CONSUMER_GROUP} 已存在")
                else:
                    raise e
                    
            return True
        except redis.ConnectionError as e:
            logger.error(f"无法连接到 Redis 服务器: {str(e)}")
            return False
    
    def validate_data(self, data):
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
    
    def parse_iso_date(self, iso_string):
        """
        从ISO格式的时间字符串中提取日期部分
        
        Args:
            iso_string (str): ISO格式的时间字符串
            
        Returns:
            str: 日期部分 (YYYY-MM-DD)
        """
        try:
            # 尝试解析ISO时间戳
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            # 如果解析失败，使用当前日期
            logger.warning(f"无法解析时间戳 '{iso_string}', 使用当前日期")
            return datetime.now().strftime('%Y-%m-%d')
    
    def write_batch_to_files(self, batch_data):
        """
        将一批数据按日期分组写入对应的日志文件
        
        Args:
            batch_data (list): 包含多条数据记录的列表
        """
        # 按日期分组数据
        date_groups = defaultdict(list)
        
        for item in batch_data:
            # 尝试从时间戳中提取日期
            timestamp_str = item.get('timestamp', '')
            date_key = self.parse_iso_date(timestamp_str)
            date_groups[date_key].append(item)
        
        # 将每组数据写入对应的文件
        for date_key, items in date_groups.items():
            filename = os.path.join(LOG_DIR, f"data_{date_key}.log")
            
            try:
                with open(filename, 'a', encoding='utf-8') as f:
                    for item in items:
                        # 将数据转换为紧凑的JSON字符串
                        json_line = json.dumps(item, separators=(',', ':'))
                        f.write(json_line + '\n')
                
                logger.info(f"批量写入 {len(items)} 条记录到文件 {filename}")
                
            except Exception as e:
                logger.error(f"写入文件 {filename} 时出错: {str(e)}")
                # 将失败的数据放入死信队列
                for item in items:
                    try:
                        self.redis_client.xadd(DEAD_LETTER_STREAM, {
                            'error': str(e),
                            'original_data': json.dumps(item)
                        })
                    except Exception as dl_error:
                        logger.error(f"写入死信队列也失败: {str(dl_error)}")
    
    def flush_batch(self):
        """强制刷新当前批次的数据到文件"""
        with self.lock:
            if self.batch_buffer:
                logger.info(f"刷新批次，处理 {len(self.batch_buffer)} 条记录")
                self.write_batch_to_files(self.batch_buffer)
                self.batch_buffer = []
                self.last_flush_time = time.time()
    
    def add_to_batch(self, data_item):
        """
        将数据项添加到批次缓存中，如果达到批次大小或超过时间间隔则写入文件
        
        Args:
            data_item (dict): 要添加的数据项
        """
        with self.lock:
            self.batch_buffer.append(data_item)
            
            # 检查是否需要刷新批次
            if (len(self.batch_buffer) >= BATCH_SIZE or 
                time.time() - self.last_flush_time >= FLUSH_INTERVAL):
                logger.info(f"达到批次条件，处理 {len(self.batch_buffer)} 条记录")
                self.write_batch_to_files(self.batch_buffer)
                self.batch_buffer = []
                self.last_flush_time = time.time()
    
    def process_message(self, msg_id, msg_data):
        """
        处理单条消息
        
        Args:
            msg_id (str): 消息ID
            msg_data (dict): 消息数据
        
        Returns:
            bool: 处理是否成功
        """
        try:
            # 解析数据
            parsed_data = {
                "timestamp": msg_data.get("timestamp"),
                "data": json.loads(msg_data.get("data", "{}")) if msg_data.get("data") else {},
                "client_ip": msg_data.get("client_ip"),
                "server_time": msg_data.get("server_time")
            }
            
            # 验证数据
            if self.validate_data(parsed_data):
                # 添加到批次缓存
                self.add_to_batch(parsed_data)
                return True
            else:
                logger.error(f"数据验证失败，消息ID: {msg_id}, 数据: {msg_data}")
                # 即使验证失败，也要确认消息，避免阻塞
                return True
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败，消息ID: {msg_id}, 错误: {str(e)}, 原始数据: {msg_data}")
            return True  # 即使解析失败，也要确认消息
        except Exception as e:
            logger.error(f"处理消息时出错，消息ID: {msg_id}, 错误: {str(e)}")
            return False
    
    def handle_signal(self, signum, frame):
        """处理退出信号，实现优雅退出"""
        logger.info(f"收到信号 {signum}，开始优雅退出...")
        self.running = False
    
    def run(self):
        """主运行循环"""
        logger.info("Redis Stream 消费者程序启动")
        
        if not self.connect_redis():
            logger.error("无法连接到Redis，程序退出")
            return
        
        # 注册信号处理器以实现优雅退出
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        logger.info(f"开始消费 Redis Stream: {REDIS_STREAM}, "
                   f"消费者组: {CONSUMER_GROUP}, "
                   f"消费者名称: {CONSUMER_NAME}")
        
        while self.running:
            try:
                # 阻塞式读取消息，从'>'开始消费新消息
                messages = self.redis_client.xreadgroup(
                    CONSUMER_GROUP,
                    CONSUMER_NAME,
                    {REDIS_STREAM: '>'},
                    count=1,
                    block=5000  # 阻塞最多5秒
                )
                
                if messages:
                    for stream, message_list in messages:
                        for msg_id, msg_data in message_list:
                            try:
                                # 处理消息
                                success = self.process_message(msg_id, msg_data)
                                
                                if success:
                                    # 确认消息处理成功
                                    self.redis_client.xack(stream, CONSUMER_GROUP, msg_id)
                                    logger.debug(f"消息 {msg_id} 处理成功并确认")
                                else:
                                    logger.error(f"消息 {msg_id} 处理失败，已放入死信队列")
                                    # 将失败的消息放入死信队列
                                    try:
                                        self.redis_client.xadd(DEAD_LETTER_STREAM, {
                                            'error': 'processing_failed',
                                            'original_msg_id': msg_id,
                                            'original_data': json.dumps(msg_data)
                                        })
                                        # 仍需确认原消息以避免重复处理
                                        self.redis_client.xack(stream, CONSUMER_GROUP, msg_id)
                                    except Exception as dl_error:
                                        logger.error(f"写入死信队列失败: {str(dl_error)}")
                                        
                            except Exception as e:
                                logger.error(f"处理消息 {msg_id} 时发生异常: {str(e)}")
                                try:
                                    # 发生异常时也尝试确认消息，避免阻塞
                                    self.redis_client.xack(stream, CONSUMER_GROUP, msg_id)
                                except Exception as ack_error:
                                    logger.error(f"确认消息 {msg_id} 时也发生异常: {str(ack_error)}")
                
            except redis.exceptions.ConnectionError:
                logger.error("Redis连接断开，尝试重新连接...")
                time.sleep(5)  # 等待后重连
                self.connect_redis()
            except Exception as e:
                logger.error(f"消费循环中发生异常: {str(e)}")
                time.sleep(1)  # 避免异常循环过快
        
        # 退出前刷新剩余的批次数据
        logger.info("正在退出，刷新剩余的批次数据...")
        self.flush_batch()
        
        logger.info("Redis Stream 消费者程序已退出")

def main():
    """主函数"""
    consumer = RedisStreamConsumer()
    consumer.run()

if __name__ == "__main__":
    main()