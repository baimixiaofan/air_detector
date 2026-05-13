# miniprogram_api.py
# 微信小程序后端 API — Flask Blueprint

import logging
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import mysql.connector

from config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    MONGO_HOST, MONGO_PORT, MONGO_DB_NAME, MONGO_COLLECTION
)

miniprogram = Blueprint('miniprogram', __name__)
logger = logging.getLogger(__name__)

# MongoDB Unicode 字段 → 小程序 ASCII 字段
_FIELD_MAP = [
    ('AQI',   'aqi'),
    ('PM₂.₅', 'pm2_5'),
    ('NO₂',   'no2'),
    ('SO₂',   'so2'),
    ('O₃',    'o3'),
]


def _get_mongo():
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    return client, client[MONGO_DB_NAME][MONGO_COLLECTION]


def _get_mysql():
    return mysql.connector.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=MYSQL_DATABASE
    )


def _ok(data=None, message='success'):
    return jsonify({'code': 200, 'message': message, 'data': data})


def _err(message, code=400):
    return jsonify({'code': code, 'message': message}), code


def _map_fields(mongo_doc):
    result = {}
    for uni, ascii_ in _FIELD_MAP:
        val = mongo_doc.get('data', {}).get(uni)
        if val is not None:
            result[ascii_] = round(float(val), 2)
    return result


# ======================== 15. 获取设备最新数据 ========================

@miniprogram.route('/api/current', methods=['GET'])
def get_current():
    device_id = request.args.get('device_id')
    if not device_id:
        return _err('缺少 device_id 参数')

    mongo_client = None
    try:
        mongo_client, col = _get_mongo()
        doc = col.find_one({'client_ip': device_id}, sort=[('server_time', -1)])
        if not doc:
            return _ok({'device_id': device_id, 'message': '暂无数据'})

        data = _map_fields(doc)
        data['device_id'] = device_id
        data['timestamp'] = doc.get('timestamp', '')
        return _ok(data)
    except PyMongoError as e:
        logger.error(f"MongoDB 查询失败: {e}")
        return _err('数据库查询失败', 500)
    finally:
        if mongo_client:
            mongo_client.close()


# ======================== 16. 获取历史数据 ========================

@miniprogram.route('/api/history', methods=['GET'])
def get_history():
    device_id = request.args.get('device_id')
    hours = request.args.get('hours', '24')
    if not device_id:
        return _err('缺少 device_id 参数')
    try:
        hours = int(hours)
    except ValueError:
        hours = 24

    mongo_client = None
    try:
        cutoff = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        mongo_client, col = _get_mongo()
        docs = col.find(
            {'client_ip': device_id, 'timestamp': {'$gte': cutoff}},
            sort=[('timestamp', 1)]
        )

        records = []
        for doc in docs:
            entry = {'sample_time': doc.get('timestamp', '')}
            entry.update(_map_fields(doc))
            records.append(entry)
        return _ok(records)
    except PyMongoError as e:
        logger.error(f"MongoDB 查询失败: {e}")
        return _err('数据库查询失败', 500)
    finally:
        if mongo_client:
            mongo_client.close()


# ======================== 17. 获取每日统计 ========================

@miniprogram.route('/api/daily_summary', methods=['GET'])
def daily_summary():
    date = request.args.get('date') or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            'SELECT device_id, stat_date, avg_aqi, max_aqi, avg_pm2_5 '
            'FROM daily_summary WHERE stat_date = %s',
            (date,)
        )
        return _ok(cur.fetchall())
    except mysql.connector.Error as e:
        logger.error(f"MySQL 查询失败: {e}")
        return _err('数据库查询失败', 500)
    finally:
        if conn:
            conn.close()


# ======================== 21. 微信登录 ========================

