<template>
  <div class="page-container">
    <PageHeader title="企业报告" subtitle="为 CRM 客户生成专业的空气质量分析报告（含图表、数据表格、PDF 导出）" />

    <!-- 企业报告 -->
    <div>
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
        <el-form-item label="选择客户" required>
          <el-select v-model="enterpriseForm.customer_id" placeholder="从CRM选择企业客户" filterable style="width: 100%;" @change="onCustomerChange">
            <el-option v-for="c in enterpriseCustomers" :key="c.id" :label="`${c.name}（${c.industry||'未分类'} · ${c.device_count}台设备）`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户名称" v-if="enterpriseForm.company_name">
          <el-input :model-value="enterpriseForm.company_name" disabled />
        </el-form-item>
        <el-form-item label="报告标题" required>
          <el-input v-model="enterpriseForm.report_title" placeholder="如：2026年Q2空气质量报告" />
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
        <div class="preview-charts-area" v-if="chartData">
          <ReportCharts :chartData="chartData" />
        </div>
        <!-- 数据来源信息 -->
        <div class="data-source-bar" v-if="chartData?.data_source">
          <h4>📡 数据来源</h4>
          <div class="source-grid">
            <div class="source-item">
              <span class="label">企业客户</span>
              <span class="value">{{ chartData.data_source.customer_name }}</span>
            </div>
            <div class="source-item">
              <span class="label">监测设备</span>
              <span class="value">{{ chartData.data_source.device_count }} 台</span>
            </div>
            <div class="source-item">
              <span class="label">数据区间</span>
              <span class="value">{{ chartData.data_source.data_period }}</span>
            </div>
            <div class="source-item">
              <span class="label">数据总量</span>
              <span class="value">{{ chartData.data_source.total_records?.toLocaleString() }} 条</span>
            </div>
          </div>
        </div>
        <!-- 数据表格 -->
        <div class="preview-tables-area" v-if="chartData">
          <ReportTables :tableData="chartData" />
        </div>
        <div class="preview-content" v-html="formatContent(previewData.content)"></div>
        <div class="preview-footer">
          <p>报告由 AirInsight 智能空气分析平台自动生成</p>
          <p>{{ formatDate(new Date().toISOString()) }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPreview = false">关闭</el-button>
        <el-button type="primary" @click="handleExportPDF(previewData)" :loading="pdfLoading">
          <el-icon><Download /></el-icon>{{ pdfLoading ? '生成中...' : '导出 PDF' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { getReports, deleteReport } from '@/api/reports'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import request from '@/api/request'
import ReportCharts from './ReportCharts.vue'
import ReportTables from './ReportTables.vue'
import * as echarts from 'echarts'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

const loading = ref(false)
const generating = ref(false)
const allReports = ref([])
const enterpriseFilter = ref('')
const showEnterpriseDialog = ref(false)
const showPreview = ref(false)
const previewData = ref(null)
const chartData = ref(null)
const pdfLoading = ref(false)
const enterpriseCustomers = ref([])

const enterpriseForm = ref({
  customer_id: null,
  company_name: '',
  report_title: '',
  report_type: 'monthly',
  metrics: ['AQI', 'PM2.5'],
  highlights: [],
  style: 'formal'
})

const filteredEnterpriseReports = computed(() => {
  let all = allReports.value
  if (!Array.isArray(all)) all = all?.list || all?.data || []
  let list = all.filter(r => r.generated_by === 'enterprise')
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

async function fetchEnterpriseCustomers() {
  try {
    const res = await request({ url: '/admin/customers/enterprise', method: 'get' })
    if (res.code === 200) enterpriseCustomers.value = res.data || []
  } catch (e) { console.warn('获取企业客户列表失败', e) }
}

function onCustomerChange(customerId) {
  const c = enterpriseCustomers.value.find(x => x.id === customerId)
  if (c) {
    enterpriseForm.value.company_name = c.name
    if (!enterpriseForm.value.report_title) {
      enterpriseForm.value.report_title = `${c.name}空气质量分析报告`
    }
  }
}

async function handleGenerateEnterprise() {
  const form = enterpriseForm.value
  if (!form.customer_id) return ElMessage.warning('请从CRM选择企业客户')
  if (!form.report_title) return ElMessage.warning('请填写报告标题')

  generating.value = true
  try {
    const res = await request({
      url: '/admin/reports/enterprise',
      method: 'post',
      data: form,
      timeout: 60000  // 报告生成需要扫描 MongoDB，60 秒
    })
    if (res.code === 200) {
      ElMessage.success('企业报告生成成功')
      showEnterpriseDialog.value = false
      enterpriseForm.value = {
        customer_id: null, company_name: '', report_title: '', report_type: 'monthly',
        metrics: ['AQI', 'PM2.5'], highlights: [], style: 'formal'
      }
      fetchReports()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.msg || '生成失败')
  } finally {
    generating.value = false
  }
}

async function fetchChartData(reportId) {
  try {
    const res = await request({ url: `/admin/reports/${reportId}/chart-data`, method: 'get', timeout: 30000 })
    if (res.code === 200) {
      chartData.value = res.data
      return res.data
    }
  } catch (e) {
    console.warn('获取图表数据失败', e)
    chartData.value = null
  }
  return null
}

async function previewReport(report) {
  try {
    const res = await request({ url: `/admin/reports/${report.id}/preview`, method: 'get' })
    if (res.code === 200) {
      previewData.value = res.data
      showPreview.value = true
      nextTick(() => fetchChartData(report.id))
    }
  } catch (e) {
    previewData.value = report
    showPreview.value = true
    nextTick(() => fetchChartData(report.id))
  }
}

async function handleExportPDF(report) {
  pdfLoading.value = true
  try {
    // 1. 加载报告数据
    const previewRes = await request({ url: `/admin/reports/${report.id}/preview`, method: 'get' })
    const data = previewRes.code === 200 ? previewRes.data : report
    previewData.value = data

    // 2. 加载图表数据
    const cd = await fetchChartData(report.id)

    if (!data) { ElMessage.warning('无报告数据'); return }

    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageW = 210
    const pageH = 297
    const margin = 16
    const contentW = pageW - margin * 2

    // ---- 辅助：截图一个元素并添加到 PDF ----
    async function captureToPdf(el, opts = {}) {
      const totalH = el.scrollHeight
      const canvas = await html2canvas(el, {
        scale: 2, useCORS: true, backgroundColor: '#ffffff',
        logging: false, width: el.scrollWidth,
        height: totalH,
        ...opts
      })
      const imgData = canvas.toDataURL('image/jpeg', 0.92)
      const imgW = contentW
      const imgH = (canvas.height / canvas.width) * imgW

      // 计算需要几页
      const pageContentH = pageH - margin * 2
      if (imgH <= pageContentH) {
        pdf.addImage(imgData, 'JPEG', margin, margin, imgW, imgH)
      } else {
        // 需要分页
        let srcY = 0
        let remaining = imgH
        let pageNum = 0
        while (remaining > 0) {
          if (pageNum > 0) pdf.addPage()
          const h = Math.min(remaining, pageContentH)
          const ratio = h / imgH
          const srcH = canvas.height * ratio
          // 裁剪 canvas 的一部分
          const pageCanvas = document.createElement('canvas')
          pageCanvas.width = canvas.width
          pageCanvas.height = canvas.height * ratio
          const ctx = pageCanvas.getContext('2d')
          ctx.drawImage(canvas, 0, srcY, canvas.width, srcH, 0, 0, canvas.width, srcH)
          const pageImg = pageCanvas.toDataURL('image/jpeg', 0.9)
          pdf.addImage(pageImg, 'JPEG', margin, margin, imgW, h)
          srcY += srcH
          remaining -= h
          pageNum++
        }
      }
      return pdf
    }

    // ---- 1. 封面页 ----
    const coverDiv = document.createElement('div')
    coverDiv.style.cssText = `width:${contentW}mm; padding:40px 32px; background:#fff; font-family:"PingFang SC","Microsoft YaHei",sans-serif;`
    const periodLabel = { daily: '日报', weekly: '周报', monthly: '月报', quarterly: '季度报告' }[data.report_type] || ''
    const healthLevel = (data.report_stats?.daily_breakdown?.length
      ? (() => {
          const aqi = data.report_stats.daily_breakdown.reduce((s, d) => s + d.avg_aqi, 0) / data.report_stats.daily_breakdown.length
          if (aqi <= 50) return { label: '优', color: '#34C759' }
          if (aqi <= 100) return { label: '良', color: '#007AFF' }
          if (aqi <= 150) return { label: '轻度污染', color: '#FF9500' }
          if (aqi <= 200) return { label: '中度污染', color: '#FF3B30' }
          return { label: '重度污染', color: '#AF52DE' }
        })()
      : { label: '--', color: '#999' })
    const stats = data.report_stats || {}
    const avgAqi = stats.daily_breakdown?.length
      ? (stats.daily_breakdown.reduce((s, d) => s + d.avg_aqi, 0) / stats.daily_breakdown.length).toFixed(1) : '--'

    coverDiv.innerHTML = `
      <div style="text-align:center; padding-top:60px;">
        <div style="font-size:12px; color:#6e6e73; letter-spacing:2px; margin-bottom:16px;">${data.company_name || '企业客户'}</div>
        <div style="font-size:28px; font-weight:700; color:#1d1d1f; margin-bottom:8px;">${data.title || '空气质量分析报告'}</div>
        <div style="font-size:13px; color:#6e6e73; margin-bottom:40px;">${periodLabel} · ${new Date().toLocaleDateString('zh-CN')}</div>
        <div style="width:80px; height:80px; border-radius:50%; background:${healthLevel.color}; margin:0 auto 16px; display:flex; align-items:center; justify-content:center;">
          <span style="font-size:32px; font-weight:700; color:#fff;">${avgAqi}</span>
        </div>
        <div style="font-size:14px; color:#6e6e73;">空气质量等级</div>
        <div style="font-size:20px; font-weight:600; color:${healthLevel.color}; margin-top:4px;">${healthLevel.label}</div>
        <div style="margin-top:40px; padding-top:20px; border-top:1px solid #e8e8ed; font-size:12px; color:#aeaeb2;">
          达标率：${stats.compliance_distribution?.reduce((s, d) => s + d.percentage, 0).toFixed(1) || '--'}% ·
          监测设备：${stats.device_count || '--'} 台 ·
          数据量：${stats.total_records?.toLocaleString() || '--'} 条
        </div>
      </div>
    `
    document.body.appendChild(coverDiv)
    await captureToPdf(coverDiv)
    document.body.removeChild(coverDiv)

    // ---- 2. 图表页（小时趋势，比日均值更好看） ----
    const trendSource = cd?.hourly_breakdown?.length ? cd.hourly_breakdown : cd?.daily_breakdown
    if (trendSource?.length) {
      pdf.addPage()
      const chartBox = document.createElement('div')
      chartBox.style.cssText = `width:${contentW}mm; padding:16px 20px; background:#fff; font-family:"PingFang SC","Microsoft YaHei",sans-serif;`
      document.body.appendChild(chartBox)

      const trendTitle = document.createElement('div')
      trendTitle.style.cssText = 'font-size:15px; font-weight:600; color:#1d1d1f; margin-bottom:8px;'
      trendTitle.textContent = cd?.hourly_breakdown?.length ? 'AQI 逐小时趋势' : 'AQI 日均值趋势'
      chartBox.appendChild(trendTitle)

      const trendDiv = document.createElement('div')
      trendDiv.style.cssText = 'width:100%; height:260px;'
      chartBox.appendChild(trendDiv)

      const trendChart = echarts.init(trendDiv)
      const labels = trendSource.map(d => (d.hour || d.date)?.slice(5) || '')
      const aqiData = trendSource.map(d => d.avg_aqi)
      const pm25Data = trendSource.map(d => d.avg_pm25)
      trendChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 50, right: 16, top: 10, bottom: 30 },
        xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, rotate: labels.length > 12 ? 45 : 0 } },
        yAxis: { type: 'value', name: 'AQI' },
        series: [
          { name: 'AQI', type: 'line', data: aqiData, smooth: true, lineStyle: { color: '#007AFF', width: 2 }, symbol: 'none',
            areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(0,122,255,0.2)' }, { offset: 1, color: 'rgba(0,122,255,0.02)' }
            ])},
            markLine: { silent: true, data: [
              { yAxis: 50, lineStyle: { color: '#34C759', type: 'dashed' }, label: { formatter: '优 50' } },
              { yAxis: 100, lineStyle: { color: '#FF9500', type: 'dashed' }, label: { formatter: '良 100' } }
            ]}
          },
          { name: 'PM2.5', type: 'line', data: pm25Data, smooth: true, lineStyle: { color: '#5856D6', width: 2 }, symbol: 'diamond', symbolSize: 4 }
        ]
      })

      // 污染物对比 + 等级分布并排
      const rowDiv = document.createElement('div')
      rowDiv.style.cssText = 'display:flex; gap:16px; margin-top:20px;'
      chartBox.appendChild(rowDiv)

      // 污染物柱状图
      const barDiv = document.createElement('div')
      barDiv.style.cssText = 'flex:1; height:240px;'
      rowDiv.appendChild(barDiv)
      const barNames = (cd.pollutant_summary || []).map(p => p.name)
      const barValues = (cd.pollutant_summary || []).map(p => p.value)
      const barColors = ['#FF9500', '#007AFF', '#5856D6', '#34C759']
      const barChart = echarts.init(barDiv)
      barChart.setOption({
        grid: { left: 40, right: 10, top: 10, bottom: 30 },
        xAxis: { type: 'category', data: barNames },
        yAxis: { type: 'value', name: 'μg/m³' },
        series: [{ type: 'bar', data: barValues.map((v, i) => ({ value: v, itemStyle: { color: barColors[i] } })), barWidth: 30, label: { show: true, position: 'top' } }]
      })

      // 等级分布环形图
      const pieDiv = document.createElement('div')
      pieDiv.style.cssText = 'flex:1; height:240px;'
      rowDiv.appendChild(pieDiv)
      const pieColors = { '优': '#34C759', '良': '#007AFF', '轻度污染': '#FF9500', '中度污染': '#FF3B30', '重度污染': '#AF52DE' }
      const pieData = (cd.compliance_distribution || []).filter(d => d.count > 0).map(d => ({ name: d.level, value: d.count, itemStyle: { color: pieColors[d.level] } }))
      const pieChart = echarts.init(pieDiv)
      pieChart.setOption({
        series: [{ type: 'pie', radius: ['45%', '70%'], data: pieData, label: { formatter: '{b}\n{d}%', fontSize: 11 } }]
      })

      // 等渲染
      await new Promise(r => setTimeout(r, 800))
      await captureToPdf(chartBox)
      trendChart.dispose()
      barChart.dispose()
      pieChart.dispose()
      document.body.removeChild(chartBox)
    }

    // ---- 2.5. 数据来源页 ----
    if (cd?.data_source) {
      pdf.addPage()
      const sourceDiv = document.createElement('div')
      sourceDiv.style.cssText = `width:${contentW}mm; padding:40px 32px; background:#fff; font-family:"PingFang SC","Microsoft YaHei",sans-serif;`
      sourceDiv.innerHTML = `
        <div style="font-size:16px; font-weight:600; color:#1d1d1f; margin-bottom:16px;">📡 数据来源</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
          <div style="background:#f5f5f7; border-radius:10px; padding:16px;">
            <div style="font-size:11px; color:#6e6e73;">企业客户</div>
            <div style="font-size:18px; font-weight:600; color:#1d1d1f; margin-top:4px;">${cd.data_source.customer_name || '--'}</div>
          </div>
          <div style="background:#f5f5f7; border-radius:10px; padding:16px;">
            <div style="font-size:11px; color:#6e6e73;">监测设备</div>
            <div style="font-size:18px; font-weight:600; color:#1d1d1f; margin-top:4px;">${cd.data_source.device_count || '--'} 台</div>
          </div>
          <div style="background:#f5f5f7; border-radius:10px; padding:16px;">
            <div style="font-size:11px; color:#6e6e73;">数据区间</div>
            <div style="font-size:18px; font-weight:600; color:#1d1d1f; margin-top:4px;">${cd.data_source.data_period || '--'}</div>
          </div>
          <div style="background:#f5f5f7; border-radius:10px; padding:16px;">
            <div style="font-size:11px; color:#6e6e73;">数据总量</div>
            <div style="font-size:18px; font-weight:600; color:#1d1d1f; margin-top:4px;">${(cd.data_source.total_records || 0).toLocaleString()} 条</div>
          </div>
        </div>
      `
      document.body.appendChild(sourceDiv)
      await captureToPdf(sourceDiv)
      document.body.removeChild(sourceDiv)
    }

    // ---- 2.8. 表格页 ----
    if (cd?.device_breakdown?.length || cd?.daily_breakdown?.length || cd?.exceedance_summary?.length) {
      pdf.addPage()
      const tablesDiv = document.createElement('div')
      tablesDiv.style.cssText = `width:${contentW}mm; padding:16px 20px; background:#fff; font-family:"PingFang SC","Microsoft YaHei",sans-serif;`
      document.body.appendChild(tablesDiv)

      // 设备逐台分析表
      if (cd.device_breakdown?.length) {
        let html = '<div style="font-size:15px; font-weight:600; color:#1d1d1f; margin-bottom:12px;">📊 设备逐台分析表</div>'
        html += '<table style="width:100%; border-collapse:collapse; font-size:12px; margin-bottom:20px;">'
        html += '<thead><tr style="background:#f5f5f7;">'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">#</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">设备</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">位置</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">平均AQI</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">PM2.5</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">达标率</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">超标</th>'
        html += '</tr></thead><tbody>'
        for (const d of cd.device_breakdown) {
          const color = d.compliance_pct >= 90 ? '#34C759' : d.compliance_pct >= 80 ? '#FF9500' : '#FF3B30'
          html += `<tr style="border-bottom:1px solid #f0f0f0;">`
          html += `<td style="padding:8px 10px; color:#aeaeb2;">${d.rank}</td>`
          html += `<td style="padding:8px 10px; font-weight:600;">${d.device_name || d.device_id}</td>`
          html += `<td style="padding:8px 10px;">${d.district || '-'}</td>`
          html += `<td style="padding:8px 10px;">${d.avg_aqi}</td>`
          html += `<td style="padding:8px 10px;">${d.avg_pm25}</td>`
          html += `<td style="padding:8px 10px; color:${color};">${d.compliance_pct}%</td>`
          html += `<td style="padding:8px 10px;">${d.exceed_count}</td>`
          html += `</tr>`
        }
        html += '</tbody></table>'
        tablesDiv.innerHTML += html
      }

      // 超标统计表
      if (cd.exceedance_summary?.length) {
        let html = '<div style="font-size:15px; font-weight:600; color:#1d1d1f; margin-bottom:12px; margin-top:20px;">⚠️ 污染物超标统计</div>'
        html += '<table style="width:100%; border-collapse:collapse; font-size:12px;">'
        html += '<thead><tr style="background:#f5f5f7;">'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">污染物</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">阈值</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">超标次数</th>'
        html += '<th style="padding:8px 10px; text-align:left; color:#6e6e73;">超标率</th>'
        html += '</tr></thead><tbody>'
        for (const e of cd.exceedance_summary) {
          html += `<tr style="border-bottom:1px solid #f0f0f0;">`
          html += `<td style="padding:8px 10px; font-weight:600;">${e.pollutant}</td>`
          html += `<td style="padding:8px 10px;">${e.threshold}</td>`
          html += `<td style="padding:8px 10px;">${e.exceed_count}</td>`
          html += `<td style="padding:8px 10px;">${e.exceed_rate}%</td>`
          html += `</tr>`
        }
        html += '</tbody></table>'
        tablesDiv.innerHTML += html
      }

      await captureToPdf(tablesDiv)
      document.body.removeChild(tablesDiv)
    }

    // ---- 3. AI 分析文字页 ----
    if (data.content) {
      pdf.addPage()
      const textDiv = document.createElement('div')
      textDiv.style.cssText = `width:${contentW}mm; padding:20px 32px; background:#fff; font-family:"PingFang SC","Microsoft YaHei",sans-serif;`
      textDiv.innerHTML = `
        <div style="font-size:18px; font-weight:600; color:#1d1d1f; margin-bottom:16px; padding-bottom:12px; border-bottom:2px solid #007AFF;">AI 分析报告</div>
        <div style="font-size:13px; line-height:1.8; color:#333; white-space:pre-wrap;">${data.content}</div>
      `
      document.body.appendChild(textDiv)
      await captureToPdf(textDiv)
      document.body.removeChild(textDiv)
    }

    // ---- 4. 品牌页脚 ----
    pdf.addPage()
    const footerDiv = document.createElement('div')
    footerDiv.style.cssText = `width:${contentW}mm; padding:60px 32px; background:#fff; text-align:center; font-family:"PingFang SC","Microsoft YaHei",sans-serif;`
    footerDiv.innerHTML = `
      <div style="font-size:14px; color:#6e6e73; margin-bottom:8px;">— 报告完 —</div>
      <div style="font-size:12px; color:#aeaeb2; margin-top:24px;">
        本报告由 AirInsight 专业空气质量监测平台自动生成<br>
        数据来源：${data.company_name || '企业客户'} 部署的空气质量监测设备<br>
        生成时间：${new Date().toLocaleString('zh-CN')}
      </div>
    `
    document.body.appendChild(footerDiv)
    await captureToPdf(footerDiv)
    document.body.removeChild(footerDiv)

    // 保存 PDF
    pdf.save(`${data.title || '空气质量报告'}.pdf`)
    ElMessage.success('PDF 导出成功')
  } catch (e) {
    console.error('PDF 导出失败', e)
    ElMessage.error('PDF 导出失败: ' + (e.message || '未知错误'))
  } finally {
    pdfLoading.value = false
  }
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
  fetchEnterpriseCustomers()
})
</script>

<style scoped>
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

.preview-charts-area {
  margin: 24px 0;
  padding: 8px;
  background: #fafafa;
  border-radius: 12px;
}

.preview-tables-area {
  margin: 24px 0;
}

.data-source-bar {
  background: linear-gradient(135deg, #f0f6ff, #f5f0ff);
  border: 1px solid #e0e8f5;
  border-radius: 12px;
  padding: 20px;
  margin: 24px 0;
}

.data-source-bar h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1d1d1f;
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.source-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-item .label {
  font-size: 11px;
  color: #6e6e73;
}

.source-item .value {
  font-size: 16px;
  font-weight: 600;
  color: #1d1d1f;
}

.preview-content :deep(img) {
  max-width: 100%;
}

@media (max-width: 768px) {
  .source-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
