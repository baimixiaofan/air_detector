<template>
  <div class="page-container">
    <PageHeader title="统计报表">
      <el-button type="primary" @click="handleExportPDF">
        <el-icon><Download /></el-icon>导出 PDF
      </el-button>
    </PageHeader>

    <FilterBar>
      <el-radio-group v-model="period">
        <el-radio-button value="daily">日报</el-radio-button>
        <el-radio-button value="weekly">周报</el-radio-button>
        <el-radio-button value="monthly">月报</el-radio-button>
      </el-radio-group>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
      <el-button type="primary" @click="handleQuery" :loading="loading">生成报表</el-button>
    </FilterBar>

    <div ref="reportRef">
      <div class="kpi-row-3" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px;">
        <StatCard title="数据完整率" :value="`${reportData.completeness || 0}%`" variant="light" />
        <StatCard title="平均 AQI" :value="reportData.avg_aqi || 0" variant="dark" />
        <StatCard title="触发告警数" :value="reportData.alert_count || 0" variant="light" />
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
        <DashboardCard title="趋势图">
          <BarChart :data="reportData.trend || []" x-key="name" :series="[{ name: 'AQI', key: 'value', color: '#e17055' }]" />
        </DashboardCard>
        <DashboardCard title="站点汇总">
          <el-table :data="reportData.site_summary || []" stripe style="width: 100%">
            <el-table-column prop="site_name" label="站点" min-width="120" />
            <el-table-column prop="avg_aqi" label="平均 AQI" width="100" />
            <el-table-column prop="data_count" label="数据条数" width="100" />
            <el-table-column label="达标率" width="100">
              <template #default="{ row }">{{ row.compliance_rate ?? 0 }}%</template>
            </el-table-column>
          </el-table>
        </DashboardCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getReportData } from '@/api/history'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import StatCard from '@/components/common/StatCard.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const period = ref('daily')
const dateRange = ref([])
const reportRef = ref(null)
const reportData = ref({})

async function handleQuery() {
  loading.value = true
  try {
    const res = await getReportData({
      period: period.value,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    })
    if (res.code === 200) {
      reportData.value = res.data || {}
    }
  } catch (e) {
    ElMessage.error('生成报表失败')
  } finally {
    loading.value = false
  }
}

async function handleExportPDF() {
  try {
    const html2canvas = (await import('html2canvas')).default
    const { jsPDF } = await import('jspdf')
    const canvas = await html2canvas(reportRef.value)
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width
    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
    pdf.save(`report_${new Date().toISOString().slice(0, 10)}.pdf`)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  }
}
</script>
