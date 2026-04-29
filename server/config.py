# config.py —— 数据库连接配置（从环境变量读取，提供默认值）

import os

# ---- MySQL 配置（日统计数据写入目标）----
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'air_user')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'abc123456')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'air_quality')

# ---- MongoDB 配置（原始数据读取来源）----
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'air_quality')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'records')
