<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { queryHistory, exportReport } from '@/api/history'
import { getSites } from '@/api/sites'

const queryForm = reactive({
  device_id: '',
  dateRange: [],
})

const siteOptions = ref([])
const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(50)
const total = ref(0)

const fetchSites = async () => {
  try {
    const res = await getSites({ page: 1, size: 100 })
    siteOptions.value = (res.list || []).map(s => ({ value: s.code, label: s.name }))
  } catch (e) {
    console.error(e)
  }
}

const handleSearch = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value,
    }
    if (queryForm.device_id) params.device_id = queryForm.device_id
    if (queryForm.dateRange && queryForm.dateRange.length === 2) {
      params.start_time = queryForm.dateRange[0] + ' 00:00:00'
      params.end_time = queryForm.dateRange[1] + ' 23:59:59'
    }
    const res = await queryHistory(params)
    tableData.value = (res.list || []).map(doc => ({
      time: doc.timestamp,
      device_id: doc.device_id,
      aqi: doc.data?.AQI ?? '-',
      pm25: doc.data?.['PM₂.₅'] ?? '-',
      no2: doc.data?.NO2 ?? '-',
      so2: doc.data?.SO2 ?? '-',
      o3: doc.data?.O3 ?? '-',
    }))
    total.value = res.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  queryForm.device_id = ''
  queryForm.dateRange = []
  tableData.value = []
  total.value = 0
}

const handleExport = async () => {
  try {
    const params = { days: 7 }
    if (queryForm.device_id) params.device_id = queryForm.device_id
    const blob = await exportReport(params)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `air_quality_report_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}

const handlePageChange = (p) => {
  currentPage.value = p
  handleSearch()
}

onMounted(() => {
  fetchSites()
})
</script>

<template>
  <div class="history-container">
    <el-card shadow="never" class="filter-card">
      <el-form :model="queryForm" inline class="demo-form-inline">
        <el-form-item label="设备ID">
          <el-input v-model="queryForm.device_id" placeholder="输入设备ID" style="width: 180px" clearable />
        </el-form-item>

        <el-form-item label="时间范围">
          <el-date-picker
            v-model="queryForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="loading">🔍 查询</el-button>
          <el-button @click="handleReset">🔄 重置</el-button>
          <el-button type="warning" plain @click="handleExport">📥 导出 CSV</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="table-card" style="margin-top: 20px">
      <el-table :data="tableData" border stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="time" label="数据时间" width="180" />
        <el-table-column prop="device_id" label="设备ID" width="150" />
        <el-table-column prop="aqi" label="AQI" width="80" />
        <el-table-column prop="pm25" label="PM2.5" width="80" />
        <el-table-column prop="no2" label="NO₂" width="80" />
        <el-table-column prop="so2" label="SO₂" width="80" />
        <el-table-column prop="o3" label="O₃" width="80" />
      </el-table>

      <div class="pagination-wrapper" v-if="total > pageSize">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.history-container {
  padding-bottom: 20px;
}
.filter-card :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 18px;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
