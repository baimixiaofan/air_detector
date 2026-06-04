<template>
  <div ref="chartRef" class="pie-chart"></div>
</template>

<script setup>
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  nameKey: { type: String, default: 'name' },
  valueKey: { type: String, default: 'value' },
  colors: {
    type: Array,
    default: () => ['#e17055', '#2d3436', '#74b9ff', '#00b894', '#fdcb6e', '#d63031']
  },
  innerRadius: { type: [String, Number], default: '50%' },
  showLabel: { type: Boolean, default: true }
})

const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chartRef.value || !props.data.length) return

  if (!chart) {
    chart = echarts.init(chartRef.value)
  }

  const total = props.data.reduce((sum, d) => sum + d[props.valueKey], 0)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    color: props.colors,
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'center',
      textStyle: { fontSize: 12, color: '#636e72' },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 12
    },
    graphic: props.innerRadius ? [{
      type: 'text',
      left: 'center',
      top: '45%',
      style: {
        text: total.toLocaleString(),
        textAlign: 'center',
        fill: '#2d3436',
        fontSize: 20,
        fontWeight: 'bold'
      }
    }] : undefined,
    series: [{
      type: 'pie',
      radius: [props.innerRadius ? String(props.innerRadius) : '0%', '70%'],
      center: ['40%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: props.showLabel ? {
        show: true,
        formatter: '{b}\n{d}%',
        fontSize: 11
      } : { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.15)' }
      },
      data: props.data.map(d => ({
        name: d[props.nameKey],
        value: d[props.valueKey]
      }))
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

watch(() => props.data, renderChart, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.pie-chart {
  width: 100%;
  height: 100%;
  min-height: 200px;
}
</style>
