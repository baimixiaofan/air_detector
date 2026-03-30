# 空气质量数据上报 API

## 接口说明
- URL: `http://<服务器IP>:5000/api/air-quality`
- 方法: POST
- 请求头: `Content-Type: application/json`
- 认证: 使用 Bearer Token

## 请求参数

### 请求头
| 参数名称 | 类型 | 说明 | 传输频率 |
|----------|------|------|----------|
| Authorization | string | 认证令牌，格式 `Bearer <token>` | 每次请求 |

### 请求体（JSON）
| 参数名称 | 类型 | 说明 | 传输频率 |
|----------|------|------|----------|
| timestamp | string | 数据生成时间，格式 `YYYY-MM-DD HH:MM:SS` | 每次请求 |
| data | object | 空气质量数据对象 | 每次请求 |
| data.AQI | float | 空气质量指数 | 每次请求 |
| data.PM₂.₅ | float | PM2.5浓度（μg/m³） | 每次请求 |
| data.NO₂ | float | 二氧化氮浓度（μg/m³） | 每次请求 |
| data.SO₂ | float | 二氧化硫浓度（μg/m³） | 每次请求 |
| data.O₃ | float | 臭氧浓度（μg/m³） | 每次请求 |

## 响应示例
成功：
```json
{
  "status": "success",
  "message": "数据接收成功",
  "data": {...}
}