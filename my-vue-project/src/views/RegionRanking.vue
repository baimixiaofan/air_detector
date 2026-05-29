<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let myChart = null

// 模拟各个区域的 PM2.5 平均浓度数据（从高到低排序）
const rankData = [
  { name: '大兴区', value: 65 },
  { name: '通州区', value: 58 },
  { name: '丰台区', value: 52 },
  { name: '朝阳区', value: 45 },
  { name: '顺义区', value: 40 },
  { name: '海淀区', value: 35 },
  { name: '东城区', value: 30 },
  { name: '西城区', value: 28 },
  { name: '密云区', value: 22 },
  { name: '怀柔区', value: 18 },
]

const initChart = () => {
  if (!chartRef.value) return
  myChart = echarts.init(chartRef.value)

  // 提取 X 轴和 Y 轴的数据，因为 ECharts 横向柱状图的数据是从下往上画的，所以要把数组反转一下
  const yAxisData = rankData.map((item) => item.name).reverse()
  const seriesData = rankData.map((item) => item.value).reverse()

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '3%',
      right: '8%',
      bottom: '3%',
      top: '2%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      name: 'PM2.5 (μg/m³)',
      splitLine: { lineStyle: { type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: yAxisData,
      axisLabel: { fontWeight: 'bold' },
    },
    series: [
      {
        name: 'PM2.5 浓度',
        type: 'bar',
        barWidth: '60%', // 柱子的宽度
        data: seriesData,
        // 给柱子加上好看的渐变色和圆角
        itemStyle: {
          borderRadius: [0, 5, 5, 0], // 右侧圆角
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' },
          ]),
        },
        // 在柱子右侧显示具体的数值
        label: {
          show: true,
          position: 'right',
          valueAnimation: true, // 数值变化时有动画
        },
      },
    ],
  }

  myChart.setOption(option)
}

const handleResize = () => {
  if (myChart) myChart.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (myChart) myChart.dispose()
})
</script>

<template>
  <div class="ranking-container">
    <el-card shadow="never" class="ranking-card">
      <template #header>
        <div class="card-header">
          <span>🏆 北京市各区 PM2.5 浓度排行（实时）</span>
          <el-tag type="info">数据更新时间: 刚刚</el-tag>
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

/* 必须给 ECharts 容器一个明确的高度 */
.chart-box {
  width: 100%;
  flex: 1; /* 让图表占满卡片剩余空间 */
  min-height: 500px;
}
</style>
