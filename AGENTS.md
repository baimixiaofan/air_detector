# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概述

空气质量数据采集与监测系统。模拟设备生成空气质量数据，通过 HTTPS 上报到云服务器，经 Redis Stream 缓冲后存入 MongoDB，每日定时聚合到 MySQL。

**部署服务器**: `47.109.191.13`（SSH: `root@47.109.191.13`，密钥登录）

## 数据流

```
模拟器(Docker) → HTTPS POST → Flask API → Redis Stream
                                                ↓
                                     consumer.py → MongoDB (原始数据)
                                                ↓
                          daily_stats_job.py (每天01:05) → MySQL (日统计)
```

## 项目结构

```
├── simulator/
│   ├── air_detector.py       # 设备模拟器 — 生成数据 → HTTP发送 → Redis心跳
│   └── start_simulators.sh   # Docker 批量启动脚本
├── server/
│   ├── config.py             # 数据库连接配置（环境变量）
│   ├── flask_api_server.py   # Flask 启动引导（Redis、日志、蓝图注册）
│   ├── miniprogram_api.py    # **所有 API 路由**（运营端 + CRUD + 小程序端）
│   ├── admin_api.py          # **管理后台 API**（Redis Token 认证 + DeepSeek AI）
│   ├── consumer.py           # Redis Stream → MongoDB 消费者
│   ├── daily_stats_job.py    # 日统计定时任务（APScheduler）
│   ├── web.html              # 监控面板前端（Chart.js）
│   └── requirements.txt
├── data_anlyse.py            # 本地数据分析工具（Tkinter GUI）
├── web-admin/                # 企业空气质量监测管理平台（Vue3）
│   ├── src/
│   │   ├── main.js           # 入口：Element Plus、Pinia、Router
│   │   ├── App.vue
│   │   ├── api/              # 接口封装
│   │   ├── router/           # 路由 + beforeEach 鉴权
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── views/            # 所有页面组件
│   │   ├── components/       # 布局/通用/图表组件
│   │   ├── utils/            # 工具函数
│   │   └── styles/           # 全局样式
│   ├── vite.config.js
│   └── package.json
└── AGENTS.md
```

## 关键配置

所有数据库连接通过环境变量配置，默认值见 [server/config.py](server/config.py)：
- **MongoDB**: `localhost:27017/air_quality.records`
- **MySQL**: `localhost:3306/air_quality`（用户 `air_user`）
- **Redis**: `localhost:6379`
- **API Key**: `111`（通过 `X-API-Key` 请求头传递）

## 部署架构

- **云主机**（阿里云 ECS, Ubuntu）运行全套服务
- **Flask API** → 端口 `5000`，通过 Nginx 反向代理提供 HTTPS（443端口）
- **Nginx** → 端口 80/443，HTTPS 终止（Let's Encrypt 证书，域名 `baimeixiaofan.xyz`，无 ICP 备案暂不可用）
- **SSL 证书路径**: `/etc/letsencrypt/live/baimeixiaofan.xyz/`，自动续期已配置
- **Redis** → `127.0.0.1:6379`，消息队列缓冲
- **MongoDB** → `127.0.0.1:27017`，存储原始数据
- **MySQL** → `127.0.0.1:3306`，存储日统计聚合数据
- **Consumer** → 运行在 `/home/flask_app/consumer.py`，消费 Redis Stream 写入 MongoDB
- **日统计任务** → 运行在 `/home/flask_app/daily_stats_job.py`（APScheduler）
- **模拟器** → Docker 容器（`--network host`），通过 HTTPS 上报数据
- **Jenkins** → 端口 `8080`，CI/CD 管理（Flask API 实际由 Jenkins  workspace 启动）
- **监控面板** → `https://47.109.191.13/monitor` 访问
- **管理后台** → `https://47.109.191.13/admin` 访问（Nginx 直接输出静态文件）
- `/admin/` 路径在 Nginx 中配置：`alias /home/flask_app/web-admin/dist;`
- Flask API 运行在 Jenkins workspace: `/var/lib/jenkins/workspace/test/`

## 常用命令

### 本地开发

```bash
# 安装依赖
pip install -r server/requirements.txt

# 启动 API 服务器
python server/flask_api_server.py

# 启动 Redis 消费者（写入 MongoDB）
python server/consumer.py

# 启动日统计定时任务
python server/daily_stats_job.py

# 启动本地模拟器（单机调试）
python simulator/air_detector.py
```

### 服务器

```bash
# SSH 登录
ssh root@47.109.191.13

# Flask API 位于 Jenkins workspace
cd /var/lib/jenkins/workspace/test/

# 重启 Flask（使用 jenkins 用户）
su - jenkins -c 'cd /var/lib/jenkins/workspace/test && nohup venv/bin/python flask_api_server.py > flask_output.log 2>&1 &'

# 重载 Nginx
sudo nginx -t && sudo systemctl reload nginx
```

