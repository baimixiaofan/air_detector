<template>
  <div class="china-map-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>
          <span v-if="!selectedProvince">全国设备分布</span>
          <span v-else>
            <el-button text @click="backToChina" class="back-btn">
              <el-icon><ArrowLeft /></el-icon>
              返回全国
            </el-button>
            {{ selectedProvince.name }} - 设备分布
          </span>
        </h1>
        <p v-if="!selectedProvince">点击省份查看详细分布</p>
        <p v-else>点击城市查看设备详情</p>
      </div>
      <div class="header-right">
        <div class="legend">
          <span class="legend-item"><span class="legend-dot good"></span>优 (0-50)</span>
          <span class="legend-item"><span class="legend-dot moderate"></span>良 (51-100)</span>
          <span class="legend-item"><span class="legend-dot unhealthy"></span>轻度 (101-150)</span>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="map-container">
      <!-- 左侧地图 -->
      <div class="map-wrapper">
        <div ref="mapChart" class="map-chart"></div>
        <div v-if="loading" class="loading-overlay">
          <el-icon class="loading-icon"><Loading /></el-icon>
          <span>加载中...</span>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="side-panel">
        <!-- 全国概览 -->
        <div v-if="!selectedProvince" class="overview-panel">
          <div class="panel-header"><h3>全国概览</h3></div>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-value">{{ totalDevices }}</span>
              <span class="stat-label">设备总数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ onlineDevices }}</span>
              <span class="stat-label">在线设备</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ coveredProvinces }}</span>
              <span class="stat-label">覆盖省份</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ avgAQI }}</span>
              <span class="stat-label">平均 AQI</span>
            </div>
          </div>
          <div class="province-list">
            <h4>省份分布（点击查看详情）</h4>
            <div v-for="province in provinceData" :key="province.name" class="province-item" @click="selectProvince(province)">
              <span class="province-name">{{ province.name }}</span>
              <span class="province-count">{{ province.devices }} 台</span>
              <span class="province-aqi" :style="{ color: getAQIColor(province.avg_aqi) }">AQI {{ province.avg_aqi }}</span>
            </div>
          </div>
        </div>

        <!-- 省份详情 -->
        <div v-else-if="!selectedCity" class="province-detail">
          <div class="panel-header">
            <el-button text @click="backToProvince" class="back-btn"><el-icon><ArrowLeft /></el-icon>返回全国</el-button>
            <h3>{{ selectedProvince.name }}</h3>
          </div>
          <div class="province-stats">
            <div class="stat-card"><div class="stat-icon">📊</div><div class="stat-info"><span class="stat-value">{{ selectedProvince.avg_aqi }}</span><span class="stat-label">AQI</span></div></div>
            <div class="stat-card"><div class="stat-icon">🖥️</div><div class="stat-info"><span class="stat-value">{{ selectedProvince.devices }}</span><span class="stat-label">设备</span></div></div>
            <div class="stat-card"><div class="stat-icon">✅</div><div class="stat-info"><span class="stat-value">{{ selectedProvince.online }}</span><span class="stat-label">在线</span></div></div>
          </div>
          <div class="city-list">
            <h4>{{ selectedProvince.cities.length === 1 ? '区县分布' : '地级市分布' }}</h4>
            <template v-if="selectedProvince.cities.length === 1">
              <div v-for="district in selectedProvince.cities[0].districts" :key="district.name" class="city-item" @click="selectCity(district)">
                <div class="city-info"><span class="city-name">{{ district.name }}</span><span class="city-devices">{{ district.devices }} 台设备</span></div>
                <div class="city-stats">
                  <span class="city-online"><span class="online-dot"></span>{{ district.online }} 在线</span>
                  <span class="city-aqi" :style="{ color: getAQIColor(district.avg_aqi) }">AQI {{ district.avg_aqi }}</span>
                </div>
              </div>
            </template>
            <template v-else>
              <div v-for="city in selectedProvince.cities" :key="city.name" class="city-item" @click="selectCity(city)">
                <div class="city-info"><span class="city-name">{{ city.name }}</span><span class="city-devices">{{ city.devices }} 台设备</span></div>
                <div class="city-stats">
                  <span class="city-online"><span class="online-dot"></span>{{ city.online }} 在线</span>
                  <span class="city-aqi" :style="{ color: getAQIColor(city.avg_aqi) }">AQI {{ city.avg_aqi }}</span>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 城市详情 -->
        <div v-else class="city-detail">
          <div class="panel-header">
            <el-button text @click="selectedCity = null" class="back-btn"><el-icon><ArrowLeft /></el-icon>返回</el-button>
            <h3>{{ selectedCity.name }}</h3>
          </div>
          <div class="city-stats-grid">
            <div class="stat-card"><div class="stat-icon">🌡️</div><div class="stat-info"><span class="stat-value">{{ selectedCity.avg_aqi }}</span><span class="stat-label">AQI</span></div></div>
            <div class="stat-card"><div class="stat-icon">🖥️</div><div class="stat-info"><span class="stat-value">{{ selectedCity.devices }}</span><span class="stat-label">设备</span></div></div>
            <div class="stat-card"><div class="stat-icon">✅</div><div class="stat-info"><span class="stat-value">{{ selectedCity.online }}</span><span class="stat-label">在线</span></div></div>
          </div>
          <div class="air-quality-detail">
            <h4>空气质量详情</h4>
            <div class="metrics-list">
              <div class="metric-item"><span class="metric-label">PM2.5</span><span class="metric-value">{{ selectedCity.avg_pm25 }} μg/m³</span></div>
            </div>
          </div>
          <div class="device-list">
            <h4>设备列表</h4>
            <div v-for="device in selectedCity.device_list" :key="device.device_id" class="device-item">
              <div class="device-status" :class="device.online ? 'online' : 'offline'"></div>
              <div class="device-info">
                <span class="device-name">{{ device.device_id }}</span>
                <span class="device-location">{{ device.user ? device.user + ' · ' + device.industry : device.industry || '' }}</span>
              </div>
              <span class="device-aqi" :style="{ color: getAQIColor(device.aqi) }">{{ device.aqi }}</span>
            </div>
            <el-empty v-if="!selectedCity.device_list?.length" description="暂无设备数据" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import chinaJson from './china.json'
