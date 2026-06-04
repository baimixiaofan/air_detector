<template>
  <div class="page-container">
    <!-- KPI Cards -->
    <div class="kpi-row">
      <StatCard
        title="监测站点"
        :value="stats.total_sites"
        :change="-2.1"
        variant="dark"
        icon="Location"
      />
      <StatCard
        title="在线设备"
        :value="stats.online_devices"
        :change="5.3"
        variant="gradient"
        icon="Connection"
        :subtitle="`离线 ${stats.offline_devices}`"
      />
      <StatCard
        title="今日数据量"
        :value="todayDataCount"
        :change="3.8"
        variant="light"
        icon="Document"
      />
      <StatCard
        title="待处理告警"
        :value="stats.pending_alerts"
        :change="stats.pending_alerts > 0 ? -12.5 : 0"
        variant="light"
        icon="WarningFilled"
      />
    </div>

    <!-- Main Chart Row -->
    <div class="chart-row">
      <DashboardCard title="24小时AQI趋势" :show-settings="true">
        <TrendChart :data="trendData" :height="280" />
      </DashboardCard>
      <DashboardCard title="告警分布">
        <PieChart
          :data="alertPieData"
          name-key="name"
          value-key="value"
          :inner-radius="'45%'"
        />
      </DashboardCard>
    </div>

    <!-- Second Row -->
    <div class="chart-row-equal" style="display: grid; gap: 16px; margin-bottom: 20px;">
      <DashboardCard title="污染物分布">
        <BarChart :data="pollutantData" x-key="name" :series="[{ name: '平均浓度', key: 'value', color: '#2d3436' }]" />
      </DashboardCard>
      <DashboardCard title="设备状态">
        <div class="device-status-grid">
          <div v-for="device in deviceStatusList" :key="device.id" class="device-status-item">
            <span class="status-dot" :class="device.online ? 'status-dot--online' : 'status-dot--offline'"></span>
            <span class="device-name">{{ device.name }}</span>
            <span class="device-aqi" :style="{ color: aqiLevel(device.aqi).color }">{{ device.aqi }}</span>
          </div>
          <el-empty v-if="!deviceStatusList.length" description="暂无设备数据" :image-size="80" />
        </div>
      </DashboardCard>
    </div>

    <!-- Diagnostics -->
    <DashboardCard title="站点智能诊断" :show-settings="true">
      <template #actions>
        <el-tag type="info" size="small">{{ aiEnabled ? 'AI 增强' : '规则模式' }}</el-tag>
        <el-icon class="card-action-btn"><Setting /></el-icon>
      </template>
      <div class="diagnostic-grid">
        <div v-for="d in diagnostics" :key="d.site_id" class="diagnostic-card">
          <div class="diag-header">
            <span class="diag-name">{{ d.site_name }}</span>
            <el-tag :type="d.health_color" size="small" effect="dark">{{ d.health_label }}</el-tag>
          </div>
          <div class="diag-body">
            <div class="risk-gauge">
              <span class="risk-value" :style="{ color: riskColor(d.risk_score) }">{{ d.risk_score }}</span>
              <span class="risk-label">风险分</span>
            </div>
            <div class="diag-metrics">
              <p>AQI 均值: <strong>{{ d.avg_aqi }}</strong></p>
              <p>超标: <strong>{{ d.exceed_days }}天</strong></p>
              <p v-if="d.primary_pollutant">主要污染物: <strong>{{ d.primary_pollutant }}</strong></p>
            </div>
          </div>
          <p class="diag-suggestion">{{ d.suggestion }}</p>
        </div>
        <el-empty v-if="!diagnostics.length" description="暂无诊断数据" />
      </div>
    </DashboardCard>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { getDashboardStats, getDashboardTrend, getAlertSummary, getDiagnostics, getDashboardRealtime } from '@/api/dashboard'
import StatCard from '@/components/common/StatCard.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { aqiLevel as aqiLevelFn, riskColor as riskColorFn } from '@/utils/format'

