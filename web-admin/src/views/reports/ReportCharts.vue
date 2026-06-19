<template>
  <div class="charts-container">
    <!-- AQI 趋势图 -->
    <div class="chart-card">
      <div class="chart-header">
        <h3>AQI 趋势</h3>
        <span v-if="comparison.aqi_change !== undefined" :class="['change-badge', comparison.aqi_change <= 0 ? 'good' : 'bad']">
          {{ comparison.aqi_change > 0 ? '↑' : '↓' }} 环比 {{ Math.abs(comparison.aqi_change) }}%
        </span>
      </div>
      <div ref="trendRef" class="chart-body"></div>
    </div>

    <!-- 污染物对比 + 等级分布 两列 -->
    <div class="chart-row-2">
      <div class="chart-card">
        <div class="chart-header">
          <h3>主要污染物均值对比</h3>
        </div>
        <div ref="barRef" class="chart-body"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <h3>AQI 等级分布</h3>
        </div>
        <div ref="pieRef" class="chart-body"></div>
      </div>
    </div>

    <!-- 上期对比卡片 -->
    <div v-if="previousPeriod" class="compare-card">
      <div class="chart-header">
        <h3>环比对比</h3>
      </div>
      <div class="compare-grid">
        <div class="compare-item">
          <span class="compare-label">平均 AQI</span>
          <div class="compare-values">
            <span class="compare-current">{{ previousPeriod.avg_aqi }}</span>
            <span class="compare-arrow">{{ comparison.aqi_change > 0 ? '↑' : '↓' }}</span>
            <span class="compare-prev">上期 {{ previousPeriod.avg_aqi }}</span>
          </div>
          <div class="compare-delta" :class="comparison.aqi_change <= 0 ? 'good' : 'bad'">
            {{ comparison.aqi_change > 0 ? '恶化' : '改善' }} {{ Math.abs(comparison.aqi_change) }}%
          </div>
        </div>
        <div class="compare-item">
          <span class="compare-label">达标率</span>
          <div class="compare-values">
            <span class="compare-current">{{ previousPeriod.compliance_rate }}%</span>
            <span class="compare-arrow">{{ comparison.compliance_change > 0 ? '↑' : '↓' }}</span>
            <span class="compare-prev">上期 {{ previousPeriod.compliance_rate }}%</span>
          </div>
          <div class="compare-delta" :class="comparison.compliance_change >= 0 ? 'good' : 'bad'">
            {{ comparison.compliance_change >= 0 ? '提升' : '下降' }} {{ Math.abs(comparison.compliance_change) }}%
          </div>
        </div>
        <div class="compare-item">
          <span class="compare-label">PM2.5</span>
          <div class="compare-values">
            <span class="compare-current">{{ previousPeriod.avg_pm25 }} μg</span>
            <span class="compare-arrow">{{ comparison.pm25_change > 0 ? '↑' : '↓' }}</span>
            <span class="compare-prev">上期 {{ previousPeriod.avg_pm25 }} μg</span>
          </div>
          <div class="compare-delta" :class="comparison.pm25_change <= 0 ? 'good' : 'bad'">
            {{ comparison.pm25_change > 0 ? '上升' : '下降' }} {{ Math.abs(comparison.pm25_change) }}%
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  chartData: { type: Object, default: () => ({}) }
})

const trendRef = ref(null)
const barRef = ref(null)
const pieRef = ref(null)

let trendChart = null
let barChart = null
let pieChart = null
let resizeObserver = null

const trendSource = computed(() => props.chartData?.hourly_breakdown?.length ? props.chartData.hourly_breakdown : (props.chartData?.daily_breakdown || []))
const distribution = computed(() => props.chartData?.compliance_distribution || [])
const pollutants = computed(() => props.chartData?.pollutant_summary || [])
const comparison = computed(() => props.chartData?.comparison || {})
const previousPeriod = computed(() => props.chartData?.previous_period || null)

