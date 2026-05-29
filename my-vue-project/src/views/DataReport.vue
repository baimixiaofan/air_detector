<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

// 模拟今天的日期
const reportDate = ref(new Date().toLocaleDateString())

// 模拟导出报表的操作
const handleExport = () => {
  ElMessage.success('正在为您生成每日 PDF 报表，请稍候...')
}

// 模拟时间轴的数据流
const activities = ref([
  { content: '系统自动生成今日空气质量预测报告', timestamp: '08:00', type: 'primary' },
  {
    content: '海淀区万柳站 PM10 数据出现异常波动，已自动标记并通知运维',
    timestamp: '09:30',
    type: 'warning',
  },
  {
    content: '环保局下发最新空气质量标准文件，系统已同步更新参数',
    timestamp: '11:15',
    type: 'success',
  },
  { content: '朝阳区奥体中心站设备自动校准完成', timestamp: '14:20', type: 'info' },
])
</script>

<template>
  <div class="report-container">
    <el-card shadow="never" class="summary-card">
      <template #header>
        <div class="card-header">
          <span>📄 每日数据简报概览</span>
          <el-button type="primary" @click="handleExport">📥 导出 PDF 报表</el-button>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="报告日期">{{ reportDate }}</el-descriptions-item>
        <el-descriptions-item label="整体评估">
          <el-tag type="success">空气优良</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="核心指标">PM2.5 平均 35 μg/m³</el-descriptions-item>
        <el-descriptions-item label="告警总数">今日共产生 3 条轻微告警</el-descriptions-item>
        <el-descriptions-item label="设备在线率">98.5%</el-descriptions-item>
        <el-descriptions-item label="专家建议">
          目前区域空气质量整体良好，建议保持现有监测频率，重点关注西北部站点的风沙影响。
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" class="timeline-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>⏱️ 今日系统运行与调度日志</span>
        </div>
      </template>

      <el-timeline>
        <el-timeline-item
          v-for="(activity, index) in activities"
          :key="index"
          :type="activity.type"
          :timestamp="activity.timestamp"
          placement="top"
        >
          <el-card shadow="hover">
            <p>{{ activity.content }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<style scoped>
.report-container {
  padding-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
