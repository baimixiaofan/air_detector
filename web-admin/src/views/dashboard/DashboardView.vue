<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6"><StatCard title="监测站点" :value="stats.total_sites" icon="Location" color="#409eff" /></el-col>
      <el-col :span="6"><StatCard title="设备总数" :value="stats.total_devices" icon="Cpu" color="#67c23a" /></el-col>
      <el-col :span="6"><StatCard title="在线设备" :value="stats.online_devices" :subtitle="`离线 ${stats.offline_devices}`" icon="Connection" color="#e6a23c" /></el-col>
      <el-col :span="6"><StatCard title="待处理告警" :value="stats.pending_alerts" icon="WarningFilled" color="#f56c6c" /></el-col>
    </el-row>

    <!-- 趋势图 + 告警统计 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="18">
        <el-card>
          <template #header>24 小时趋势</template>
          <TrendChart :data="trendData" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <template #header>告警统计</template>
          <div class="alert-stat">
            <div class="alert-item">
              <span class="alert-dot critical"></span>
              <span>严重</span>
              <span class="alert-count">{{ alertSummary.critical }}</span>
            </div>
            <div class="alert-item">
              <span class="alert-dot warning"></span>
              <span>警告</span>
              <span class="alert-count">{{ alertSummary.warning }}</span>
            </div>
            <div class="alert-item">
              <span class="alert-dot info"></span>
              <span>提示</span>
              <span class="alert-count">{{ alertSummary.info }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 智能诊断卡片 -->
    <el-card class="diagnostic-section">
      <template #header>
        <span>站点智能诊断</span>
        <el-tag type="info" size="small" style="margin-left: 8px">
          {{ aiEnabled ? 'AI 增强' : '规则模式' }}
        </el-tag>
      </template>
      <el-row :gutter="16">
        <el-col v-for="d in diagnostics" :key="d.site_id" :span="6" style="margin-bottom: 16px">
          <el-card shadow="hover" class="diagnostic-card" :body-style="{ padding: '16px' }">
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
          </el-card>
        </el-col>
        <el-empty v-if="diagnostics.length === 0" description="暂无诊断数据" />
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { getDashboardStats, getDashboardTrend, getAlertSummary, getDiagnostics } from '@/api/dashboard'
import StatCard from '@/components/common/StatCard.vue'
import TrendChart from '@/components/charts/TrendChart.vue'

const stats = ref({ total_sites: 0, total_devices: 0, online_devices: 0, offline_devices: 0, pending_alerts: 0 })
const trendData = ref([])
const alertSummary = ref({ info: 0, warning: 0, critical: 0 })
const diagnostics = ref([])
const aiEnabled = ref(false)
let timer = null

function riskColor(score) {
  if (score <= 30) return '#67c23a'
  if (score <= 50) return '#e6a23c'
  if (score <= 70) return '#f56c6c'
  return '#c03639'
}

async function fetchData() {
  const [s, t, a, d] = await Promise.all([
    getDashboardStats(),
    getDashboardTrend(),
    getAlertSummary(),
    getDiagnostics()
  ])
  if (s.code === 200) stats.value = s.data
  if (t.code === 200) trendData.value = t.data
  if (a.code === 200) alertSummary.value = a.data
  if (d.code === 200) {
    diagnostics.value = d.data
    aiEnabled.value = d.data.some(x => x.ai_generated)
  }
}

onMounted(() => {
  fetchData()
  timer = setInterval(fetchData, 30000)  // 30s polling
})

onBeforeUnmount(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.dashboard { margin: -20px; padding: 20px; }
.stat-row { margin-bottom: 16px !important; }
.chart-row { margin-bottom: 16px !important; }
.alert-stat { padding: 8px 0; }
.alert-item { display: flex; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.alert-item:last-child { border-bottom: none; }
.alert-dot { width: 10px; height: 10px; border-radius: 50%; }
.alert-dot.critical { background: #f56c6c; }
.alert-dot.warning { background: #e6a23c; }
.alert-dot.info { background: #909399; }
.alert-count { margin-left: auto; font-weight: bold; }
.diagnostic-card { cursor: pointer; }
.diagnostic-card:hover { transform: translateY(-2px); transition: 0.3s; }
.diag-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.diag-name { font-weight: bold; font-size: 14px; }
.diag-body { display: flex; gap: 16px; margin-bottom: 8px; }
.risk-gauge { text-align: center; min-width: 60px; }
.risk-value { font-size: 28px; font-weight: bold; display: block; }
.risk-label { font-size: 11px; color: #909399; }
.diag-metrics { flex: 1; font-size: 12px; color: #606266; }
.diag-metrics p { margin: 4px 0; }
.diag-suggestion { font-size: 12px; color: #909399; line-height: 1.5; border-top: 1px solid #f0f0f0; padding-top: 8px; }
</style>
