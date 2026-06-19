<template>
  <div class="page-container">
    <PageHeader title="历史数据" subtitle="输入设备 ID 查询历史趋势" />

    <div class="query-bar">
      <el-input v-model="deviceId" placeholder="输入设备ID，如 CQ_001 或 AQ_北京市_345" style="width: 360px;" clearable @keyup.enter="fetchData" />
      <el-select v-model="hours" style="width: 120px;">
        <el-option label="近 6 小时" :value="6" />
        <el-option label="近 12 小时" :value="12" />
        <el-option label="近 24 小时" :value="24" />
        <el-option label="近 48 小时" :value="48" />
        <el-option label="近 7 天" :value="168" />
      </el-select>
      <el-button type="primary" @click="fetchData" :loading="loading">查询</el-button>
    </div>

    <div v-if="error" class="error-msg">{{ error }}</div>

    <div v-if="chartData.length" class="chart-box">
      <div class="chart-header">
        <h3>{{ deviceId }} · 空气质量趋势</h3>
        <div class="chart-stats">
          <span>平均 <strong>{{ avg }}</strong></span>
          <span>最高 <strong style="color:#FF3B30">{{ max }}</strong></span>
          <span>最低 <strong style="color:#34C759">{{ min }}</strong></span>
          <span>{{ chartData.length }} 条数据</span>
        </div>
      </div>
      <div ref="chartRef" class="chart-body"></div>
    </div>

    <el-empty v-else-if="!loading && searched" description="该设备暂无历史数据" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '@/api/request'
import PageHeader from '@/components/common/PageHeader.vue'

const deviceId = ref('')
const hours = ref(24)
const loading = ref(false)
const chartData = ref([])
const error = ref('')
const searched = ref(false)
const chartRef = ref(null)
let chart = null
let ro = null

const avg = computed(() => chartData.value.length ? (chartData.value.reduce((s, d) => s + d.aqi, 0) / chartData.value.length).toFixed(1) : 0)
const max = computed(() => chartData.value.length ? Math.max(...chartData.value.map(d => d.aqi)).toFixed(1) : 0)
const min = computed(() => chartData.value.length ? Math.min(...chartData.value.map(d => d.aqi)).toFixed(1) : 0)

async function fetchData() {
  if (!deviceId.value.trim()) return
  loading.value = true
  error.value = ''
  searched.value = true
  try {
    const res = await request({
      url: '/history',
      params: { device_id: deviceId.value.trim(), hours: hours.value }
    })
    // /api/history 返回纯数组，不是 {code, data} 格式
    const list = Array.isArray(res) ? res : (res?.data || res?.records || [])
    if (!list.length) {
      error.value = '该设备暂无历史数据'
      chartData.value = []
      return
    }
    chartData.value = list.map(d => ({
      time: d.sample_time || d.timestamp || d.time || '',
      aqi: d.AQI ?? d.aqi ?? d.data?.AQI ?? 0,
      pm25: d.PM2_5 ?? d.pm25 ?? d['PM₂.₅'] ?? d.data?.['PM₂.₅'] ?? 0
    })).filter(d => d.time)
    error.value = ''
    nextTick(renderChart)
  } catch (e) {
    error.value = '查询失败'
    chartData.value = []
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (chart) chart.dispose()
  if (!chartRef.value || !chartData.value.length) return
  chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['AQI', 'PM2.5'], bottom: 0 },
    grid: { left: 50, right: 16, top: 10, bottom: 40 },
    xAxis: { type: 'category', data: chartData.value.map(d => d.time), axisLabel: { fontSize: 11, rotate: 30 } },
    yAxis: { type: 'value', name: 'AQI' },
    series: [
      { name: 'AQI', type: 'line', data: chartData.value.map(d => d.aqi), smooth: true,
        lineStyle: { color: '#007AFF', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0,122,255,0.2)' }, { offset: 1, color: 'rgba(0,122,255,0.02)' }
        ])},
        markLine: { silent: true, data: [
          { yAxis: 50, lineStyle: { color: '#34C759', type: 'dashed' }, label: { formatter: '优 50' } },
          { yAxis: 100, lineStyle: { color: '#FF9500', type: 'dashed' }, label: { formatter: '良 100' } }
        ]},
        symbol: 'circle', symbolSize: 4
      },
      { name: 'PM2.5', type: 'line', data: chartData.value.map(d => d.pm25), smooth: true,
        lineStyle: { color: '#5856D6', width: 2 }, symbol: 'diamond', symbolSize: 4 }
    ]
  })
  ro = new ResizeObserver(() => chart?.resize())
  ro.observe(chartRef.value)
}

onMounted(() => { if (deviceId.value) fetchData() })
onBeforeUnmount(() => { if (chart) chart.dispose(); if (ro) ro.disconnect() })
</script>

<style scoped>
.query-bar {
  display: flex; gap: 12px; align-items: center; margin-bottom: 20px;
  background: #fff; border: 1px solid rgba(0,0,0,0.06); border-radius: 14px; padding: 16px 20px;
}
.error-msg {
  padding: 12px 16px; background: rgba(255,59,48,0.08); color: #FF3B30;
  border-radius: 8px; font-size: 13px; margin-bottom: 16px;
}
.chart-box {
  background: #fff; border: 1px solid rgba(0,0,0,0.06); border-radius: 14px; padding: 20px;
}
.chart-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
}
.chart-header h3 { margin: 0; font-size: 15px; font-weight: 600; color: #1d1d1f; }
.chart-stats { display: flex; gap: 16px; font-size: 13px; color: #6e6e73; }
.chart-body { width: 100%; height: 400px; }
</style>