function renderCharts() {
  if (!trendRef.value || !barRef.value || !pieRef.value) return

  // --- AQI 趋势 ---
  if (trendChart) trendChart.dispose()
  trendChart = echarts.init(trendRef.value)

  const dates = trendSource.value.map(d => (d.hour || d.date)?.slice(5) || '')
  const aqiData = trendSource.value.map(d => d.avg_aqi)
  const pm25Data = trendSource.value.map(d => d.avg_pm25)

  // AQI 等级颜色区域
  const areaStyle = {
    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: 'rgba(255,59,48,0.25)' },
      { offset: 0.5, color: 'rgba(255,149,0,0.15)' },
      { offset: 1, color: 'rgba(52,199,89,0.05)' }
    ])
  }

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['AQI', 'PM2.5'], bottom: 0, textStyle: { fontSize: 12 } },
    grid: { left: 50, right: 16, top: 10, bottom: 36 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', name: 'AQI', nameTextStyle: { fontSize: 11 } },
    series: [
      {
        name: 'AQI', type: 'line', data: aqiData, smooth: true,
        lineStyle: { width: 2, color: '#007AFF' },
        areaStyle, symbol: 'circle', symbolSize: 4,
        markLine: {
          silent: true, data: [
            { yAxis: 50, label: { formatter: '优 50', fontSize: 10 }, lineStyle: { color: '#34C759', type: 'dashed' } },
            { yAxis: 100, label: { formatter: '良 100', fontSize: 10 }, lineStyle: { color: '#FF9500', type: 'dashed' } }
          ]
        }
      },
      {
        name: 'PM2.5', type: 'line', data: pm25Data, smooth: true,
        lineStyle: { width: 2, color: '#5856D6' },
        symbol: 'diamond', symbolSize: 4
      }
    ]
  })

  // --- 污染物柱状图 ---
  if (barChart) barChart.dispose()
  barChart = echarts.init(barRef.value)

  const barNames = pollutants.map(p => p.name)
  const barValues = pollutants.map(p => p.value)
  const barColors = ['#FF9500', '#007AFF', '#5856D6', '#34C759']

  barChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 16, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: barNames, axisLabel: { fontSize: 12 } },
    yAxis: { type: 'value', name: 'μg/m³', nameTextStyle: { fontSize: 11 } },
    series: [{
      type: 'bar', data: barValues.map((v, i) => ({ value: v, itemStyle: { color: barColors[i], borderRadius: [4, 4, 0, 0] } })),
      barWidth: 40, label: { show: true, position: 'top', formatter: '{c}', fontSize: 11 }
    }]
  })

  // --- 等级分布环形图 ---
  if (pieChart) pieChart.dispose()
  pieChart = echarts.init(pieRef.value)

  const pieColors = { '优': '#34C759', '良': '#007AFF', '轻度污染': '#FF9500', '中度污染': '#FF3B30', '重度污染': '#AF52DE' }
  const pieData = distribution.filter(d => d.count > 0).map(d => ({
    name: d.level, value: d.count,
    itemStyle: { color: pieColors[d.level] || '#999' }
  }))

  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 条 ({d}%)' },
    series: [{
      type: 'pie', radius: ['45%', '70%'], avoidLabelOverlap: true,
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
      emphasis: { label: { fontSize: 13, fontWeight: 'bold' } },
      data: pieData
    }]
  })

  // 响应式
  if (resizeObserver) resizeObserver.disconnect()
  resizeObserver = new ResizeObserver(() => {
    trendChart?.resize()
    barChart?.resize()
    pieChart?.resize()
  })
  resizeObserver.observe(trendRef.value)
  resizeObserver.observe(barRef.value)
  resizeObserver.observe(pieRef.value)
}

watch(() => props.chartData, () => nextTick(renderCharts), { deep: true })

onMounted(() => {
  nextTick(renderCharts)
})
</script>

<style scoped>
.charts-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-card {
  background: #fff;
  border: 1px solid #e8e8ed;
  border-radius: 12px;
  padding: 20px;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.chart-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
}

.chart-body {
  width: 100%;
  height: 260px;
}

.chart-row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.change-badge {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.change-badge.good { background: rgba(52,199,89,0.12); color: #34C759; }
.change-badge.bad { background: rgba(255,59,48,0.12); color: #FF3B30; }

/* 环比对比卡片 */
.compare-card {
  background: #fff;
  border: 1px solid #e8e8ed;
  border-radius: 12px;
  padding: 20px;
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 8px;
}

.compare-item {
  background: #f5f5f7;
  border-radius: 10px;
  padding: 16px;
}

.compare-label {
  font-size: 12px;
  color: #6e6e73;
  display: block;
  margin-bottom: 8px;
}

.compare-values {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

.compare-current {
  font-size: 24px;
  font-weight: 700;
  color: #1d1d1f;
}

.compare-arrow {
  font-size: 14px;
  color: #6e6e73;
}

.compare-prev {
  font-size: 12px;
  color: #6e6e73;
}

.compare-delta {
  font-size: 13px;
  font-weight: 500;
}

.compare-delta.good { color: #34C759; }
.compare-delta.bad { color: #FF3B30; }

@media (max-width: 768px) {
  .chart-row-2 { grid-template-columns: 1fr; }
  .compare-grid { grid-template-columns: 1fr; }
}
</style>
