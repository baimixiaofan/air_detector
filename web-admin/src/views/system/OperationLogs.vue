<template>
  <div class="page-container">
    <PageHeader title="操作日志" />

    <FilterBar>
      <el-input v-model="filters.username" placeholder="用户名" clearable prefix-icon="User" />
      <el-select v-model="filters.action" placeholder="操作类型" clearable>
        <el-option label="登录" value="login" />
        <el-option label="创建" value="create" />
        <el-option label="更新" value="update" />
        <el-option label="删除" value="delete" />
      </el-select>
      <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" />
      <el-button type="primary" @click="fetchData" :loading="loading">查询</el-button>
    </FilterBar>

    <DashboardCard>
      <el-table :data="filteredData" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="action" label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small">{{ actionLabel(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="目标类型" width="120" />
        <el-table-column prop="detail" label="详情" min-width="200" />
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
      </el-table>

      <div class="table-pagination">
        <el-pagination v-model:current-page="page" :total="filteredData.length" :page-size="50" layout="total, prev, pager, next" background />
      </div>
    </DashboardCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getOperationLogs } from '@/api/system'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const tableData = ref([])
const page = ref(1)
const filters = ref({ username: '', action: '', dateRange: null })

const filteredData = computed(() => {
  return tableData.value.filter(d => {
    if (filters.value.username && !d.username.includes(filters.value.username)) return false
    if (filters.value.action && d.action !== filters.value.action) return false
    return true
  })
})

const actionMap = { login: '登录', create: '创建', update: '更新', delete: '删除' }
const actionColors = { login: '', create: 'success', update: 'warning', delete: 'danger' }
function actionLabel(a) { return actionMap[a] || a }
function actionTagType(a) { return actionColors[a] || '' }

async function fetchData() {
  loading.value = true
  try { const res = await getOperationLogs(); if (res.code === 200) tableData.value = res.data || [] }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.table-pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
