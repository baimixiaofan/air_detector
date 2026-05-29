<script setup>
import { ref } from 'vue'

const tableData = ref([
  { month: '2026-01', site: '奥体中心站', avgPm25: 45, maxAqi: 110, overDays: 3 },
  { month: '2026-02', site: '奥体中心站', avgPm25: 38, maxAqi: 95, overDays: 1 },
  { month: '2026-03', site: '奥体中心站', avgPm25: 55, maxAqi: 135, overDays: 5 },
  { month: '2026-04', site: '奥体中心站', avgPm25: 42, maxAqi: 105, overDays: 2 },
  { month: '2026-05', site: '奥体中心站', avgPm25: 35, maxAqi: 85, overDays: 0 },
])
</script>

<template>
  <div class="report-container">
    <el-card shadow="never">
      <template #header>
        <div style="font-weight: bold">📊 2026年度各月空气质量统计月报</div>
      </template>

      <el-table :data="tableData" border show-summary stripe style="width: 100%">
        <el-table-column prop="month" label="统计月份" width="180" />
        <el-table-column prop="site" label="监测站点" width="180" />
        <el-table-column prop="avgPm25" label="平均 PM2.5 (μg/m³)" sortable />
        <el-table-column prop="maxAqi" label="月内最高 AQI" sortable />
        <el-table-column prop="overDays" label="污染超标天数" sortable>
          <template #default="scope">
            <span :style="{ color: scope.row.overDays > 2 ? 'red' : 'inherit' }">
              {{ scope.row.overDays }} 天
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.report-container {
  padding-bottom: 20px;
}
</style>