import { getDeviceDistribution } from '@/api/dashboard'

const mapChart = ref(null)
let chart = null
const selectedProvince = ref(null)
const selectedCity = ref(null)
const loading = ref(false)
const provinceData = ref([])

const PROVINCE_CODES = {
  '北京市': '110000', '天津市': '120000', '河北省': '130000', '山西省': '140000',
  '内蒙古': '150000', '辽宁省': '210000', '吉林省': '220000', '黑龙江省': '230000',
  '上海市': '310000', '江苏省': '320000', '浙江省': '330000', '安徽省': '340000',
  '福建省': '350000', '江西省': '360000', '山东省': '370000', '河南省': '410000',
  '湖北省': '420000', '湖南省': '430000', '广东省': '440000', '广西': '450000',
  '海南省': '460000', '重庆市': '500000', '四川省': '510000', '贵州省': '520000',
  '云南省': '530000', '西藏': '540000', '陕西省': '610000', '甘肃省': '620000',
  '青海省': '630000', '宁夏': '640000', '新疆': '650000', '台湾省': '710000',
  '香港': '810000', '澳门': '820000',
}

// 计算属性
const totalDevices = computed(() => provinceData.value.reduce((s, p) => s + p.devices, 0))
const onlineDevices = computed(() => provinceData.value.reduce((s, p) => s + p.online, 0))
const coveredProvinces = computed(() => provinceData.value.length)
const avgAQI = computed(() => {
  const total = provinceData.value.reduce((s, p) => s + (p.avg_aqi || 0) * p.devices, 0)
  const count = totalDevices.value
  return count ? Math.round(total / count) : 0
})

function getAQIColor(aqi) {
  if (!aqi || aqi <= 50) return '#34C759'
  if (aqi <= 100) return '#FF9500'
  return '#FF3B30'
}

// 从后端获取数据
async function fetchDistribution() {
  loading.value = true
  try {
    const res = await getDeviceDistribution()
    if (res.code === 200) {
      provinceData.value = (res.data.provinces || []).map(p => ({
        ...p,
        code: p.code || PROVINCE_CODES[p.name] || ''
      }))
      if (chart && !selectedProvince.value) initChinaMap()
    }
  } catch (e) {
    console.error('获取设备分布失败:', e)
  } finally {
    loading.value = false
  }
}