### 管理后台开发

```bash
cd web-admin
npm install
npm run dev          # 开发模式（Vite proxy /api → localhost:5000）
npm run build        # 生产构建 → dist/
```

### 部署管理后台

```bash
# 构建前端
cd web-admin && npm run build
# 上传到服务器
scp -r dist/* root@47.109.191.13:/home/flask_app/web-admin/dist/

# 上传后端（若改了 admin_api.py）
scp server/admin_api.py server/flask_api_server.py root@47.109.191.13:/var/lib/jenkins/workspace/test/

# 重启
ssh root@47.109.191.13 "su - jenkins -c 'cd /var/lib/jenkins/workspace/test && nohup venv/bin/python flask_api_server.py > flask_output.log 2>&1 &'"
```

### API 端点

所有路由定义在 [miniprogram_api.py](server/miniprogram_api.py) 中。

**运营 / 监控：**

| 方法 | 路由 | 说明 |
|---|---|---|
| POST | `/api/air-quality` | 接收设备数据（需 API Key + MD5） |
| GET | `/api/status` | 模拟器运行状态 |
| GET | `/api/flask-status` | Flask 服务在线/下线状态 |
| GET | `/api/queue_data` | Redis 队列信息 |
| GET/POST | `/api/config/api_key` | 读取/更新 API Key |
| POST | `/api/toggle-status` | 切换服务在线/下线 |
| POST | `/api/start_simulator` | 启动 Docker 模拟器 |
| GET | `/api/admin/customers/enterprise` | 企业客户列表（带设备数） |
| GET | `/api/admin/reports/{id}/chart-data` | 报告图表/表格数据 |
| POST | `/api/stop_all` | 停止所有模拟器容器 |
| GET | `/api/docker_logs` | 指定容器日志 |
| GET | `/api/server_logs` | 服务器端日志 |
| GET | `/api/nginx-logs` | Nginx 访问日志（HTTPS 验证） |
| GET | `/monitor` | 监控面板页面 |

**MySQL CRUD（支持 `?field=value` 筛选）：**
`/api/devices`, `/api/daily-summary`, `/api/air-quality-records`, `/api/user-favorites`, `/api/user-alerts`, `/api/users`

**微信小程序端点：**

| 方法 | 路由 | 说明 |
|---|---|---|
| GET | `/api/current?device_id=` | 设备最新数据（从 MongoDB） |
| GET | `/api/history?device_id=&hours=` | 历史数据 |
| GET | `/api/daily_summary?date=` | 每日统计（从 MySQL daily_summary） |
| POST | `/api/login` | 微信登录 `{code}` |
| POST | `/api/favorites/add` | 添加收藏 `{open_id, device_id}` |
| POST | `/api/favorites/remove` | 取消收藏 |
| GET | `/api/favorites/list?open_id=` | 收藏列表 |
| POST | `/api/devices/bind` | 绑定设备 `{open_id, device_id}` |
| POST | `/api/devices/unbind` | 解绑设备 |
| GET | `/api/devices/list?open_id=` | 我的设备列表（含在线状态） |
| PUT | `/api/devices/location` | 更新设备经纬度 `{longitude, latitude}` |

## 架构要点

### 文件职责
- [flask_api_server.py](server/flask_api_server.py) — 仅启动引导：Redis 连接、日志配置、pymysql 兼容层、注册蓝图
- [miniprogram_api.py](server/miniprogram_api.py) — **小程序全部 API 路由**，通过 `import flask_api_server as _srv` 共享 Redis 等状态
- [admin_api.py](server/admin_api.py) — **管理后台全部 API 路由**，Redis Token 认证，集成 DeepSeek AI 分析
- DeepSeek API Key: 通过 `DEEPSEEK_API_KEY` 环境变量配置，有默认值 `sk-19745d6c32e64f7bb828a3d31180d97b`

### 管理后台（web-admin/）
- 前端：Vue3 + Element Plus + ECharts + Leaflet
- 后端：Flask 蓝图 `/api/admin/*`，Redis Token 认证
- 访问：`https://baimeixiaofan.xyz/admin`（ICP 备案已通过）
- 默认账号：admin / admin123
- 角色：admin（管理员）、ops（运维）、viewer（查看者）
- **每次添加新功能都要修改 AGENTS.md 和计划文件**

### 前端设计系统（AirInsight）
- **设计风格**：Apple 风格暗色主题，模仿 Apple 和南孚电池网站
- **主色调**：Apple Blue `#007AFF` + Purple `#5856D6`
- **背景**：纯黑 `#000000` + 半透明玻璃效果
- **设计令牌**：`web-admin/src/styles/tokens.css`
- **全局样式**：`web-admin/src/styles/global.css`
- **Element Plus 暗色主题**：已集成 `element-plus/theme-chalk/dark/css-vars.css`
- **页面过渡动画**：`page-content` 过渡效果

