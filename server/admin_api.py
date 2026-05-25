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
    """所有活跃设备最新 AQI 数据"""
    try:
        db = _get_mongo()
        coll = db[MONGO_COLLECTION]
        # 取每个设备最新一条
        device_ids = coll.distinct('device_id')
        results = []
        for did in device_ids:
            doc = coll.find_one(
                {'device_id': did},
                sort=[('timestamp', pymongo.DESCENDING)]
            )
            if doc:
                data = doc.get('data', {})
                results.append({
                    'device_id': did,
                    'aqi': data.get('AQI'),
                    'pm25': data.get('PM₂.₅'),
                    'no2': data.get('NO₂'),
                    'so2': data.get('SO₂'),
                    'o3': data.get('O₃'),
                    'timestamp': doc.get('timestamp'),
                    'server_time': doc.get('server_time')
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
