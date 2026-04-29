# daily_stats_job.py
# 空气质量日统计定时任务
# 每天凌晨 01:05 自动计算前一天的统计数据，写入 daily_summary 表

import logging
import os
import sys
import traceback
from datetime import datetime, timedelta

import pymysql
from apscheduler.schedulers.blocking import BlockingScheduler

# 从 config.py 导入数据库连接配置
from config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
    MYSQL_PASSWORD, MYSQL_DATABASE
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

def get_db_connection():
    """创建并返回 MySQL 数据库连接"""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor   # 查询结果以字典形式返回
        )
        logger.debug(f"已连接到 MySQL: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
        return conn
    except pymysql.Error as e:
        logger.error(f"连接 MySQL 数据库失败: {e}")
        raise


def ensure_unique_index(cursor):
    """
    确保 daily_summary 表存在 (device_id, stat_date) 唯一索引。
    如果不存在则自动创建，用于支持 INSERT ... ON DUPLICATE KEY UPDATE  upsert 操作。
    """
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
    计算前一天的空气质量日统计数据，写入 daily_summary 表。

    统计指标（按设备分组）：
      - avg_aqi    : 当日 AQI 平均值，保留两位小数
      - max_aqi    : 当日 AQI 最大值
      - avg_pm2_5  : 当日 PM2.5 平均值，保留两位小数

    使用 INSERT ... ON DUPLICATE KEY UPDATE 实现：
      - 如果某设备某天还没有记录 → 插入新行
      - 如果已有记录（例如补跑或重跑） → 更新已有行
    """
    conn = None
    try:
        # 计算前一天的日期字符串，例如 '2026-04-28'
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        logger.info(f"========== 开始计算 {yesterday} 的空气质量日统计数据 ==========")

        # 1. 建立数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()

        # 2. 确保唯一索引存在（首次运行时自动创建）
        ensure_unique_index(cursor)

        # 3. 检查前一天是否有原始记录，避免对空表执行无意义聚合
        cursor.execute("""
            SELECT COUNT(*) AS cnt
            FROM air_quality_records
            WHERE DATE(sample_time) = %s
        """, (yesterday,))
        row_count = cursor.fetchone()['cnt']

        if row_count == 0:
            logger.warning(f"{yesterday} 没有原始数据（air_quality_records 为空），跳过统计计算")
            return

        logger.info(f"{yesterday} 共有 {row_count} 条原始记录，开始按设备聚合统计...")

        # 4. 按设备分组，计算日统计指标
        cursor.execute("""
            SELECT
                device_id,
                ROUND(AVG(aqi), 2)   AS avg_aqi,
                MAX(aqi)             AS max_aqi,
                ROUND(AVG(pm2_5), 2) AS avg_pm2_5
            FROM air_quality_records
            WHERE DATE(sample_time) = %s
            GROUP BY device_id
        """, (yesterday,))
        stats_rows = cursor.fetchall()

        if not stats_rows:
            logger.warning(f"{yesterday} 聚合结果为空，无数据写入")
            return

        # 5. 将统计结果 upsert 到 daily_summary 表
        insert_count = 0
        update_count = 0

        for row in stats_rows:
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
            """, (
                row['device_id'],
                yesterday,
                row['avg_aqi'],
                row['max_aqi'],
                row['avg_pm2_5']
            ))
            # rowcount = 1 表示插入新行，2 表示更新已有行
            if cursor.rowcount == 1:
                insert_count += 1
            else:
                update_count += 1

        conn.commit()
        logger.info(
            f"{yesterday} 日统计完成 —— "
            f"新插入 {insert_count} 台设备，更新 {update_count} 台设备，"
            f"共计 {len(stats_rows)} 台设备"
        )

    except pymysql.Error as e:
        logger.error(f"数据库操作失败: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        logger.error(f"计算日统计数据时发生未知错误: {e}")
        logger.error(traceback.format_exc())  # 打印完整堆栈便于排查
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logger.debug("数据库连接已关闭")


# ======================== 主入口 ========================

def main():
    """启动定时任务调度器，每天凌晨 01:05 执行一次日统计"""
    logger.info("=" * 50)
    logger.info("空气质量日统计定时任务启动")
    logger.info(f"目标数据库 : {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")
    logger.info(f"执行计划   : 每天凌晨 01:05")
    logger.info("=" * 50)

    # 创建 BlockingScheduler 实例
    scheduler = BlockingScheduler()

    # 添加定时任务
    scheduler.add_job(
        compute_daily_stats,
        trigger='cron',              # cron 表达式触发
        hour=1,
        minute=5,
        id='daily_air_quality_stats',
        name='空气质量日统计',
        misfire_grace_time=3600,     # 错过 1 小时内仍可补执行
        coalesce=True                # 若积压多次则只跑最新的一次
    )

    # ------------------------------------------------------------
    # 调试用：取消下面这行注释，可在启动时立即执行一次统计任务
    # ------------------------------------------------------------
    # compute_daily_stats()

    try:
        logger.info("调度器已启动，等待定时触发...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("收到退出信号，调度器正在停止...")
        scheduler.shutdown()
        logger.info("调度器已停止")


if __name__ == '__main__':
    main()
