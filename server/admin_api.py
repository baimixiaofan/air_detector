"""
admin_api.py —— 企业空气质量监测管理平台后端 API
蓝图: admin_api, 前缀 /api/admin
认证: Redis Token（24h 过期）
"""

import json
import logging
import os
import secrets
from datetime import datetime
from functools import wraps

from flask import Blueprint, request, jsonify, g
import pymysql
import pymongo
import requests as _requests

from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
from config import MONGO_HOST, MONGO_PORT, MONGO_DB_NAME, MONGO_COLLECTION

logger = logging.getLogger(__name__)

admin_api = Blueprint('admin_api', __name__)

# ---- 延迟导入：flask_api_server 中的 redis_client ----
_srv = None


def _get_srv():
    global _srv
    if _srv is None:
        import flask_api_server as s
        _srv = s
    return _srv


# ---- 数据库连接 ----

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


# ---- Redis Token 认证 ----

TOKEN_PREFIX = 'admin_token:'
TOKEN_TTL = 86400  # 24 小时


def _redis():
    return _get_srv().redis_client


def _gen_token():
    return secrets.token_hex(32)


def _save_token(token, user_id, username, role):
    r = _redis()
    if r is None:
        return False
    data = json.dumps({'user_id': user_id, 'username': username, 'role': role})
    r.setex(f'{TOKEN_PREFIX}{token}', TOKEN_TTL, data)
    return True


def _get_token_data(token):
    r = _redis()
    if r is None:
        return None
    data = r.get(f'{TOKEN_PREFIX}{token}')
    if data is None:
        return None
    # 滑动续期
    r.expire(f'{TOKEN_PREFIX}{token}', TOKEN_TTL)
    return json.loads(data)


def _del_token(token):
    r = _redis()
    if r is None:
        return
    r.delete(f'{TOKEN_PREFIX}{token}')


# ---- 认证装饰器 ----

def require_admin_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'code': 401, 'msg': '未提供认证令牌'}), 401
        token = auth[7:]
        user_data = _get_token_data(token)
        if user_data is None:
            return jsonify({'code': 401, 'msg': '令牌无效或已过期'}), 401
        g.current_user = user_data
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        @require_admin_auth
        def decorated(*args, **kwargs):
            if g.current_user.get('role') not in roles:
                return jsonify({'code': 403, 'msg': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ---- 操作日志辅助 ----

def _log_action(action, target_type=None, target_id=None, details=None):
    """记录操作日志到 admin_operation_logs 表"""
    user = g.get('current_user', {})
    user_id = user.get('user_id', 0)
    username = user.get('username', 'unknown')
    ip = request.remote_addr or ''
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO admin_operation_logs (admin_user_id, username, action, target_type, target_id, details, ip_address) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (user_id, username, action, target_type, target_id, json.dumps(details, ensure_ascii=False) if details else None, ip)
            )
        conn.commit()
    except Exception as e:
        logger.error(f'操作日志写入失败: {e}')
    finally:
        conn.close()


# ---- DeepSeek AI 辅助 ----

_DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
_DEEPSEEK_MODEL = 'deepseek-chat'
_DEEPSEEK_TIMEOUT = 15


def _call_deepseek(prompt, max_tokens=300):
    """调用 DeepSeek API，失败返回 None"""
    if not _DEEPSEEK_API_KEY:
        return None
    try:
        resp = _requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {_DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': _DEEPSEEK_MODEL,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.7,
                'max_tokens': max_tokens
            },
            timeout=_DEEPSEEK_TIMEOUT
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        logger.warning(f'DeepSeek API 调用失败: {e}')
    return None


# ====================================================================
# 认证接口
# ====================================================================

@admin_api.route('/login', methods=['POST'])
def login():
    body = request.json or {}
    username = body.get('username', '').strip()
    password = body.get('password', '').strip()
    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, username, password_hash, display_name, role, status FROM admin_users WHERE username=%s', (username,))
            user = cur.fetchone()
    finally:
        conn.close()

    if not user:
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401
    if user['status'] != 1:
        return jsonify({'code': 403, 'msg': '账号已被禁用'}), 403

    # 验证密码 — werkzeug 的 check_password_hash
    from werkzeug.security import check_password_hash
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

    # 生成 token
    token = _gen_token()
    _save_token(token, user['id'], user['username'], user['role'])

    # 更新最后登录时间
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('UPDATE admin_users SET last_login=NOW() WHERE id=%s', (user['id'],))
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        'code': 200,
        'data': {
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'display_name': user['display_name'],
                'role': user['role']
            }
        }
    })


@admin_api.route('/profile', methods=['GET'])
@require_admin_auth
def profile():
    return jsonify({
        'code': 200,
        'data': g.current_user
    })


@admin_api.route('/logout', methods=['POST'])
@require_admin_auth
def logout():
    auth = request.headers.get('Authorization', '')
    token = auth[7:]
    _del_token(token)
    return jsonify({'code': 200, 'msg': '已退出登录'})


# ====================================================================
# 数据看板接口
# ====================================================================

@admin_api.route('/dashboard/stats', methods=['GET'])
@require_admin_auth
def dashboard_stats():
    """总览：站点数、设备数、在线数、今日告警数"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS cnt FROM sites WHERE status=1')
            total_sites = cur.fetchone()['cnt']
            cur.execute('SELECT COUNT(DISTINCT device_id) AS cnt FROM site_devices')
            total_devices = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM alert_records WHERE status='pending'")
            pending_alerts = cur.fetchone()['cnt']
    finally:
        conn.close()

    # 在线设备数：从 MongoDB 取最近 5 分钟有数据的设备
    online = 0
    try:
        db = _get_mongo()
        five_min_ago = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        online = db[MONGO_COLLECTION].distinct('device_id', {'timestamp': {'$gte': five_min_ago}})
        online = len(online)
    except Exception as e:
        logger.error(f'MongoDB 查询失败: {e}')

    return jsonify({
        'code': 200,
        'data': {
            'total_sites': total_sites,
            'total_devices': total_devices,
            'online_devices': online,
            'offline_devices': max(0, total_devices - online),
            'pending_alerts': pending_alerts
        }
    })


@admin_api.route('/dashboard/realtime', methods=['GET'])
@require_admin_auth
def dashboard_realtime():
    """所有活跃设备最新 AQI 数据（含地理位置和用户标签）"""
    try:
        db = _get_mongo()
        coll = db[MONGO_COLLECTION]
        device_ids = coll.distinct('device_id')
        results = []
        for did in device_ids:
            doc = coll.find_one(
                {'device_id': did},
                sort=[('timestamp', pymongo.DESCENDING)]
            )
            if doc:
                data = doc.get('data', {})
                loc = doc.get('location', {})
                user = doc.get('user_info', {})
                results.append({
                    'device_id': did,
                    'aqi': data.get('AQI'),
                    'pm25': data.get('PM₂.₅'),
                    'no2': data.get('NO₂'),
                    'so2': data.get('SO₂'),
                    'o3': data.get('O₃'),
                    'timestamp': doc.get('timestamp'),
                    'server_time': doc.get('server_time'),
                    'location': {
                        'province': loc.get('province', ''),
                        'city': loc.get('city', ''),
                        'district': loc.get('district', ''),
                        'latitude': loc.get('latitude'),
                        'longitude': loc.get('longitude')
                    } if loc else None,
                    'user_info': {
                        'name': user.get('name', ''),
                        'industry': user.get('industry', '')
                    } if user else None
                })
        results.sort(key=lambda x: x.get('device_id', ''))
        return jsonify({'code': 200, 'data': results})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_api.route('/dashboard/alert-summary', methods=['GET'])
@require_admin_auth
def dashboard_alert_summary():
    """未处理告警按严重程度统计"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT severity, COUNT(*) AS cnt
                FROM alert_records
                WHERE status='pending'
                GROUP BY severity
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    summary = {'info': 0, 'warning': 0, 'critical': 0}
    for row in rows:
        summary[row['severity']] = row['cnt']
    return jsonify({'code': 200, 'data': summary})


