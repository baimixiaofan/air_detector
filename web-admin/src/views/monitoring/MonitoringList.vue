<template>
  <div class="page-container">
    <PageHeader title="实时监控">
      <div class="refresh-control">
        <el-switch v-model="autoRefresh" active-text="自动刷新" />
        <el-tag type="info" size="small">{{ refreshInterval / 1000 }}s</el-tag>
      </div>
    </PageHeader>

    <div class="kpi-row-3" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px;">
      <StatCard title="在线设备" :value="onlineCount" variant="gradient" icon="Connection" />
      <StatCard title="离线设备" :value="offlineCount" variant="light" icon="CircleClose" />
      <StatCard title="平均 AQI" :value="avgAqi" variant="dark" icon="TrendCharts" />
    </div>

    <DashboardCard title="实时数据" :show-settings="true">
      <el-table :data="deviceData" v-loading="loading" stripe style="width: 100%" @row-click="handleRowClick">
        <el-table-column prop="device_id" label="设备编码" min-width="140" />
        <el-table-column label="AQI" width="100">
          <template #default="{ row }">
            <span class="aqi-pill" :style="{ background: aqiLevel(row.aqi).bg, color: aqiLevel(row.aqi).color }">
              {{ row.aqi ?? '--' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="pm25" label="PM2.5" width="90" />
        <el-table-column prop="no2" label="NO₂" width="90" />
        <el-table-column prop="so2" label="SO₂" width="90" />
        <el-table-column prop="o3" label="O₃" width="90" />
        <el-table-column prop="pm10" label="PM10" width="90" />
        <el-table-column label="更新时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.timestamp) }}
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>

    <!-- Detail Drawer -->
    <el-drawer v-model="drawerVisible" :title="`设备详情 - ${selectedDevice?.device_id}`" size="500px">
      <div v-if="selectedDevice" class="detail-content">
        <div class="kpi-row-3" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px;">
          <div class="detail-kpi">
            <span class="detail-kpi__label">AQI</span>
            <span class="detail-kpi__value" :style="{ color: aqiLevel(selectedDevice.aqi).color }">{{ selectedDevice.aqi }}</span>
          </div>
          <div class="detail-kpi">
            <span class="detail-kpi__label">PM2.5</span>
            <span class="detail-kpi__value">{{ selectedDevice.pm25 }}</span>
          </div>
          <div class="detail-kpi">
            <span class="detail-kpi__label">状态</span>
            <span class="status-badge status-badge--success"><span class="status-dot"></span>在线</span>
          </div>
        </div>
        <TrendChart :data="detailTrend" :height="200" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getRealtimeData } from '@/api/monitoring'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import StatCard from '@/components/common/StatCard.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import { formatDateTime, aqiLevel as aqiLevelFn } from '@/utils/format'

const loading = ref(false)
const deviceData = ref([])
const autoRefresh = ref(true)
const refreshInterval = ref(5000)
const drawerVisible = ref(false)
const selectedDevice = ref(null)
const detailTrend = ref([])
let timer = null

const onlineCount = computed(() => deviceData.value.filter(d => d.online !== false).length)
const offlineCount = computed(() => deviceData.value.length - onlineCount.value)
const avgAqi = computed(() => {
  const devices = deviceData.value.filter(d => d.aqi)
  if (!devices.length) return 0
  return Math.round(devices.reduce((s, d) => s + d.aqi, 0) / devices.length)
})

function aqiLevel(aqi) {
  return aqiLevelFn(aqi)
}

async function fetchData() {
  loading.value = !deviceData.value.length
  try {
    const res = await getRealtimeData()
    if (res.code === 200 && res.data) {
      deviceData.value = res.data.devices || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function handleRowClick(row) {
  selectedDevice.value = row
  detailTrend.value = Array.from({ length: 24 }, (_, i) => ({
    hour: `${String(i).padStart(2, '0')}:00`,
    avg_aqi: Math.round((row.aqi || 50) + (Math.random() - 0.5) * 40)
  }))
  drawerVisible.value = true
}

function startTimer() {
  stopTimer()
  if (autoRefresh.value) {
    timer = setInterval(fetchData, refreshInterval.value)
  }
}

function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onMounted(() => {
  fetchData()
  startTimer()
})

onBeforeUnmount(stopTimer)
</script>

<style scoped>
.refresh-control {
  display: flex;
  align-items: center;
  gap: 8px;
}
.aqi-pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
  font-size: var(--font-size-caption);
}
.detail-content {
  padding: 0 4px;
}
.detail-kpi {
  text-align: center;
  padding: 12px;
  background: #fafbfc;
  border-radius: var(--radius-sm);
}
.detail-kpi__label {
  display: block;
  font-size: var(--font-size-caption);
  color: var(--text-muted);
  margin-bottom: 4px;
}
.detail-kpi__value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}
</style>
