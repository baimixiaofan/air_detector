<template>
  <div class="page-container">
    <PageHeader title="区域排行" subtitle="按区域/企业/设备查看空气质量排名" />

    <FilterBar>
      <el-select v-model="selectedProvince" placeholder="选择省份" clearable style="width: 140px;" @change="onProvinceChange">
        <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
      </el-select>
      <el-select v-model="selectedCity" placeholder="选择城市" clearable style="width: 140px;" v-if="cities.length" @change="onCityChange">
        <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
      </el-select>
      <el-select v-model="selectedDistrict" placeholder="选择区县" clearable style="width: 140px;" v-if="districts.length" @change="fetchData">
        <el-option v-for="d in districts" :key="d" :label="d" :value="d" />
      </el-select>
      <el-select v-model="customerType" placeholder="客户类型" style="width: 130px;">
        <el-option label="全部" value="all" />
        <el-option label="企业" value="enterprise" />
        <el-option label="个人" value="individual" />
      </el-select>
      <el-select v-model="days" placeholder="时间范围" style="width: 130px;">
        <el-option label="近 7 天" :value="7" />
        <el-option label="近 30 天" :value="30" />
        <el-option label="近 90 天" :value="90" />
      </el-select>
      <el-button type="primary" @click="fetchData" :loading="loading">刷新</el-button>
    </FilterBar>

    <div style="display: grid; grid-template-columns: 1.3fr 0.7fr; gap: 16px;">
      <DashboardCard :title="cardTitle">
        <el-table :data="rankings" v-loading="loading" stripe style="width: 100%">
          <el-table-column label="排名" width="70" align="center">
            <template #default="{ $index }">
              <span class="rank-badge" :class="rankBadgeClass($index)">{{ $index + 1 }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="selectedDistrict ? '设备名称' : '区域'" min-width="160">
            <template #default="{ row }">
              <span class="rank-name">{{ row.name }}</span>
              <span v-if="!selectedDistrict" class="type-tag type-dist">区域</span>
              <span v-else class="type-tag type-dev">设备</span>
            </template>
          </el-table-column>
          <el-table-column label="平均 AQI" width="100" sortable prop="avg_aqi">
            <template #default="{ row }">
              <span :style="{ color: aqiColor(row.avg_aqi), fontWeight: 600 }">{{ row.avg_aqi }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="selectedDistrict ? '最高 AQI' : 'AQI 范围'" width="120">
            <template #default="{ row }">{{ selectedDistrict ? row.max_aqi : `${row.min_aqi} ~ ${row.max_aqi}` }}</template>
          </el-table-column>
          <el-table-column v-if="!selectedDistrict" label="设备数" width="80" sortable prop="device_count">
            <template #default="{ row }">{{ row.device_count }}</template>
          </el-table-column>
          <el-table-column label="PM2.5" width="80" sortable prop="avg_pm25">
            <template #default="{ row }">{{ row.avg_pm25 }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!rankings.length && !loading" description="暂无排行数据" />
      </DashboardCard>

      <DashboardCard title="排行柱状图" v-if="rankings.length">
        <BarChart
          :data="rankings.slice(0, 10).map(r => ({ name: r.name.length > 6 ? r.name.slice(0, 6) + '..' : r.name, value: r.avg_aqi }))"
          x-key="name"
          :series="[{ name: 'AQI', key: 'value', color: '#e17055' }]"
          :horizontal="true"
        />
      </DashboardCard>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getRankings, getRankingAreas } from '@/api/rankings'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import BarChart from '@/components/charts/BarChart.vue'

const loading = ref(false)
const customerType = ref('all')
const days = ref(7)
const rankings = ref([])
const provinces = ref([])
const cities = ref([])
const districts = ref([])
const selectedProvince = ref('')
const selectedCity = ref('')
const selectedDistrict = ref('')

const cardTitle = computed(() => {
  if (selectedDistrict.value) return `${selectedDistrict.value} · 设备排名`
  if (selectedCity.value) return `${selectedCity.value} · 区域排名`
  if (selectedProvince.value) return `${selectedProvince.value} · 城市排名`
  return '全国 · 省份排名'
})

function aqiColor(aqi) {
  if (aqi <= 50) return '#34C759'
  if (aqi <= 100) return '#007AFF'
  if (aqi <= 150) return '#FF9500'
  return '#FF3B30'
}

function rankBadgeClass(i) {
  return i === 0 ? 'rank-1' : i === 1 ? 'rank-2' : i === 2 ? 'rank-3' : ''
}

async function fetchAreas() {
  try {
    const res = await getRankingAreas({})
    if (res.code === 200) provinces.value = res.data || []
  } catch (e) { console.warn(e) }
}

function onProvinceChange(val) {
  selectedCity.value = ''
  selectedDistrict.value = ''
  cities.value = []
  districts.value = []
  if (!val) { fetchData(); return }
  getRankingAreas({ province: val }).then(res => {
    if (res.code === 200) cities.value = res.data || []
    fetchData()
  })
}

function onCityChange(val) {
  selectedDistrict.value = ''
  districts.value = []
  if (!val || !selectedProvince.value) { fetchData(); return }
  // 获取区县列表
  getRankingAreas({ province: selectedProvince.value, city: val }).then(res => {
    if (res.code === 200) districts.value = res.data || []
    fetchData()
  })
}

async function fetchData() {
  loading.value = true
  try {
    // 区县层级 → 展示具体设备排名
    const isDistrictLevel = !!selectedDistrict.value
    const params = {
      days: days.value,
      group_by: isDistrictLevel ? 'device' : 'district',
      limit: 30
    }
    if (selectedProvince.value) params.province = selectedProvince.value
    if (selectedCity.value) params.city = selectedCity.value
    if (selectedDistrict.value) params.district = selectedDistrict.value
    const res = await getRankings(params)
    if (res.code === 200) rankings.value = res.data || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(() => {
  fetchData()
  fetchAreas()
})

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
.rank-name { font-weight: 500; margin-right: 6px; }
.type-tag { font-size: 11px; padding: 1px 6px; border-radius: 8px; background: rgba(88,86,214,0.1); color: #5856D6; }
</style>
