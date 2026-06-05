<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { getDashboardStats, getDashboardTrend } from '@/api/dashboard'

const chartRef = ref(null)
let myChart = null
const timeRange = ref('today')

const statsData = ref({
  total_sites: 0,
  total_devices: 0,
  online_devices: 0,
  pending_alerts: 0,
})

const fetchRealData = async () => {
  try {
    // 拉取顶部 4 个卡片的统计数据
    const statsRes = await getDashboardStats()
    statsData.value = statsRes

    // 拉取图表的 24 小时趋势数据
    const trendRes = await getDashboardTrend()

    const xData = trendRes.map((item) => item.hour.slice(-2) + ':00')
    const pm25Data = trendRes.map((item) => item.avg_pm25)
    const aqiData = trendRes.map((item) => item.avg_aqi)

    initChart(xData, pm25Data, aqiData)
  } catch (error) {
    console.error('获取看板数据失败', error)
    ElMessage.error('获取实时数据失败，请检查后端服务是否开启！')
  }
}

// 💡 4. 图表初始化函数（接收真实的 x轴、PM2.5 和 AQI 数据）
const initChart = (xData, pm25Data, aqiData) => {
  if (!chartRef.value) return
  if (!myChart) {
    // 如果还没初始化，就初始化一次
    myChart = echarts.init(chartRef.value)
  }

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      backdropFilter: 'blur(10px)',
      borderColor: 'transparent',
      padding: 16,
      borderRadius: 12,
      boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
      textStyle: { color: '#334155', fontWeight: 500 },
      axisPointer: { type: 'line', lineStyle: { color: '#cbd5e1', type: 'dashed' } },
    },
    // 把假数据的 PM10 和 温度 删掉，换成后端真实返回的 AQI 指数
    legend: {
      data: ['PM2.5 浓度', 'AQI 综合指数'],
      top: 0,
      icon: 'circle',
      itemGap: 24,
      textStyle: { color: '#64748b', fontWeight: 'bold' },
    },
    grid: { left: '2%', right: '2%', bottom: '2%', containLabel: true, top: '50px' },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData, // 💡 使用真实的 X 轴时间
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8', margin: 16 },
    },
    yAxis: [
      {
        type: 'value',
        name: '数值',
        nameTextStyle: { color: '#94a3b8', padding: [0, 0, 0, 20] },
        splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
        axisLabel: { color: '#94a3b8' },
      },
    ],
    series: [
      {
        name: 'PM2.5 浓度',
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 4,
          color: '#3b82f6',
          shadowColor: 'rgba(59, 130, 246, 0.3)',
          shadowBlur: 10,
        },
        itemStyle: { color: '#3b82f6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.4)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.0)' },
          ]),
        },
        data: pm25Data, // 💡 真实的 PM2.5 数据
      },
      {
        name: 'AQI 综合指数',
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 4,
          color: '#f59e0b',
          shadowColor: 'rgba(245, 158, 11, 0.3)',
          shadowBlur: 10,
        },
        itemStyle: { color: '#f59e0b' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(245, 158, 11, 0.4)' },
            { offset: 1, color: 'rgba(245, 158, 11, 0.0)' },
          ]),
        },
        data: aqiData, // 💡 真实的 AQI 数据
      },
    ],
  }

  // 使用 true 强制刷新图表数据
  myChart.setOption(option, true)
}

onMounted(() => {
  // 💡 页面一挂载，就去请求真数据
  fetchRealData()
  window.addEventListener('resize', () => myChart?.resize())
})

onUnmounted(() => {
  window.removeEventListener('resize', () => myChart?.resize())
  myChart?.dispose()
})
</script>

<template>
  <div class="dashboard-container">
    <el-row :gutter="20" class="top-cards">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="data-card">
          <div class="card-watermark">🌍</div>
          <div class="card-title">监控站点总数</div>
          <div class="card-value gradient-blue">
            {{ statsData.total_sites }}<span class="unit">个</span>
          </div>
          <div class="card-trend">较上月新增 <span class="trend-badge up">↑ 12%</span></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="data-card">
          <div class="card-watermark">⚙️</div>
          <div class="card-title">接入设备总数</div>
          <div class="card-value gradient-green">
            {{ statsData.total_devices }}<span class="unit">台</span>
          </div>
          <div class="card-trend">数据库直连同步中...</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="data-card">
          <div class="card-watermark">⚡</div>
          <div class="card-title">设备实时在线</div>
          <div class="card-value gradient-orange">
            {{ statsData.online_devices }}<span class="unit">台</span>
          </div>
          <div class="card-trend">
            当前在线率
            <span class="trend-badge up"
              >{{
                statsData.total_devices
                  ? Math.round((statsData.online_devices / statsData.total_devices) * 100)
                  : 0
              }}%</span
            >
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="data-card">
          <div class="card-watermark">⚠️</div>
          <div class="card-title">未处理告警</div>
          <div class="card-value gradient-red">
            {{ statsData.pending_alerts }}<span class="unit">条</span>
          </div>
          <div class="card-trend" v-if="statsData.pending_alerts > 0">
            需要立即派单 <span class="trend-badge down">加急</span>
          </div>
          <div class="card-trend" v-else>
            当前系统运行平稳 <span class="trend-badge up">正常</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="chart-card">
      <template #header>
        <div class="chart-header">
          <span>📈 24 小时真实环境数据趋势</span>
          <el-radio-group v-model="timeRange" size="small">
            <el-radio-button label="today">今日实时</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="chartRef" class="chart-box"></div>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard-container {
  padding-bottom: 20px;
}
.top-cards {
  margin-bottom: 24px;
}

/* 统一卡片风格：大圆角、无边框、平滑阴影 */
.data-card,
.chart-card {
  border-radius: 16px;
  border: none !important;
  background-color: #ffffff;
  position: relative;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.data-card:hover {
  transform: translateY(-5px);
  box-shadow:
    0 20px 25px -5px rgba(0, 0, 0, 0.1),
    0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
}

/* 右下角极其巨大的半透明水印图标 */
.card-watermark {
  position: absolute;
  right: -20px;
  bottom: -30px;
  font-size: 100px;
  opacity: 0.04;
  transform: rotate(-15deg);
  pointer-events: none;
}

.card-title {
  font-size: 14px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 12px;
}

.card-value {
  font-size: 40px;
  font-weight: 900;
  font-family: 'Arial', sans-serif;
  margin-bottom: 16px;
  line-height: 1;
}

.unit {
  font-size: 14px;
  margin-left: 6px;
  font-weight: normal;
  color: #94a3b8;
}

/* 🎨 核心魔法：让文字变成绝美的渐变色 */
.gradient-blue {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.gradient-green {
  background: linear-gradient(135deg, #10b981, #34d399);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.gradient-orange {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.gradient-red {
  background: linear-gradient(135deg, #ef4444, #f87171);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.card-trend {
  font-size: 13px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 8px;
}

.trend-badge {
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: bold;
}
.up {
  color: #10b981;
  background: rgba(16, 185, 129, 0.1);
}
.down {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #334155;
}

.chart-box {
  width: 100%;
  height: 420px;
}

/* 暗黑模式适配 */
html.dark .data-card,
html.dark .chart-card {
  background-color: #1e293b;
}
</style>
