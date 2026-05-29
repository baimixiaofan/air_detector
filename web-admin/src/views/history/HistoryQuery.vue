<template>
  <div class="page-container">
    <PageHeader title="数据查询" />

    <FilterBar>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
      <el-select v-model="selectedSites" multiple collapse-tags placeholder="选择站点" clearable>
        <el-option v-for="s in sites" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="selectedPollutants" multiple collapse-tags placeholder="选择指标" clearable>
        <el-option v-for="p in pollutants" :key="p.key" :label="p.label" :value="p.key" />
      </el-select>
      <el-select v-model="granularity" placeholder="数据粒度">
        <el-option label="按小时" value="hourly" />
        <el-option label="按天" value="daily" />
      </el-select>
      <el-button type="primary" @click="handleQuery" :loading="loading">查询</el-button>
      <el-button @click="handleExport">导出 CSV</el-button>
    </FilterBar>

    <div v-if="queryResult.length" class="kpi-row-3" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px;">
      <StatCard title="平均 AQI" :value="avgAqi" variant="light" />
      <StatCard title="最大 AQI" :value="maxAqi" variant="light" />
      <StatCard title="最小 AQI" :value="minAqi" variant="light" />
    </div>

    <div style="display: grid; grid-template-columns: 1fr; gap: 16px;">
      <DashboardCard title="趋势图">
        <TrendChart :data="queryResult" :series="chartSeries" :height="280" />
      </DashboardCard>

      <DashboardCard title="数据明细">
        <el-table :data="queryResult" stripe style="width: 100%" max-height="400">
          <el-table-column prop="timestamp" label="时间" width="160">
            <template #default="{ row }">{{ formatDateTime(row.timestamp) }}</template>
          </el-table-column>
          <el-table-column prop="device_id" label="设备" width="140" />
          <el-table-column prop="aqi" label="AQI" width="80" />
          <el-table-column prop="pm25" label="PM2.5" width="80" />
          <el-table-column prop="pm10" label="PM10" width="80" />
          <el-table-column prop="no2" label="NO₂" width="80" />
          <el-table-column prop="so2" label="SO₂" width="80" />
          <el-table-column prop="o3" label="O₃" width="80" />
        </el-table>
      </DashboardCard>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { queryHistory } from '@/api/history'
import { getSites } from '@/api/sites'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import StatCard from '@/components/common/StatCard.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import { formatDateTime, exportToCSV } from '@/utils/format'
import { POLLUTANTS } from '@/utils/constants'
import { ElMessage } from 'element-plus'

const pollutants = POLLUTANTS
const loading = ref(false)
const sites = ref([])
const dateRange = ref([])
const selectedSites = ref([])
const selectedPollutants = ref(['pm25', 'no2'])
const granularity = ref('hourly')
const queryResult = ref([])

const chartSeries = computed(() => {
  return selectedPollutants.value.map(key => {
    const p = pollutants.find(x => x.key === key)
    return { name: p?.label || key, key, color: key === 'pm25' ? '#e17055' : key === 'no2' ? '#2d3436' : '#74b9ff' }
  })
})

const avgAqi = computed(() => {
  if (!queryResult.value.length) return 0
  return Math.round(queryResult.value.reduce((s, d) => s + (d.aqi || 0), 0) / queryResult.value.length)
})
const maxAqi = computed(() => Math.max(...queryResult.value.map(d => d.aqi || 0), 0))
const minAqi = computed(() => Math.min(...queryResult.value.filter(d => d.aqi).map(d => d.aqi), Infinity) || 0)

async function handleQuery() {
  loading.value = true
  try {
    const res = await queryHistory({
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      sites: selectedSites.value,
      granularity: granularity.value
    })
    if (res.code === 200) {
      queryResult.value = res.data || []
    }
  } catch (e) {
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

function handleExport() {
  if (!queryResult.value.length) return ElMessage.warning('暂无数据')
  const columns = [
    { key: 'timestamp', label: '时间' },
    { key: 'device_id', label: '设备' },
    { key: 'aqi', label: 'AQI' },
    { key: 'pm25', label: 'PM2.5' },
    { key: 'no2', label: 'NO₂' },
    { key: 'so2', label: 'SO₂' },
    { key: 'o3', label: 'O₃' }
  ]
  exportToCSV(queryResult.value, columns, `history_data_${new Date().toISOString().slice(0, 10)}.csv`)
  ElMessage.success('导出成功')
}

onMounted(async () => {
  const res = await getSites()
  if (res.code === 200) sites.value = res.data || []
})
</script>