@admin_api.route('/dashboard/trend', methods=['GET'])
@require_admin_auth
def dashboard_trend():
    """24h AQI/PM2.5 趋势（按小时聚合）"""
    import re
    try:
        db = _get_mongo()
        coll = db[MONGO_COLLECTION]
        from datetime import timedelta
        since = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        pipeline = [
            {'$match': {'timestamp': {'$gte': since}}},
            {'$group': {
                '_id': {'$substr': ['$timestamp', 0, 13]},  # 按小时分组
                'avg_aqi': {'$avg': '$data.AQI'},
                'avg_pm25': {'$avg': '$data.PM₂.₅'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        results = list(coll.aggregate(pipeline))
        return jsonify({
            'code': 200,
            'data': [{
                'hour': r['_id'],
                'avg_aqi': round(r['avg_aqi'], 1),
                'avg_pm25': round(r['avg_pm25'], 1),
                'count': r['count']
            } for r in results]
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ====================================================================
# 智能诊断 API
# ====================================================================

_DIAGNOSTICS_TEMPLATES = {
    'good': {'label': '优秀', 'color': 'green', 'suggestion': '空气质量良好，建议继续保持通风。'},
    'moderate': {'label': '良好', 'color': 'yellow', 'suggestion': '空气质量尚可，建议定期开窗通风。'},
    'lightly_polluted': {'label': '轻度污染', 'color': 'orange', 'suggestion': '建议减少开窗，敏感人群注意减少户外活动。'},
    'moderately_polluted': {'label': '中度污染', 'color': 'red', 'suggestion': '建议开启空气净化设备，关闭门窗。'},
    'heavily_polluted': {'label': '重度污染', 'color': 'purple', 'suggestion': '严重污染！建议开启净化设备并减少外出。'},
}


def _calc_risk_score(aqi_avg, exceed_days):
    """计算 0-100 风险评分"""
    score = 0
    if aqi_avg <= 50:
        score = 10
    elif aqi_avg <= 100:
        score = 30
    elif aqi_avg <= 150:
        score = 50
    elif aqi_avg <= 200:
        score = 70
    else:
        score = 90
    # 超标天数加成
    score += min(exceed_days * 5, 20)
    return min(score, 100)


def _get_health_level(aqi_avg):
    if aqi_avg <= 50:
        return 'good'
    elif aqi_avg <= 100:
        return 'moderate'
    elif aqi_avg <= 150:
        return 'lightly_polluted'
    elif aqi_avg <= 200:
        return 'moderately_polluted'
    else:
        return 'heavily_polluted'


def _get_primary_pollutant(stats):
    """找出主要超标污染物"""
    thresholds = {'avg_pm25': 75, 'avg_no2': 80, 'avg_so2': 50, 'avg_o3': 100}
    candidates = []
    for key, val in stats.items():
        if key in thresholds and val is not None and val > thresholds[key]:
            candidates.append((val / thresholds[key], key))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    mapper = {'avg_pm25': 'PM2.5', 'avg_no2': 'NO2', 'avg_so2': 'SO2', 'avg_o3': 'O3'}
    return mapper.get(candidates[0][1], candidates[0][1])


def _generate_diagnostic_prompt(site_name, site_type, stats, health_level, risk_score):
    """为 AI 诊断生成 prompt"""
    return f"""你是一个空气质量分析专家。请对以下监测站点进行健康诊断：

站点名称：{site_name}
站点类型：{site_type}
最近 7 天数据：
- 平均 AQI：{stats.get('avg_aqi', 'N/A')}
- 最大 AQI：{stats.get('max_aqi', 'N/A')}
- 平均 PM2.5：{stats.get('avg_pm25', 'N/A')}
- 平均 NO2：{stats.get('avg_no2', 'N/A')}
- 平均 SO2：{stats.get('avg_so2', 'N/A')}
- 平均 O3：{stats.get('avg_o3', 'N/A')}
- 超标天数：{stats.get('exceed_days', 0)} 天
- 健康等级：{health_level}
- 风险评分：{risk_score}/100

请用一段不超过 200 字的简洁文字输出：
1. 总体健康评估结论
2. 主要污染物问题
3. 具体的改善建议

语气要专业、客观、有建设性。"""


@admin_api.route('/dashboard/diagnostics', methods=['GET'])
@require_admin_auth
def dashboard_diagnostics():
    """所有站点的智能诊断卡"""
    from datetime import timedelta
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, code, area, site_type, address, longitude, latitude FROM sites WHERE status=1')
            sites = cur.fetchall()
    finally:
        conn.close()

    db = _get_mongo()
    coll = db[MONGO_COLLECTION]

    diagnostics = []
    for site in sites:
        # 获取该站点绑定的设备
        conn2 = _get_mysql()
        try:
            with conn2.cursor() as cur:
                cur.execute('SELECT device_id FROM site_devices WHERE site_id=%s', (site['id'],))
                devices = [r['device_id'] for r in cur.fetchall()]
        finally:
            conn2.close()

        if not devices:
            continue

        # 从 MongoDB 获取最近 7 天数据
        pipeline = [
            {'$match': {'device_id': {'$in': devices}, 'timestamp': {'$gte': seven_days_ago}}},
            {'$group': {
                '_id': None,
                'avg_aqi': {'$avg': '$data.AQI'},
                'max_aqi': {'$max': '$data.AQI'},
                'avg_pm25': {'$avg': '$data.PM₂.₅'},
                'avg_no2': {'$avg': '$data.NO₂'},
                'avg_so2': {'$avg': '$data.SO₂'},
                'avg_o3': {'$avg': '$data.O₃'},
                'count': {'$sum': 1}
            }}
        ]
        results = list(coll.aggregate(pipeline))
        if not results:
            continue
        stats = results[0]
        # 计算近似超标天数
        exceed_pipeline = [
            {'$match': {'device_id': {'$in': devices}, 'timestamp': {'$gte': seven_days_ago}, 'data.AQI': {'$gte': 100}}},
            {'$group': {'_id': {'$substr': ['$timestamp', 0, 10]}, 'count': {'$sum': 1}}},
            {'$count': 'days'}
        ]
        exceed_result = list(coll.aggregate(exceed_pipeline))
        exceed_days = exceed_result[0]['days'] if exceed_result else 0

        avg_aqi = round(stats.get('avg_aqi', 0), 1)
        health_level = _get_health_level(avg_aqi)
        risk_score = _calc_risk_score(avg_aqi, exceed_days)
        primary = _get_primary_pollutant(stats)

        # AI 诊断
        site_type = site.get('site_type', 'office')
        ai_diagnosis = _call_deepseek(
            _generate_diagnostic_prompt(site['name'], site_type, {**stats, 'exceed_days': exceed_days}, health_level, risk_score),
            max_tokens=300
        )

        level_info = _DIAGNOSTICS_TEMPLATES.get(health_level, _DIAGNOSTICS_TEMPLATES['moderate'])
        suggestion = ai_diagnosis or level_info['suggestion']

        diagnostics.append({
            'site_id': site['id'],
            'site_name': site['name'],
            'area': site['area'],
            'site_type': site_type,
            'health_level': health_level,
            'health_label': level_info['label'],
            'health_color': level_info['color'],
            'risk_score': risk_score,
            'avg_aqi': avg_aqi,
            'max_aqi': round(stats.get('max_aqi', 0), 1),
            'primary_pollutant': primary,
            'exceed_days': exceed_days,
            'suggestion': suggestion,
            'ai_generated': ai_diagnosis is not None
        })

    return jsonify({'code': 200, 'data': diagnostics})


@admin_api.route('/dashboard/diagnostics/<int:site_id>', methods=['GET'])
@require_admin_auth
def dashboard_diagnostics_detail(site_id):
    """单个站点诊断详情"""
    # 重用上面的逻辑，单站点版本
    from datetime import timedelta
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, code, area, site_type, address, longitude, latitude FROM sites WHERE id=%s', (site_id,))
            site = cur.fetchone()
            if not site:
                return jsonify({'code': 404, 'msg': '站点不存在'}), 404
            cur.execute('SELECT device_id FROM site_devices WHERE site_id=%s', (site_id,))
            devices = [r['device_id'] for r in cur.fetchall()]
    finally:
        conn.close()

    if not devices:
        return jsonify({'code': 400, 'msg': '该站点未绑定设备'}), 400

    db = _get_mongo()
    coll = db[MONGO_COLLECTION]

    pipeline = [
        {'$match': {'device_id': {'$in': devices}, 'timestamp': {'$gte': seven_days_ago}}},
        {'$group': {
            '_id': None,
            'avg_aqi': {'$avg': '$data.AQI'},
            'max_aqi': {'$max': '$data.AQI'},
            'avg_pm25': {'$avg': '$data.PM₂.₅'},
            'avg_no2': {'$avg': '$data.NO₂'},
            'avg_so2': {'$avg': '$data.SO₂'},
            'avg_o3': {'$avg': '$data.O₃'},
            'count': {'$sum': 1}
        }}
    ]
    results = list(coll.aggregate(pipeline))
    if not results:
        return jsonify({'code': 404, 'msg': '该站点暂无数据'}), 404

    stats = results[0]
    exceed_pipeline = [
        {'$match': {'device_id': {'$in': devices}, 'timestamp': {'$gte': seven_days_ago}, 'data.AQI': {'$gte': 100}}},
        {'$group': {'_id': {'$substr': ['$timestamp', 0, 10]}, 'count': {'$sum': 1}}},
        {'$count': 'days'}
    ]
    exceed_days = list(coll.aggregate(exceed_pipeline))
    exceed_days = exceed_days[0]['days'] if exceed_days else 0

    avg_aqi = round(stats.get('avg_aqi', 0), 1)
    health_level = _get_health_level(avg_aqi)
    risk_score = _calc_risk_score(avg_aqi, exceed_days)
    primary = _get_primary_pollutant(stats)
    level_info = _DIAGNOSTICS_TEMPLATES.get(health_level, _DIAGNOSTICS_TEMPLATES['moderate'])

    ai_diagnosis = _call_deepseek(
        _generate_diagnostic_prompt(site['name'], site.get('site_type', 'office'), {**stats, 'exceed_days': exceed_days}, health_level, risk_score),
        max_tokens=500
    )
    suggestion = ai_diagnosis or level_info['suggestion']

    # 每日趋势
    daily_trend = list(coll.aggregate([
        {'$match': {'device_id': {'$in': devices}, 'timestamp': {'$gte': seven_days_ago}}},
        {'$group': {
            '_id': {'$substr': ['$timestamp', 0, 10]},
            'avg_aqi': {'$avg': '$data.AQI'},
            'avg_pm25': {'$avg': '$data.PM₂.₅'},
            'count': {'$sum': 1}
        }},
        {'$sort': {'_id': 1}}
    ]))

    return jsonify({
        'code': 200,
        'data': {
            'site': {
                'id': site['id'], 'name': site['name'], 'code': site['code'],
                'area': site['area'], 'site_type': site['site_type'],
                'address': site['address'], 'longitude': site['longitude'], 'latitude': site['latitude']
            },
            'diagnosis': {
                'health_level': health_level,
                'health_label': level_info['label'],
                'health_color': level_info['color'],
                'risk_score': risk_score,
                'avg_aqi': avg_aqi,
                'max_aqi': round(stats.get('max_aqi', 0), 1),
                'avg_pm25': round(stats.get('avg_pm25', 0), 1),
                'avg_no2': round(stats.get('avg_no2', 0), 1),
                'avg_so2': round(stats.get('avg_so2', 0), 1),
                'avg_o3': round(stats.get('avg_o3', 0), 1),
                'primary_pollutant': primary,
                'exceed_days': exceed_days,
                'total_records': stats.get('count', 0),
                'suggestion': suggestion,
                'ai_generated': ai_diagnosis is not None
            },
            'daily_trend': [{
                'date': r['_id'],
                'avg_aqi': round(r['avg_aqi'], 1),
                'avg_pm25': round(r['avg_pm25'], 1)
            } for r in daily_trend]
        }
    })


# ====================================================================
# 设备管理 API
# ====================================================================

@admin_api.route('/devices', methods=['GET'])
@require_admin_auth
def get_devices():
    """设备列表（支持分页、筛选）"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '')
    offset = (page - 1) * size

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            where = '1=1'
            params = []
            if keyword:
                where += ' AND (d.name LIKE %s OR d.device_id LIKE %s)'
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            if status:
                where += ' AND d.status = %s'
                params.append(int(status))

            cur.execute(f'SELECT COUNT(*) AS cnt FROM devices d WHERE {where}', params)
            total = cur.fetchone()['cnt']

            cur.execute(
                f'SELECT d.* FROM devices d WHERE {where} ORDER BY d.id DESC LIMIT %s OFFSET %s',
                params + [size, offset]
            )
            devices = cur.fetchall()

            # 获取每个设备的站点信息
            for d in devices:
                cur.execute(
                    'SELECT s.id AS site_id, s.name AS site_name FROM site_devices sd '
                    'JOIN sites s ON s.id = sd.site_id WHERE sd.device_id = %s',
                    (d.get('device_id', d.get('id')),)
                )
                site = cur.fetchone()
                d['site'] = site if site else None
    finally:
        conn.close()

    # 获取在线状态（从 MongoDB 最近 5 分钟有数据）
    try:
        db = _get_mongo()
        coll = db[MONGO_COLLECTION]
        five_min_ago = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        online_ids = set(coll.distinct('device_id', {'timestamp': {'$gte': five_min_ago}}))
        for d in devices:
            d['online'] = d.get('device_id', d.get('id')) in online_ids
    except Exception:
        for d in devices:
            d['online'] = False

    return jsonify({'code': 200, 'data': {'list': devices, 'total': total, 'page': page, 'size': size}})


@admin_api.route('/devices/<int:device_pk_id>', methods=['GET'])
@require_admin_auth
def get_device_detail(device_pk_id):
    """设备详情"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM devices WHERE id=%s', (device_pk_id,))
            device = cur.fetchone()
            if not device:
                return jsonify({'code': 404, 'msg': '设备不存在'}), 404
            cur.execute(
                'SELECT s.id AS site_id, s.name AS site_name FROM site_devices sd '
                'JOIN sites s ON s.id = sd.site_id WHERE sd.device_id = %s',
                (device.get('device_id', device.get('id')),)
            )
            device['site'] = cur.fetchone()
    finally:
        conn.close()

    # 获取最新数据
    try:
        db = _get_mongo()
        doc = db[MONGO_COLLECTION].find_one(
            {'device_id': device.get('device_id', device.get('id'))},
            sort=[('timestamp', pymongo.DESCENDING)]
        )
        if doc:
            device['latest_data'] = doc.get('data', {})
            device['latest_timestamp'] = doc.get('timestamp')
    except Exception:
        pass

    return jsonify({'code': 200, 'data': device})


@admin_api.route('/devices', methods=['POST'])
@require_admin_auth
def create_device():
    """新增设备"""
    body = request.json or {}
    name = body.get('name', '').strip()
    device_id = body.get('device_id', '').strip()
    if not name or not device_id:
        return jsonify({'code': 400, 'msg': '设备名称和设备ID不能为空'}), 400

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM devices WHERE device_id=%s', (device_id,))
            if cur.fetchone():
                return jsonify({'code': 400, 'msg': '设备ID已存在'}), 400
            cur.execute(
                'INSERT INTO devices (name, device_id, status) VALUES (%s, %s, %s)',
                (name, device_id, body.get('status', 1))
            )
            new_id = cur.lastrowid
            # 绑定站点
            site_id = body.get('site_id')
            if site_id:
                cur.execute('INSERT IGNORE INTO site_devices (site_id, device_id) VALUES (%s, %s)', (site_id, device_id))
        conn.commit()
        _log_action('新增设备', 'device', new_id, {'name': name, 'device_id': device_id})
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'id': new_id}, 'msg': '设备已添加'})


@admin_api.route('/devices/<int:device_pk_id>', methods=['PUT'])
@require_admin_auth
def update_device(device_pk_id):
    """更新设备"""
    body = request.json or {}
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM devices WHERE id=%s', (device_pk_id,))
            device = cur.fetchone()
            if not device:
                return jsonify({'code': 404, 'msg': '设备不存在'}), 404

            fields = []
            params = []
            for key in ('name', 'status', 'device_id'):
                if key in body:
                    fields.append(f'{key}=%s')
                    params.append(body[key])
            if fields:
                params.append(device_pk_id)
                cur.execute(f'UPDATE devices SET {", ".join(fields)} WHERE id=%s', params)

            # 更新站点绑定
            if 'site_id' in body:
                old_did = device.get('device_id', device.get('id'))
                cur.execute('DELETE FROM site_devices WHERE device_id=%s', (old_did,))
                if body['site_id']:
                    cur.execute('INSERT IGNORE INTO site_devices (site_id, device_id) VALUES (%s, %s)', (body['site_id'], old_did))
        conn.commit()
        _log_action('更新设备', 'device', device_pk_id, body)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '设备已更新'})


@admin_api.route('/devices/<int:device_pk_id>', methods=['DELETE'])
@require_admin_auth
def delete_device(device_pk_id):
    """删除设备"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT device_id FROM devices WHERE id=%s', (device_pk_id,))
            device = cur.fetchone()
            if not device:
                return jsonify({'code': 404, 'msg': '设备不存在'}), 404
            cur.execute('DELETE FROM devices WHERE id=%s', (device_pk_id,))
            cur.execute('DELETE FROM site_devices WHERE device_id=%s', (device['device_id'],))
        conn.commit()
        _log_action('删除设备', 'device', device_pk_id)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '设备已删除'})


@admin_api.route('/devices/<device_id>/status', methods=['GET'])
@require_admin_auth
def get_device_status(device_id):
    """设备在线状态"""
    online = False
    try:
        db = _get_mongo()
        doc = db[MONGO_COLLECTION].find_one(
            {'device_id': device_id},
            sort=[('timestamp', pymongo.DESCENDING)]
        )
        if doc:
            ts = doc.get('timestamp', '')
            # 判断最近 5 分钟是否有数据
            if ts:
                from datetime import timedelta
                last_time = datetime.strptime(ts[:19], '%Y-%m-%d %H:%M:%S')
                online = (datetime.now() - last_time) < timedelta(minutes=5)
    except Exception:
        pass

    return jsonify({'code': 200, 'data': {'device_id': device_id, 'online': online}})


@admin_api.route('/devices/<device_id>/realtime', methods=['GET'])
@require_admin_auth
def get_device_realtime(device_id):
    """设备实时数据"""
    try:
        db = _get_mongo()
        doc = db[MONGO_COLLECTION].find_one(
            {'device_id': device_id},
            sort=[('timestamp', pymongo.DESCENDING)]
        )
        if not doc:
            return jsonify({'code': 404, 'msg': '暂无数据'}), 404
        return jsonify({
            'code': 200,
            'data': {
                'device_id': device_id,
                'data': doc.get('data', {}),
                'timestamp': doc.get('timestamp'),
                'server_time': doc.get('server_time')
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ====================================================================
# 站点管理 API
# ====================================================================

@admin_api.route('/sites', methods=['GET'])
@require_admin_auth
def get_sites():
    """站点列表"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    keyword = request.args.get('keyword', '').strip()
    offset = (page - 1) * size

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            where = '1=1'
            params = []
            if keyword:
                where += ' AND (name LIKE %s OR code LIKE %s OR area LIKE %s)'
                params.extend([f'%{keyword}%'] * 3)

            cur.execute(f'SELECT COUNT(*) AS cnt FROM sites WHERE {where}', params)
            total = cur.fetchone()['cnt']
            cur.execute(f'SELECT * FROM sites WHERE {where} ORDER BY id DESC LIMIT %s OFFSET %s', params + [size, offset])
            sites = cur.fetchall()

            # 每个站点绑定的设备数
            for s in sites:
                cur.execute('SELECT COUNT(*) AS cnt FROM site_devices WHERE site_id=%s', (s['id'],))
                s['device_count'] = cur.fetchone()['cnt']
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'list': sites, 'total': total, 'page': page, 'size': size}})