const stats = ref({ total_sites: 0, total_devices: 0, online_devices: 0, offline_devices: 0, pending_alerts: 0 })
const trendData = ref([])
const alertSummary = ref({ info: 0, warning: 0, critical: 0 })
const diagnostics = ref([])
const aiEnabled = ref(false)
const todayDataCount = ref(0)
const deviceStatusList = ref([])
const pollutantData = ref([])
let timer = null

const alertPieData = ref([])

function aqiLevel(aqi) {
  return aqiLevelFn(aqi)
}

function riskColor(score) {
  return riskColorFn(score)
}

async function fetchData() {
  try {
    const [s, t, a, d] = await Promise.all([
      getDashboardStats(),
      getDashboardTrend(),
      getAlertSummary(),
      getDiagnostics()
    ])
    if (s.code === 200) stats.value = s.data
    if (t.code === 200) trendData.value = t.data
    if (a.code === 200) {
      alertSummary.value = a.data
      alertPieData.value = [
        { name: '严重', value: a.data.critical || 0 },
        { name: '警告', value: a.data.warning || 0 },
        { name: '提示', value: a.data.info || 0 }
      ].filter(d => d.value > 0)
    }
    if (d.code === 200) {
      diagnostics.value = d.data
      aiEnabled.value = d.data.some(x => x.ai_generated)
    }

    // Fetch realtime data for device status
    const rt = await getDashboardRealtime()
    if (rt.code === 200 && rt.data) {
      todayDataCount.value = rt.data.total_count || 0
      deviceStatusList.value = (rt.data.devices || []).slice(0, 8).map(dev => ({
        id: dev.client_ip || dev.device_id,
        name: dev.client_ip || dev.device_id,
        online: dev.online !== false,
        aqi: dev.aqi || 0
      }))
      // Build pollutant averages
      if (rt.data.devices && rt.data.devices.length) {
        const devices = rt.data.devices
        pollutantData.value = [
          { name: 'PM2.5', value: Math.round(devices.reduce((s, d) => s + (d.pm25 || 0), 0) / devices.length) },
          { name: 'PM10', value: Math.round(devices.reduce((s, d) => s + (d.pm10 || 0), 0) / devices.length) },
          { name: 'NO₂', value: Math.round(devices.reduce((s, d) => s + (d.no2 || 0), 0) / devices.length) },
          { name: 'SO₂', value: Math.round(devices.reduce((s, d) => s + (d.so2 || 0), 0) / devices.length) },
          { name: 'O₃', value: Math.round(devices.reduce((s, d) => s + (d.o3 || 0), 0) / devices.length) }
        ]
      }
    }
  } catch (e) {
    console.error('Dashboard fetch error:', e)
  }
}

onMounted(() => {
  fetchData()
  timer = setInterval(fetchData, 30000)
})

onBeforeUnmount(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.device-status-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
}
.device-status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: #fafbfc;
  transition: background var(--transition-fast);
}
.device-status-item:hover {
  background: #f0f2f5;
}
.status-dot--online {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
  animation: pulse 2s infinite;
}
.status-dot--offline {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}
.device-name {
  flex: 1;
  font-size: var(--font-size-body);
  color: var(--text-primary);
}
.device-aqi {
  font-weight: 600;
  font-size: var(--font-size-body);
}

.diagnostic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.diagnostic-card {
  background: #fafbfc;
  border-radius: var(--radius-sm);
  padding: 16px;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
  cursor: pointer;
}
.diagnostic-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.diag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.diag-name {
  font-weight: 600;
  font-size: var(--font-size-body);
  color: var(--text-primary);
}
.diag-body {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
}
.risk-gauge {
  text-align: center;
  min-width: 56px;
}
.risk-value {
  font-size: 28px;
  font-weight: 700;
  display: block;
  line-height: 1.1;
}
.risk-label {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
}
.diag-metrics {
  flex: 1;
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
}
.diag-metrics p {
  margin: 4px 0;
}
.diag-suggestion {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
  line-height: 1.5;
  border-top: 1px solid #f0f2f5;
  padding-top: 8px;
}
</style>