@miniprogram.route('/api/login', methods=['POST'])
def login():
    body = request.json or {}
    code = body.get('code', '')
    if not code:
        return _err('缺少 code 参数')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM users WHERE open_id = %s', (code,))
        user = cur.fetchone()

        if not user:
            cur.execute(
                'INSERT INTO users (open_id, nickname, avatar_url, create_time, update_time) '
                'VALUES (%s, %s, %s, NOW(), NOW())',
                (code, None, None)
            )
            conn.commit()
            user = {'open_id': code, 'nickname': None, 'avatar_url': None}

        return _ok({
            'open_id': user['open_id'],
            'nickname': user.get('nickname'),
            'avatar_url': user.get('avatar_url')
        })
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"登录失败: {e}")
        return _err('登录失败', 500)
    finally:
        if conn:
            conn.close()


# ======================== 22. 绑定设备 ========================

@miniprogram.route('/api/devices/bind', methods=['POST'])
def bind_device():
    body = request.json or {}
    open_id = body.get('open_id')
    device_id = body.get('device_id')
    if not open_id or not device_id:
        return _err('缺少 open_id 或 device_id 参数')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()

        cur.execute('SELECT id FROM user_devices WHERE open_id=%s AND device_id=%s', (open_id, device_id))
        if not cur.fetchone():
            cur.execute('INSERT INTO user_devices (open_id, device_id) VALUES (%s, %s)', (open_id, device_id))
        conn.commit()
        return _ok(message='绑定成功')
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"绑定失败: {e}")
        return _err('绑定失败', 500)
    finally:
        if conn:
            conn.close()


# ======================== 23. 解绑设备 ========================

@miniprogram.route('/api/devices/unbind', methods=['POST'])
def unbind_device():
    body = request.json or {}
    open_id = body.get('open_id')
    device_id = body.get('device_id')
    if not open_id or not device_id:
        return _err('缺少 open_id 或 device_id 参数')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('DELETE FROM user_devices WHERE open_id=%s AND device_id=%s', (open_id, device_id))
        conn.commit()
        return _ok(message='解绑成功')
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"解绑失败: {e}")
        return _err('解绑失败', 500)
    finally:
        if conn:
            conn.close()


# ======================== 24. 获取我的设备列表 ========================

@miniprogram.route('/api/devices/list', methods=['GET'])
def list_devices():
    open_id = request.args.get('open_id')
    if not open_id:
        return _err('缺少 open_id 参数')

    conn = mongo_client = None
    try:
        conn = _get_mysql()
        cur = conn.cursor(dictionary=True)

        cur.execute('SELECT device_id, bind_time FROM user_devices WHERE open_id=%s', (open_id,))
        bound = cur.fetchall()
        if not bound:
            return _ok([])

        device_ids = [r['device_id'] for r in bound]

        # 从 devices 表获取位置信息
        ph = ','.join(['%s'] * len(device_ids))
        cur.execute(f'SELECT device_id, location_name, longitude, latitude FROM devices WHERE device_id IN ({ph})', device_ids)
        device_info = {r['device_id']: r for r in cur.fetchall()}

        # 从 MongoDB 获取最新上报时间
        mongo_client, col = _get_mongo()
        pipeline = [
            {'$match': {'client_ip': {'$in': device_ids}}},
            {'$sort': {'server_time': -1}},
            {'$group': {
                '_id': '$client_ip',
                'latest_time': {'$first': '$timestamp'},
                'server_time':  {'$first': '$server_time'}
            }}
        ]
        latest = {d['_id']: d for d in col.aggregate(pipeline)}

        now = datetime.now()
        result = []
        for b in bound:
            did = b['device_id']
            info = device_info.get(did, {})
            lat = latest.get(did, {})
            last_ts = lat.get('server_time', '')
            is_online = False
            if last_ts:
                try:
                    dt = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
                    if (now - dt.replace(tzinfo=None)).total_seconds() < 90:
                        is_online = True
                except (ValueError, AttributeError):
                    pass

            result.append({
                'device_id': did,
                'location_name': info.get('location_name', ''),
                'status': 'online' if is_online else 'offline',
                'last_longitude': info.get('longitude'),
                'last_latitude':  info.get('latitude'),
                'last_update': lat.get('latest_time', ''),
                'bind_time': b.get('bind_time').strftime('%Y-%m-%d %H:%M:%S') if b.get('bind_time') else ''
            })

        return _ok(result)
    except (PyMongoError, mysql.connector.Error) as e:
        logger.error(f"查询设备列表失败: {e}")
        return _err('查询失败', 500)
    finally:
        if conn:
            conn.close()
        if mongo_client:
            mongo_client.close()


