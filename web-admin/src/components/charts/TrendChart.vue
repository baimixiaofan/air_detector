<template>
  <div ref="chartRef" style="width: 100%; height: 300px"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  series: { type: Array, default: () => [
    { name: 'AQI', key: 'avg_aqi', color: '#e74c3c' },
    { name: 'PM2.5', key: 'avg_pm25', color: '#f39c12' }
  ]},
  xKey: { type: String, default: 'hour' }
})

const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: props.series.map(s => s.name), top: 0 },
    grid: { left: 50, right: 20, bottom: 30, top: 40 },
    xAxis: {
      type: 'category',
      data: props.data.map(d => d[props.xKey]),
      axisLabel: { fontSize: 11 }
    },
    yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed' } } },
    series: props.series.map(s => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: props.data.map(d => d[s.key]),
      itemStyle: { color: s.color },
      areaStyle: { color: s.color + '22' }
    }))
  }
  chart.setOption(option, true)
}

onMounted(() => {
  renderChart()
  window.addEventListener('resize', () => chart?.resize())
})

watch(() => props.data, renderChart, { deep: true })

onBeforeUnmount(() => {
  chart?.dispose()
})
</script>
