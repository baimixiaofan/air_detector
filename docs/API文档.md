# API 接口文档

Base URL：`https://47.109.191.13:5000`

认证方式：`X-API-Key: 111`（仅运营端接口需要）

统一响应格式（小程序端）：

```json
{"code": 200, "data": {...}, "message": "success"}
{"code": 400, "data": null, "message": "错误描述"}
```

---

## 一、运营/监控接口

### 接收设备数据

```
POST /api/air-quality
Headers: X-API-Key: 111, X-Content-MD5: <md5>
Body: {
  "device_id": "CQ_001",
  "timestamp": "2026-05-15 14:30:00",
  "data": {"AQI": 68.5, "PM₂.₅": 35.2, "NO₂": 42.1, "SO₂": 15.8, "O₃": 55.3}
}
```

→ 存入 Redis Stream `data_stream`，由 consumer.py 写入 MongoDB

### 模拟器运行状态

```
GET /api/status
```

返回各模拟器心跳状态（需 Redis 中有 `simulator_stats`）

### Flask 服务在线状态

```
GET /api/flask-status
```

返回服务在线/下线状态

### Redis 队列信息

```
GET /api/queue_data
```

返回 `data_stream` 待消费消息数

### 切换服务在线/下线

```
POST /api/toggle-status
```

切换 `flask_online` 标志（用于测试模拟器重传机制）

### 读取/更新 API Key

```
GET  /api/config/api_key          → 读取当前 API Key
POST /api/config/api_key          → 更新 API Key
Body: {"api_key": "new_key"}
```

### 启动模拟器

```
POST /api/start_simulator
Body: {"count": 3}
```

在服务器上启动 N 个 Docker 模拟器容器

### 停止所有模拟器

```
POST /api/stop_all
```

### 获取容器日志

```
GET /api/docker_logs?container=CQ_001
```

### 获取服务器日志

```
GET /api/server_logs?lines=100
```

### Nginx 访问日志

```
GET /api/nginx-logs?lines=100
```

### 监控面板

```
GET /monitor
```

返回监控面板 HTML 页面（Chart.js 前端）

### 报警演示 — 触发

```
POST /api/device/<code>/trigger-alert
```

向 MongoDB 插入一条 AQI=300 的模拟数据（用于一键报警测试）

### 报警演示 — 清除

```
POST /api/device/<code>/clear-alert
```

删除刚才插入的超阈值模拟数据

---

## 二、MySQL CRUD 通用接口

