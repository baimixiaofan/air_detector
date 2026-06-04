<template>
  <div ref="chartRef" class="sparkline"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  color: { type: String, default: '#e17055' },
  height: { type: Number, default: 30 }
})

const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chartRef.value || !props.data.length) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const option = {
    grid: { left: 0, right: 0, top: 0, bottom: 0 },
    xAxis: { type: 'category', show: false, data: props.data.map((_, i) => i) },
    yAxis: { type: 'value', show: false },
    series: [{
      type: 'line',
      data: props.data,
      smooth: true,
      symbol: 'none',
      lineStyle: { color: props.color, width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: props.color + '40' },
          { offset: 1, color: props.color + '05' }
        ])
      }
    }]
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

watch(() => props.data, renderChart, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.sparkline {
  width: 100%;
}
</style>
