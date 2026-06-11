<template>
  <div class="page-container">
    <PageHeader title="空气质量分析" subtitle="筛选空气质量差的用户/设备，便于精准营销和产品推荐" />

    <!-- 筛选栏 -->
    <FilterBar>
      <el-select v-model="filters.days" placeholder="统计周期" style="width: 140px;">
        <el-option label="最近 7 天" :value="7" />
        <el-option label="最近 15 天" :value="15" />
        <el-option label="最近 30 天" :value="30" />
        <el-option label="最近 60 天" :value="60" />
        <el-option label="最近 90 天" :value="90" />
      </el-select>
      <el-select v-model="filters.aqi_threshold" placeholder="AQI 阈值" style="width: 160px;">
        <el-option label="AQI ≥ 50（良好以下）" :value="50" />
        <el-option label="AQI ≥ 100（轻度污染）" :value="100" />
        <el-option label="AQI ≥ 150（中度污染）" :value="150" />
        <el-option label="AQI ≥ 200（重度污染）" :value="200" />
      </el-select>
      <el-input-number v-model="filters.min_exceed_days" :min="1" :max="90" placeholder="最少超标天数" style="width: 160px;" />
      <el-input v-model="filters.area" placeholder="区域筛选（可选）" style="width: 160px;" clearable />
      <el-button type="primary" @click="fetchData" :loading="loading">
        <el-icon><Search /></el-icon>分析
      </el-button>
      <el-button @click="handleExport" :loading="exporting">
        <el-icon><Download /></el-icon>导出 CSV
      </el-button>
    </FilterBar>

    <!-- 统计卡片 -->
    <div class="kpi-row" style="margin-bottom: 24px;">
      <StatCard title="符合条件用户" :value="summary.total_users" variant="dark" icon="User" subtitle="空气质量差的设备数" />
      <StatCard title="平均 AQI" :value="summary.total_avg_aqi" variant="gradient" icon="TrendCharts" subtitle="所有筛选设备的均值" />
      <StatCard title="统计周期" :value="summary.days + '天'" variant="light" icon="Calendar" :subtitle="`AQI ≥ ${summary.aqi_threshold}`" />
      <StatCard title="超标天数阈值" :value="summary.min_exceed_days + '天'" variant="light" icon="Warning" subtitle="最少超标天数" />
    </div>

    <!-- 数据表格 -->
    <DashboardCard title="空气质量差的用户/设备列表">
      <el-table :data="tableData" v-loading="loading" stripe style="width: 100%;" max-height="520">
        <el-table-column prop="device_id" label="设备 ID" width="120" fixed />
        <el-table-column prop="nickname" label="用户" width="120">
          <template #default="{ row }">
            <span>{{ row.nickname || '未绑定' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="site_name" label="站点" width="150" />
        <el-table-column prop="area" label="区域" width="120" />
        <el-table-column prop="avg_aqi" label="平均 AQI" width="110" sortable>
          <template #default="{ row }">
            <span :style="{ color: row.health_level.color, fontWeight: 600 }">{{ row.avg_aqi }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="max_aqi" label="最大 AQI" width="110" sortable />
        <el-table-column prop="avg_pm25" label="PM2.5" width="100" sortable />
        <el-table-column prop="exceed_days" label="超标天数" width="110" sortable>
          <template #default="{ row }">
            <el-tag :type="row.exceed_days >= 20 ? 'danger' : row.exceed_days >= 10 ? 'warning' : 'info'" size="small">
              {{ row.exceed_days }} 天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="primary_pollutant" label="主要污染物" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.primary_pollutant }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="health_level" label="健康等级" width="120">
          <template #default="{ row }">
            <span class="status-badge" :style="{ background: row.health_level.color + '15', color: row.health_level.color }">
              {{ row.health_level.label }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="room_location" label="安装位置" width="100">
          <template #default="{ row }">
            <span>{{ roomMap[row.room_location] || row.room_location || '-' }}</span>
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getPoorAirUsers, exportPoorAirUsers } from '@/api/analytics'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import StatCard from '@/components/common/StatCard.vue'

const loading = ref(false)
const exporting = ref(false)
const tableData = ref([])
const summary = ref({ total_users: 0, total_avg_aqi: 0, days: 30, aqi_threshold: 50, min_exceed_days: 1 })

const filters = reactive({
  days: 30,
  aqi_threshold: 50,
  min_exceed_days: 1,
  area: ''
})

const roomMap = {
  living_room: '客厅',
  bedroom: '卧室',
  kitchen: '厨房',
  study: '书房',
  balcony: '阳台',
  dining_room: '餐厅',
  bathroom: '卫生间',
  hall: '门厅'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getPoorAirUsers(filters)
    if (res.code === 200) {
      tableData.value = res.data.list
      summary.value = res.data.summary
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const res = await exportPoorAirUsers(filters)
    const blob = new Blob(['﻿' + res], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `空气质量差用户_${filters.days}天.csv`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    console.error(e)
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
</style>
