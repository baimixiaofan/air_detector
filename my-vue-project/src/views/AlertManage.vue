<script setup>
import { ref, computed, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 当前选中的 Tab（默认看“待处理”）
const activeTab = ref('pending')

// 模拟的告警数据源
const allAlerts = ref([
  {
    id: 'AL-1001',
    time: '2026-05-28 14:20',
    site: '海淀区万柳站',
    level: '严重',
    desc: 'PM10 浓度持续 1 小时爆表',
    status: 'pending',
  },
  {
    id: 'AL-1002',
    time: '2026-05-28 13:15',
    site: '朝阳区奥体中心站',
    level: '警告',
    desc: '设备电量低于 15%',
    status: 'pending',
  },
  {
    id: 'AL-1003',
    time: '2026-05-28 10:05',
    site: '西城区万寿西宫站',
    level: '提示',
    desc: '风向传感器数据波动异常',
    status: 'pending',
  },
  {
    id: 'AL-1004',
    time: '2026-05-27 09:30',
    site: '通州区梨园站',
    level: '严重',
    desc: '站点意外断电离线',
    status: 'resolved',
  },
  {
    id: 'AL-1005',
    time: '2026-05-26 16:45',
    site: '东城区天坛站',
    level: '警告',
    desc: '温度传感器需要校准',
    status: 'resolved',
  },
])

// 💡 核心逻辑：根据当前选中的 Tab，动态过滤出要在表格里显示的数据
const filteredAlerts = computed(() => {
  if (activeTab.value === 'all') return allAlerts.value
  return allAlerts.value.filter((item) => item.status === activeTab.value)
})

// 抽屉与表单逻辑
const drawerVisible = ref(false)
const currentAlert = ref({}) // 记录当前正在处理哪一条告警
const processForm = reactive({
  remark: '',
  action: '维修人员已出发',
})

// 点击“去处理”按钮
const handleProcess = (row) => {
  currentAlert.value = row
  processForm.remark = '' // 清空上次填写的记录
  drawerVisible.value = true
}

// 提交工单处理
const submitProcess = () => {
  if (!processForm.remark) {
    ElMessage.warning('请填写处理备注！')
    return
  }

  // 在真实项目里这里会发请求给后端，这里我们模拟前端修改状态
  const target = allAlerts.value.find((item) => item.id === currentAlert.value.id)
  if (target) {
    target.status = 'resolved'
  }

  drawerVisible.value = false
  ElMessage.success(`告警单 ${currentAlert.value.id} 处理完毕！`)
}

// 批量处理逻辑
const selectedRows = ref([])
const handleSelectionChange = (val) => {
  selectedRows.value = val
}

const handleBatchResolve = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先在表格左侧勾选要处理的告警！')
    return
  }

  ElMessageBox.confirm(
    `确定要将这 ${selectedRows.value.length} 条告警一键标记为已解决吗？`,
    '批量处理提示',
    {
      type: 'warning',
    },
  )
    .then(() => {
      selectedRows.value.forEach((row) => {
        const target = allAlerts.value.find((item) => item.id === row.id)
        if (target) target.status = 'resolved'
      })
      ElMessage.success('批量处理成功！')
    })
    .catch(() => {})
}
</script>

<template>
  <div class="alert-container">
    <el-card shadow="never" class="table-card">
      <div class="header-toolbar">
        <el-tabs v-model="activeTab" class="demo-tabs">
          <el-tab-pane label="🔴 待处理告警" name="pending"></el-tab-pane>
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
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="time" label="报警时间" width="160" />
        <el-table-column prop="site" label="报警站点" width="160" />

        <el-table-column prop="level" label="紧急程度" width="100">
          <template #default="scope">
            <el-tag
              :type="
                scope.row.level === '严重'
                  ? 'danger'
                  : scope.row.level === '警告'
                    ? 'warning'
                    : 'info'
              "
              effect="dark"
            >
              {{ scope.row.level }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="desc" label="告警详情" min-width="250" />

        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="scope">
            <el-button
              v-if="scope.row.status === 'pending'"
              type="danger"
              size="small"
              @click="handleProcess(scope.row)"
            >
              去处理
            </el-button>
            <el-button v-else type="success" size="small" disabled plain> 已解决 </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="drawerVisible" title="🛠️ 告警工单处理" size="400px">
      <div class="drawer-content">
        <el-descriptions title="告警基本信息" :column="1" border style="margin-bottom: 20px">
          <el-descriptions-item label="单号">{{ currentAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="站点">{{ currentAlert.site }}</el-descriptions-item>
          <el-descriptions-item label="详情"
            ><span style="color: red">{{ currentAlert.desc }}</span></el-descriptions-item
          >
        </el-descriptions>

        <el-form :model="processForm" label-position="top">
          <el-form-item label="采取的动作">
            <el-select v-model="processForm.action" style="width: 100%">
              <el-option label="维修人员已出发" value="维修人员已出发" />
              <el-option label="系统已自动重启恢复" value="系统已自动重启恢复" />
              <el-option label="误报，直接忽略" value="误报，直接忽略" />
            </el-select>
          </el-form-item>
          <el-form-item label="处理备注 (必填)">
            <el-input
              v-model="processForm.remark"
              type="textarea"
              rows="4"
              placeholder="请输入具体的处理过程..."
            />
          </el-form-item>
        </el-form>

        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">暂不处理</el-button>
          <el-button type="primary" @click="submitProcess">提交并标记为已解决</el-button>
        </div>
      </div>
    </el-drawer>
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
/* 去掉 Tabs 默认底部的外边距，让排版更紧凑 */
:deep(.el-tabs__header) {
  margin: 0;
}
.drawer-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.drawer-footer {
  margin-top: auto; /* 把按钮推到抽屉最底部 */
  padding-top: 20px;
  text-align: right;
  border-top: 1px solid #ebeef5;
}
</style>
