<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let myChart = null

const initChart = () => {
  if (!chartRef.value) return
  myChart = echarts.init(chartRef.value, 'dark')

  const option = {
    // 💡 2. 加上透明背景
    backgroundColor: 'transparent',
    title: { text: '近七日 PM2.5 浓度多站对比趋势' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['奥体中心站', '万柳站', '天坛站'], top: '30px' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true, top: '80px' },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    },
    yAxis: { type: 'value', name: '浓度 (μg/m³)' },
    series: [
      { name: '奥体中心站', type: 'line', data: [32, 35, 45, 50, 48, 30, 28], smooth: true },
      { name: '万柳站', type: 'line', data: [85, 90, 110, 120, 95, 80, 75], smooth: true },
      { name: '天坛站', type: 'line', data: [40, 42, 38, 45, 55, 50, 42], smooth: true },
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
  <div class="compare-container">
    <el-card shadow="never" class="chart-card">
      <div ref="chartRef" class="chart-box"></div>
    </el-card>
  </div>
</template>

<style scoped>
.compare-container {
  padding-bottom: 20px;
}
.chart-card {
  height: calc(100vh - 120px);
}
.chart-box {
  width: 100%;
  height: 100%;
  min-height: 500px;
}
</style>