@admin_api.route('/sites/<int:site_id>', methods=['GET'])
@require_admin_auth
def get_site_detail(site_id):
    """站点详情"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM sites WHERE id=%s', (site_id,))
            site = cur.fetchone()
            if not site:
                return jsonify({'code': 404, 'msg': '站点不存在'}), 404
            cur.execute('SELECT device_id FROM site_devices WHERE site_id=%s', (site_id,))
            site['devices'] = [r['device_id'] for r in cur.fetchall()]
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': site})


@admin_api.route('/sites', methods=['POST'])
@require_admin_auth
def create_site():
    """新增站点"""
    body = request.json or {}
    name = body.get('name', '').strip()
    code = body.get('code', '').strip()
    if not name or not code:
        return jsonify({'code': 400, 'msg': '站点名称和编号不能为空'}), 400

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM sites WHERE code=%s', (code,))
            if cur.fetchone():
                return jsonify({'code': 400, 'msg': '站点编号已存在'}), 400
            cur.execute(
                'INSERT INTO sites (name, code, area, site_type, address, longitude, latitude, status) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (name, code, body.get('area', ''), body.get('site_type', 'office'),
                 body.get('address', ''), body.get('longitude'), body.get('latitude'), body.get('status', 1))
            )
            new_id = cur.lastrowid
        conn.commit()
        _log_action('新增站点', 'site', new_id, {'name': name, 'code': code})
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'id': new_id}, 'msg': '站点已添加'})


@admin_api.route('/sites/<int:site_id>', methods=['PUT'])
@require_admin_auth
def update_site(site_id):
    """更新站点"""
    body = request.json or {}
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM sites WHERE id=%s', (site_id,))
            if not cur.fetchone():
                return jsonify({'code': 404, 'msg': '站点不存在'}), 404

            fields = []
            params = []
            for key in ('name', 'code', 'area', 'site_type', 'address', 'longitude', 'latitude', 'status'):
                if key in body:
                    fields.append(f'{key}=%s')
                    params.append(body[key])
            if fields:
                params.append(site_id)
                cur.execute(f'UPDATE sites SET {", ".join(fields)} WHERE id=%s', params)
        conn.commit()
        _log_action('更新站点', 'site', site_id, body)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '站点已更新'})


@admin_api.route('/sites/<int:site_id>', methods=['DELETE'])
@require_admin_auth
def delete_site(site_id):
    """删除站点"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM sites WHERE id=%s', (site_id,))
            if not cur.fetchone():
                return jsonify({'code': 404, 'msg': '站点不存在'}), 404
            cur.execute('DELETE FROM sites WHERE id=%s', (site_id,))
            cur.execute('DELETE FROM site_devices WHERE site_id=%s', (site_id,))
        conn.commit()
        _log_action('删除站点', 'site', site_id)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '站点已删除'})


@admin_api.route('/sites/<int:site_id>/devices', methods=['GET'])
@require_admin_auth
def get_site_devices(site_id):
    """站点下设备列表"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT sd.device_id, sd.created_at AS bind_time, d.name AS device_name, d.status '
                'FROM site_devices sd LEFT JOIN devices d ON d.device_id = sd.device_id '
                'WHERE sd.site_id = %s', (site_id,)
            )
            devices = cur.fetchall()
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': devices})


@admin_api.route('/sites/<int:site_id>/devices', methods=['POST'])
@require_admin_auth
def bind_site_device(site_id):
    """绑定设备到站点"""
    body = request.json or {}
    device_id = body.get('device_id', '').strip()
    if not device_id:
        return jsonify({'code': 400, 'msg': '设备ID不能为空'}), 400

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM sites WHERE id=%s', (site_id,))
            if not cur.fetchone():
                return jsonify({'code': 404, 'msg': '站点不存在'}), 404
            cur.execute('SELECT id FROM site_devices WHERE site_id=%s AND device_id=%s', (site_id, device_id))
            if cur.fetchone():
                return jsonify({'code': 400, 'msg': '设备已绑定'}), 400
            cur.execute('INSERT INTO site_devices (site_id, device_id) VALUES (%s, %s)', (site_id, device_id))
        conn.commit()
        _log_action('绑定设备', 'site_device', site_id, {'device_id': device_id})
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '设备已绑定'})


@admin_api.route('/sites/<int:site_id>/devices/<device_id>', methods=['DELETE'])
@require_admin_auth
def unbind_site_device(site_id, device_id):
    """解绑设备"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM site_devices WHERE site_id=%s AND device_id=%s', (site_id, device_id))
        conn.commit()
        _log_action('解绑设备', 'site_device', site_id, {'device_id': device_id})
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '设备已解绑'})


# ====================================================================
# 告警管理 API
# ====================================================================

@admin_api.route('/alerts/records', methods=['GET'])
@require_admin_auth
def get_alert_records():
    """告警记录列表"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    status = request.args.get('status', '')
    severity = request.args.get('severity', '')
    offset = (page - 1) * size

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            where = '1=1'
            params = []
            if status:
                where += ' AND status=%s'
                params.append(status)
            if severity:
                where += ' AND severity=%s'
                params.append(severity)

            cur.execute(f'SELECT COUNT(*) AS cnt FROM alert_records WHERE {where}', params)
            total = cur.fetchone()['cnt']
            cur.execute(
                f'SELECT * FROM alert_records WHERE {where} ORDER BY created_at DESC LIMIT %s OFFSET %s',
                params + [size, offset]
            )
            records = cur.fetchall()
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'list': records, 'total': total, 'page': page, 'size': size}})


@admin_api.route('/alerts/rules', methods=['GET'])
@require_admin_auth
def get_alert_rules():
    """告警规则列表"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM alert_rules ORDER BY id DESC')
            rules = cur.fetchall()
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': rules})


