# daily_stats_job.py
# 空气质量日统计定时任务
# 每天凌晨 01:05 从 MongoDB 读取原始数据，计算日统计后写入 MySQL

import logging
import os
import sys
import traceback
from datetime import datetime, timedelta

import pymysql
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from apscheduler.schedulers.blocking import BlockingScheduler

from config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
    MYSQL_PASSWORD, MYSQL_DATABASE,
    MONGO_HOST, MONGO_PORT, MONGO_DB_NAME, MONGO_COLLECTION
)

# ======================== 日志配置 ========================
LOG_DIR = os.getenv('LOG_DIR', '.')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=numeric_level,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'daily_stats.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ======================== 数据库工具函数 ========================

def get_mongo_collection():
    """连接 MongoDB，返回集合对象"""
    try:
        client = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,
            serverSelectionTimeoutMS=5000
        )
        # 测试连接
        client.admin.command('ping')
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION]
        logger.debug(f"已连接到 MongoDB: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}.{MONGO_COLLECTION}")
        return client, collection
    except PyMongoError as e:
        logger.error(f"连接 MongoDB 失败: {e}")
        raise


def get_mysql_connection():
    """连接 MySQL，返回连接对象"""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.debug(f"已连接到 MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
        return conn
    except pymysql.Error as e:
        logger.error(f"连接 MySQL 失败: {e}")
        raise


def ensure_unique_index(cursor):
    """确保 daily_summary 表存在 (device_id, stat_date) 唯一索引"""
    try:
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM information_schema.statistics
            WHERE table_schema = %s
              AND table_name = 'daily_summary'
              AND index_name = 'uk_device_date'
        """, (MYSQL_DATABASE,))
        result = cursor.fetchone()

        if result['cnt'] == 0:
            cursor.execute("""
                CREATE UNIQUE INDEX uk_device_date
                ON daily_summary (device_id, stat_date)
            """)
            logger.info("已创建唯一索引 uk_device_date (device_id, stat_date)")
        else:
            logger.debug("唯一索引 uk_device_date 已存在，跳过创建")
    except pymysql.Error as e:
        logger.error(f"检查或创建唯一索引失败: {e}")
        raise


# ======================== 核心统计任务 ========================

def compute_daily_stats():
    """
    从 MongoDB 读取前一天的原始数据，
    按设备（client_ip）聚合统计，写入 MySQL 的 daily_summary 表。
    """
    mongo_client = None
    mysql_conn = None
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        logger.info(f"========== 开始计算 {yesterday} 的空气质量日统计数据 ==========")

        # ---------- 1. 从 MongoDB 聚合数据 ----------
        mongo_client, collection = get_mongo_collection()

        pipeline = [
            # 匹配昨天的时间戳（timestamp 字段格式: "YYYY-MM-DD HH:MM:SS"）
            {"$match": {"timestamp": {"$regex": f"^{yesterday}"}}},
            # 按 client_ip 分组，计算统计指标
            {"$group": {
                "_id": "$client_ip",
                "avg_aqi":   {"$avg": "$data.AQI"},
                "max_aqi":   {"$max": "$data.AQI"},
                "avg_pm2_5": {"$avg": "$data.PM₂.₅"}
            }}
        ]

        stats = list(collection.aggregate(pipeline))

        if not stats:
            logger.warning(f"{yesterday} 在 MongoDB 中没有原始数据，跳过统计计算")
            return

        logger.info(f"{yesterday} 从 MongoDB 聚合到 {len(stats)} 台设备的数据")

        # ---------- 2. 写入 MySQL ----------
        mysql_conn = get_mysql_connection()
        cursor = mysql_conn.cursor()

        ensure_unique_index(cursor)

        insert_count = 0
        update_count = 0

        for row in stats:
            device_id = row['_id']
            avg_aqi = round(row['avg_aqi'], 2)
            max_aqi = round(row['max_aqi'], 2)
            avg_pm2_5 = round(row['avg_pm2_5'], 2)

            cursor.execute("""
                INSERT INTO daily_summary
                    (device_id, stat_date, avg_aqi, max_aqi, avg_pm2_5, create_time)
                VALUES
                    (%s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    avg_aqi   = VALUES(avg_aqi),
                    max_aqi   = VALUES(max_aqi),
                    avg_pm2_5 = VALUES(avg_pm2_5),
                    create_time = NOW()
            """, (device_id, yesterday, avg_aqi, max_aqi, avg_pm2_5))

            if cursor.rowcount == 1:
                insert_count += 1
            else:
                update_count += 1

        mysql_conn.commit()

        # 打印每个设备的统计值
        for row in stats:
            logger.info(
                f"  {row['_id']}: avg_aqi={row['avg_aqi']:.2f}, "
                f"max_aqi={row['max_aqi']:.2f}, avg_pm2_5={row['avg_pm2_5']:.2f}"
            )
        logger.info(
            f"{yesterday} 日统计完成 —— "
            f"新插入 {insert_count} 条, 更新 {update_count} 条, 共 {len(stats)} 条"
        )

    except PyMongoError as e:
        logger.error(f"MongoDB 操作失败: {e}")
    except pymysql.Error as e:
        logger.error(f"MySQL 操作失败: {e}")
        if mysql_conn:
            mysql_conn.rollback()
    except Exception as e:
        logger.error(f"未知错误: {e}")
        logger.error(traceback.format_exc())
        if mysql_conn:
            mysql_conn.rollback()
    finally:
        if mongo_client:
            mongo_client.close()
        if mysql_conn:
            mysql_conn.close()


# ======================== 主入口 ========================

def main():
    """启动定时任务调度器"""
    logger.info("=" * 50)
    logger.info("空气质量日统计定时任务启动")
    logger.info(f"MongoDB : {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}.{MONGO_COLLECTION}")
    logger.info(f"MySQL   : {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    logger.info(f"执行计划: 每天凌晨 01:05")
    logger.info("=" * 50)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        compute_daily_stats,
        trigger='cron',
        hour=1,
        minute=5,
        id='daily_air_quality_stats',
        name='空气质量日统计',
        misfire_grace_time=3600,
        coalesce=True
    )

    # 调试用：取消注释可在启动时立即执行一次
    # compute_daily_stats()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("收到退出信号，调度器停止")
        scheduler.shutdown()


if __name__ == '__main__':
    main()
