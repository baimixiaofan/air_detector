-- ============================================================
-- 管理后台建表 SQL
-- 数据库: air_quality
-- ============================================================

USE air_quality;

-- 1. 管理员账号
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) DEFAULT '',
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' COMMENT 'admin/ops/viewer',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1=启用 0=禁用',
    last_login DATETIME DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 监测站点
CREATE TABLE IF NOT EXISTS sites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    area VARCHAR(100) DEFAULT '',
    site_type VARCHAR(50) DEFAULT 'office' COMMENT 'office/factory/outdoor/school',
    address VARCHAR(255) DEFAULT '',
    longitude DECIMAL(10,7) DEFAULT NULL,
    latitude DECIMAL(10,7) DEFAULT NULL,
    status TINYINT NOT NULL DEFAULT 1 COMMENT '1=启用 0=禁用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 站点-设备绑定
CREATE TABLE IF NOT EXISTS site_devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_id INT NOT NULL,
    device_id VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_site_device (site_id, device_id),
    KEY idx_device_id (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. 告警规则
CREATE TABLE IF NOT EXISTS alert_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    metric VARCHAR(50) NOT NULL COMMENT 'AQI/PM25/NO2/SO2/O3',
    operator VARCHAR(10) NOT NULL DEFAULT '>' COMMENT '>/>=/</<=/==',
    threshold DECIMAL(10,2) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'warning' COMMENT 'info/warning/critical',
    site_id INT DEFAULT NULL COMMENT 'NULL=全局规则',
    enabled TINYINT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 告警记录
CREATE TABLE IF NOT EXISTS alert_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT DEFAULT NULL,
    device_id VARCHAR(100) NOT NULL,
    site_id INT DEFAULT NULL,
    metric VARCHAR(50) NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    threshold DECIMAL(10,2) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'warning',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/acknowledged/resolved',
    acknowledged_by VARCHAR(50) DEFAULT NULL,
    acknowledged_at DATETIME DEFAULT NULL,
    resolved_by VARCHAR(50) DEFAULT NULL,
    resolved_at DATETIME DEFAULT NULL,
    message VARCHAR(500) DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_status (status),
    KEY idx_device (device_id),
    KEY idx_severity (severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. 设备远程配置
CREATE TABLE IF NOT EXISTS device_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(100) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value VARCHAR(500) DEFAULT '',
    description VARCHAR(255) DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_device_key (device_id, config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. 操作审计日志
CREATE TABLE IF NOT EXISTS admin_operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_user_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) DEFAULT NULL,
    target_id VARCHAR(50) DEFAULT NULL,
    details TEXT DEFAULT NULL,
    ip_address VARCHAR(50) DEFAULT '',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_user (admin_user_id),
    KEY idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. 企业信息
CREATE TABLE IF NOT EXISTS company_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL DEFAULT '',
    logo_url VARCHAR(500) DEFAULT '',
    address VARCHAR(255) DEFAULT '',
    contact_name VARCHAR(100) DEFAULT '',
    contact_phone VARCHAR(50) DEFAULT '',
    contact_email VARCHAR(100) DEFAULT '',
    description TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. 智能报告
CREATE TABLE IF NOT EXISTS intelligence_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    report_type VARCHAR(20) NOT NULL DEFAULT 'daily' COMMENT 'daily/weekly/monthly/quarterly',
    site_id INT DEFAULT NULL,
    content TEXT DEFAULT NULL,
    summary VARCHAR(1000) DEFAULT '',
    generated_by VARCHAR(50) DEFAULT 'system' COMMENT 'system/ai/enterprise',
    status VARCHAR(20) NOT NULL DEFAULT 'completed' COMMENT 'pending/completed/failed',
    company_name VARCHAR(200) DEFAULT '' COMMENT '企业报告-客户公司名',
    report_style VARCHAR(20) DEFAULT 'formal' COMMENT 'formal/casual',
    report_period VARCHAR(50) DEFAULT '' COMMENT '报告期间描述',
    metrics_included VARCHAR(200) DEFAULT '' COMMENT '包含的指标列表',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY idx_type (report_type),
    KEY idx_created (created_at),
    KEY idx_company (company_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 11. 客户管理
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '客户名称',
    type VARCHAR(20) NOT NULL DEFAULT 'enterprise' COMMENT 'enterprise/individual',
    contact_name VARCHAR(50) DEFAULT '' COMMENT '联系人',
    phone VARCHAR(20) DEFAULT '' COMMENT '电话',
    email VARCHAR(100) DEFAULT '' COMMENT '邮箱',
    address VARCHAR(200) DEFAULT '' COMMENT '地址',
    industry VARCHAR(50) DEFAULT '' COMMENT '行业：地产/酒店/学校/医院/办公',
    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active/inactive',
    notes TEXT DEFAULT NULL COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_type (type),
    KEY idx_industry (industry),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. 售后工单
CREATE TABLE IF NOT EXISTS work_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL UNIQUE COMMENT '工单编号 WO-20250611-001',
    type VARCHAR(20) NOT NULL DEFAULT 'fault' COMMENT 'fault/repair/inspection/complaint',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' COMMENT 'low/medium/high/urgent',
    device_id VARCHAR(100) DEFAULT NULL COMMENT '关联设备',
    customer_id INT DEFAULT NULL COMMENT '关联客户',
    title VARCHAR(200) NOT NULL COMMENT '工单标题',
    description TEXT DEFAULT NULL COMMENT '问题描述',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/processing/review/closed',
    assignee VARCHAR(50) DEFAULT NULL COMMENT '处理人',
    result TEXT DEFAULT NULL COMMENT '处理结果',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    closed_at DATETIME DEFAULT NULL,
    KEY idx_status (status),
    KEY idx_device (device_id),
    KEY idx_customer (customer_id),
    KEY idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 默认数据
-- ============================================================

-- 默认管理员 (admin / admin123)
INSERT IGNORE INTO admin_users (username, password_hash, display_name, role, status)
VALUES ('admin', 'scrypt:32768:8:1$hP58f18BRMclYyR7$3565427e4c98bc7e98df98184989877b551d24104fcd03355f3df6b3b65a6279559ee8123a81f2bc4ccb517976b7fbfb1eebd170f42d1d0389e1f4a021b78b4c', '系统管理员', 'admin', 1);

-- 默认企业信息
INSERT IGNORE INTO company_info (id, name, description) VALUES (1, '空气质量监测中心', '企业空气质量监测管理平台');