@admin_api.route('/alerts/rules', methods=['POST'])
@require_admin_auth
def create_alert_rule():
    """新增告警规则"""
    body = request.json or {}
    name = body.get('name', '').strip()
    metric = body.get('metric', '').strip()
    if not name or not metric:
        return jsonify({'code': 400, 'msg': '规则名称和指标不能为空'}), 400

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO alert_rules (name, metric, operator, threshold, severity, site_id, enabled) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (name, metric, body.get('operator', '>'), body.get('threshold', 0),
                 body.get('severity', 'warning'), body.get('site_id'), body.get('enabled', 1))
            )
            new_id = cur.lastrowid
        conn.commit()
        _log_action('新增告警规则', 'alert_rule', new_id, {'name': name})
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'id': new_id}, 'msg': '规则已添加'})


@admin_api.route('/alerts/rules/<int:rule_id>', methods=['PUT'])
@require_admin_auth
def update_alert_rule(rule_id):
    """更新告警规则"""
    body = request.json or {}
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM alert_rules WHERE id=%s', (rule_id,))
            if not cur.fetchone():
                return jsonify({'code': 404, 'msg': '规则不存在'}), 404

            fields = []
            params = []
            for key in ('name', 'metric', 'operator', 'threshold', 'severity', 'site_id', 'enabled'):
                if key in body:
                    fields.append(f'{key}=%s')
                    params.append(body[key])
            if fields:
                params.append(rule_id)
                cur.execute(f'UPDATE alert_rules SET {", ".join(fields)} WHERE id=%s', params)
        conn.commit()
        _log_action('更新告警规则', 'alert_rule', rule_id, body)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '规则已更新'})


@admin_api.route('/alerts/rules/<int:rule_id>', methods=['DELETE'])
@require_admin_auth
def delete_alert_rule(rule_id):
    """删除告警规则"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM alert_rules WHERE id=%s', (rule_id,))
        conn.commit()
        _log_action('删除告警规则', 'alert_rule', rule_id)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '规则已删除'})


@admin_api.route('/alerts/records/<int:record_id>/acknowledge', methods=['POST'])
@require_admin_auth
def acknowledge_alert(record_id):
    """确认告警"""
    user = g.current_user
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE alert_records SET status='acknowledged', acknowledged_by=%s, acknowledged_at=NOW() WHERE id=%s AND status='pending'",
                (user.get('username'), record_id)
            )
            if cur.rowcount == 0:
                return jsonify({'code': 400, 'msg': '告警不存在或已被处理'}), 400
        conn.commit()
        _log_action('确认告警', 'alert_record', record_id)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '告警已确认'})


@admin_api.route('/alerts/records/<int:record_id>/resolve', methods=['POST'])
@require_admin_auth
def resolve_alert(record_id):
    """解决告警"""
    user = g.current_user
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE alert_records SET status='resolved', resolved_by=%s, resolved_at=NOW() WHERE id=%s AND status IN ('pending','acknowledged')",
                (user.get('username'), record_id)
            )
            if cur.rowcount == 0:
                return jsonify({'code': 400, 'msg': '告警不存在或已解决'}), 400
        conn.commit()
        _log_action('解决告警', 'alert_record', record_id)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '告警已解决'})


# ====================================================================
# 历史数据 API
# ====================================================================

@admin_api.route('/history/query', methods=['GET'])
@require_admin_auth
def query_history():
    """历史数据查询"""
    device_id = request.args.get('device_id', '')
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 50))

    try:
        db = _get_mongo()
        coll = db[MONGO_COLLECTION]

        query = {}
        if device_id:
            query['device_id'] = device_id
        if start_time or end_time:
            ts_query = {}
            if start_time:
                ts_query['$gte'] = start_time
            if end_time:
                ts_query['$lte'] = end_time
            query['timestamp'] = ts_query

        total = coll.count_documents(query)
        skip = (page - 1) * size
        docs = list(coll.find(query, {'_id': 0}).sort('timestamp', -1).skip(skip).limit(size))

        return jsonify({'code': 200, 'data': {'list': docs, 'total': total, 'page': page, 'size': size}})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_api.route('/history/comparison', methods=['GET'])
@require_admin_auth
def get_comparison_data():
    """多设备/多时段对比"""
    device_ids = request.args.get('device_ids', '')
    start_time = request.args.get('start_time', '')
    end_time = request.args.get('end_time', '')

    if not device_ids:
        return jsonify({'code': 400, 'msg': '请选择对比设备'}), 400

    id_list = [d.strip() for d in device_ids.split(',') if d.strip()]

    try:
        db = _get_mongo()
        coll = db[MONGO_COLLECTION]

        results = {}
        for did in id_list:
            query = {'device_id': did}
            if start_time or end_time:
                ts_query = {}
                if start_time:
                    ts_query['$gte'] = start_time
                if end_time:
                    ts_query['$lte'] = end_time
                query['timestamp'] = ts_query

            pipeline = [
                {'$match': query},
                {'$group': {
                    '_id': {'$substr': ['$timestamp', 0, 13]},
                    'avg_aqi': {'$avg': '$data.AQI'},
                    'avg_pm25': {'$avg': '$data.PM₂.₅'},
                    'avg_no2': {'$avg': '$data.NO₂'},
                    'avg_so2': {'$avg': '$data.SO₂'},
                    'avg_o3': {'$avg': '$data.O₃'},
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            data = list(coll.aggregate(pipeline))
            results[did] = [{
                'hour': r['_id'],
                'avg_aqi': round(r['avg_aqi'], 1) if r['avg_aqi'] else 0,
                'avg_pm25': round(r['avg_pm25'], 1) if r['avg_pm25'] else 0,
                'count': r['count']
            } for r in data]

        return jsonify({'code': 200, 'data': results})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_api.route('/history/report', methods=['GET'])
@require_admin_auth
def get_report_data():
    """统计报表"""
    device_id = request.args.get('device_id', '')
    days = int(request.args.get('days', 7))

    try:
        from datetime import timedelta
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        db = _get_mongo()
        coll = db[MONGO_COLLECTION]

        query = {'timestamp': {'$gte': since}}
        if device_id:
            query['device_id'] = device_id

        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': {'$substr': ['$timestamp', 0, 10]},
                'avg_aqi': {'$avg': '$data.AQI'},
                'max_aqi': {'$max': '$data.AQI'},
                'min_aqi': {'$min': '$data.AQI'},
                'avg_pm25': {'$avg': '$data.PM₂.₅'},
                'avg_no2': {'$avg': '$data.NO₂'},
                'avg_so2': {'$avg': '$data.SO₂'},
                'avg_o3': {'$avg': '$data.O₃'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id': 1}}
        ]
        data = list(coll.aggregate(pipeline))

        return jsonify({
            'code': 200,
            'data': [{
                'date': r['_id'],
                'avg_aqi': round(r['avg_aqi'], 1),
                'max_aqi': round(r['max_aqi'], 1),
                'min_aqi': round(r['min_aqi'], 1),
                'avg_pm25': round(r['avg_pm25'], 1),
                'avg_no2': round(r.get('avg_no2', 0) or 0, 1),
                'avg_so2': round(r.get('avg_so2', 0) or 0, 1),
                'avg_o3': round(r.get('avg_o3', 0) or 0, 1),
                'count': r['count']
            } for r in data]
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_api.route('/history/report/export', methods=['GET'])
@require_admin_auth
def export_report():
    """导出报表 CSV"""
    import csv
    import io
    from flask import Response

    device_id = request.args.get('device_id', '')
    days = int(request.args.get('days', 7))

    try:
        from datetime import timedelta
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        db = _get_mongo()
        coll = db[MONGO_COLLECTION]

        query = {'timestamp': {'$gte': since}}
        if device_id:
            query['device_id'] = device_id

        docs = list(coll.find(query, {'_id': 0}).sort('timestamp', -1).limit(10000))

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['时间', '设备ID', 'AQI', 'PM2.5', 'NO2', 'SO2', 'O3'])

        for doc in docs:
            data = doc.get('data', {})
            writer.writerow([
                doc.get('timestamp', ''),
                doc.get('device_id', ''),
                data.get('AQI', ''),
                data.get('PM₂.₅', ''),
                data.get('NO₂', ''),
                data.get('SO₂', ''),
                data.get('O₃', '')
            ])

        csv_content = output.getvalue()
        output.close()

        return Response(
            '﻿' + csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=air_quality_report_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ====================================================================
# 排行榜 API
# ====================================================================

@admin_api.route('/rankings', methods=['GET'])
@require_admin_auth
def get_rankings():
    """设备/站点 AQI 排行"""
    days = int(request.args.get('days', 7))
    limit = int(request.args.get('limit', 20))

    try:
        from datetime import timedelta
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        db = _get_mongo()
        coll = db[MONGO_COLLECTION]

        pipeline = [
            {'$match': {'timestamp': {'$gte': since}}},
            {'$group': {
                '_id': '$device_id',
                'avg_aqi': {'$avg': '$data.AQI'},
                'max_aqi': {'$max': '$data.AQI'},
                'avg_pm25': {'$avg': '$data.PM₂.₅'},
                'count': {'$sum': 1}
            }},
            {'$sort': {'avg_aqi': -1}},
            {'$limit': limit}
        ]
        results = list(coll.aggregate(pipeline))

        rankings = [{
            'rank': i + 1,
            'device_id': r['_id'],
            'avg_aqi': round(r['avg_aqi'], 1),
            'max_aqi': round(r['max_aqi'], 1),
            'avg_pm25': round(r['avg_pm25'], 1),
            'record_count': r['count']
        } for i, r in enumerate(results)]

        return jsonify({'code': 200, 'data': rankings})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_api.route('/rankings/trend', methods=['GET'])
@require_admin_auth
def get_ranking_trend():
    """排行变化趋势"""
    days = int(request.args.get('days', 7))
    device_id = request.args.get('device_id', '')

    try:
        from datetime import timedelta
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        db = _get_mongo()
        coll = db[MONGO_COLLECTION]

        match = {'timestamp': {'$gte': since}}
        if device_id:
            match['device_id'] = device_id

        pipeline = [
            {'$match': match},
            {'$group': {
                '_id': {
                    'date': {'$substr': ['$timestamp', 0, 10]},
                    'device_id': '$device_id'
                },
                'avg_aqi': {'$avg': '$data.AQI'}
            }},
            {'$sort': {'_id.date': 1}}
        ]
        results = list(coll.aggregate(pipeline))

        # 按日期分组
        trend = {}
        for r in results:
            date = r['_id']['date']
            if date not in trend:
                trend[date] = []
            trend[date].append({
                'device_id': r['_id']['device_id'],
                'avg_aqi': round(r['avg_aqi'], 1)
            })

        # 每天按 AQI 排序
        for date in trend:
            trend[date].sort(key=lambda x: x['avg_aqi'], reverse=True)
            for i, item in enumerate(trend[date]):
                item['rank'] = i + 1

        return jsonify({'code': 200, 'data': trend})
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ====================================================================
# 智能报告 API
# ====================================================================

@admin_api.route('/reports', methods=['GET'])
@require_admin_auth
def get_reports():
    """报告列表"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    report_type = request.args.get('report_type', '')
    offset = (page - 1) * size

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            where = '1=1'
            params = []
            if report_type:
                where += ' AND report_type=%s'
                params.append(report_type)

            cur.execute(f'SELECT COUNT(*) AS cnt FROM intelligence_reports WHERE {where}', params)
            total = cur.fetchone()['cnt']
            cur.execute(
                f'SELECT * FROM intelligence_reports WHERE {where} ORDER BY created_at DESC LIMIT %s OFFSET %s',
                params + [size, offset]
            )
            reports = cur.fetchall()
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'list': reports, 'total': total, 'page': page, 'size': size}})


