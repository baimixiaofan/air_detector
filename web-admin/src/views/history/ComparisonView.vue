<template>
  <div class="page-container">
    <PageHeader title="多站对比" />

    <FilterBar>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
      <el-select v-model="selectedSites" multiple collapse-tags placeholder="选择站点（最多5个）" clearable :max="5">
        <el-option v-for="s in sites" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-select v-model="selectedPollutant" placeholder="选择指标">
        <el-option v-for="p in pollutants" :key="p.key" :label="p.label" :value="p.key" />
      </el-select>
      <el-button type="primary" @click="handleQuery" :loading="loading">对比分析</el-button>
    </FilterBar>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
      <DashboardCard title="AQI 对比">
        <BarChart :data="comparisonBarData" x-key="name" :series="[{ name: '平均 AQI', key: 'value', color: '#2d3436' }]" />
      </DashboardCard>
      <DashboardCard title="趋势叠加">
        <TrendChart :data="trendData" :series="trendSeries" :height="280" />
      </DashboardCard>
    </div>

    <DashboardCard title="对比明细" style="margin-top: 16px;">
      <el-table :data="comparisonTable" stripe style="width: 100%">
        <el-table-column prop="site_name" label="站点" min-width="150" />
        <el-table-column prop="avg_aqi" label="平均 AQI" width="100" />
        <el-table-column prop="max_aqi" label="最大 AQI" width="100" />
        <el-table-column prop="min_aqi" label="最小 AQI" width="100" />
        <el-table-column label="趋势" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.trend > 0 ? '#d63031' : '#00b894' }">
              {{ row.trend > 0 ? '↑' : '↓' }} {{ Math.abs(row.trend) }}%
            </span>
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getComparisonData } from '@/api/history'
import { getSites } from '@/api/sites'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import BarChart from '@/components/charts/BarChart.vue'
import TrendChart from '@/components/charts/TrendChart.vue'
import { POLLUTANTS } from '@/utils/constants'
import { ElMessage } from 'element-plus'

const pollutants = POLLUTANTS
const loading = ref(false)
const sites = ref([])
const dateRange = ref([])
const selectedSites = ref([])
const selectedPollutant = ref('pm25')
const comparisonBarData = ref([])
const trendData = ref([])
const comparisonTable = ref([])

const trendSeries = computed(() => {
  const colors = ['#e17055', '#2d3436', '#74b9ff', '#00b894', '#fdcb6e']
  return selectedSites.value.map((id, i) => {
    const s = sites.value.find(x => x.id === id)
    return { name: s?.name || id, key: `site_${id}`, color: colors[i % colors.length] }
  })
})

async function handleQuery() {
  loading.value = true
  try {
    const res = await getComparisonData({
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      site_ids: selectedSites.value,
      pollutant: selectedPollutant.value
    })
    if (res.code === 200) {
      comparisonBarData.value = res.data.bar || []
      trendData.value = res.data.trend || []
      comparisonTable.value = res.data.table || []
    }
  } catch (e) {
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const res = await getSites()
  if (res.code === 200) sites.value = res.data || []
})
</script>
