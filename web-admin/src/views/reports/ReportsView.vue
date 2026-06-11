<template>
  <div class="page-container">
    <PageHeader title="数据报告" subtitle="智能简报与企业级空气质量报告生成" />

    <!-- Tab 切换 -->
    <div class="tab-bar">
      <button :class="['tab-btn', { active: activeTab === 'smart' }]" @click="activeTab = 'smart'">
        <el-icon><Document /></el-icon>智能简报
      </button>
      <button :class="['tab-btn', { active: activeTab === 'enterprise' }]" @click="activeTab = 'enterprise'">
        <el-icon><OfficeBuilding /></el-icon>企业报告
      </button>
    </div>

    <!-- 智能简报 Tab -->
    <div v-if="activeTab === 'smart'">
      <FilterBar>
        <el-select v-model="smartFilter" placeholder="报告类型" style="width: 140px;">
          <el-option label="全部" value="" />
          <el-option label="日报" value="daily" />
          <el-option label="周报" value="weekly" />
          <el-option label="月报" value="monthly" />
        </el-select>
        <el-button type="primary" @click="handleGenerateSmart" :loading="generating">
          <el-icon><Plus /></el-icon>生成日报
        </el-button>
      </FilterBar>

      <div class="report-grid">
        <div v-for="report in smartReports" :key="report.id" class="report-card" @click="previewReport(report)">
          <div class="report-card-header">
            <el-tag :type="report.report_type === 'daily' ? 'success' : report.report_type === 'weekly' ? 'warning' : 'primary'" size="small">
              {{ { daily: '日报', weekly: '周报', monthly: '月报' }[report.report_type] || report.report_type }}
            </el-tag>
            <span class="report-date">{{ formatDate(report.created_at) }}</span>
          </div>
          <h3 class="report-title">{{ report.title }}</h3>
          <p class="report-summary">{{ report.summary }}</p>
          <div class="report-footer">
            <span class="report-status" :class="report.status">
              {{ { completed: '已完成', pending: '生成中', failed: '失败' }[report.status] }}
            </span>
            <el-button text type="danger" size="small" @click.stop="handleDelete(report.id)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="!smartReports.length && !loading" description="暂无智能简报" />
      </div>
    </div>

    <!-- 企业报告 Tab -->
    <div v-if="activeTab === 'enterprise'">
      <FilterBar>
        <el-input v-model="enterpriseFilter" placeholder="搜索客户公司名" style="width: 200px;" clearable />
        <el-button type="primary" @click="showEnterpriseDialog = true">
          <el-icon><Plus /></el-icon>生成企业报告
        </el-button>
      </FilterBar>

      <div class="report-grid">
        <div v-for="report in filteredEnterpriseReports" :key="report.id" class="report-card enterprise" @click="previewReport(report)">
          <div class="report-card-header">
            <el-tag type="primary" size="small">企业报告</el-tag>
            <span class="report-date">{{ formatDate(report.created_at) }}</span>
          </div>
          <h3 class="report-title">{{ report.title }}</h3>
          <p class="report-company">🏢 {{ report.company_name || '未指定客户' }}</p>
          <p class="report-summary">{{ report.summary }}</p>
          <div class="report-footer">
            <span class="report-status" :class="report.status">
              {{ { completed: '已完成', pending: '生成中', failed: '失败' }[report.status] }}
            </span>
            <div>
              <el-button text type="primary" size="small" @click.stop="handleExportPDF(report)">导出 PDF</el-button>
              <el-button text type="danger" size="small" @click.stop="handleDelete(report.id)">删除</el-button>
            </div>
          </div>
        </div>
        <el-empty v-if="!filteredEnterpriseReports.length && !loading" description="暂无企业报告" />
      </div>
    </div>

    <!-- 企业报告生成对话框 -->
    <el-dialog v-model="showEnterpriseDialog" title="生成企业报告" width="560px" :close-on-click-modal="false">
      <el-form :model="enterpriseForm" label-width="100px">
        <el-form-item label="客户公司名" required>
          <el-input v-model="enterpriseForm.company_name" placeholder="如：XX地产集团" />
        </el-form-item>
        <el-form-item label="报告标题" required>
          <el-input v-model="enterpriseForm.report_title" placeholder="如：2025年Q2空气质量报告" />
        </el-form-item>
        <el-form-item label="报告类型">
          <el-select v-model="enterpriseForm.report_type" style="width: 100%;">
            <el-option label="日报" value="daily" />
            <el-option label="周报" value="weekly" />
            <el-option label="月报" value="monthly" />
            <el-option label="季度报告" value="quarterly" />
          </el-select>
        </el-form-item>
        <el-form-item label="报告风格">
          <el-radio-group v-model="enterpriseForm.style">
            <el-radio value="formal">正式专业</el-radio>
            <el-radio value="casual">简洁易读</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="监测指标">
          <el-checkbox-group v-model="enterpriseForm.metrics">
            <el-checkbox value="AQI" label="AQI" />
            <el-checkbox value="PM2.5" label="PM2.5" />
            <el-checkbox value="NO₂" label="NO₂" />
            <el-checkbox value="SO₂" label="SO₂" />
            <el-checkbox value="O₃" label="O₃" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="客户亮点">
          <div v-for="(h, i) in enterpriseForm.highlights" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px;">
            <el-input v-model="enterpriseForm.highlights[i]" placeholder="如：对比上月改善15%" />
            <el-button text type="danger" @click="enterpriseForm.highlights.splice(i, 1)">删除</el-button>
          </div>
          <el-button text @click="enterpriseForm.highlights.push('')" :disabled="enterpriseForm.highlights.length >= 5">
            + 添加亮点
          </el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEnterpriseDialog = false">取消</el-button>
        <el-button type="primary" @click="handleGenerateEnterprise" :loading="generating">
          生成报告
        </el-button>
      </template>
    </el-dialog>

    <!-- 报告预览对话框 -->
    <el-dialog v-model="showPreview" title="报告预览" width="80%" top="5vh" fullscreen>
      <div class="preview-container" v-if="previewData">
        <div class="preview-header">
          <h1>{{ previewData.title }}</h1>
          <div class="preview-meta">
            <span v-if="previewData.company_name">🏢 {{ previewData.company_name }}</span>
            <span>📅 {{ formatDate(previewData.created_at) }}</span>
            <span>📊 {{ { daily: '日报', weekly: '周报', monthly: '月报', quarterly: '季度报告' }[previewData.report_type] }}</span>
          </div>
        </div>
        <div class="preview-content" v-html="formatContent(previewData.content)"></div>
        <div class="preview-footer">
          <p>报告由 AirInsight 智能空气分析平台自动生成</p>
          <p>{{ formatDate(new Date().toISOString()) }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPreview = false">关闭</el-button>
        <el-button type="primary" @click="handleExportPDF(previewData)">
          <el-icon><Download /></el-icon>导出 PDF
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getReports, generateReport, deleteReport } from '@/api/reports'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import request from '@/api/request'

