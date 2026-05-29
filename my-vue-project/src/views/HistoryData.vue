<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// 1. 查询表单的数据对象
const queryForm = reactive({
  site: '',
  dateRange: [], // 选中的时间范围 [开始日期, 结束日期]
  indicator: 'pm25',
})

// 模拟可选的站点列表
const siteOptions = [
  { value: 'ST-001', label: '朝阳区奥体中心站' },
  { value: 'ST-002', label: '海淀区万柳站' },
  { value: 'ST-003', label: '东城区天坛站' },
  { value: 'ST-004', label: '西城区万寿西宫站' },
]

// 2. 模拟大量的历史表格数据
const tableData = ref([
  {
    time: '2026-05-28 00:00:00',
    siteName: '朝阳区奥体中心站',
    value: 32,
    unit: 'μg/m³',
    status: '正常',
  },
  {
    time: '2026-05-27 23:00:00',
    siteName: '朝阳区奥体中心站',
    value: 35,
    unit: 'μg/m³',
    status: '正常',
  },
  {
    time: '2026-05-27 22:00:00',
    siteName: '朝阳区奥体中心站',
    value: 40,
    unit: 'μg/m³',
    status: '正常',
  },
  {
    time: '2026-05-27 21:00:00',
    siteName: '朝阳区奥体中心站',
    value: 55,
    unit: 'μg/m³',
    status: '超标',
  },
  {
    time: '2026-05-27 20:00:00',
    siteName: '朝阳区奥体中心站',
    value: 48,
    unit: 'μg/m³',
    status: '正常',
  },
])

// 3. 分页相关数据
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(145) // 模拟总共有 145 条历史数据

// 点击搜索
const handleSearch = () => {
  ElMessage.success('已触发历史数据条件查询（前端模拟）')
}

// 点击重置
const handleReset = () => {
  queryForm.site = ''
  queryForm.dateRange = []
  queryForm.indicator = 'pm25'
  ElMessage.info('查询条件已重置')
}

// 点击导出
const handleExport = () => {
  ElMessage.success('正在导出历史数据 Excel 表格...')
}
</script>

<template>
  <div class="history-container">
    <el-card shadow="never" class="filter-card">
      <el-form :model="queryForm" inline class="demo-form-inline">
        <el-form-item label="监测站点">
          <el-select
            v-model="queryForm.site"
            placeholder="请选择站点"
            style="width: 200px"
            clearable
          >
            <el-option
              v-for="item in siteOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
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

        <el-form-item label="监测指标">
          <el-select v-model="queryForm.indicator" style="width: 120px">
            <el-option label="PM2.5" value="pm25" />
            <el-option label="PM10" value="pm10" />
            <el-option label="AQI" value="aqi" />
            <el-option label="温度" value="temp" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">🔍 查询</el-button>
          <el-button @click="handleReset">🔄 重置</el-button>
          <el-button type="warning" plain @click="handleExport">📥 导出 Excel</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="table-card" style="margin-top: 20px">
      <el-table :data="tableData" border stripe style="width: 100%">
        <el-table-column prop="time" label="数据时间" width="180" />
        <el-table-column prop="siteName" label="站点名称" min-width="180" />
        <el-table-column label="监测指标" width="120">
          <template #default>
            <span>{{ queryForm.indicator.toUpperCase() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="监测数值" width="120" />
        <el-table-column prop="unit" label="单位" width="100" />
        <el-table-column prop="status" label="状态" width="120" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === '正常' ? 'success' : 'danger'">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
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
  margin-bottom: 0; /* 让行内表单垂直居中，不占多余高度 */
  margin-right: 18px;
}
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
