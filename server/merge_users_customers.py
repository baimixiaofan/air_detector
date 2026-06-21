"""
迁移 customers → users 合并脚本
"""
import pymysql
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

conn = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT,
                       user=MYSQL_USER, password=MYSQL_PASSWORD,
                       database=MYSQL_DATABASE, charset='utf8mb4')
cur = conn.cursor()

def has_column(table, col):
    cur.execute("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
                (MYSQL_DATABASE, table, col))
    return cur.fetchone()[0] > 0

def add_column(table, col, definition):
    if not has_column(table, col):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN `{col}` {definition}")
        conn.commit()
        print(f'  ✔ {table}.{col} 添加成功')
    else:
        print(f'  - {table}.{col} 已存在')

def drop_column(table, col):
    if has_column(table, col):
        cur.execute(f"ALTER TABLE {table} DROP COLUMN {col}")
        conn.commit()
        print(f'  ✔ {table}.{col} 删除成功')
    else:
        print(f'  - {table}.{col} 不存在')

# 1. users 加字段
add_column('users', 'customer_type', "VARCHAR(20) DEFAULT 'individual' COMMENT 'individual/enterprise'")
add_column('users', 'industry', "VARCHAR(50) DEFAULT '' COMMENT '行业'")
add_column('users', 'contact_name', "VARCHAR(50) DEFAULT '' COMMENT '联系人'")
add_column('users', 'address', "VARCHAR(200) DEFAULT '' COMMENT '地址'")
add_column('users', 'notes', "TEXT DEFAULT NULL COMMENT '备注'")
add_column('users', 'status', "VARCHAR(20) DEFAULT 'active' COMMENT 'active/inactive'")
add_column('users', 'source', "VARCHAR(20) DEFAULT 'wechat' COMMENT 'wechat/admin_added'")

# 2. customers 数据迁入 users
cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME='customers'", (MYSQL_DATABASE,))
has_customers_table = cur.fetchone()[0] > 0

if has_customers_table:
    cur.execute("SELECT COUNT(*) FROM customers")
    cnt = cur.fetchone()[0]
    if cnt > 0:
        cur.execute('''
            INSERT IGNORE INTO users (open_id, nickname, contact_name, phone, email, address, industry, customer_type, status, notes, source, create_time, update_time)
            SELECT CONCAT('crm_', id), name, contact_name, phone, email, address, industry,
                   CASE WHEN type = 'enterprise' THEN 'enterprise' ELSE 'individual' END,
                   status, notes, 'admin_added', created_at, updated_at
            FROM customers
        ''')
        conn.commit()
        print(f'  ✔ customers → users 迁移 {cnt} 条')
    else:
        print('  - customers 表无数据')
else:
    print('  - customers 表不存在')

# 3. devices 的 customer_id 转为 open_id
if has_column('devices', 'customer_id'):
    cur.execute("SELECT COUNT(*) FROM devices WHERE customer_id IS NOT NULL AND (open_id IS NULL OR open_id = '')")
    dev_cnt = cur.fetchone()[0]
    if dev_cnt > 0:
        cur.execute('''
            UPDATE devices d
            JOIN users u ON CONCAT('crm_', d.customer_id) = u.open_id AND u.source = 'admin_added'
            SET d.open_id = u.open_id,
                d.contact_name = COALESCE(d.contact_name, u.contact_name),
                d.customer_type = u.customer_type,
                d.industry = COALESCE(d.industry, u.industry)
            WHERE d.customer_id IS NOT NULL AND (d.open_id IS NULL OR d.open_id = '')
        ''')
        conn.commit()
        print(f'  ✔ devices.customer_id → open_id 迁移 {dev_cnt} 台')
    else:
        print('  - devices 无待迁移 customer_id')
    drop_column('devices', 'customer_id')
else:
    print('  - devices.customer_id 已不存在')

# 4. 删 customers 表
if has_customers_table:
    cur.execute("DROP TABLE customers")
    conn.commit()
    print('  ✔ 删除 customers 表')
else:
    print('  - customers 表已删除')

print('\n迁移完成')

cur.close()
conn.close()
