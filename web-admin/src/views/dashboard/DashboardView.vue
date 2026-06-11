<template>
  <div class="dashboard">
    <!-- Hero Section - 数据价值主张 -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          <span>实时监测中</span>
        </div>
        <h1 class="hero-title">
          <span class="title-gradient">智能空气分析</span>
          <br />
          <span class="title-sub">让数据创造价值</span>
        </h1>
        <p class="hero-desc">
          通过 AI 深度分析家庭空气质量数据，为您生成个性化的健康建议、
          环境优化方案和商业洞察报告
        </p>
      </div>
      <div class="hero-visual">
        <div class="air-orb">
          <div class="orb-ring orb-ring-1"></div>
          <div class="orb-ring orb-ring-2"></div>
          <div class="orb-ring orb-ring-3"></div>
          <div class="orb-core">
            <span class="orb-value">{{ currentAQI }}</span>
            <span class="orb-label">AQI</span>
          </div>
        </div>
      </div>
    </section>

    <!-- KPI Cards - 核心指标 -->
    <section class="kpi-section">
      <div class="section-header">
        <h2>核心指标</h2>
        <span class="section-badge">实时更新</span>
      </div>
      <div class="kpi-grid">
        <div class="kpi-card" v-for="kpi in kpiData" :key="kpi.id">
          <div class="kpi-icon" :style="{ background: kpi.gradient }">
            <span class="icon-emoji">{{ kpi.icon }}</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ kpi.value }}</span>
            <span class="kpi-label">{{ kpi.label }}</span>
          </div>
          <div class="kpi-trend" :class="kpi.trend > 0 ? 'trend-up' : 'trend-down'">
            <span class="trend-arrow">{{ kpi.trend > 0 ? '↑' : '↓' }}</span>
            <span class="trend-value">{{ Math.abs(kpi.trend) }}%</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 数据价值分析 -->
    <section class="insights-section">
      <div class="section-header">
        <h2>数据价值洞察</h2>
        <span class="section-badge">AI 驱动</span>
      </div>
      <div class="insights-grid">
        <!-- 健康评分 -->
        <div class="insight-card health-card">
          <div class="card-header">
            <div class="card-icon health-icon">❤️</div>
            <div class="card-title">
              <h3>健康评分</h3>
              <p>基于空气质量的健康指数</p>
            </div>
          </div>
          <div class="health-score">
            <div class="score-ring">
              <svg viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="8" />
                <circle cx="50" cy="50" r="45" fill="none" stroke="url(#healthGradient)" stroke-width="8"
                  stroke-linecap="round" :stroke-dasharray="healthScoreDash" />
              </svg>
              <div class="score-value">{{ healthScore }}</div>
            </div>
            <div class="health-metrics">
              <div class="metric-item" v-for="metric in healthMetrics" :key="metric.label">
                <span class="metric-dot" :style="{ background: metric.color }"></span>
                <span class="metric-label">{{ metric.label }}</span>
                <span class="metric-value">{{ metric.value }}</span>
              </div>
            </div>
          </div>
          <div class="card-footer">
            <span class="insight-tag">健康建议</span>
            <span class="insight-text">{{ healthInsight }}</span>
          </div>
        </div>

        <!-- 环境优化建议 -->
        <div class="insight-card optimize-card">
          <div class="card-header">
            <div class="card-icon optimize-icon">🌿</div>
            <div class="card-title">
              <h3>环境优化</h3>
              <p>智能改善建议</p>
            </div>
          </div>
          <div class="optimize-list">
            <div class="optimize-item" v-for="(item, index) in optimizeSuggestions" :key="index">
              <div class="item-number">{{ index + 1 }}</div>
              <div class="item-content">
                <h4>{{ item.title }}</h4>
                <p>{{ item.desc }}</p>
              </div>
              <div class="item-impact" :class="'impact-' + item.level">
                {{ item.level === 'high' ? '高' : item.level === 'medium' ? '中' : '低' }}
              </div>
            </div>
          </div>
        </div>

        <!-- 商业价值洞察 -->
        <div class="insight-card business-card">
          <div class="card-header">
            <div class="card-icon business-icon">📊</div>
            <div class="card-title">
              <h3>商业洞察</h3>
              <p>数据驱动的价值发现</p>
            </div>
          </div>
          <div class="business-metrics">
            <div class="biz-metric" v-for="biz in businessMetrics" :key="biz.label">
              <div class="biz-icon">{{ biz.icon }}</div>
              <div class="biz-content">
                <span class="biz-value">{{ biz.value }}</span>
                <span class="biz-label">{{ biz.label }}</span>
              </div>
              <div class="biz-trend" :class="biz.trend > 0 ? 'trend-up' : 'trend-down'">
                {{ biz.trend > 0 ? '+' : '' }}{{ biz.trend }}%
              </div>
            </div>
          </div>
          <div class="card-footer">
            <span class="insight-tag">机会识别</span>
            <span class="insight-text">{{ businessInsight }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 24小时趋势 -->
    <section class="trend-section">
      <div class="section-header">
        <h2>24小时趋势</h2>
        <div class="trend-tabs">
          <button v-for="tab in trendTabs" :key="tab.key"
            :class="['tab-btn', { active: activeTrendTab === tab.key }]"
            @click="activeTrendTab = tab.key">
            {{ tab.label }}
          </button>
        </div>
      </div>
      <div class="trend-chart-container">
        <div class="chart-header">
          <div class="chart-legend">
            <span class="legend-item" v-for="legend in chartLegends" :key="legend.label">
              <span class="legend-dot" :style="{ background: legend.color }"></span>
              {{ legend.label }}
            </span>
          </div>
          <div class="chart-stats">
            <span class="stat-item">
              <span class="stat-label">平均</span>
              <span class="stat-value">{{ trendAvg }}</span>
            </span>
            <span class="stat-item">
              <span class="stat-label">最高</span>
              <span class="stat-value">{{ trendMax }}</span>
            </span>
            <span class="stat-item">
              <span class="stat-label">最低</span>
              <span class="stat-value">{{ trendMin }}</span>
            </span>
          </div>
        </div>
        <TrendChart :data="trendData" :height="300" />
      </div>
    </section>

    <!-- 设备状态 -->
    <section class="devices-section">
      <div class="section-header">
        <h2>设备状态</h2>
        <span class="section-badge">{{ onlineDevices }}/{{ totalDevices }} 在线</span>
      </div>
      <div class="devices-grid">
        <div class="device-card" v-for="device in deviceStatusList" :key="device.id"
          :class="{ 'device-online': device.online, 'device-offline': !device.online }">
          <div class="device-header">
            <div class="device-status-dot" :class="device.online ? 'dot-online' : 'dot-offline'"></div>
            <span class="device-name">{{ device.name }}</span>
          </div>
          <div class="device-metrics">
            <div class="device-aqi" :style="{ color: aqiLevel(device.aqi).color }">
              <span class="aqi-value">{{ device.aqi }}</span>
              <span class="aqi-label">AQI</span>
            </div>
            <div class="device-pollutants">
              <span class="pollutant" v-for="(val, key) in device.pollutants" :key="key">
                <span class="pollutant-name">{{ key }}</span>
                <span class="pollutant-value">{{ val }}</span>
              </span>
            </div>
          </div>
          <div class="device-footer">
            <span class="device-location">{{ device.location }}</span>
            <span class="device-update">{{ device.lastUpdate }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 智能诊断 -->
    <section class="diagnostics-section">
      <div class="section-header">
        <h2>智能诊断</h2>
        <span class="section-badge">AI 增强</span>
      </div>
      <div class="diagnostics-grid">
        <div class="diagnostic-card" v-for="d in diagnostics" :key="d.site_id">
          <div class="diag-header">
            <div class="diag-site">
              <h3>{{ d.site_name }}</h3>
              <el-tag :type="d.health_color" size="small" effect="dark">{{ d.health_label }}</el-tag>
            </div>
            <div class="diag-score" :style="{ color: riskColor(d.risk_score) }">
              <span class="score-num">{{ d.risk_score }}</span>
              <span class="score-label">风险分</span>
            </div>
          </div>
          <div class="diag-body">
            <div class="diag-metrics">
              <div class="diag-metric">
                <span class="metric-label">AQI 均值</span>
                <span class="metric-value">{{ d.avg_aqi }}</span>
              </div>
              <div class="diag-metric">
                <span class="metric-label">超标天数</span>
                <span class="metric-value">{{ d.exceed_days }}天</span>
              </div>
              <div class="diag-metric" v-if="d.primary_pollutant">
                <span class="metric-label">主要污染物</span>
                <span class="metric-value">{{ d.primary_pollutant }}</span>
              </div>
            </div>
          </div>
          <div class="diag-footer">
            <div class="diag-suggestion">
              <span class="suggestion-icon">💡</span>
              <span class="suggestion-text">{{ d.suggestion }}</span>
            </div>
          </div>
        </div>
        <el-empty v-if="!diagnostics.length" description="暂无诊断数据" />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getDashboardStats, getDashboardTrend, getAlertSummary, getDiagnostics, getDashboardRealtime } from '@/api/dashboard'
import TrendChart from '@/components/charts/TrendChart.vue'
import { aqiLevel as aqiLevelFn, riskColor as riskColorFn } from '@/utils/format'

// ===== 数据 =====
const stats = ref({ total_sites: 0, total_devices: 0, online_devices: 0, offline_devices: 0, pending_alerts: 0 })
const trendData = ref([])
const diagnostics = ref([])
const deviceStatusList = ref([])
const pollutantData = ref([])
const activeTrendTab = ref('aqi')

// ===== 计算属性 =====
const currentAQI = computed(() => {
  if (deviceStatusList.value.length) {
    const avg = deviceStatusList.value.reduce((sum, d) => sum + (d.aqi || 0), 0) / deviceStatusList.value.length
    return Math.round(avg)
  }
  return 42 // 默认值
})

const healthScore = computed(() => {
  const aqi = currentAQI.value
  if (aqi <= 50) return 95
  if (aqi <= 100) return 80
  if (aqi <= 150) return 60
  if (aqi <= 200) return 40
  return 20
})

const healthScoreDash = computed(() => {
  const circumference = 2 * Math.PI * 45
  return `${(healthScore.value / 100) * circumference} ${circumference}`
})

const healthMetrics = computed(() => [
  { label: 'PM2.5', value: pollutantData.value.find(p => p.name === 'PM2.5')?.value || 0, color: '#007AFF' },
  { label: 'PM10', value: pollutantData.value.find(p => p.name === 'PM10')?.value || 0, color: '#5856D6' },
  { label: 'NO₂', value: pollutantData.value.find(p => p.name === 'NO₂')?.value || 0, color: '#30D158' },
  { label: 'O₃', value: pollutantData.value.find(p => p.name === 'O₃')?.value || 0, color: '#FFD60A' }
])

const healthInsight = computed(() => {
  const score = healthScore.value
  if (score >= 90) return '空气质量优秀，适合户外活动'
  if (score >= 70) return '空气质量良好，敏感人群注意'
  if (score >= 50) return '轻度污染，建议减少户外运动'
  return '空气质量较差，建议开启净化器'
})

const optimizeSuggestions = ref([
  { title: '开启新风系统', desc: '当前PM2.5偏高，建议开启新风系统改善室内空气质量', level: 'high' },
  { title: '增加绿植', desc: '在客厅和卧室增加绿植，可有效吸收有害气体', level: 'medium' },
  { title: '定时通风', desc: '建议每天上午10点和下午3点各通风15分钟', level: 'low' },
  { title: '使用空气净化器', desc: '卧室建议使用HEPA滤网空气净化器', level: 'high' }
])

const businessMetrics = ref([
  { icon: '📈', label: '数据价值评分', value: '87分', trend: 12 },
  { icon: '🎯', label: '用户健康指数', value: '92%', trend: 8 },
  { icon: '💰', label: '节能潜力', value: '¥156/月', trend: -5 },
  { icon: '🏠', label: '房产增值', value: '+2.3%', trend: 15 }
])

const businessInsight = ref('基于您家的空气质量数据，我们识别到3个商业机会...')

const trendTabs = [
  { key: 'aqi', label: 'AQI' },
  { key: 'pm25', label: 'PM2.5' },
  { key: 'temp', label: '温度' },
  { key: 'humidity', label: '湿度' }
]

const chartLegends = [
  { label: 'AQI', color: '#007AFF' },
  { label: 'PM2.5', color: '#5856D6' },
  { label: '温度', color: '#30D158' }
]

const trendAvg = computed(() => {
  if (!trendData.value.length) return '--'
  const avg = trendData.value.reduce((sum, d) => sum + (d.aqi || 0), 0) / trendData.value.length
  return Math.round(avg)
})

const trendMax = computed(() => {
  if (!trendData.value.length) return '--'
  return Math.max(...trendData.value.map(d => d.aqi || 0))
})

const trendMin = computed(() => {
  if (!trendData.value.length) return '--'
  return Math.min(...trendData.value.map(d => d.aqi || 0))
})

const onlineDevices = computed(() => deviceStatusList.value.filter(d => d.online).length)
const totalDevices = computed(() => deviceStatusList.value.length)

// ===== 方法 =====
function aqiLevel(aqi) {
  return aqiLevelFn(aqi)
}

function riskColor(score) {
  return riskColorFn(score)
}

// ===== 数据获取 =====
let timer = null

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
    if (d.code === 200) diagnostics.value = d.data

    // 实时数据（后端直接返回数组，不是 {devices: [...]} 包装）
    const rt = await getDashboardRealtime()
    if (rt.code === 200 && Array.isArray(rt.data)) {
      const devices = rt.data
      deviceStatusList.value = devices.slice(0, 8).map(dev => ({
        id: dev.device_id,
        name: dev.location
          ? `${dev.location.province || ''} ${dev.location.district || ''}`.trim() || dev.device_id
          : dev.user_info?.name || dev.device_id,
        online: true,
        aqi: dev.aqi || 0,
        pollutants: {
          'PM2.5': dev.pm25 || 0,
          'NO₂': dev.no2 || 0,
          'SO₂': dev.so2 || 0,
          'O₃': dev.o3 || 0
        },
        location: dev.location
          ? `${dev.location.city || ''} ${dev.location.district || ''}`.trim()
          : '未知位置',
        lastUpdate: dev.timestamp || '刚刚'
      }))

      if (devices.length) {
        pollutantData.value = [
          { name: 'PM2.5', value: Math.round(devices.reduce((s, d) => s + (d.pm25 || 0), 0) / devices.length) },
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
.dashboard {
  min-height: 100vh;
  padding: 24px;
  background: var(--page-bg);
}

/* ===== Hero Section ===== */
.hero-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 60px 40px;
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.1), rgba(88, 86, 214, 0.1));
  border-radius: var(--radius-xl);
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(0, 122, 255, 0.05) 0%, transparent 50%);
  animation: float 6s ease-in-out infinite;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 600px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(48, 209, 88, 0.15);
  border-radius: 20px;
  margin-bottom: 24px;
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
  animation: pulse 2s ease-in-out infinite;
}