所有表支持 `?field=value` 筛选，支持标准 RESTful CRUD。

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/devices` | GET | 设备列表 |
| `/api/devices` | POST | 创建设备 |
| `/api/devices/<id>` | GET | 设备详情 |
| `/api/devices/<id>` | PUT | 更新设备 |
| `/api/devices/<id>` | DELETE | 删除设备 |
| `/api/daily-summary` | GET | 日统计列表 |
| `/api/daily-summary` | POST | 创建日统计 |
| `/api/daily-summary/<id>` | GET | 日统计详情 |
| `/api/daily-summary/<id>` | PUT | 更新日统计 |
| `/api/daily-summary/<id>` | DELETE | 删除日统计 |
| `/api/air-quality-records` | GET | 历史记录列表（MySQL 侧，无数据） |
| `/api/air-quality-records` | POST | 创建历史记录 |
| `/api/air-quality-records/<id>` | GET/PUT/DELETE | 单条操作 |
| `/api/user-favorites` | GET/POST | 收藏列表/添加 |
| `/api/user-favorites/<id>` | GET/PUT/DELETE | 单条操作 |
| `/api/user-alerts` | GET/POST | 报警设置列表/添加 |
| `/api/user-alerts/<id>` | GET/PUT/DELETE | 单条操作 |
| `/api/users` | GET/POST | 用户列表/添加 |
| `/api/users/<id>` | GET/PUT/DELETE | 单条操作 |

---

## 三、微信小程序接口

### 用户登录

```
POST /api/login
Body: {"code": "wx_code"}
```

调微信 jscode2session 换取 open_id，返回：

```json
{"code": 200, "data": {"open_id": "oxxx", "is_new": true}, "message": "登录成功"}
```

### 绑定设备

```
POST /api/devices/bind
Body: {"open_id": "oxxx", "device_id": "CQ_001", "room_location": "living_room"}
```

`room_location` 可选值：`living_room` / `bedroom` / `kitchen` / `study` / `balcony` / `dining_room` / `bathroom` / `hall`，默认 `living_room`

### 解绑设备

```
POST /api/devices/unbind
Body: {"open_id": "oxxx", "device_id": "CQ_001"}
```

### 设备列表

```
GET /api/devices/list?open_id=oxxx
```

返回用户绑定的设备列表（含 room_location、在线状态）

### 更新设备位置

```
PUT /api/devices/location
Body: {"device_id": "CQ_001", "longitude": 106.55, "latitude": 29.56}
```

### 获取最新数据

```
GET /api/current?device_id=CQ_001
```

从 MongoDB 读取最新一条记录，返回：

```json
{"code": 200, "data": {
  "aqi": 68.5, "pm2_5": 35.2, "no2": 42.1, "so2": 15.8, "o3": 55.3,
  "device_id": "CQ_001",
  "timestamp": "2026-05-15 14:30:00",
  "alert": true,
  "alert_level": "severe"
}}
```

> `alert` / `alert_level`：当 AQI ≥ 阈值时出现。默认阈值 150，可在小程序中自定义。

### 获取历史数据

```
GET /api/history?device_id=CQ_001&hours=24
```

从 MongoDB 按时间正序返回数据列表：

```json
{"code": 200, "data": [
  {"sample_time": "2026-05-15 12:30:00", "aqi": 55.0, "pm2_5": 25.0, "no2": 30.0, "so2": 10.0, "o3": 45.0},
  ...
]}
```

支持 `hours`：`6` / `12` / `24` / `48` / `168`（7天）

### 获取日统计摘要

```
GET /api/daily_summary?date=2026-05-15&device_id=CQ_001
```

从 MySQL daily_summary 表读取：

```json
{"code": 200, "data": [
  {"device_id": "CQ_001", "stat_date": "2026-05-15", "avg_aqi": 72.3, "max_aqi": 120, "avg_pm2_5": 35.1}
]}
```

### 添加收藏

```
POST /api/favorites/add
Body: {"open_id": "oxxx", "device_id": "CQ_001"}
```

### 取消收藏

```
POST /api/favorites/remove
Body: {"open_id": "oxxx", "device_id": "CQ_001"}
```

### 收藏列表

```
GET /api/favorites/list?open_id=oxxx
```

### 获取报警设置

```
GET /api/alerts?open_id=oxxx&device_id=CQ_001
```

### 设置报警阈值

```
POST /api/alerts/set
Body: {"open_id": "oxxx", "device_id": "CQ_001", "aqi_max": 150, "pm2_5_max": 100}
```

### AI 空气质量分析

```
POST /api/ai/analyze
Body: {"device_id": "CQ_001", "hours": 24}
```

从 MongoDB 取最近 N 条数据 → 调用 DeepSeek API → 返回分析文本：

```json
{"code": 200, "data": {"analysis": "今日室内空气质量总体良好..."}}
```

> API Key 配置在代码中或环境变量 `DEEPSEEK_API_KEY`

---

## 四、设备配置

文件：`server/device_config.json`

```json
{"devices": [
  {"code": "CQ_001", "name": "重庆-解放碑", "longitude": 106.55, "latitude": 29.56},
  {"code": "CQ_002", "name": "重庆-观音桥", "longitude": 106.53, "latitude": 29.58},
  {"code": "CQ_003", "name": "重庆-南滨路", "longitude": 106.58, "latitude": 29.54},
  {"code": "CQ_004", "name": "重庆-大学城", "longitude": 106.31, "latitude": 29.60},
  {"code": "CQ_005", "name": "重庆-江北机场", "longitude": 106.64, "latitude": 29.72},
  {"code": "CQ_006", "name": "重庆-磁器口", "longitude": 106.45, "latitude": 29.57},
  {"code": "CQ_007", "name": "重庆-南山", "longitude": 106.60, "latitude": 29.53}
]}
```

设备绑定时会校验 `code` 是否在此配置中。

---

## 五、数据流总图

```
模拟器(Docker)
  ↓ HTTPS POST /api/air-quality (+ MD5 + API Key)
Flask API
  ↓ Redis Stream(data_stream)
consumer.py
  ↓ 批量写入
MongoDB records              ← 实时/历史数据从此读取
  ↓ daily_stats_job.py (01:05)
MySQL daily_summary          ← 日统计摘要从此读取

微信小程序
  ↓ HTTPS
Flask API (各 /api/* 端点)
  ↓
MySQL (users, user_devices, user_favorites, user_alerts)
```
