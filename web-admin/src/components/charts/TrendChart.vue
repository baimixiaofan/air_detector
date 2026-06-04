<template>
  <div ref="chartRef" class="trend-chart"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  series: {
    type: Array,
    default: () => [
      { name: 'AQI', key: 'avg_aqi', color: '#e17055' },
      { name: 'PM2.5', key: 'avg_pm25', color: '#2d3436' }
    ]
  },
  xKey: { type: String, default: 'hour' },
  height: { type: Number, default: 300 }
})

const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chartRef.value || !props.data.length) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#f0f2f5',
      borderWidth: 1,
      textStyle: { color: '#2d3436', fontSize: 12 }
    },
    legend: {
      data: props.series.map(s => s.name),
      top: 0,
      textStyle: { fontSize: 12, color: '#636e72' },
      itemWidth: 12,
      itemHeight: 8
    },
    grid: {
      left: 12,
      right: 16,
      top: 36,
      bottom: 12,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: props.data.map(d => d[props.xKey]),
      axisLabel: { fontSize: 11, color: '#636e72' },
      axisLine: { lineStyle: { color: '#f0f2f5' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f2f5' } },
      axisLabel: { fontSize: 11, color: '#636e72' }
    },
    series: props.series.map(s => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: props.data.map(d => d[s.key]),
      itemStyle: { color: s.color },
      lineStyle: { width: 2.5 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: s.color + '30' },
          { offset: 1, color: s.color + '05' }
        ])
      },
      symbol: 'circle',
      symbolSize: 6
    }))
  }

  chart.setOption(option, true)
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  chartRef.value.style.height = props.height + 'px'
  renderChart()
  window.addEventListener('resize', handleResize)
})

watch(() => [props.data, props.series], renderChart, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.trend-chart {
  width: 100%;
}
</style>
