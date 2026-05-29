<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

// 模拟设备数据
const tableData = ref([
  {
    id: 'DEV-8801',
    name: '高精度PM2.5传感器',
    site: '朝阳区奥体中心站',
    battery: 98,
    isRunning: true,
  },
  { id: 'DEV-8802', name: '温湿度一体机', site: '海淀区万柳站', battery: 15, isRunning: true },
  { id: 'DEV-8803', name: '风向风速仪', site: '东城区天坛站', battery: 85, isRunning: false },
  { id: 'DEV-8804', name: '噪音监测仪', site: '西城区万寿西宫站', battery: 60, isRunning: true },
])

// 监听开关切换事件
const handleSwitchChange = (newValue, row) => {
  if (newValue) {
    ElMessage.success(`设备 ${row.id} 已远程启动`)
  } else {
    ElMessage.warning(`设备 ${row.id} 已远程停用`)
  }
}
</script>

<template>
  <div class="device-manage-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>⚙️ 设备状态监控</span>
          <el-button type="primary" plain>扫描发现新设备</el-button>
        </div>
      </template>

      <el-table :data="tableData" border style="width: 100%">
        <el-table-column prop="id" label="设备编号" width="120" />
        <el-table-column prop="name" label="设备名称" min-width="150" />
        <el-table-column prop="site" label="所属站点" min-width="150" />

        <el-table-column label="设备电量" width="180">
          <template #default="scope">
            <el-progress
              :percentage="scope.row.battery"
              :status="scope.row.battery < 20 ? 'exception' : 'success'"
            />
          </template>
        </el-table-column>

        <el-table-column label="远程控制 (启/停)" width="150" align="center">
          <template #default="scope">
            <el-switch
              v-model="scope.row.isRunning"
              inline-prompt
              active-text="开"
              inactive-text="关"
              @change="(val) => handleSwitchChange(val, scope.row)"
            />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.device-manage-container {
  padding-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
