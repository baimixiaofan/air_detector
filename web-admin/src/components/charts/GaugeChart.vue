<template>
  <div ref="chartRef" class="gauge-chart"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  value: { type: Number, default: 0 },
  max: { type: Number, default: 300 },
  title: { type: String, default: 'AQI' },
  thresholds: {
    type: Array,
    default: () => [
      { value: 50, color: '#00b894' },
      { value: 100, color: '#fdcb6e' },
      { value: 150, color: '#e17055' },
      { value: 200, color: '#d63031' },
      { value: 300, color: '#8f3f97' }
    ]
  }
})

const chartRef = ref(null)
let chart = null

function getColor(value) {
  for (const t of props.thresholds) {
    if (value <= t.value) return t.color
  }
  return props.thresholds[props.thresholds.length - 1].color
}

function renderChart() {
  if (!chartRef.value) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const color = getColor(props.value)

  const option = {
    series: [{
      type: 'gauge',
      startAngle: 220,
      endAngle: -40,
      min: 0,
      max: props.max,
      splitNumber: 6,
      pointer: { show: false },
      progress: {
        show: true,
        width: 14,
        roundCap: true,
        itemStyle: { color }
      },
      axisLine: {
        lineStyle: {
          width: 14,
          color: [[1, '#f0f2f5']]
        },
        roundCap: true
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        valueAnimation: true,
        fontSize: 28,
        fontWeight: 'bold',
        color,
        offsetCenter: [0, '10%'],
        formatter: '{value}'
      },
      title: {
        show: true,
        offsetCenter: [0, '45%'],
        fontSize: 13,
        color: '#636e72'
      },
      data: [{ value: props.value, name: props.title }]
    }]
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

watch(() => [props.value, props.max], renderChart)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.gauge-chart {
  width: 100%;
  height: 100%;
  min-height: 150px;
}
</style>
