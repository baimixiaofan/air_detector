<template>
  <div ref="chartRef" class="bar-chart"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  xKey: { type: String, default: 'name' },
  series: {
    type: Array,
    default: () => [{ name: '数值', key: 'value', color: '#e17055' }]
  },
  horizontal: { type: Boolean, default: false },
  stacked: { type: Boolean, default: false }
})

const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chartRef.value || !props.data.length) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const xAxisData = props.data.map(d => d[props.xKey])
  const seriesData = props.series.map(s => ({
    name: s.name,
    type: 'bar',
    data: props.data.map(d => d[s.key]),
    itemStyle: {
      color: s.color || '#e17055',
      borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]
    },
    barMaxWidth: 40,
    stack: props.stacked ? 'total' : undefined
  }))

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: props.series.length > 1 ? { top: 0, textStyle: { fontSize: 12 } } : undefined,
    grid: {
      left: props.horizontal ? 80 : 12,
      right: 16,
      top: props.series.length > 1 ? 36 : 12,
      bottom: props.horizontal ? 12 : 36,
      containLabel: !props.horizontal
    },
    xAxis: props.horizontal ? {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f2f5' } },
      axisLabel: { fontSize: 11, color: '#636e72' }
    } : {
      type: 'category',
      data: xAxisData,
      axisLabel: { fontSize: 11, color: '#636e72', rotate: xAxisData.length > 8 ? 30 : 0 },
      axisLine: { lineStyle: { color: '#f0f2f5' } },
      axisTick: { show: false }
    },
    yAxis: props.horizontal ? {
      type: 'category',
      data: xAxisData,
      axisLabel: { fontSize: 11, color: '#636e72' },
      axisLine: { show: false },
      axisTick: { show: false }
    } : {
      type: 'value',
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f2f5' } },
      axisLabel: { fontSize: 11, color: '#636e72' }
    },
    series: props.horizontal ? seriesData.map(s => ({ ...s, data: props.data.map(d => d[s.key]) })) : seriesData
  }

  chart.setOption(option, true)
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
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
.bar-chart {
  width: 100%;
  height: 100%;
  min-height: 200px;
}
</style>
