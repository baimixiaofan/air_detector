<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAlertRecords, acknowledgeAlert, resolveAlert } from '@/api/alerts'

const activeTab = ref('pending')
const allAlerts = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

const fetchAlerts = async () => {
  loading.value = true
  try {
    const params = { page: page.value, size: 50 }
    if (activeTab.value !== 'all') {
      params.status = activeTab.value
    }
    const res = await getAlertRecords(params)
    allAlerts.value = res.list || []
    total.value = res.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const filteredAlerts = computed(() => allAlerts.value)

const severityMap = { critical: '严重', warning: '警告', info: '提示' }
const getSeverityLabel = (s) => severityMap[s] || s
const getSeverityType = (s) => s === 'critical' ? 'danger' : s === 'warning' ? 'warning' : 'info'

const drawerVisible = ref(false)
const currentAlert = ref({})

const handleProcess = async (row) => {
  try {
    await resolveAlert(row.id)
    ElMessage.success(`告警 #${row.id} 已标记为解决`)
    fetchAlerts()
  } catch (e) {
    console.error(e)
  }
}

const handleAcknowledge = async (row) => {
  try {
    await acknowledgeAlert(row.id)
    ElMessage.success(`告警 #${row.id} 已确认`)
    fetchAlerts()
  } catch (e) {
    console.error(e)
  }
}

const selectedRows = ref([])
const handleSelectionChange = (val) => {
  selectedRows.value = val
}

const handleBatchResolve = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先勾选要处理的告警！')
    return
  }
  ElMessageBox.confirm(`确定要将这 ${selectedRows.value.length} 条告警标记为已解决吗？`, '批量处理', { type: 'warning' })
    .then(async () => {
      for (const row of selectedRows.value) {
        try {
          await resolveAlert(row.id)
        } catch (e) { /* skip */ }
      }
      ElMessage.success('批量处理成功！')
      fetchAlerts()
    })
    .catch(() => {})
}

const handleTabChange = () => {
  page.value = 1
  fetchAlerts()
}

onMounted(() => {
  fetchAlerts()
})
</script>

<template>
  <div class="alert-container">
    <el-card shadow="never" class="table-card">
      <div class="header-toolbar">
        <el-tabs v-model="activeTab" class="demo-tabs" @tab-change="handleTabChange">
          <el-tab-pane label="🔴 待处理告警" name="pending"></el-tab-pane>
          <el-tab-pane label="🟡 已确认告警" name="acknowledged"></el-tab-pane>
          <el-tab-pane label="🟢 已解决历史" name="resolved"></el-tab-pane>
          <el-tab-pane label="📄 全部告警单" name="all"></el-tab-pane>
        </el-tabs>

        <el-button
          v-if="activeTab === 'pending' || activeTab === 'all'"
          type="primary"
          plain
          @click="handleBatchResolve"
        >
          ✅ 一键批量解决
        </el-button>
      </div>

      <el-table
        :data="filteredAlerts"
        border
        stripe
        style="width: 100%"
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="告警ID" width="80" />
        <el-table-column prop="created_at" label="报警时间" width="180" />
        <el-table-column prop="device_id" label="设备ID" width="150" />
        <el-table-column prop="metric" label="指标" width="80" />
        <el-table-column label="当前值 / 阈值" width="140">
          <template #default="scope">
            {{ scope.row.value }} / {{ scope.row.threshold }}
          </template>
        </el-table-column>
        <el-table-column label="紧急程度" width="100">
          <template #default="scope">
            <el-tag :type="getSeverityType(scope.row.severity)" effect="dark">
              {{ getSeverityLabel(scope.row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="告警详情" min-width="200" />
        <el-table-column label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.status === 'pending'" type="danger" size="small">待处理</el-tag>
            <el-tag v-else-if="scope.row.status === 'acknowledged'" type="warning" size="small">已确认</el-tag>
            <el-tag v-else type="success" size="small">已解决</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="scope">
            <template v-if="scope.row.status === 'pending'">
              <el-button type="warning" size="small" @click="handleAcknowledge(scope.row)">确认</el-button>
              <el-button type="success" size="small" @click="handleProcess(scope.row)">解决</el-button>
            </template>
            <el-button v-else-if="scope.row.status === 'acknowledged'" type="success" size="small" @click="handleProcess(scope.row)">解决</el-button>
            <el-tag v-else type="info" size="small">已完成</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > 50">
        <el-pagination background layout="prev, pager, next" :total="total" :page-size="50" :current-page="page" @current-change="(p) => { page = p; fetchAlerts() }" />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.alert-container {
  padding-bottom: 20px;
}
.header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
:deep(.el-tabs__header) {
  margin: 0;
}
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
