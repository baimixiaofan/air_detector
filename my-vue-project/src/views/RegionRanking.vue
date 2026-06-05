<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { getRankings } from '@/api/rankings'

const chartRef = ref(null)
let myChart = null
const loading = ref(false)
const rankings = ref([])

const fetchRankings = async () => {
  loading.value = true
  try {
    const res = await getRankings({ days: 7, limit: 20 })
    rankings.value = res || []
    updateChart()
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const updateChart = () => {
  if (!myChart || rankings.value.length === 0) return

  const sortedData = [...rankings.value].sort((a, b) => a.avg_aqi - b.avg_aqi)
  const yData = sortedData.map(item => item.device_id)
  const aqiData = sortedData.map(item => item.avg_aqi)
  const pm25Data = sortedData.map(item => item.avg_pm25)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: 'rgba(0, 162, 255, 0.3)',
      textStyle: { color: '#1e293b', fontWeight: 'bold' },
    },
    legend: {
      data: ['平均AQI', '平均PM2.5'],
      top: 0,
    },
    grid: { left: '2%', right: '6%', bottom: '2%', top: '40px', containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { type: 'dashed', color: 'rgba(0, 162, 255, 0.1)' } },
    },
    yAxis: {
      type: 'category',
      data: yData,
      axisLabel: { color: '#334155', fontWeight: 'bold', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(0, 162, 255, 0.2)' } },
      axisTick: { show: false },
    },
    series: [
      {
        name: '平均AQI',
        type: 'bar',
        data: aqiData,
        barWidth: '35%',
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#00a2ff' },
            { offset: 1, color: '#0055ff' },
          ]),
        },
        label: { show: true, position: 'right', color: '#00a2ff', fontWeight: 900 },
      },
      {
        name: '平均PM2.5',
        type: 'bar',
        data: pm25Data,
        barWidth: '35%',
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#faad14' },
            { offset: 1, color: '#d48806' },
          ]),
        },
        label: { show: true, position: 'right', color: '#faad14', fontWeight: 900 },
      },
    ],
    animationDurationUpdate: 800,
    animationEasingUpdate: 'cubicInOut',
  }

  myChart.setOption(option, true)
}

onMounted(() => {
  myChart = echarts.init(chartRef.value)
  fetchRankings()
  window.addEventListener('resize', () => myChart?.resize())
})

onUnmounted(() => {
  window.removeEventListener('resize', () => myChart?.resize())
  myChart?.dispose()
})
</script>

<template>
  <div class="ranking-container">
    <el-card shadow="never" class="ranking-card" v-loading="loading">
      <template #header>
        <div class="header-toolbar">
          <span class="title">🏆 设备 AQI 排行榜（近 7 天）</span>
        </div>
      </template>

      <div ref="chartRef" class="chart-box"></div>
    </el-card>
  </div>
</template>

<style scoped>
.ranking-container {
  padding-bottom: 20px;
}
.ranking-card {
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}
:deep(.el-card__body) {
  flex-grow: 1;
  padding: 20px;
}
.header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.title {
  font-size: 16px;
  font-weight: 900;
  color: #0088ff;
}
.chart-box {
  width: 100%;
  height: 100%;
  min-height: 500px;
}
</style>