# ======================== 25. 更新设备位置 ========================

@miniprogram.route('/api/devices/location', methods=['PUT'])
def update_location():
    body = request.json or {}
    device_id = body.get('device_id')
    longitude = body.get('longitude')
    latitude  = body.get('latitude')
    if not device_id or longitude is None or latitude is None:
        return _err('缺少 device_id、longitude 或 latitude 参数')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('SELECT id FROM devices WHERE device_id=%s', (device_id,))
        if cur.fetchone():
            cur.execute("UPDATE devices SET longitude=%s, latitude=%s WHERE device_id=%s",
                        (longitude, latitude, device_id))
        else:
            cur.execute("INSERT INTO devices (device_id, longitude, latitude, status, create_time) "
                        "VALUES (%s,%s,%s,'offline',NOW())",
                        (device_id, longitude, latitude))
        conn.commit()
        return _ok(message='位置更新成功')
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"位置更新失败: {e}")
        return _err('位置更新失败', 500)
    finally:
        if conn:
            conn.close()


# ======================== 18. 添加收藏 ========================

@miniprogram.route('/api/favorites/add', methods=['POST'])
def add_favorite():
    body = request.json or {}
    open_id = body.get('open_id')
    device_id = body.get('device_id')
    if not open_id or not device_id:
        return _err('缺少 open_id 或 device_id 参数')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('SELECT id FROM user_favorites WHERE open_id=%s AND device_id=%s', (open_id, device_id))
        if not cur.fetchone():
            cur.execute('INSERT INTO user_favorites (open_id, device_id) VALUES (%s,%s)', (open_id, device_id))
        conn.commit()
        return _ok(message='收藏成功')
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"收藏失败: {e}")
        return _err('收藏失败', 500)
    finally:
        if conn:
            conn.close()


# ======================== 19. 取消收藏 ========================

@miniprogram.route('/api/favorites/remove', methods=['POST'])
def remove_favorite():
    body = request.json or {}
    open_id = body.get('open_id')
    device_id = body.get('device_id')
    if not open_id or not device_id:
        return _err('缺少 open_id 或 device_id 参数')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor()
        cur.execute('DELETE FROM user_favorites WHERE open_id=%s AND device_id=%s', (open_id, device_id))
        conn.commit()
        return _ok(message='取消收藏成功')
    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"取消收藏失败: {e}")
        return _err('取消收藏失败', 500)
    finally:
        if conn:
            conn.close()


# ======================== 20. 获取收藏列表 ========================

@miniprogram.route('/api/favorites/list', methods=['GET'])
def list_favorites():
    open_id = request.args.get('open_id')
    if not open_id:
        return _err('缺少 open_id 参数')

    conn = None
    try:
        conn = _get_mysql()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            'SELECT f.device_id, d.location_name, f.create_time AS add_time '
            'FROM user_favorites f LEFT JOIN devices d ON f.device_id = d.device_id '
            'WHERE f.open_id = %s ORDER BY f.create_time DESC',
            (open_id,)
        )
        rows = cur.fetchall()
        for row in rows:
            if row.get('add_time'):
                row['add_time'] = row['add_time'].strftime('%Y-%m-%d %H:%M:%S')
        return _ok(rows)
    except mysql.connector.Error as e:
        logger.error(f"查询收藏失败: {e}")
        return _err('查询失败', 500)
    finally:
        if conn:
            conn.close()
