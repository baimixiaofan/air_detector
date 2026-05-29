<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

// 模拟实时的空气质量监测数据
const tableData = ref([
  {
    id: 'ST-001',
    name: '朝阳区奥体中心站',
    aqi: 45,
    pm25: 32,
    pm10: 45,
    temp: 22.5,
    time: '10:05:00',
  },
  {
    id: 'ST-002',
    name: '海淀区万柳站',
    aqi: 115,
    pm25: 85,
    pm10: 120,
    temp: 23.1,
    time: '10:05:05',
  },
  { id: 'ST-003', name: '东城区天坛站', aqi: 55, pm25: 38, pm10: 60, temp: 21.8, time: '10:04:50' },
  {
    id: 'ST-004',
    name: '西城区万寿西宫站',
    aqi: 85,
    pm25: 60,
    pm10: 90,
    temp: 22.0,
    time: '10:05:12',
  },
  {
    id: 'ST-005',
    name: '通州区梨园站',
    aqi: 165,
    pm25: 120,
    pm10: 180,
    temp: 24.2,
    time: '10:05:01',
  },
])

// 💡 新技能：封装一个函数，根据 AQI 数值自动计算标签颜色
const getAqiType = (aqi) => {
  if (aqi <= 50) return 'success' // 绿灯：优
  if (aqi <= 100) return 'warning' // 黄灯：良
  return 'danger' // 红灯：污染
}

// 封装一个函数，根据 AQI 数值自动计算文字状态
const getAqiText = (aqi) => {
  if (aqi <= 50) return '优'
  if (aqi <= 100) return '良'
  return '污染'
}

const handleRefresh = () => {
  ElMessage.success('数据已获取最新实时状态！')
}
</script>

<template>
  <div class="list-view-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>📋 实时监测数据列表</span>
          <el-button type="success" plain icon="Refresh" @click="handleRefresh"
            >手动刷新数据</el-button
          >
        </div>
      </template>

      <el-table :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="name" label="监测站点" min-width="160" />

        <el-table-column prop="aqi" label="AQI 指数" width="120" sortable>
          <template #default="scope">
            <el-tag :type="getAqiType(scope.row.aqi)" effect="dark">
              {{ scope.row.aqi }} ({{ getAqiText(scope.row.aqi) }})
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="pm25" label="PM2.5 (μg/m³)" width="150" sortable />
        <el-table-column prop="pm10" label="PM10 (μg/m³)" width="150" sortable />
        <el-table-column prop="temp" label="温度 (℃)" width="120" />
        <el-table-column prop="time" label="最近更新时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.list-view-container {
  padding-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