.hero-badge span:last-child {
  font-size: var(--font-size-body);
  color: var(--color-success);
  font-weight: 500;
}

.hero-title {
  margin-bottom: 20px;
}

.title-gradient {
  font-size: 48px;
  font-weight: 700;
  background: linear-gradient(135deg, #007AFF, #5856D6, #FF6B9D);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient-shift 4s ease infinite;
}

.title-sub {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  opacity: 0.9;
}

.hero-desc {
  font-size: var(--font-size-body);
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 32px;
}

.hero-visual {
  position: relative;
  z-index: 1;
}

.air-orb {
  position: relative;
  width: 200px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.orb-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid;
  animation: float 6s ease-in-out infinite;
}

.orb-ring-1 {
  width: 200px;
  height: 200px;
  border-color: rgba(0, 122, 255, 0.2);
  animation-delay: 0s;
}

.orb-ring-2 {
  width: 160px;
  height: 160px;
  border-color: rgba(88, 86, 214, 0.2);
  animation-delay: -2s;
}

.orb-ring-3 {
  width: 120px;
  height: 120px;
  border-color: rgba(255, 107, 157, 0.2);
  animation-delay: -4s;
}

.orb-core {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  border-radius: 50%;
  box-shadow: 0 0 40px rgba(0, 122, 255, 0.4);
}

.orb-value {
  font-size: 36px;
  font-weight: 700;
  color: white;
  line-height: 1;
}

.orb-label {
  font-size: var(--font-size-caption);
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

/* ===== KPI Section ===== */
.kpi-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: var(--font-size-h2);
  font-weight: 600;
  color: var(--text-primary);
}

.section-badge {
  padding: 4px 12px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  backdrop-filter: var(--glass-blur);
  transition: all var(--transition-normal);
}

.kpi-card:hover {
  background: var(--card-hover-bg);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.kpi-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-emoji {
  font-size: 24px;
}

.kpi-content {
  flex: 1;
}

.kpi-value {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}

.kpi-label {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
}

.kpi-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: var(--font-size-caption);
  font-weight: 500;
}

.trend-up {
  background: rgba(48, 209, 88, 0.15);
  color: var(--color-success);
}

.trend-down {
  background: rgba(255, 69, 58, 0.15);
  color: var(--color-danger);
}

.trend-arrow {
  font-size: 12px;
}

/* ===== Insights Section ===== */
.insights-section {
  margin-bottom: 32px;
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}

.insight-card {
  padding: 28px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  backdrop-filter: var(--glass-blur);
  transition: all var(--transition-normal);
}

.insight-card:hover {
  background: var(--card-hover-bg);
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.health-icon {
  background: rgba(255, 69, 58, 0.15);
}

.optimize-icon {
  background: rgba(48, 209, 88, 0.15);
}

.business-icon {
  background: rgba(0, 122, 255, 0.15);
}

.card-title h3 {
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.card-title p {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
}

/* Health Card */
.health-score {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
}

.score-ring {
  position: relative;
  width: 120px;
  height: 120px;
}

.score-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-ring circle:last-child {
  transition: stroke-dasharray 0.6s ease;
}

.score-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.health-metrics {
  flex: 1;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
}

.metric-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.metric-label {
  flex: 1;
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
}

.metric-value {
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--text-primary);
}

.card-footer {
  padding-top: 20px;
  border-top: 1px solid var(--glass-border);
}

.insight-tag {
  display: inline-block;
  padding: 4px 10px;
  background: var(--color-primary-light);
  border-radius: 8px;
  font-size: var(--font-size-caption);
  color: var(--color-primary);
  margin-bottom: 8px;
}

.insight-text {
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Optimize Card */
.optimize-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.optimize-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.optimize-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.item-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-caption);
  font-weight: 600;
  color: var(--color-primary);
}

.item-content {
  flex: 1;
}

.item-content h4 {
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.item-content p {
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
  line-height: 1.5;
}

.item-impact {
  padding: 4px 10px;
  border-radius: 8px;
  font-size: var(--font-size-caption);
  font-weight: 500;
}

.impact-high {
  background: rgba(255, 69, 58, 0.15);
  color: var(--color-danger);
}

.impact-medium {
  background: rgba(255, 214, 10, 0.15);
  color: var(--color-warning);
}

.impact-low {
  background: rgba(48, 209, 88, 0.15);
  color: var(--color-success);
}

/* Business Card */
.business-metrics {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.biz-metric {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-md);
}

.biz-icon {
  font-size: 24px;
}

.biz-content {
  flex: 1;
}

.biz-value {
  display: block;
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--text-primary);
}

.biz-label {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
}

.biz-trend {
  font-size: var(--font-size-body);
  font-weight: 600;
}

/* ===== Trend Section ===== */
.trend-section {
  margin-bottom: 32px;
}

.trend-tabs {
  display: flex;
  gap: 8px;
}

.tab-btn {
  padding: 8px 16px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  background: var(--glass-hover-bg);
}

.tab-btn.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.trend-chart-container {
  padding: 28px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  backdrop-filter: var(--glass-blur);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.chart-legend {
  display: flex;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.chart-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
}

.stat-value {
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--text-primary);
}

/* ===== Devices Section ===== */
.devices-section {
  margin-bottom: 32px;
}

.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.device-card {
  padding: 24px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  backdrop-filter: var(--glass-blur);
  transition: all var(--transition-normal);
}

.device-card:hover {
  background: var(--card-hover-bg);
  transform: translateY(-2px);
}

.device-online {
  border-left: 3px solid var(--color-success);
}

.device-offline {
  border-left: 3px solid var(--text-muted);
}

.device-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.device-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-online {
  background: var(--color-success);
  box-shadow: 0 0 8px rgba(48, 209, 88, 0.5);
}

.dot-offline {
  background: var(--text-muted);
}

.device-name {
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--text-primary);
}