// 选择省份
async function selectProvince(province) {
  selectedProvince.value = province
  selectedCity.value = null
  const code = province.code || PROVINCE_CODES[province.name]
  if (code) {
    loading.value = true
    try {
      // 先用直连，失败则走自己后端代理
      let json
      try {
        const resp = await fetch(`https://geo.datav.aliyun.com/areas_v3/bound/${code}_full.json`)
        json = await resp.json()
      } catch {
        const resp = await fetch(`/api/admin/geo/province/${code}`)
        json = await resp.json()
      }
      echarts.registerMap(province.name, json)
      // 如果只有1个城市（直辖市），用区县数据；否则用城市数据
      let chartData = []
      if (province.cities && province.cities.length === 1 && province.cities[0].districts) {
        chartData = province.cities[0].districts.map(d => ({ name: d.name, value: d.avg_aqi || 0, devices: d.devices, aqi: d.avg_aqi || 0, online: d.online }))
      } else {
        chartData = (province.cities || []).map(c => ({ name: c.name, value: c.avg_aqi || 0, devices: c.devices, aqi: c.avg_aqi || 0, online: c.online }))
      }
      if (chart) {
        chart.setOption({
          tooltip: {
            trigger: 'item',
            formatter: p => {
              const d = chartData.find(c => c.name === p.name)
              if (!d) return p.name
              const level = d.aqi <= 50 ? '优' : d.aqi <= 100 ? '良' : '污染'
              const color = d.aqi <= 50 ? '#34C759' : d.aqi <= 100 ? '#FF9500' : '#FF3B30'
              return `<b>${p.name}</b><br/>AQI: <span style="color:${color};font-weight:700">${d.aqi}</span> (${level})<br/>设备: ${d.devices} 台<br/>在线: ${d.online || 0}`
            }
          },
          visualMap: {
            type: 'piecewise',
            pieces: [
              { min: 0, max: 50, label: '优 (0-50)', color: '#34C759' },
              { min: 51, max: 100, label: '良 (51-100)', color: '#FF9500' },
              { min: 101, label: '污染 (>100)', color: '#FF3B30' }
            ],
            left: 20, bottom: 20,
            textStyle: { color: '#6E6E73', fontSize: 12 }
          },
          series: [{
            type: 'map',
            map: province.name,
            roam: true,
            zoom: 2.5,
            scaleLimit: { min: 1, max: 10 },
            label: { show: true, fontSize: 12, color: '#1D1D1F' },
            emphasis: { label: { fontSize: 14, fontWeight: 'bold', color: '#0066CC' }, itemStyle: { areaColor: '#E3F2FD', borderColor: '#0066CC', borderWidth: 2 } },
            data: chartData
          }]
        }, true)
      }
    } catch (e) {
      console.error('加载省份地图失败:', e)
    } finally {
      loading.value = false
    }
  }
}

function selectCity(city) {
  selectedCity.value = city
}

function backToProvince() {
  selectedProvince.value = null
  selectedCity.value = null
  initChinaMap()
}

// 初始化全国地图
function initChinaMap() {
  if (!chart) chart = echarts.init(mapChart.value)
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: p => {
        const d = provinceData.value.find(x => x.name === p.name)
        if (!d) return p.name
        const level = d.avg_aqi <= 50 ? '优' : d.avg_aqi <= 100 ? '良' : '污染'
        const color = d.avg_aqi <= 50 ? '#34C759' : d.avg_aqi <= 100 ? '#FF9500' : '#FF3B30'
        return `<b>${p.name}</b><br/>AQI: <span style="color:${color};font-weight:700">${d.avg_aqi}</span> (${level})<br/>设备: ${d.devices} 台<br/>在线: ${d.online}`
      }
    },
    visualMap: {
      type: 'piecewise',
      pieces: [
        { min: 0, max: 50, label: '优 (0-50)', color: '#34C759' },
        { min: 51, max: 100, label: '良 (51-100)', color: '#FF9500' },
        { min: 101, label: '污染 (>100)', color: '#FF3B30' }
      ],
      left: 20, bottom: 20,
      textStyle: { color: '#6E6E73', fontSize: 12 }
    },
    series: [{
      type: 'map', map: 'china', roam: true, zoom: 1.2, scaleLimit: { min: 1, max: 5 },
      label: { show: true, fontSize: 12, color: '#1D1D1F' },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold', color: '#0066CC' }, itemStyle: { areaColor: '#E3F2FD', borderColor: '#0066CC', borderWidth: 2 } },
      data: provinceData.value.map(p => ({ name: p.name, value: p.avg_aqi || 0, devices: p.devices, aqi: p.avg_aqi || 0, online: p.online }))
    }]
  }
  chart.setOption(option)
  chart.on('click', params => {
    const province = provinceData.value.find(p => p.name === params.name)
    if (province) selectProvince(province)
  })
}

function handleResize() { chart?.resize() }

