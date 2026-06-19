"""
告警检查引擎 —— 后台线程，每5分钟扫描 MongoDB 数据，对比 alert_rules 阈值
超出阈值则创建 alert_records，并可发送邮件通知
"""
import json
import logging
import os
import smtplib
import threading
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText

import pymongo
import pymysql

from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from config import MONGO_HOST, MONGO_PORT, MONGO_DB_NAME, MONGO_COLLECTION

logger = logging.getLogger(__name__)

# 邮件配置（环境变量）
SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
SMTP_FROM = os.getenv('SMTP_FROM', '')
ALERT_NOTIFY_EMAIL = os.getenv('ALERT_NOTIFY_EMAIL', '')

# 指标 → MongoDB 字段名映射
METRIC_FIELD_MAP = {
    'aqi': 'data.AQI',
    'pm25': 'data.PM₂.₅',
    'no2': 'data.NO₂',
    'so2': 'data.SO₂',
    'o3': 'data.O₃',
}


def _get_mysql():
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
    )


def _get_mongo():
    client = pymongo.MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    return client[MONGO_DB_NAME]


def send_email(subject, body):
    """发送邮件通知"""
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM, ALERT_NOTIFY_EMAIL]):
        logger.debug('邮件未配置，跳过')
        return False
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = ALERT_NOTIFY_EMAIL
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        logger.info(f'邮件已发送: {subject}')
        return True
    except Exception as e:
        logger.warning(f'邮件发送失败: {e}')
        return False


def check_alerts():
    """单次告警检查：遍历启用规则 → 查 MongoDB → 创建记录 → 通知"""
    db = _get_mongo()
    coll = db[MONGO_COLLECTION]
    since = (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

    # 读取启用规则
    conn = _get_mysql()
    rules = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM alert_rules WHERE enabled = 1")
            rules = cur.fetchall()
    finally:
        conn.close()

    if not rules:
        logger.debug('无启用规则，跳过检查')
        return

    logger.debug(f'检查 {len(rules)} 条告警规则...')

    for rule in rules:
        metric = rule['metric'].lower()
        field = METRIC_FIELD_MAP.get(metric)
        if not field:
            continue

        operator = rule['operator']
        threshold = rule['threshold']
        rule_id = rule['id']
        severity = rule['severity']
        site_id = rule.get('site_id')

        # 构建 MongoDB 查询
        # 生成阈值条件
        if operator == '>':
            cond = {'$gt': threshold}
        elif operator == '>=':
            cond = {'$gte': threshold}
        elif operator == '<':
            cond = {'$lt': threshold}
        elif operator == '<=':
            cond = {'$lte': threshold}
        else:
            cond = {'$eq': threshold}

        match = {'timestamp': {'$gte': since}, field: cond}
        if site_id:
            match.get('site_id', {})  # site_id not in MongoDB, skip for now

        try:
            # 查出超标的设备及具体值
            exceeded = list(coll.find(match, {field: 1, 'device_id': 1, 'timestamp': 1}).limit(10))
        except Exception as e:
            logger.warning(f'规则 #{rule_id} 查询失败: {e}')
            continue

        if not exceeded:
            continue

        # 创建告警记录
        conn2 = _get_mysql()
        try:
            with conn2.cursor() as cur:
                for doc in exceeded:
                    device_id = doc.get('device_id', 'unknown')
                    value = 0
                    # 从嵌套字段取值
                    parts = field.split('.')
                    v = doc
                    for p in parts:
                        v = v.get(p, {}) if isinstance(v, dict) else 0
                    value = round(float(v), 2) if isinstance(v, (int, float)) else 0

                    # 去重：5分钟内同一个设备同一个规则不重复创建
                    cur.execute(
                        "SELECT COUNT(*) AS cnt FROM alert_records WHERE rule_id=%s AND device_id=%s AND status='pending' AND created_at>=%s",
                        (rule_id, device_id, (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S'))
                    )
                    if cur.fetchone()['cnt'] > 0:
                        continue

                    cur.execute('''
                        INSERT INTO alert_records (rule_id, device_id, site_id, metric, value, threshold, severity, message)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        rule_id, device_id, site_id,
                        metric, value, threshold, severity,
                        f'{metric.upper()} 当前值 {value}，超过阈值 {threshold}'
                    ))
                    logger.info(f'⚠️ 告警: {device_id} {metric}={value} > {threshold}')

            conn2.commit()

            # 通知设备主人
            notified_owners = set()
            for doc in exceeded:
                device_id = doc.get('device_id', '')
                if not device_id or device_id in notified_owners:
                    continue
                notified_owners.add(device_id)
                try:
                    # 查设备主人
                    cur.execute('''
                        SELECT u.open_id, u.email, u.phone
                        FROM user_devices ud
                        LEFT JOIN users u ON ud.open_id = u.open_id
                        WHERE ud.device_id = %s LIMIT 1
                    ''', (device_id,))
                    owner = cur.fetchone()
                    if owner and owner.get('email'):
                        subject = f'[AirInsight] 设备告警: {device_id}'
                        body = f'您的设备 {device_id} 触发告警\n\n规则: {rule["name"]}\n指标: {metric}\n当前值: {value}\n阈值: {operator} {threshold}\n时间: {doc.get("timestamp","")}\n\n请及时处理。'
                        send_email(subject, body)
                except Exception as e:
                    logger.warning(f'通知设备主人失败 {device_id}: {e}')

            # 管理员备用通知（没有主人的设备）
            orphan_devices = [d for d in exceeded if not notified_owners or d.get('device_id','') not in notified_owners]
            if orphan_devices and ALERT_NOTIFY_EMAIL:
                subject = f'[AirInsight] 未关联用户的设备告警'
                body = f'以下设备无绑定用户，告警无法送达:\n'
                for doc in orphan_devices[:5]:
                    body += f'  {doc.get("device_id","?")} {doc.get("timestamp","?")}\n'
                send_email(subject, body)

        except Exception as e:
            logger.warning(f'创建告警记录失败: {e}')
        finally:
            conn2.close()


def start_alert_checker(interval=300):
    """在后台线程中定时运行告警检查"""
    logger.info(f'告警检查引擎启动，间隔 {interval} 秒')
    while True:
        try:
            check_alerts()
        except Exception as e:
            logger.error(f'告警检查异常: {e}')
        time.sleep(interval)


def run_async():
    """启动告警检查后台线程（供 flask_api_server 调用）"""
    t = threading.Thread(target=start_alert_checker, daemon=True)
    t.start()
    return t
