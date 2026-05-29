<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let myChart = null
// 用来控制图表右上角的切换按钮
const timeRange = ref('today')

// 💡 图表高级化配置核心
const initChart = () => {
  if (!chartRef.value) return
  myChart = echarts.init(chartRef.value, 'dark')

  const option = {
    // 💡 2. 在 option 的最开头，加上背景透明属性
    backgroundColor: 'transparent',
    // 高级 Tooltip (毛玻璃悬浮框)
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
    legend: {
      data: ['PM2.5', 'PM10', '温度'],
      top: 0,
      icon: 'circle',
      itemGap: 24,
      textStyle: { color: '#64748b' },
    },
    grid: { left: '2%', right: '2%', bottom: '2%', containLabel: true, top: '50px' },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: [
        '00:00',
        '02:00',
        '04:00',
        '06:00',
        '08:00',
        '10:00',
        '12:00',
        '14:00',
        '16:00',
        '18:00',
        '20:00',
        '22:00',
      ],
      axisLine: { show: false }, // 隐藏 X 轴黑线
      axisTick: { show: false }, // 隐藏刻度
      axisLabel: { color: '#94a3b8', margin: 16 },
    },
    yAxis: [
      {
        type: 'value',
        name: '浓度 (μg/m³)',
        nameTextStyle: { color: '#94a3b8', padding: [0, 0, 0, 20] },
        splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }, // 极其微弱的虚线网格
        axisLabel: { color: '#94a3b8' },
      },
      {
        type: 'value',
        name: '温度 (℃)',
        nameTextStyle: { color: '#94a3b8' },
        splitLine: { show: false },
        axisLabel: { color: '#94a3b8' },
      },
    ],
    series: [
      {
        name: 'PM2.5',
        type: 'line',
        smooth: true, // 极其丝滑的曲线
        showSymbol: false, // 平时隐藏折线点，鼠标放上去才显示
        lineStyle: {
          width: 4,
          color: '#3b82f6',
          shadowColor: 'rgba(59, 130, 246, 0.3)',
          shadowBlur: 10,
        },
        itemStyle: { color: '#3b82f6' },
        // 💡 核心魔法：渐变面积填充
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.4)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.0)' },
          ]),
        },
        data: [35, 32, 28, 30, 45, 55, 60, 50, 42, 38, 36, 33],
      },
      {
        name: 'PM10',
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
        data: [50, 48, 45, 47, 65, 80, 85, 75, 60, 55, 50, 48],
      },
      {
        name: '温度',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 4,
          color: '#10b981',
          shadowColor: 'rgba(16, 185, 129, 0.3)',
          shadowBlur: 10,
        },
        itemStyle: { color: '#10b981' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.4)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.0)' },
          ]),
        },
        data: [15, 14, 13, 14, 16, 20, 24, 25, 22, 19, 17, 16],
      },
    ],
  }

  myChart.setOption(option)
}

onMounted(() => {
  initChart()
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
          <div class="card-value gradient-blue">128<span class="unit">个</span></div>
          <div class="card-trend">较上月新增 <span class="trend-badge up">↑ 12%</span></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="data-card">
          <div class="card-watermark">⚙️</div>
          <div class="card-title">接入设备总数</div>
          <div class="card-value gradient-green">3,240<span class="unit">台</span></div>
          <div class="card-trend">全部网格化部署完毕</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="data-card">
          <div class="card-watermark">⚡</div>
          <div class="card-title">设备实时在线</div>
          <div class="card-value gradient-orange">3,102<span class="unit">台</span></div>
          <div class="card-trend">当前在线率 <span class="trend-badge up">95.7%</span></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="data-card">
          <div class="card-watermark">⚠️</div>
          <div class="card-title">今日待处理告警</div>
          <div class="card-value gradient-red">5<span class="unit">条</span></div>
          <div class="card-trend">较昨日同期 <span class="trend-badge down">↓ 2条</span></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="chart-card">
      <template #header>
        <div class="chart-header">
          <span>📈 24 小时环境数据趋势概览</span>
          <el-radio-group v-model="timeRange" size="small">
            <el-radio-button label="today">今日实时</el-radio-button>
            <el-radio-button label="week">本周均值</el-radio-button>
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