onMounted(() => {
  echarts.registerMap('china', chinaJson)
  initChinaMap()
  fetchDistribution()
  window.addEventListener('resize', handleResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.china-map-page { padding: 24px 32px; height: calc(100vh - var(--navbar-height)); display: flex; flex-direction: column; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header-left h1 { font-size: 24px; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 12px; }
.header-left p { font-size: 14px; color: var(--text-secondary); margin-top: 4px; }
.back-btn { font-size: 14px; color: var(--color-primary); }
.legend { display: flex; gap: 20px; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }
.legend-dot { width: 12px; height: 12px; border-radius: 3px; }
.legend-dot.good { background: #34C759; }
.legend-dot.moderate { background: #FF9500; }
.legend-dot.unhealthy { background: #FF6B00; }
.map-container { flex: 1; display: flex; gap: 24px; min-height: 0; }
.map-wrapper { flex: 1; background: var(--card-bg); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); overflow: hidden; position: relative; }
.map-chart { width: 100%; height: 100%; }
.loading-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.8); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; z-index: 10; }
.loading-icon { font-size: 32px; color: var(--color-primary); animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.side-panel { width: 380px; background: var(--card-bg); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); overflow-y: auto; }
.panel-header { padding: 20px 24px; border-bottom: 1px solid var(--card-border); display: flex; align-items: center; gap: 12px; position: sticky; top: 0; background: var(--card-bg); z-index: 10; }
.panel-header h3 { font-size: 18px; font-weight: 600; color: var(--text-primary); }
.overview-panel { height: 100%; display: flex; flex-direction: column; }
.stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; padding: 20px 24px; }
.stat-item { text-align: center; padding: 16px; background: #F9FAFB; border-radius: 12px; }
.stat-item .stat-value { display: block; font-size: 28px; font-weight: 700; color: var(--color-primary); margin-bottom: 4px; }
.stat-item .stat-label { font-size: 12px; color: var(--text-secondary); }
.province-list { flex: 1; padding: 0 24px 24px; overflow-y: auto; }
.province-list h4 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
.province-item { display: flex; align-items: center; padding: 12px 16px; border-radius: 10px; cursor: pointer; transition: all 0.2s; }
.province-item:hover { background: #F5F5F7; transform: translateX(4px); }
.province-name { flex: 1; font-size: 14px; font-weight: 500; color: var(--text-primary); }
.province-count { font-size: 13px; color: var(--text-secondary); margin-right: 16px; }
.province-aqi { font-size: 14px; font-weight: 600; }
.province-detail, .city-detail { height: 100%; display: flex; flex-direction: column; }
.province-stats, .city-stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; padding: 20px 24px; }
.stat-card { text-align: center; padding: 16px 12px; background: #F9FAFB; border-radius: 12px; }
.stat-icon { font-size: 24px; margin-bottom: 8px; }
.stat-card .stat-value { display: block; font-size: 24px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px; }
.stat-card .stat-label { font-size: 11px; color: var(--text-secondary); }
.city-list { flex: 1; padding: 0 24px 24px; overflow-y: auto; }
.city-list h4 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
.city-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: #F9FAFB; border-radius: 12px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s; }
.city-item:hover { background: #E8F4FD; transform: translateX(4px); }
.city-info { flex: 1; }
.city-name { display: block; font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.city-devices { font-size: 13px; color: var(--text-secondary); }
.city-stats { text-align: right; }
.city-online { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }
.online-dot { width: 8px; height: 8px; border-radius: 50%; background: #34C759; }
.city-aqi { font-size: 16px; font-weight: 700; }
.air-quality-detail { padding: 0 24px 20px; }
.air-quality-detail h4 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
.metrics-list { background: #F9FAFB; border-radius: 12px; padding: 16px; }
.metric-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--card-border); }
.metric-item:last-child { border-bottom: none; }
.metric-label { font-size: 14px; color: var(--text-secondary); }
.metric-value { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.device-list { flex: 1; padding: 0 24px 24px; overflow-y: auto; }
.device-list h4 { font-size: 14px; font-weight: 600; color: var(--text-secondary); margin-bottom: 12px; }
.device-item { display: flex; align-items: center; gap: 12px; padding: 14px 16px; background: #F9FAFB; border-radius: 12px; margin-bottom: 10px; }
.device-status { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.device-status.online { background: #34C759; box-shadow: 0 0 8px rgba(52,199,89,0.4); }
.device-status.offline { background: #AEAEB2; }
.device-info { flex: 1; }
.device-name { display: block; font-size: 14px; font-weight: 500; color: var(--text-primary); margin-bottom: 2px; }
.device-location { font-size: 12px; color: var(--text-secondary); }
.device-aqi { font-size: 18px; font-weight: 700; }
</style>
