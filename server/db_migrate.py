"""
数据库迁移脚本
用法：python db_migrate.py
"""
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

conn = pymysql.connect(
    host=MYSQL_HOST, port=MYSQL_PORT,
    user=MYSQL_USER, password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE, charset='utf8mb4'
)
cur = conn.cursor()

def add_column(table, column, definition):
    cur.execute("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_NAME=%s AND COLUMN_NAME=%s", (table, column))
    if cur.fetchone()[0] == 0:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")
        conn.commit()
        print(f'✅ {table}.{column} 已添加')
        return True
    else:
        print(f'✅ {table}.{column} 已存在')
        return False

add_column('intelligence_reports', 'report_stats',
    "report_stats JSON DEFAULT NULL COMMENT '预计算统计数据'")

add_column('intelligence_reports', 'customer_id',
    "customer_id INT DEFAULT NULL COMMENT '关联CRM客户ID'")
cur.execute("SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_NAME='intelligence_reports' AND INDEX_NAME='idx_customer'")
if cur.fetchone()[0] == 0:
    cur.execute("ALTER TABLE intelligence_reports ADD KEY idx_customer (customer_id)")
    conn.commit()
    print('✅ idx_customer 索引已添加')

add_column('users', 'email',
    "email VARCHAR(100) DEFAULT '' COMMENT '用户邮箱（用于告警通知）'")
add_column('users', 'phone',
    "phone VARCHAR(20) DEFAULT '' COMMENT '用户手机号'")
add_column('users', 'gender',
    "gender TINYINT DEFAULT 0 COMMENT '性别: 0未知 1男 2女'")
add_column('users', 'last_login_at',
    "last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间'")
add_column('users', 'last_login_ip',
    "last_login_ip VARCHAR(64) DEFAULT NULL COMMENT '最后登录IP'")

cur.close()
conn.close()
print('✅ 数据库迁移完成')