### 企业报告系统（商业化核心）
- **报告生成**：DeepSeek AI 生成报告文本（max_tokens=1000，含环比数据 + 客户行业上下文）
- **图表**：前端 ECharts 渲染（AQI趋势/污染物对比/等级分布环形图），html2canvas 截图嵌入 PDF
- **表格**：ReportTables.vue 三张表（逐设备分析、日均对比、超标统计），PDF 和预览都包含
- **CRM 数据源**：报告从 `customers` 表选择企业客户 → `devices.customer_id` 解析设备 → MongoDB 查数据
- **数据来源块**：报告预览显示客户名、设备数、数据区间、数据总量
- **PDF 导出**：前端 html2canvas + jspdf（封面 → 数据来源 → 图表 → 表格 → AI 分析 → 页脚）
- **环比对比**：自动计算上期数据对比（AQI/PM2.5/达标率 环比变化百分比）
- **报告数据缓存**：`intelligence_reports.report_stats` JSON 列 + `intelligence_reports.customer_id`

### 商业价值定位
- **健康评分**：基于空气质量的健康指数（0-100分）
- **环境优化建议**：AI 驱动的改善方案（新风系统、绿植、通风等）
- **商业洞察**：数据驱动的价值发现（节能潜力、房产增值、用户健康指数）
- **趋势预测**：基于历史数据的预测分析

### 管理后台新增 MySQL 表
- `admin_users` — 后台账号（username, password_hash, role）
- `sites` — 监测站点（name, code, area, site_type, 经纬度）
- `site_devices` — 站点-设备绑定
- `alert_rules` / `alert_records` — 告警规则与记录
- `device_configs` — 设备远程配置
- `admin_operation_logs` — 操作审计日志
- `company_info` — 企业信息
- `intelligence_reports` — 智能报告（有 `report_stats JSON` 列存储预计算图表数据）
- `product_recommendations` — 产品推荐配置

### 管理后台 API 路由（admin_api.py）
| 模块 | 路由 | 说明 |
|------|------|------|
| 认证 | POST /api/admin/login | 登录获取 token |
| | GET /api/admin/profile | 当前用户信息 |
| | POST /api/admin/logout | 退出登录 |
| 看板 | GET /api/admin/dashboard/stats | 总览统计 |
| | GET /api/admin/dashboard/trend | 24h 趋势 |
| | GET /api/admin/dashboard/realtime | 实时数据 |
| | GET /api/admin/dashboard/alert-summary | 告警统计 |
| 诊断 | GET /api/admin/dashboard/diagnostics | 所有站点智能诊断 |
| | GET /api/admin/dashboard/diagnostics/{id} | 单站点诊断详情 |
| 客户 | GET /api/admin/customers/enterprise | 企业客户列表（含设备数量） |
| 报告 | POST /api/admin/reports/enterprise | 生成企业报告（支持customer_id + 逐设备 + 超标统计） |
| | GET /api/admin/reports/{id}/preview | 报告预览（report_stats 自动解析为 JSON） |
| | GET /api/admin/reports/{id}/chart-data | 获取报告图表数据（日分解/等级分布/环比） |
| | GET /api/admin/reports | 报告列表 |
| | POST /api/admin/reports/generate | 生成智能简报 |
| | DELETE /api/admin/reports/{id} | 删除报告 |

### ⚠️ 循环导入警告
`miniprogram_api.py` 不能**在文件顶部**写 `import flask_api_server as _srv`。必须把该导入放在**文件底部**（所有路由函数定义之后），否则启动时会出现：
```
ImportError: cannot import name 'miniprogram' from partially initialized module
```

### 数据源选择
- **实时/历史数据**（`/api/current`, `/api/history`）→ MongoDB `air_quality.records`
- **每日统计**（`/api/daily_summary`）→ MySQL `daily_summary` 表
- **用户/绑定/收藏** → MySQL（`users`, `user_devices`, `user_favorites` 表）
- `air_quality_records` 表未被自动化流水线填充，无实时数据

### 设备标识
MongoDB 中设备由 `client_ip` 标识（Docker 容器的内网 IP），与 MySQL `daily_summary.device_id` 一致。小程序端统一使用 `client_ip` 作为设备 ID。

## 注意点

- 日统计使用 MongoDB `$regex` 匹配时间戳，每天凌晨 01:05 执行
- 模拟器有本地缓存重传机制（失败数据存 `failed_data_cache.json`）
- 所有 HTTP 请求跳过 SSL 验证（`verify=False`）
- 服务器有 Jenkins CI/CD，Flask API 由 Jenkins workspace 下的进程管理
- 每次添加新功能都要修改 AGENTS.md
- 正式上线后遵守：本地修改 → push GitHub → Jenkins 拉取部署流程。开发阶段可直接 scp 上传 + 重启 Flask 快速验证
每一句结束要喵喵叫一下喵