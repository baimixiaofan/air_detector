<template>
  <div class="page-container">
    <PageHeader title="告警记录" :subtitle="`待处理 ${pendingCount} 条`" />

    <FilterBar>
      <el-select v-model="filters.severity" placeholder="严重程度" clearable>
        <el-option label="严重" value="critical" />
        <el-option label="警告" value="warning" />
        <el-option label="提示" value="info" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable>
        <el-option label="待处理" value="pending" />
        <el-option label="已确认" value="acknowledged" />
        <el-option label="已解决" value="resolved" />
      </el-select>
      <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" />
      <el-button type="primary" @click="fetchData" :loading="loading">查询</el-button>
    </FilterBar>

    <DashboardCard>
      <el-table :data="filteredData" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="site_name" label="站点" width="140" />
        <el-table-column prop="device_id" label="设备" width="140" />
        <el-table-column label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="alertSeverityType(row.severity)" size="small">{{ alertSeverityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警内容" min-width="200" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="alertStatusType(row.status)" size="small">{{ alertStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" link type="primary" @click="handleAcknowledge(row.id)">确认</el-button>
            <el-button v-if="row.status !== 'resolved'" link type="success" @click="handleResolve(row.id)">解决</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pagination">
        <el-pagination v-model:current-page="page" :total="filteredData.length" :page-size="20" layout="total, prev, pager, next" background />
      </div>
    </DashboardCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getAlertRecords, acknowledgeAlert, resolveAlert } from '@/api/alerts'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import { formatDateTime } from '@/utils/format'
import { ALERT_SEVERITY, ALERT_STATUS } from '@/utils/constants'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const filters = ref({ severity: '', status: '', dateRange: null })

const pendingCount = computed(() => tableData.value.filter(d => d.status === 'pending').length)
const filteredData = computed(() => {
  return tableData.value.filter(d => {
    if (filters.value.severity && d.severity !== filters.value.severity) return false
    if (filters.value.status && d.status !== filters.value.status) return false
    return true
  })
})

function alertSeverityLabel(s) { return ALERT_SEVERITY[s]?.label || s }
function alertSeverityType(s) { return ALERT_SEVERITY[s]?.tagType || '' }
function alertStatusLabel(s) { return ALERT_STATUS[s]?.label || s }
function alertStatusType(s) { return ALERT_STATUS[s]?.tagType || '' }

async function fetchData() {
  loading.value = true
  try {
    const res = await getAlertRecords()
    if (res.code === 200) {
      // 后端返回 {list: [...], total: ...}
      tableData.value = Array.isArray(res.data) ? res.data : (res.data?.list || [])
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function handleAcknowledge(id) {
  try { await acknowledgeAlert(id); ElMessage.success('已确认'); fetchData() }
  catch (e) { ElMessage.error('操作失败') }
}

async function handleResolve(id) {
  try { await resolveAlert(id); ElMessage.success('已解决'); fetchData() }
  catch (e) { ElMessage.error('操作失败') }
}

onMounted(fetchData)
</script>

<style scoped>
.table-pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
