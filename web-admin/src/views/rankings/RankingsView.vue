<template>
  <div class="page-container">
    <PageHeader title="区域排行" />

    <FilterBar>
      <el-select v-model="period" placeholder="时间范围">
        <el-option label="今日" value="today" />
        <el-option label="本周" value="week" />
        <el-option label="本月" value="month" />
      </el-select>
      <el-select v-model="pollutant" placeholder="选择指标">
        <el-option label="AQI" value="aqi" />
        <el-option label="PM2.5" value="pm25" />
        <el-option label="NO₂" value="no2" />
      </el-select>
      <el-button type="primary" @click="fetchData" :loading="loading">刷新</el-button>
    </FilterBar>

    <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 16px;">
      <DashboardCard title="站点排名">
        <el-table :data="rankings" v-loading="loading" stripe style="width: 100%" :row-class-name="rankRowClass">
          <el-table-column label="排名" width="70" align="center">
            <template #default="{ $index }">
              <span class="rank-badge" :class="rankBadgeClass($index)">{{ $index + 1 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="site_name" label="站点" min-width="150" />
          <el-table-column label="平均 AQI" width="110">
            <template #default="{ row }">
              <span :style="{ color: aqiLevel(row.avg_aqi).color, fontWeight: 600 }">{{ row.avg_aqi }}</span>
            </template>
          </el-table-column>
          <el-table-column label="趋势" width="80">
            <template #default="{ row }">
              <span :style="{ color: row.trend > 0 ? '#d63031' : '#00b894' }">{{ row.trend > 0 ? '↑' : '↓' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="等级" width="100">
            <template #default="{ row }">
              <span class="status-badge" :class="`status-badge--${row.aqi <= 100 ? 'success' : row.aqi <= 150 ? 'warning' : 'danger'}`">
                {{ aqiLevel(row.avg_aqi).label }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </DashboardCard>

      <DashboardCard title="可视化排行">
        <BarChart :data="rankings.map(r => ({ name: r.site_name, value: r.avg_aqi }))" x-key="name" :series="[{ name: 'AQI', key: 'value', color: '#e17055' }]" :horizontal="true" />
      </DashboardCard>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRankings } from '@/api/rankings'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { aqiLevel as aqiLevelFn } from '@/utils/format'

const loading = ref(false)
const period = ref('today')
const pollutant = ref('aqi')
const rankings = ref([])

function aqiLevel(aqi) { return aqiLevelFn(aqi) }
function rankBadgeClass(i) { return i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : i === 2 ? 'rank-3' : '' }
function rankRowClass({ rowIndex }) { return rowIndex < 3 ? `rank-row-${rowIndex + 1}` : '' }

async function fetchData() {
  loading.value = true
  try { const res = await getRankings({ period: period.value, pollutant: pollutant.value }); if (res.code === 200) rankings.value = res.data || [] }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.rank-badge {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%;
  font-weight: 700; font-size: 12px;
}
.rank-1 { background: #ffeaa7; color: #d68910; }
.rank-2 { background: #d5dbdb; color: #566573; }
.rank-3 { background: #edbb99; color: #a04000; }
:deep(.rank-row-1) { background: rgba(255, 234, 167, 0.15) !important; }
:deep(.rank-row-2) { background: rgba(213, 219, 219, 0.1) !important; }
:deep(.rank-row-3) { background: rgba(237, 187, 153, 0.1) !important; }
</style>
