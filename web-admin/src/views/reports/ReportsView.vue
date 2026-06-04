<template>
  <div class="page-container">
    <PageHeader title="数据简报">
      <el-button type="primary" @click="handleGenerate" :loading="generating"><el-icon><DocumentAdd /></el-icon>生成新简报</el-button>
    </PageHeader>

    <div class="report-grid">
      <DashboardCard v-for="report in reports" :key="report.id" class="report-card">
        <div class="report-card__header">
          <el-tag :type="report.type === 'daily' ? '' : report.type === 'weekly' ? 'warning' : 'success'" size="small">
            {{ report.type === 'daily' ? '日报' : report.type === 'weekly' ? '周报' : '月报' }}
          </el-tag>
          <span class="report-date">{{ formatDate(report.created_at) }}</span>
        </div>
        <h4 class="report-title">{{ report.title }}</h4>
        <p class="report-summary">{{ report.summary }}</p>
        <div class="report-card__footer">
          <span :class="report.status === 'completed' ? 'text-success' : 'text-muted'">
            {{ report.status === 'completed' ? '已完成' : '生成中...' }}
          </span>
        </div>
      </DashboardCard>
      <el-empty v-if="!reports.length" description="暂无简报" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getIntelligenceReports, generateReport } from '@/api/reports'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import { formatDate } from '@/utils/format'
import { ElMessage } from 'element-plus'

const reports = ref([])
const generating = ref(false)

async function fetchData() {
  try { const res = await getIntelligenceReports(); if (res.code === 200) reports.value = res.data || [] }
  catch (e) { console.error(e) }
}

async function handleGenerate() {
  generating.value = true
  try { await generateReport({ type: 'daily' }); ElMessage.success('简报生成中'); fetchData() }
  catch (e) { ElMessage.error('生成失败') }
  finally { generating.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.report-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.report-card { cursor: pointer; }
.report-card__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.report-date { font-size: var(--font-size-caption); color: var(--text-muted); }
.report-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.report-summary { font-size: var(--font-size-body); color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px; }
.report-card__footer { border-top: 1px solid #f0f2f5; padding-top: 10px; font-size: var(--font-size-caption); }
.text-success { color: var(--color-success); }
.text-muted { color: var(--text-muted); }
</style>
