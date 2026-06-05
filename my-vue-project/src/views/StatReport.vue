<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getReportData } from '@/api/history'

const tableData = ref([])
const loading = ref(false)
const days = ref(7)

const fetchReport = async () => {
  loading.value = true
  try {
    const res = await getReportData({ days: days.value })
    tableData.value = res || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleDaysChange = (val) => {
  days.value = val
  fetchReport()
}

onMounted(() => {
  fetchReport()
})
</script>

<template>
  <div class="report-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>📊 空气质量统计报表</span>
          <el-radio-group v-model="days" @change="handleDaysChange" size="small">
            <el-radio-button :value="7">近7天</el-radio-button>
            <el-radio-button :value="14">近14天</el-radio-button>
            <el-radio-button :value="30">近30天</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="tableData" border show-summary stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="avg_aqi" label="平均 AQI" sortable />
        <el-table-column prop="max_aqi" label="最高 AQI" sortable />
        <el-table-column prop="min_aqi" label="最低 AQI" sortable />
        <el-table-column prop="avg_pm25" label="平均 PM2.5 (μg/m³)" sortable />
        <el-table-column prop="avg_no2" label="平均 NO₂" sortable />
        <el-table-column prop="avg_so2" label="平均 SO₂" sortable />
        <el-table-column prop="avg_o3" label="平均 O₃" sortable />
        <el-table-column prop="count" label="数据条数" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.report-container {
  padding-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
