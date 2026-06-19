# api_server.py
import json
import logging
import os
import sys
import time
import subprocess
from datetime import datetime

import redis
from flask import Flask, request, jsonify, send_from_directory
import tenacity
from functools import wraps
import hashlib
import pymysql.cursors
from flask_cors import CORS

# 兼容层：pymysql 替代 mysql.connector
import types as _types
_mysql_mod = _types.ModuleType('mysql')
_mysql_mod.connector = pymysql
_mysql_mod.connector.Error = pymysql.Error
sys.modules['mysql'] = _mysql_mod
sys.modules['mysql.connector'] = pymysql

_orig_mysql_cursor = pymysql.Connection.cursor
def _compat_cursor(self, dictionary=None, **kwargs):
    return _orig_mysql_cursor(self)
pymysql.Connection.cursor = _compat_cursor

# 环境变量配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_STREAM = os.getenv('REDIS_STREAM', 'data_stream')
API_KEY = os.getenv('API_KEY', '')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Redis 连接
try:
    redis_client = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
        decode_responses=True, max_connections=50,
        socket_connect_timeout=3, socket_timeout=3
    )
    redis_client.ping()
    print(f"成功连接到 Redis 服务器: {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError as e:
    print(f"无法连接到 Redis 服务器: {e}")
    redis_client = None
except Exception as e:
    print(f"连接 Redis 时发生未知错误: {e}")
    redis_client = None

app = Flask(__name__)
CORS(app)

flask_online = True  # 服务在线/下线状态

# 日志
numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
try:
    _log_handlers = [logging.FileHandler(os.getenv('LOG_DIR', '.') + '/server.log'), logging.StreamHandler()]
except (OSError, PermissionError):
    _log_handlers = [logging.StreamHandler()]
logging.basicConfig(level=numeric_level, format='%(asctime)s %(levelname)s: %(message)s', handlers=_log_handlers)
logger = logging.getLogger(__name__)


# ======================== 注册蓝图 ========================
from miniprogram_api import miniprogram
app.register_blueprint(miniprogram)
logger.info("小程序后端蓝图已注册")

from admin_api import admin_api
app.register_blueprint(admin_api, url_prefix='/api/admin')
logger.info("管理后台蓝图已注册")

# 启动告警检查引擎（后台线程，每5分钟）
try:
    from alert_checker import run_async as start_alert_checker
    start_alert_checker()
    logger.info("告警检查引擎已启动")
except Exception as e:
    logger.warning(f"告警检查引擎启动失败: {e}")


if __name__ == '__main__':
    print("正在启动空气质量数据API服务器...")
    print(f"Redis连接状态: {'已连接' if redis_client else '未连接'}")
    logger.info("空气质量数据API服务器启动")
    app.run(host='0.0.0.0', port=5000, debug=(os.getenv('FLASK_DEBUG', 'False').lower() == 'true'))
