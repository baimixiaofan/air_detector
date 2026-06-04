<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let myChart = null

// 💡 1. 当前选中的对比指标
const currentMetric = ref('pm25')

// 💡 2. 各个指标的专属配置字典（包含名称、单位、专属渐变色）
const metricsConfig = {
  pm25: { name: 'PM2.5', unit: 'μg/m³', color: ['#00a2ff', '#0055ff'] }, // 科技蓝
  pm10: { name: 'PM10', unit: 'μg/m³', color: ['#faad14', '#d48806'] }, // 预警橙
  aqi: { name: 'AQI 指数', unit: '', color: ['#ff4d4f', '#cf1322'] }, // 警告红
  humidity: { name: '环境湿度', unit: '%', color: ['#13c2c2', '#08979c'] }, // 清爽青
}

// 💡 3. 模拟各区全面的综合数据池
const rawData = [
  { name: '大兴区', pm25: 65, pm10: 90, aqi: 85, humidity: 45 },
  { name: '通州区', pm25: 58, pm10: 82, aqi: 75, humidity: 50 },
  { name: '丰台区', pm25: 52, pm10: 75, aqi: 70, humidity: 48 },
  { name: '朝阳区', pm25: 45, pm10: 65, aqi: 60, humidity: 55 },
  { name: '顺义区', pm25: 40, pm10: 55, aqi: 52, humidity: 42 },
  { name: '海淀区', pm25: 35, pm10: 50, aqi: 48, humidity: 38 },
  { name: '东城区', pm25: 30, pm10: 45, aqi: 42, humidity: 40 },
  { name: '西城区', pm25: 28, pm10: 40, aqi: 38, humidity: 35 },
  { name: '密云区', pm25: 22, pm10: 30, aqi: 28, humidity: 60 },
  { name: '怀柔区', pm25: 18, pm10: 25, aqi: 25, humidity: 65 },
]

// 💡 4. 核心图表更新逻辑 (包含动态洗牌排序)
const updateChart = () => {
  if (!myChart) return

  const metric = metricsConfig[currentMetric.value]

  // 核心魔法：根据当前选中的指标，动态对数据进行重新排序
  // ECharts 的横向柱状图是自下而上画的，所以这里升序排列，最大的值就会排在最顶端
  const sortedData = [...rawData].sort((a, b) => a[currentMetric.value] - b[currentMetric.value])

  const yAxisData = sortedData.map((item) => item.name)
  const seriesData = sortedData.map((item) => item[currentMetric.value])

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: 'rgba(0, 162, 255, 0.3)',
      textStyle: { color: '#1e293b', fontWeight: 'bold' },
      formatter: `{b} : {c} ${metric.unit}`,
    },
    grid: { left: '2%', right: '6%', bottom: '2%', top: '20px', containLabel: true },
    xAxis: {
      type: 'value',
      name: metric.unit,
      nameTextStyle: { color: '#64748b', padding: [0, 0, 0, 20] },
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { type: 'dashed', color: 'rgba(0, 162, 255, 0.1)' } },
    },
    yAxis: {
      type: 'category',
      data: yAxisData,
      axisLabel: { color: '#334155', fontWeight: 'bold' },
      axisLine: { lineStyle: { color: 'rgba(0, 162, 255, 0.2)' } },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: seriesData,
        barWidth: '40%', // 让柱子细一点，更具现代感
        itemStyle: {
          borderRadius: [0, 4, 4, 0], // 右侧圆角
          // 动态应用该指标的专属渐变色
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: metric.color[0] },
            { offset: 1, color: metric.color[1] },
          ]),
          shadowColor: metric.color[0] + '40', // 40 代表透明度
          shadowBlur: 10,
        },
        label: {
          show: true,
          position: 'right',
          color: metric.color[0], // 数据标签的颜色跟着变
          fontWeight: 900,
          formatter: `{c}`,
        },
      },
    ],
    // 💡 开启丝滑过渡动画，让条形图切换时像是在“赛跑洗牌”
    animationDurationUpdate: 800,
    animationEasingUpdate: 'cubicInOut',
  }

  myChart.setOption(option, true)
}

// 监听上方按钮的切换
watch(currentMetric, () => {
  updateChart()
})

onMounted(() => {
  myChart = echarts.init(chartRef.value)
  updateChart()
  window.addEventListener('resize', () => myChart?.resize())
})

onUnmounted(() => {
  window.removeEventListener('resize', () => myChart?.resize())
  myChart?.dispose()
})
</script>

<template>
  <div class="ranking-container">
    <el-card shadow="never" class="ranking-card">
      <template #header>
        <div class="header-toolbar">
          <span class="title">🏆 北京市各区实时环境排行</span>

          <el-radio-group v-model="currentMetric" size="large" class="cyber-radio">
            <el-radio-button label="pm25">PM2.5 浓度</el-radio-button>
            <el-radio-button label="pm10">PM10 浓度</el-radio-button>
            <el-radio-button label="aqi">AQI 综合指数</el-radio-button>
            <el-radio-button label="humidity">环境湿度</el-radio-button>
          </el-radio-group>
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

/* 深度定制按钮组，完美融入白昼科幻风 */
.cyber-radio :deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(0, 162, 255, 0.2);
  color: #64748b;
  font-weight: bold;
  box-shadow: none !important;
  transition: all 0.3s;
}

.cyber-radio :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #00a2ff;
  border-color: #00a2ff;
  color: #ffffff;
  box-shadow: 0 0 10px rgba(0, 162, 255, 0.5) !important;
}

.cyber-radio :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-left: 1px solid rgba(0, 162, 255, 0.2);
}
</style>