@admin_api.route('/reports/<int:report_id>', methods=['GET'])
@require_admin_auth
def get_report_detail(report_id):
    """报告详情"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM intelligence_reports WHERE id=%s', (report_id,))
            report = cur.fetchone()
            if not report:
                return jsonify({'code': 404, 'msg': '报告不存在'}), 404
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': report})


@admin_api.route('/reports/generate', methods=['POST'])
@require_admin_auth
def generate_report():
    """生成智能报告"""
    body = request.json or {}
    report_type = body.get('report_type', 'daily')
    site_id = body.get('site_id')

    title_map = {'daily': '日报', 'weekly': '周报', 'monthly': '月报'}
    title = f"空气质量{title_map.get(report_type, report_type)}报告 - {datetime.now().strftime('%Y-%m-%d')}"

    # 获取数据用于生成报告
    try:
        from datetime import timedelta
        days_map = {'daily': 1, 'weekly': 7, 'monthly': 30}
        days = days_map.get(report_type, 1)
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        db = _get_mongo()
        coll = db[MONGO_COLLECTION]

        match = {'timestamp': {'$gte': since}}
        if site_id:
            # 获取站点绑定的设备
            conn = _get_mysql()
            try:
                with conn.cursor() as cur:
                    cur.execute('SELECT device_id FROM site_devices WHERE site_id=%s', (site_id,))
                    devices = [r['device_id'] for r in cur.fetchall()]
            finally:
                conn.close()
            if devices:
                match['device_id'] = {'$in': devices}

        pipeline = [
            {'$match': match},
            {'$group': {
                '_id': None,
                'avg_aqi': {'$avg': '$data.AQI'},
                'max_aqi': {'$max': '$data.AQI'},
                'min_aqi': {'$min': '$data.AQI'},
                'avg_pm25': {'$avg': '$data.PM₂.₅'},
                'count': {'$sum': 1}
            }}
        ]
        stats = list(coll.aggregate(pipeline))
        stats = stats[0] if stats else {}

        # 用 DeepSeek 生成报告内容
        prompt = f"""请生成一份空气质量{title_map.get(report_type, report_type)}报告，包含以下数据：
- 平均AQI：{round(stats.get('avg_aqi', 0), 1)}
- 最高AQI：{round(stats.get('max_aqi', 0), 1)}
- 最低AQI：{round(stats.get('min_aqi', 0), 1)}
- 平均PM2.5：{round(stats.get('avg_pm25', 0), 1)}
- 数据条数：{stats.get('count', 0)}

请用简洁专业的语言，包含：总体评价、主要问题、改善建议。控制在300字以内。"""

        ai_content = _call_deepseek(prompt, max_tokens=500)
        content = ai_content or f"本{title_map.get(report_type, '')}期间，平均AQI为{round(stats.get('avg_aqi', 0), 1)}，PM2.5均值为{round(stats.get('avg_pm25', 0), 1)}。"

    except Exception as e:
        content = f"报告生成时发生错误: {str(e)}"

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO intelligence_reports (title, report_type, site_id, content, summary, generated_by, status) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (title, report_type, site_id, content, content[:200], 'ai', 'completed')
            )
            new_id = cur.lastrowid
        conn.commit()
        _log_action('生成报告', 'report', new_id, {'type': report_type})
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'id': new_id, 'title': title}, 'msg': '报告已生成'})


@admin_api.route('/reports/<int:report_id>', methods=['DELETE'])
@require_admin_auth
def delete_report(report_id):
    """删除报告"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM intelligence_reports WHERE id=%s', (report_id,))
        conn.commit()
        _log_action('删除报告', 'report', report_id)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '报告已删除'})


# ====================================================================
# 系统管理 API
# ====================================================================

@admin_api.route('/company-info', methods=['GET'])
@require_admin_auth
def get_company_info():
    """企业信息"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM company_info ORDER BY id LIMIT 1')
            info = cur.fetchone()
    finally:
        conn.close()

    if not info:
        return jsonify({'code': 200, 'data': {}})

    return jsonify({'code': 200, 'data': info})


@admin_api.route('/company-info', methods=['PUT'])
@require_admin_auth
def update_company_info():
    """更新企业信息"""
    body = request.json or {}
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM company_info ORDER BY id LIMIT 1')
            existing = cur.fetchone()
            if existing:
                fields = []
                params = []
                for key in ('name', 'logo_url', 'address', 'contact_name', 'contact_phone', 'contact_email', 'description'):
                    if key in body:
                        fields.append(f'{key}=%s')
                        params.append(body[key])
                if fields:
                    params.append(existing['id'])
                    cur.execute(f'UPDATE company_info SET {", ".join(fields)} WHERE id=%s', params)
            else:
                cur.execute(
                    'INSERT INTO company_info (name, logo_url, address, contact_name, contact_phone, contact_email, description) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (body.get('name', ''), body.get('logo_url', ''), body.get('address', ''),
                     body.get('contact_name', ''), body.get('contact_phone', ''),
                     body.get('contact_email', ''), body.get('description', ''))
                )
        conn.commit()
        _log_action('更新企业信息', 'company_info', 1, body)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '企业信息已更新'})


@admin_api.route('/users', methods=['GET'])
@require_admin_auth
def get_admin_users():
    """管理员列表"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    offset = (page - 1) * size

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS cnt FROM admin_users')
            total = cur.fetchone()['cnt']
            cur.execute(
                'SELECT id, username, display_name, role, status, last_login, created_at '
                'FROM admin_users ORDER BY id DESC LIMIT %s OFFSET %s',
                (size, offset)
            )
            users = cur.fetchall()
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'list': users, 'total': total, 'page': page, 'size': size}})


@admin_api.route('/users', methods=['POST'])
@require_admin_auth
@require_role('admin')
def create_admin_user():
    """新增管理员"""
    from werkzeug.security import generate_password_hash

    body = request.json or {}
    username = body.get('username', '').strip()
    password = body.get('password', '').strip()
    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM admin_users WHERE username=%s', (username,))
            if cur.fetchone():
                return jsonify({'code': 400, 'msg': '用户名已存在'}), 400
            cur.execute(
                'INSERT INTO admin_users (username, password_hash, display_name, role, status) VALUES (%s, %s, %s, %s, %s)',
                (username, generate_password_hash(password),
                 body.get('display_name', username), body.get('role', 'viewer'), body.get('status', 1))
            )
            new_id = cur.lastrowid
        conn.commit()
        _log_action('新增管理员', 'admin_user', new_id, {'username': username})
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'id': new_id}, 'msg': '管理员已添加'})


@admin_api.route('/users/<int:user_id>', methods=['PUT'])
@require_admin_auth
@require_role('admin')
def update_admin_user(user_id):
    """更新管理员"""
    from werkzeug.security import generate_password_hash

    body = request.json or {}
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM admin_users WHERE id=%s', (user_id,))
            if not cur.fetchone():
                return jsonify({'code': 404, 'msg': '用户不存在'}), 404

            fields = []
            params = []
            for key in ('display_name', 'role', 'status'):
                if key in body:
                    fields.append(f'{key}=%s')
                    params.append(body[key])
            if 'password' in body and body['password']:
                fields.append('password_hash=%s')
                params.append(generate_password_hash(body['password']))
            if fields:
                params.append(user_id)
                cur.execute(f'UPDATE admin_users SET {", ".join(fields)} WHERE id=%s', params)
        conn.commit()
        _log_action('更新管理员', 'admin_user', user_id, body)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '管理员已更新'})


@admin_api.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin_auth
@require_role('admin')
def delete_admin_user(user_id):
    """删除管理员"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, username FROM admin_users WHERE id=%s', (user_id,))
            user = cur.fetchone()
            if not user:
                return jsonify({'code': 404, 'msg': '用户不存在'}), 404
            if user['username'] == 'admin':
                return jsonify({'code': 400, 'msg': '不能删除默认管理员'}), 400
            cur.execute('DELETE FROM admin_users WHERE id=%s', (user_id,))
        conn.commit()
        _log_action('删除管理员', 'admin_user', user_id)
    finally:
        conn.close()

    return jsonify({'code': 200, 'msg': '管理员已删除'})


@admin_api.route('/operation-logs', methods=['GET'])
@require_admin_auth
def get_operation_logs():
    """操作日志"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    offset = (page - 1) * size

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS cnt FROM admin_operation_logs')
            total = cur.fetchone()['cnt']
            cur.execute(
                'SELECT * FROM admin_operation_logs ORDER BY created_at DESC LIMIT %s OFFSET %s',
                (size, offset)
            )
            logs = cur.fetchall()
    finally:
        conn.close()

    return jsonify({'code': 200, 'data': {'list': logs, 'total': total, 'page': page, 'size': size}})


# ====================================================================
# 监控扩展 API
# ====================================================================

