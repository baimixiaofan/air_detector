<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

const chartRef = ref(null)
let myChart = null

// 💡 1. 构建全国“省份 - 站点”树形数据字典 (此处列举代表性省份，真实项目由后端提供)
const nationwideData = [
  {
    province: '北京市',
    stations: [
      { id: 'BJ-01', name: '朝阳区奥体中心站' },
      { id: 'BJ-02', name: '海淀区万柳站' },
      { id: 'BJ-03', name: '东城区天坛站' },
      { id: 'BJ-04', name: '西城区万寿西宫站' },
    ],
  },
  {
    province: '上海市',
    stations: [
      { id: 'SH-01', name: '浦东新区张江站' },
      { id: 'SH-02', name: '静安区静安寺站' },
      { id: 'SH-03', name: '徐汇区徐家汇站' },
    ],
  },
  {
    province: '广东省',
    stations: [
      { id: 'GD-01', name: '广州天河体育中心站' },
      { id: 'GD-02', name: '深圳南山科技园站' },
      { id: 'GD-03', name: '东莞松山湖监测点' },
    ],
  },
  {
    province: '四川省',
    stations: [
      { id: 'SC-01', name: '成都武侯祠站' },
      { id: 'SC-02', name: '绵阳游仙区监测点' },
    ],
  },
  {
    province: '新疆维吾尔自治区',
    stations: [
      { id: 'XJ-01', name: '乌鲁木齐天山区站' },
      { id: 'XJ-02', name: '喀什地区中心站' },
    ],
  },
]

// 将树形数据展平，方便通过 ID 快速查名字
const stationMap = {}
nationwideData.forEach((prov) => {
  prov.stations.forEach((st) => {
    stationMap[st.id] = st.name
  })
})

// 默认对比北京奥体和上海张江
const selectedStations = ref(['BJ-01', 'SH-01'])

// 💡 2. 为三根对比线分配固定的高级配色（科技蓝、警告红、安全绿）
const themeColors = ['#00a2ff', '#ff4d4f', '#10b981']

// 💡 3. 模拟数据生成器与缓存池
const dataCache = {}
const getStationData = (id) => {
  // 如果这个站点之前没生成过数据，就随机生成 7 天的 PM2.5 趋势并存下来
  if (!dataCache[id]) {
    dataCache[id] = Array.from({ length: 7 }, () => Math.floor(Math.random() * 80) + 20)
  }
  return dataCache[id] // 如果有，就返回存好的数据，保证同一个站点数据不变
}

// 💡 4. 核心图表刷新逻辑
const updateChart = () => {
  if (!myChart) return

  const selectedKeys = selectedStations.value

  if (selectedKeys.length === 0) {
    ElMessage.warning('请至少选择一个站点进行查看')
  }

  const legendData = []
  const seriesData = []

  // 根据当前选中的站点动态拼装线条
  selectedKeys.forEach((id, index) => {
    const stationName = stationMap[id]
    const lineColor = themeColors[index] // 按选中顺序分配颜色
    const stationData = getStationData(id) // 动态获取或生成数据

    legendData.push(stationName)
    seriesData.push({
      name: stationName,
      type: 'line',
      smooth: true,
      symbolSize: 8,
      lineStyle: { width: 3, color: lineColor, shadowColor: lineColor + '66', shadowBlur: 10 },
      itemStyle: { color: lineColor },
      data: stationData,
    })
  })

  // 注入新配置，强制重绘
  myChart.setOption(
    {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        borderColor: 'rgba(0, 162, 255, 0.3)',
        textStyle: { color: '#1e293b' },
      },
      legend: {
        data: legendData,
        top: '2%',
        textStyle: { color: '#334155', fontWeight: 'bold' },
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true, top: '80px' },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: ['06-01', '06-02', '06-03', '06-04', '06-05', '06-06', '06-07'],
        axisLabel: { color: '#64748b', margin: 15 },
        axisLine: { lineStyle: { color: 'rgba(0, 162, 255, 0.2)' } },
      },
      yAxis: {
        type: 'value',
        name: 'PM2.5 浓度 (μg/m³)',
        nameTextStyle: { color: '#64748b', padding: [0, 0, 0, 30] },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { type: 'dashed', color: 'rgba(0, 162, 255, 0.1)' } },
      },
      series: seriesData,
    },
    true,
  )
}

watch(selectedStations, () => {
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
  <div class="compare-container">
    <el-card shadow="never" class="chart-card">
      <template #header>
        <div class="header-toolbar">
          <span class="title">📊 跨区多站综合数据对比</span>

          <el-select
            v-model="selectedStations"
            multiple
            :multiple-limit="3"
            placeholder="请跨区选择对比站点 (最多3个)"
            style="width: 400px"
          >
            <el-option-group
              v-for="prov in nationwideData"
              :key="prov.province"
              :label="prov.province"
            >
              <el-option
                v-for="station in prov.stations"
                :key="station.id"
                :label="station.name"
                :value="station.id"
              />
            </el-option-group>
          </el-select>
        </div>
      </template>

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

:deep(.el-select__tags .el-tag) {
  background-color: rgba(0, 162, 255, 0.1);
  color: #0088ff;
  border: 1px solid rgba(0, 162, 255, 0.3);
}

/* 增强下拉框里省份分组标题的视觉效果 */
:deep(.el-select-group__title) {
  color: #00a2ff;
  font-weight: bold;
  font-size: 13px;
  background: rgba(0, 162, 255, 0.05);
  padding: 8px 20px;
}
</style>