const activeTab = ref('smart')
const loading = ref(false)
const generating = ref(false)
const allReports = ref([])
const smartFilter = ref('')
const enterpriseFilter = ref('')
const showEnterpriseDialog = ref(false)
const showPreview = ref(false)
const previewData = ref(null)

const enterpriseForm = ref({
  company_name: '',
  report_title: '',
  report_type: 'monthly',
  metrics: ['AQI', 'PM2.5'],
  highlights: [],
  style: 'formal'
})

const smartReports = computed(() => {
  let list = allReports.value.filter(r => r.generated_by !== 'enterprise')
  if (smartFilter.value) list = list.filter(r => r.report_type === smartFilter.value)
  return list
})

const filteredEnterpriseReports = computed(() => {
  let list = allReports.value.filter(r => r.generated_by === 'enterprise')
  if (enterpriseFilter.value) {
    const q = enterpriseFilter.value.toLowerCase()
    list = list.filter(r => (r.company_name || '').toLowerCase().includes(q))
  }
  return list
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function formatContent(content) {
  if (!content) return ''
  return content
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/#{3}\s?(.*)/g, '<h4>$1</h4>')
    .replace(/#{2}\s?(.*)/g, '<h3>$1</h3>')
    .replace(/#{1}\s?(.*)/g, '<h2>$1</h2>')
}

async function fetchReports() {
  loading.value = true
  try {
    const res = await getReports({ page: 1, page_size: 100 })
    if (res.code === 200) {
      allReports.value = res.data.list || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function handleGenerateSmart() {
  generating.value = true
  try {
    const res = await generateReport({ type: 'daily' })
    if (res.code === 200) {
      ElMessage.success('智能简报生成成功')
      fetchReports()
    }
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}

async function handleGenerateEnterprise() {
  const form = enterpriseForm.value
  if (!form.company_name) return ElMessage.warning('请填写客户公司名')
  if (!form.report_title) return ElMessage.warning('请填写报告标题')

  generating.value = true
  try {
    const res = await request({
      url: '/api/admin/reports/enterprise',
      method: 'post',
      data: form
    })
    if (res.code === 200) {
      ElMessage.success('企业报告生成成功')
      showEnterpriseDialog.value = false
      enterpriseForm.value = {
        company_name: '', report_title: '', report_type: 'monthly',
        metrics: ['AQI', 'PM2.5'], highlights: [], style: 'formal'
      }
      fetchReports()
    }
  } catch (e) {
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}

async function previewReport(report) {
  try {
    const res = await request({ url: `/api/admin/reports/${report.id}/preview`, method: 'get' })
    if (res.code === 200) {
      previewData.value = res.data
      showPreview.value = true
    }
  } catch (e) {
    previewData.value = report
    showPreview.value = true
  }
}

async function handleExportPDF(report) {
  ElMessage.info('PDF 导出功能准备中，请使用浏览器打印功能（Ctrl+P）导出')
  previewData.value = report
  showPreview.value = true
}

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm('确认删除此报告？', '提示')
    const res = await deleteReport(id)
    if (res.code === 200) {
      ElMessage.success('已删除')
      fetchReports()
    }
  } catch (e) { /* cancelled */ }
}

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.tab-bar {
  display: flex;
  gap: 4px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 20px;
  width: fit-content;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: var(--sidebar-hover-bg);
}

.tab-btn.active {
  background: var(--color-primary);
  color: #fff;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.report-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s;
}

.report-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.report-card.enterprise {
  border-left: 3px solid var(--color-primary);
}

.report-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.report-date {
  font-size: 13px;
  color: var(--text-muted);
}

.report-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.report-company {
  font-size: 14px;
  color: var(--color-primary);
  margin-bottom: 8px;
}

.report-summary {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 16px;
}

.report-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--card-border);
}

.report-status {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 12px;
}

.report-status.completed {
  background: rgba(52, 199, 89, 0.1);
  color: #34C759;
}

.report-status.pending {
  background: rgba(255, 149, 0, 0.1);
  color: #FF9500;
}

.report-status.failed {
  background: rgba(255, 59, 48, 0.1);
  color: #FF3B30;
}

/* 预览 */
.preview-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
}

.preview-header {
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 24px;
  border-bottom: 2px solid var(--color-primary);
}

.preview-header h1 {
  font-size: 28px;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.preview-meta {
  display: flex;
  justify-content: center;
  gap: 24px;
  font-size: 14px;
  color: var(--text-secondary);
}

.preview-content {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-primary);
}

.preview-content :deep(h2) {
  font-size: 20px;
  margin: 24px 0 12px;
  color: var(--color-primary);
}

.preview-content :deep(h3) {
  font-size: 17px;
  margin: 20px 0 10px;
}

.preview-footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}
</style>