@admin_api.route('/dashboard/realtime/<device_id>', methods=['GET'])
@require_admin_auth
def get_realtime_by_device(device_id):
    """单设备实时数据"""
    try:
        db = _get_mongo()
        doc = db[MONGO_COLLECTION].find_one(
            {'device_id': device_id},
            sort=[('timestamp', pymongo.DESCENDING)]
        )
        if not doc:
            return jsonify({'code': 404, 'msg': '暂无数据'}), 404

        data = doc.get('data', {})
        return jsonify({
            'code': 200,
            'data': {
                'device_id': device_id,
                'aqi': data.get('AQI'),
                'pm25': data.get('PM₂.₅'),
                'no2': data.get('NO₂'),
                'so2': data.get('SO₂'),
                'o3': data.get('O₃'),
                'timestamp': doc.get('timestamp'),
                'server_time': doc.get('server_time')
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


@admin_api.route('/dashboard/map', methods=['GET'])
@require_admin_auth
def get_map_data():
    """地图数据（站点坐标 + 实时 AQI）"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT id, name, code, area, longitude, latitude, status FROM sites WHERE status=1')
            sites = cur.fetchall()
    finally:
        conn.close()

    db = _get_mongo()
    coll = db[MONGO_COLLECTION]

    map_data = []
    for site in sites:
        # 获取站点绑定的设备
        conn2 = _get_mysql()
        try:
            with conn2.cursor() as cur:
                cur.execute('SELECT device_id FROM site_devices WHERE site_id=%s', (site['id'],))
                devices = [r['device_id'] for r in cur.fetchall()]
        finally:
            conn2.close()

        latest = None
        if devices:
            try:
                doc = coll.find_one(
                    {'device_id': {'$in': devices}},
                    sort=[('timestamp', pymongo.DESCENDING)]
                )
                if doc:
                    latest = doc.get('data', {})
            except Exception:
                pass

        map_data.append({
            'site_id': site['id'],
            'name': site['name'],
            'code': site['code'],
            'area': site['area'],
            'longitude': float(site['longitude']) if site['longitude'] else None,
            'latitude': float(site['latitude']) if site['latitude'] else None,
            'aqi': latest.get('AQI') if latest else None,
            'pm25': latest.get('PM₂.₅') if latest else None,
            'device_count': len(devices)
        })

    return jsonify({'code': 200, 'data': map_data})


# ============================================================
#  空气质量差用户分析 + 企业报告
# ============================================================

def _get_health_level(aqi):
    """根据 AQI 返回健康等级"""
    if aqi is None:
        return {'key': 'unknown', 'label': '未知', 'color': '#999'}
    if aqi <= 50:
        return {'key': 'good', 'label': '优秀', 'color': '#34C759'}
    if aqi <= 100:
        return {'key': 'moderate', 'label': '良好', 'color': '#FF9500'}
    if aqi <= 150:
        return {'key': 'lightly_polluted', 'label': '轻度污染', 'color': '#FF6B00'}
    if aqi <= 200:
        return {'key': 'moderately_polluted', 'label': '中度污染', 'color': '#FF3B30'}
    return {'key': 'heavily_polluted', 'label': '重度污染', 'color': '#8B0000'}


def _get_primary_pollutant(pm25, no2, so2, o3):
    """判定主要污染物"""
    candidates = []
    if pm25 and pm25 > 75:
        candidates.append(('PM2.5', pm25 / 75))
    if no2 and no2 > 80:
        candidates.append(('NO₂', no2 / 80))
    if so2 and so2 > 50:
        candidates.append(('SO₂', so2 / 50))
    if o3 and o3 > 100:
        candidates.append(('O₃', o3 / 100))
    if not candidates:
        return '无'
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]


@admin_api.route('/api/admin/analytics/poor-air-users', methods=['GET'])
@require_admin_auth
def get_poor_air_users():
    """筛选空气质量差的用户/设备"""
    days = int(request.args.get('days', 30))
    aqi_threshold = float(request.args.get('aqi_threshold', 100))
    min_exceed_days = int(request.args.get('min_exceed_days', 7))
    area = request.args.get('area', '')

    # 从 MongoDB 聚合：按 device_id 计算最近 N 天的平均 AQI 和超标天数
    mongo = _get_mongo()
    coll = mongo[MONGO_COLLECTION]
    from datetime import datetime, timedelta
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    pipeline = [
        {'$match': {'timestamp': {'$gte': since}}},
        {'$group': {
            '_id': '$device_id',
            'avg_aqi': {'$avg': '$data.AQI'},
            'max_aqi': {'$max': '$data.AQI'},
            'avg_pm25': {'$avg': '$data.PM₂.₅'},
            'avg_no2': {'$avg': '$data.NO₂'},
            'avg_so2': {'$avg': '$data.SO₂'},
            'avg_o3': {'$avg': '$data.O₃'},
            'total_records': {'$sum': 1},
            'exceed_days': {
                '$sum': {
                    '$cond': [{'$gte': ['$data.AQI', aqi_threshold]}, 1, 0]
                }
            }
        }},
        {'$match': {'exceed_days': {'$gte': min_exceed_days}}},
        {'$sort': {'avg_aqi': -1}}
    ]

    results = list(coll.aggregate(pipeline))

    # 关联 MySQL 查询用户和站点信息
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            # 获取所有用户-设备绑定
            cur.execute('''
                SELECT ud.device_id, ud.open_id, ud.room_location,
                       u.nickname, u.avatar_url
                FROM user_devices ud
                LEFT JOIN users u ON ud.open_id = u.open_id
            ''')
            user_map = {}
            for row in cur.fetchall():
                user_map[row['device_id']] = row

            # 获取所有站点-设备绑定
            cur.execute('''
                SELECT sd.device_id, s.name AS site_name, s.area, s.site_type
                FROM site_devices sd
                JOIN sites s ON sd.site_id = s.id
            ''')
            site_map = {}
            for row in cur.fetchall():
                site_map[row['device_id']] = row

            # 获取设备注册信息
            cur.execute('SELECT device_id, location_name FROM devices')
            device_map = {}
            for row in cur.fetchall():
                device_map[row['device_id']] = row
    finally:
        conn.close()

    # 组装结果
    data = []
    for r in results:
        device_id = r['_id']
        avg_aqi = round(r['avg_aqi'], 1) if r['avg_aqi'] else 0
        max_aqi = round(r['max_aqi'], 1) if r['max_aqi'] else 0
        avg_pm25 = round(r['avg_pm25'], 1) if r['avg_pm25'] else 0
        avg_no2 = round(r['avg_no2'], 1) if r['avg_no2'] else 0
        avg_so2 = round(r['avg_so2'], 1) if r['avg_so2'] else 0
        avg_o3 = round(r['avg_o3'], 1) if r['avg_o3'] else 0

        # 按区域筛选
        site_info = site_map.get(device_id, {})
        if area and site_info.get('area', '') != area:
            continue

        user_info = user_map.get(device_id, {})
        device_info = device_map.get(device_id, {})

        data.append({
            'device_id': device_id,
            'nickname': user_info.get('nickname', '未绑定用户'),
            'room_location': user_info.get('room_location', ''),
            'site_name': site_info.get('site_name', '未关联站点'),
            'area': site_info.get('area', '未知区域'),
            'site_type': site_info.get('site_type', ''),
            'location_name': device_info.get('location_name', ''),
            'avg_aqi': avg_aqi,
            'max_aqi': max_aqi,
            'avg_pm25': avg_pm25,
            'avg_no2': avg_no2,
            'avg_so2': avg_so2,
            'avg_o3': avg_o3,
            'exceed_days': r['exceed_days'],
            'total_records': r['total_records'],
            'health_level': _get_health_level(avg_aqi),
            'primary_pollutant': _get_primary_pollutant(avg_pm25, avg_no2, avg_so2, avg_o3)
        })

    # 统计汇总
    total_users = len(data)
    total_avg_aqi = round(sum(d['avg_aqi'] for d in data) / total_users, 1) if total_users else 0

    return jsonify({
        'code': 200,
        'data': {
            'list': data,
            'summary': {
                'total_users': total_users,
                'total_avg_aqi': total_avg_aqi,
                'days': days,
                'aqi_threshold': aqi_threshold,
                'min_exceed_days': min_exceed_days
            }
        }
    })


@admin_api.route('/api/admin/analytics/poor-air-users/export', methods=['GET'])
@require_admin_auth
def export_poor_air_users():
    """导出空气质量差用户 CSV"""
    # 复用查询逻辑
    from flask import Response
    import io, csv

    days = int(request.args.get('days', 30))
    aqi_threshold = float(request.args.get('aqi_threshold', 100))
    min_exceed_days = int(request.args.get('min_exceed_days', 7))
    area = request.args.get('area', '')

    mongo = _get_mongo()
    coll = mongo[MONGO_COLLECTION]
    from datetime import datetime, timedelta
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    pipeline = [
        {'$match': {'timestamp': {'$gte': since}}},
        {'$group': {
            '_id': '$device_id',
            'avg_aqi': {'$avg': '$data.AQI'},
            'max_aqi': {'$max': '$data.AQI'},
            'avg_pm25': {'$avg': '$data.PM₂.₅'},
            'avg_no2': {'$avg': '$data.NO₂'},
            'avg_so2': {'$avg': '$data.SO₂'},
            'avg_o3': {'$avg': '$data.O₃'},
            'exceed_days': {
                '$sum': {'$cond': [{'$gte': ['$data.AQI', aqi_threshold]}, 1, 0]}
            }
        }},
        {'$match': {'exceed_days': {'$gte': min_exceed_days}}},
        {'$sort': {'avg_aqi': -1}}
    ]
    results = list(coll.aggregate(pipeline))

    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT ud.device_id, u.nickname
                FROM user_devices ud LEFT JOIN users u ON ud.open_id = u.open_id
            ''')
            user_map = {r['device_id']: r for r in cur.fetchall()}

            cur.execute('''
                SELECT sd.device_id, s.name AS site_name, s.area
                FROM site_devices sd JOIN sites s ON sd.site_id = s.id
            ''')
            site_map = {r['device_id']: r for r in cur.fetchall()}
    finally:
        conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['设备ID', '用户昵称', '站点', '区域', '平均AQI', '最大AQI',
                     '平均PM2.5', '平均NO₂', '平均SO₂', '平均O₃', '超标天数', '健康等级', '主要污染物'])

    for r in results:
        device_id = r['_id']
        avg_aqi = round(r['avg_aqi'], 1) if r['avg_aqi'] else 0
        site = site_map.get(device_id, {})
        if area and site.get('area', '') != area:
            continue
        user = user_map.get(device_id, {})
        health = _get_health_level(avg_aqi)
        writer.writerow([
            device_id,
            user.get('nickname', '未绑定'),
            site.get('site_name', ''),
            site.get('area', ''),
            avg_aqi,
            round(r['max_aqi'], 1) if r['max_aqi'] else 0,
            round(r['avg_pm25'], 1) if r['avg_pm25'] else 0,
            round(r['avg_no2'], 1) if r['avg_no2'] else 0,
            round(r['avg_so2'], 1) if r['avg_so2'] else 0,
            round(r['avg_o3'], 1) if r['avg_o3'] else 0,
            r['exceed_days'],
            health['label'],
            _get_primary_pollutant(
                r.get('avg_pm25'), r.get('avg_no2'),
                r.get('avg_so2'), r.get('avg_o3')
            )
        ])

    csv_content = output.getvalue()
    output.close()

    return Response(
        '﻿' + csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=poor_air_users_{days}d.csv'}
    )


@admin_api.route('/api/admin/reports/enterprise', methods=['POST'])
@require_admin_auth
def generate_enterprise_report():
    """生成企业级报告"""
    data = request.get_json() or {}
    company_name = data.get('company_name', '客户')
    report_title = data.get('report_title', '空气质量分析报告')
    report_type = data.get('report_type', 'monthly')
    site_ids = data.get('site_ids', [])
    metrics = data.get('metrics', ['AQI', 'PM2.5'])
    highlights = data.get('highlights', [])
    style = data.get('style', 'formal')

    # 确定查询天数
    days_map = {'daily': 1, 'weekly': 7, 'monthly': 30, 'quarterly': 90}
    days = days_map.get(report_type, 30)

    # 查询站点绑定的设备
    conn = _get_mysql()
    device_ids = []
    site_names = []
    try:
        with conn.cursor() as cur:
            if site_ids:
                placeholders = ','.join(['%s'] * len(site_ids))
                cur.execute(f'SELECT id, name FROM sites WHERE id IN ({placeholders})', site_ids)
                site_names = [r['name'] for r in cur.fetchall()]

                cur.execute(f'SELECT device_id FROM site_devices WHERE site_id IN ({placeholders})', site_ids)
                device_ids = [r['device_id'] for r in cur.fetchall()]
            else:
                cur.execute('SELECT device_id FROM site_devices')
                device_ids = [r['device_id'] for r in cur.fetchall()]
    finally:
        conn.close()

    # 从 MongoDB 聚合数据
    mongo = _get_mongo()
    coll = mongo[MONGO_COLLECTION]
    from datetime import datetime, timedelta
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    match_filter = {'timestamp': {'$gte': since}}
    if device_ids:
        match_filter['device_id'] = {'$in': device_ids}

    pipeline = [
        {'$match': match_filter},
        {'$group': {
            '_id': None,
            'avg_aqi': {'$avg': '$data.AQI'},
            'max_aqi': {'$max': '$data.AQI'},
            'min_aqi': {'$min': '$data.AQI'},
            'avg_pm25': {'$avg': '$data.PM₂.₅'},
            'avg_no2': {'$avg': '$data.NO₂'},
            'avg_so2': {'$avg': '$data.SO₂'},
            'avg_o3': {'$avg': '$data.O₃'},
            'total_records': {'$sum': 1},
            'device_count': {'$addToSet': '$device_id'}
        }}
    ]
    agg = list(coll.aggregate(pipeline))

    if not agg:
        stats = {'avg_aqi': 0, 'max_aqi': 0, 'min_aqi': 0, 'avg_pm25': 0,
                 'avg_no2': 0, 'avg_so2': 0, 'avg_o3': 0, 'total_records': 0, 'device_count': 0}
    else:
        a = agg[0]
        stats = {
            'avg_aqi': round(a.get('avg_aqi', 0) or 0, 1),
            'max_aqi': round(a.get('max_aqi', 0) or 0, 1),
            'min_aqi': round(a.get('min_aqi', 0) or 0, 1),
            'avg_pm25': round(a.get('avg_pm25', 0) or 0, 1),
            'avg_no2': round(a.get('avg_no2', 0) or 0, 1),
            'avg_so2': round(a.get('avg_so2', 0) or 0, 1),
            'avg_o3': round(a.get('avg_o3', 0) or 0, 1),
            'total_records': a.get('total_records', 0),
            'device_count': len(a.get('device_count', []))
        }

    # 计算达标率（AQI <= 100 的比例）
    if stats['total_records'] > 0:
        exceed_pipeline = [
            {'$match': match_filter},
            {'$group': {
                '_id': None,
                'good_count': {'$sum': {'$cond': [{'$lte': ['$data.AQI', 100]}, 1, 0]}}
            }}
        ]
        exceed_agg = list(coll.aggregate(exceed_pipeline))
        good_count = exceed_agg[0]['good_count'] if exceed_agg else 0
        stats['compliance_rate'] = round(good_count / stats['total_records'] * 100, 1)
    else:
        stats['compliance_rate'] = 0

    # 调用 DeepSeek AI 生成报告
    health = _get_health_level(stats['avg_aqi'])
    highlights_text = '；'.join(highlights) if highlights else '无'
    sites_text = '、'.join(site_names) if site_names else '全部站点'

    period_map = {'daily': '日', 'weekly': '周', 'monthly': '月', 'quarterly': '季度'}
    period = period_map.get(report_type, '月')

    prompt = f"""你是一位专业的空气质量分析师，请为以下企业客户撰写一份正式的空气质量{period}度报告。

客户公司：{company_name}
报告标题：{report_title}
监测范围：{sites_text}
监测设备数：{stats['device_count']} 台
监测数据量：{stats['total_records']} 条
报告期间：最近 {days} 天

数据统计：
- 平均AQI：{stats['avg_aqi']}（等级：{health['label']}）
- AQI范围：{stats['min_aqi']} ~ {stats['max_aqi']}
- 平均PM2.5：{stats['avg_pm25']} μg/m³
- 平均NO₂：{stats['avg_no2']} μg/m³
- 平均SO₂：{stats['avg_so2']} μg/m³
- 平均O₃：{stats['avg_o3']} μg/m³
- 空气质量达标率：{stats['compliance_rate']}%

客户指定亮点：{highlights_text}

要求：
1. 报告风格：{'正式、专业、数据驱动' if style == 'formal' else '简洁、易读、图文并茂'}
2. 报告结构：执行摘要 → 核心数据分析 → 趋势解读 → 改善建议 → 总结
3. 语言要专业但易懂，适合企业决策者阅读
4. 如有客户亮点，要在报告中突出展示
5. 报告长度：500-800字"""

    try:
        ai_content = _call_deepseek(prompt)
    except Exception:
        ai_content = f"""【{report_title}】

执行摘要：
本{period}度监测期间，{company_name}旗下 {stats['device_count']} 台监测设备共采集 {stats['total_records']} 条空气质量数据。

核心数据：
- 空气质量指数（AQI）均值为 {stats['avg_aqi']}，整体空气质量等级为"{health['label']}"
- PM2.5均值 {stats['avg_pm25']} μg/m³，NO₂均值 {stats['avg_no2']} μg/m³
- 空气质量达标率为 {stats['compliance_rate']}%

改善建议：
建议持续关注空气质量变化趋势，针对重点污染源采取改善措施，确保室内环境健康达标。"""

    # 写入数据库
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO intelligence_reports
                (title, report_type, site_id, content, summary, generated_by, status,
                 company_name, report_style, report_period, metrics_included)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                report_title, report_type,
                site_ids[0] if site_ids else None,
                ai_content, ai_content[:200],
                'enterprise', 'completed',
                company_name, style, f'最近{days}天',
                ','.join(metrics)
            ))
            report_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    _log_action('generate_enterprise_report', 'report', str(report_id),
                   f'生成企业报告：{company_name} - {report_title}')

    return jsonify({
        'code': 200,
        'data': {
            'id': report_id,
            'title': report_title,
            'company_name': company_name,
            'content': ai_content,
            'stats': stats,
            'report_type': report_type
        }
    })


@admin_api.route('/api/admin/reports/<int:rid>/preview', methods=['GET'])
@require_admin_auth
def preview_report(rid):
    """报告预览"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM intelligence_reports WHERE id = %s', (rid,))
            report = cur.fetchone()
    finally:
        conn.close()

    if not report:
        return jsonify({'code': 404, 'msg': '报告不存在'})

    return jsonify({'code': 200, 'data': report})


# ============================================================
#  产品型号管理
# ============================================================

@admin_api.route('/api/admin/products', methods=['GET'])
@require_admin_auth
def list_products():
    """产品型号列表"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM product_models ORDER BY id DESC')
            products = cur.fetchall()
            # 统计每个型号的设备数
            for p in products:
                cur.execute('SELECT COUNT(*) AS cnt FROM devices WHERE product_model_id = %s', (p['id'],))
                row = cur.fetchone()
                p['device_count'] = row['cnt'] if row else 0
    finally:
        conn.close()
    return jsonify({'code': 200, 'data': products})


@admin_api.route('/api/admin/products', methods=['POST'])
@require_admin_auth
def create_product():
    """新增产品型号"""
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'code': 400, 'msg': '产品名称不能为空'})
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO product_models (name, product_line, sensor_types, description, status)
                VALUES (%s, %s, %s, %s, %s)
            ''', (data['name'], data.get('product_line', ''), data.get('sensor_types', ''),
                  data.get('description', ''), data.get('status', 1)))
            pid = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    _log_action('create_product', 'product', str(pid), f'新增产品型号：{data["name"]}')
    return jsonify({'code': 200, 'data': {'id': pid}})


@admin_api.route('/api/admin/products/<int:pid>', methods=['PUT'])
@require_admin_auth
def update_product(pid):
    """更新产品型号"""
    data = request.get_json() or {}
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            fields = []
            values = []
            for k in ['name', 'product_line', 'sensor_types', 'description', 'status']:
                if k in data:
                    fields.append(f'{k} = %s')
                    values.append(data[k])
            if not fields:
                return jsonify({'code': 400, 'msg': '无更新字段'})
            values.append(pid)
            cur.execute(f'UPDATE product_models SET {", ".join(fields)} WHERE id = %s', values)
        conn.commit()
    finally:
        conn.close()
    return jsonify({'code': 200, 'msg': '更新成功'})


@admin_api.route('/api/admin/products/<int:pid>', methods=['DELETE'])
@require_admin_auth
def delete_product(pid):
    """删除产品型号"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM product_models WHERE id = %s', (pid,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ============================================================
#  客户管理 CRM
# ============================================================

@admin_api.route('/api/admin/customers', methods=['GET'])
@require_admin_auth
def list_customers():
    """客户列表"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            # 筛选
            conditions = []
            params = []
            ctype = request.args.get('type')
            industry = request.args.get('industry')
            status = request.args.get('status')
            if ctype:
                conditions.append('type = %s')
                params.append(ctype)
            if industry:
                conditions.append('industry = %s')
                params.append(industry)
            if status:
                conditions.append('status = %s')
                params.append(status)

            where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
            cur.execute(f'SELECT * FROM customers {where} ORDER BY id DESC', params)
            customers = cur.fetchall()

            # 统计每个客户的设备数
            for c in customers:
                cur.execute('SELECT COUNT(*) AS cnt FROM devices WHERE customer_id = %s', (c['id'],))
                row = cur.fetchone()
                c['device_count'] = row['cnt'] if row else 0
    finally:
        conn.close()
    return jsonify({'code': 200, 'data': customers})


@admin_api.route('/api/admin/customers', methods=['POST'])
@require_admin_auth
def create_customer():
    """新增客户"""
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'code': 400, 'msg': '客户名称不能为空'})
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO customers (name, type, contact_name, phone, email, address, industry, status, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (data['name'], data.get('type', 'enterprise'), data.get('contact_name', ''),
                  data.get('phone', ''), data.get('email', ''), data.get('address', ''),
                  data.get('industry', ''), data.get('status', 'active'), data.get('notes', '')))
            cid = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    _log_action('create_customer', 'customer', str(cid), f'新增客户：{data["name"]}')
    return jsonify({'code': 200, 'data': {'id': cid}})


@admin_api.route('/api/admin/customers/<int:cid>', methods=['PUT'])
@require_admin_auth
def update_customer(cid):
    """更新客户"""
    data = request.get_json() or {}
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            fields = []
            values = []
            for k in ['name', 'type', 'contact_name', 'phone', 'email', 'address', 'industry', 'status', 'notes']:
                if k in data:
                    fields.append(f'{k} = %s')
                    values.append(data[k])
            if not fields:
                return jsonify({'code': 400, 'msg': '无更新字段'})
            values.append(cid)
            cur.execute(f'UPDATE customers SET {", ".join(fields)} WHERE id = %s', values)
        conn.commit()
    finally:
        conn.close()
    return jsonify({'code': 200, 'msg': '更新成功'})


@admin_api.route('/api/admin/customers/<int:cid>', methods=['DELETE'])
@require_admin_auth
def delete_customer(cid):
    """删除客户"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM customers WHERE id = %s', (cid,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ============================================================
#  售后工单
# ============================================================

def _gen_order_no():
    """生成工单编号 WO-YYYYMMDD-NNN"""
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM work_orders WHERE order_no LIKE %s", (f'WO-{today}-%',))
            count = cur.fetchone()['cnt'] + 1
    finally:
        conn.close()
    return f'WO-{today}-{count:03d}'


@admin_api.route('/api/admin/workorders', methods=['GET'])
@require_admin_auth
def list_workorders():
    """工单列表"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            conditions = []
            params = []
            status = request.args.get('status')
            priority = request.args.get('priority')
            wtype = request.args.get('type')
            if status:
                conditions.append('w.status = %s')
                params.append(status)
            if priority:
                conditions.append('w.priority = %s')
                params.append(priority)
            if wtype:
                conditions.append('w.type = %s')
                params.append(wtype)

            where = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
            cur.execute(f'''
                SELECT w.*, c.name AS customer_name
                FROM work_orders w
                LEFT JOIN customers c ON w.customer_id = c.id
                {where}
                ORDER BY
                    CASE w.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                    w.created_at DESC
            ''', params)
            orders = cur.fetchall()
    finally:
        conn.close()
    return jsonify({'code': 200, 'data': orders})


@admin_api.route('/api/admin/workorders', methods=['POST'])
@require_admin_auth
def create_workorder():
    """新增工单"""
    data = request.get_json() or {}
    if not data.get('title'):
        return jsonify({'code': 400, 'msg': '工单标题不能为空'})
    order_no = _gen_order_no()
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO work_orders (order_no, type, priority, device_id, customer_id, title, description, status, assignee)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (order_no, data.get('type', 'fault'), data.get('priority', 'medium'),
                  data.get('device_id'), data.get('customer_id'),
                  data['title'], data.get('description', ''),
                  'pending', data.get('assignee', '')))
            wid = cur.lastrowid
        conn.commit()
    finally:
        conn.close()
    _log_action('create_workorder', 'workorder', str(wid), f'新增工单：{order_no} - {data["title"]}')
    return jsonify({'code': 200, 'data': {'id': wid, 'order_no': order_no}})


@admin_api.route('/api/admin/workorders/<int:wid>', methods=['PUT'])
@require_admin_auth
def update_workorder(wid):
    """更新工单"""
    data = request.get_json() or {}
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            fields = []
            values = []
            for k in ['type', 'priority', 'device_id', 'customer_id', 'title', 'description',
                       'status', 'assignee', 'result']:
                if k in data:
                    fields.append(f'{k} = %s')
                    values.append(data[k])
            # 如果状态改为 closed，记录关闭时间
            if data.get('status') == 'closed':
                fields.append('closed_at = NOW()')
            if not fields:
                return jsonify({'code': 400, 'msg': '无更新字段'})
            values.append(wid)
            cur.execute(f'UPDATE work_orders SET {", ".join(fields)} WHERE id = %s', values)
        conn.commit()
    finally:
        conn.close()
    return jsonify({'code': 200, 'msg': '更新成功'})


@admin_api.route('/api/admin/workorders/<int:wid>', methods=['DELETE'])
@require_admin_auth
def delete_workorder(wid):
    """删除工单"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM work_orders WHERE id = %s', (wid,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ============================================================
#  Dashboard 厂商经营指标
# ============================================================

@admin_api.route('/api/admin/dashboard/device-distribution', methods=['GET'])
@require_admin_auth
def get_device_distribution():
    """按省份/城市聚合设备分布数据（从 MongoDB location 字段读取）"""
    from datetime import datetime, timedelta
    mongo = _get_mongo()
    coll = mongo[MONGO_COLLECTION]

    # 5 分钟前的时间，用于判断在线
    five_min_ago = (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

    # 获取所有设备最新一条记录
    device_ids = coll.distinct('device_id')
    device_latest = []
    for did in device_ids:
        doc = coll.find_one({'device_id': did}, sort=[('timestamp', pymongo.DESCENDING)])
        if doc:
            device_latest.append(doc)

    # 按省份聚合
    province_map = {}
    # 省份 code 映射
    province_codes = {
        '北京市': '110000', '天津市': '120000', '河北省': '130000', '山西省': '140000',
        '内蒙古': '150000', '辽宁省': '210000', '吉林省': '220000', '黑龙江省': '230000',
        '上海市': '310000', '江苏省': '320000', '浙江省': '330000', '安徽省': '340000',
        '福建省': '350000', '江西省': '360000', '山东省': '370000', '河南省': '410000',
        '湖北省': '420000', '湖南省': '430000', '广东省': '440000', '广西': '450000',
        '海南省': '460000', '重庆市': '500000', '四川省': '510000', '贵州省': '520000',
        '云南省': '530000', '西藏': '540000', '陕西省': '610000', '甘肃省': '620000',
        '青海省': '630000', '宁夏': '640000', '新疆': '650000', '台湾省': '710000',
        '香港': '810000', '澳门': '820000',
    }

    for doc in device_latest:
        loc = doc.get('location', {})
        province = loc.get('province', '未知')
        city = loc.get('city', '未知')
        district = loc.get('district', '未知')
        data = doc.get('data', {})
        aqi = data.get('AQI', 0)
        is_online = doc.get('timestamp', '') >= five_min_ago

        if province not in province_map:
            province_map[province] = {
                'name': province,
                'code': province_codes.get(province, ''),
                'devices': 0, 'online': 0,
                'aqi_sum': 0, 'pm25_sum': 0,
                'cities': {}
            }
        p = province_map[province]
        p['devices'] += 1
        if is_online:
            p['online'] += 1
        p['aqi_sum'] += aqi or 0
        p['pm25_sum'] += data.get('PM₂.₅', 0) or 0

        if city not in p['cities']:
            p['cities'][city] = {
                'name': city, 'devices': 0, 'online': 0,
                'aqi_sum': 0, 'pm25_sum': 0, 'districts': {}
            }
        c = p['cities'][city]
        c['devices'] += 1
        if is_online:
            c['online'] += 1
        c['aqi_sum'] += aqi or 0
        c['pm25_sum'] += data.get('PM₂.₅', 0) or 0

        if district not in c['districts']:
            c['districts'][district] = {
                'name': district, 'devices': 0, 'online': 0,
                'aqi_sum': 0, 'device_list': []
            }
        d = c['districts'][district]
        d['devices'] += 1
        if is_online:
            d['online'] += 1
        d['aqi_sum'] += aqi or 0
        d['device_list'].append({
            'device_id': doc.get('device_id'),
            'aqi': aqi,
            'online': is_online,
            'user': doc.get('user_info', {}).get('name', ''),
            'industry': doc.get('user_info', {}).get('industry', '')
        })

    # 格式化输出
    provinces = []
    for pname, pdata in province_map.items():
        cities = []
        for cname, cdata in pdata['cities'].items():
            districts = []
            for dname, ddata in cdata['districts'].items():
                avg_aqi = round(ddata['aqi_sum'] / ddata['devices'], 1) if ddata['devices'] else 0
                districts.append({
                    'name': dname, 'devices': ddata['devices'], 'online': ddata['online'],
                    'avg_aqi': avg_aqi, 'device_list': ddata['device_list']
                })
            avg_aqi = round(cdata['aqi_sum'] / cdata['devices'], 1) if cdata['devices'] else 0
            avg_pm25 = round(cdata['pm25_sum'] / cdata['devices'], 1) if cdata['devices'] else 0
            cities.append({
                'name': cname, 'devices': cdata['devices'], 'online': cdata['online'],
                'avg_aqi': avg_aqi, 'avg_pm25': avg_pm25, 'districts': districts
            })
        avg_aqi = round(pdata['aqi_sum'] / pdata['devices'], 1) if pdata['devices'] else 0
        avg_pm25 = round(pdata['pm25_sum'] / pdata['devices'], 1) if pdata['devices'] else 0
        provinces.append({
            'name': pname, 'code': pdata['code'],
            'devices': pdata['devices'], 'online': pdata['online'],
            'avg_aqi': avg_aqi, 'avg_pm25': avg_pm25,
            'cities': sorted(cities, key=lambda x: x['devices'], reverse=True)
        })

    provinces.sort(key=lambda x: x['devices'], reverse=True)
    return jsonify({'code': 200, 'data': {'provinces': provinces}})


@admin_api.route('/api/admin/dashboard/vendor-stats', methods=['GET'])
@require_admin_auth
def get_vendor_stats():
    """厂商经营指标统计"""
    conn = _get_mysql()
    try:
        with conn.cursor() as cur:
            # 设备总数和在线数
            cur.execute('SELECT COUNT(*) AS total FROM devices')
            total_devices = cur.fetchone()['total']

            # 本月新增设备
            cur.execute("SELECT COUNT(*) AS cnt FROM devices WHERE create_time >= DATE_FORMAT(NOW(), '%%Y-%%m-01')")
            new_devices_month = cur.fetchone()['cnt']

            # 客户数
            cur.execute("SELECT COUNT(*) AS total FROM customers WHERE status = 'active'")
            total_customers = cur.fetchone()['total']

            # 本月新增客户
            cur.execute("SELECT COUNT(*) AS cnt FROM customers WHERE created_at >= DATE_FORMAT(NOW(), '%%Y-%%m-01')")
            new_customers_month = cur.fetchone()['cnt']

            # 待处理工单
            cur.execute("SELECT COUNT(*) AS cnt FROM work_orders WHERE status = 'pending'")
            pending_orders = cur.fetchone()['cnt']

            # 处理中工单
            cur.execute("SELECT COUNT(*) AS cnt FROM work_orders WHERE status = 'processing'")
            processing_orders = cur.fetchone()['cnt']

            # 产品型号数
            cur.execute("SELECT COUNT(*) AS total FROM product_models WHERE status = 1")
            total_products = cur.fetchone()['total']

            # 本月告警数
            cur.execute("SELECT COUNT(*) AS cnt FROM alert_records WHERE created_at >= DATE_FORMAT(NOW(), '%%Y-%%m-01')")
            alerts_month = cur.fetchone()['cnt']
    finally:
        conn.close()

    # 从 MongoDB 获取在线设备数
    mongo = _get_mongo()
    coll = mongo[MONGO_COLLECTION]
    from datetime import datetime, timedelta
    five_min_ago = (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    online_devices = len(coll.distinct('device_id', {'timestamp': {'$gte': five_min_ago}}))

    return jsonify({
        'code': 200,
        'data': {
            'total_devices': total_devices,
            'online_devices': online_devices,
            'offline_devices': total_devices - online_devices,
            'online_rate': round(online_devices / total_devices * 100, 1) if total_devices else 0,
            'new_devices_month': new_devices_month,
            'total_customers': total_customers,
            'new_customers_month': new_customers_month,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'total_products': total_products,
            'alerts_month': alerts_month
        }
    })