.device-metrics {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.device-aqi {
  text-align: center;
}

.aqi-value {
  display: block;
  font-size: 36px;
  font-weight: 700;
  line-height: 1.1;
}

.aqi-label {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
}

.device-pollutants {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pollutant {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pollutant-name {
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
}

.pollutant-value {
  font-size: var(--font-size-body);
  font-weight: 500;
  color: var(--text-primary);
}

.device-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid var(--glass-border);
}

.device-location {
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
}

.device-update {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
}

/* ===== Diagnostics Section ===== */
.diagnostics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.diagnostic-card {
  padding: 28px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  backdrop-filter: var(--glass-blur);
  transition: all var(--transition-normal);
}

.diagnostic-card:hover {
  background: var(--card-hover-bg);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.diag-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.diag-site h3 {
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.diag-score {
  text-align: center;
}

.score-num {
  display: block;
  font-size: 32px;
  font-weight: 700;
  line-height: 1.1;
}

.score-label {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
}

.diag-body {
  margin-bottom: 20px;
}

.diag-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.diag-metric {
  text-align: center;
}

.metric-label {
  display: block;
  font-size: var(--font-size-caption);
  color: var(--text-muted);
  margin-bottom: 4px;
}

.metric-value {
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--text-primary);
}

.diag-footer {
  padding-top: 20px;
  border-top: 1px solid var(--glass-border);
}

.diag-suggestion {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.suggestion-icon {
  font-size: 16px;
}

.suggestion-text {
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
  line-height: 1.6;
}

/* ===== Responsive ===== */
@media (max-width: 1200px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
    padding: 40px 24px;
  }

  .title-gradient {
    font-size: 36px;
  }

  .title-sub {
    font-size: 24px;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 16px;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .insights-grid {
    grid-template-columns: 1fr;
  }

  .devices-grid {
    grid-template-columns: 1fr;
  }

  .diagnostics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
