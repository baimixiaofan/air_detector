<template>
  <div class="page-container">
    <PageHeader title="售后工单" subtitle="设备故障报修、维修记录与处理流程管理">
      <el-button type="primary" @click="openDialog()"><el-icon><Plus /></el-icon>新建工单</el-button>
    </PageHeader>

    <FilterBar>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 130px;">
        <el-option label="待处理" value="pending" />
        <el-option label="处理中" value="processing" />
        <el-option label="待验收" value="review" />
        <el-option label="已关闭" value="closed" />
      </el-select>
      <el-select v-model="filters.priority" placeholder="优先级" clearable style="width: 130px;">
        <el-option label="紧急" value="urgent" />
        <el-option label="高" value="high" />
        <el-option label="中" value="medium" />
        <el-option label="低" value="low" />
      </el-select>
      <el-select v-model="filters.type" placeholder="类型" clearable style="width: 130px;">
        <el-option label="故障" value="fault" />
        <el-option label="维修" value="repair" />
        <el-option label="巡检" value="inspection" />
        <el-option label="投诉" value="complaint" />
      </el-select>
      <el-button @click="fetchOrders"><el-icon><Search /></el-icon>查询</el-button>
    </FilterBar>

    <!-- 统计卡片 -->
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px;">
      <StatCard title="待处理" :value="statusCount('pending')" variant="light" icon="Warning" />
      <StatCard title="处理中" :value="statusCount('processing')" variant="light" icon="Loading" />
      <StatCard title="待验收" :value="statusCount('review')" variant="light" icon="CircleCheck" />
      <StatCard title="已关闭" :value="statusCount('closed')" variant="light" icon="CircleCheckFilled" />
    </div>

    <DashboardCard>
      <el-table :data="orders" v-loading="loading" stripe>
        <el-table-column prop="order_no" label="工单编号" width="160" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="typeMap[row.type]?.tag" size="small">{{ typeMap[row.type]?.label || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="priorityMap[row.priority]?.tag" size="small" effect="dark">
              {{ priorityMap[row.priority]?.label || row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户" width="140">
          <template #default="{ row }">{{ row.customer_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="assignee" label="处理人" width="100">
          <template #default="{ row }">{{ row.assignee || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.tag" size="small">
              {{ statusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="110">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-button v-if="row.status !== 'closed'" text type="success" size="small" @click="handleClose(row)">关闭</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑工单' : '新建工单'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" placeholder="工单标题" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" style="width: 100%;">
            <el-option label="故障报修" value="fault" />
            <el-option label="维修" value="repair" />
            <el-option label="巡检" value="inspection" />
            <el-option label="投诉" value="complaint" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="form.priority" style="width: 100%;">
            <el-option label="紧急" value="urgent" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联设备">
          <el-input v-model="form.device_id" placeholder="设备ID（可选）" />
        </el-form-item>
        <el-form-item label="处理人">
          <el-input v-model="form.assignee" placeholder="指派给谁" />
        </el-form-item>
        <el-form-item label="问题描述">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="详细描述问题" />
        </el-form-item>
        <el-form-item label="处理结果" v-if="editingId">
          <el-input v-model="form.result" type="textarea" :rows="3" placeholder="处理结果记录" />
        </el-form-item>
        <el-form-item label="状态" v-if="editingId">
          <el-select v-model="form.status" style="width: 100%;">
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="待验收" value="review" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getWorkOrders, createWorkOrder, updateWorkOrder, deleteWorkOrder } from '@/api/workorders'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import StatCard from '@/components/common/StatCard.vue'

const loading = ref(false)
const submitting = ref(false)
const orders = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const filters = reactive({ status: '', priority: '', type: '' })

const form = ref({
  title: '', type: 'fault', priority: 'medium', device_id: '',
  customer_id: null, assignee: '', description: '', result: '', status: 'pending'
})

const typeMap = {
  fault: { label: '故障', tag: 'danger' },
  repair: { label: '维修', tag: 'warning' },
  inspection: { label: '巡检', tag: 'primary' },
  complaint: { label: '投诉', tag: 'info' }
}
const priorityMap = {
  urgent: { label: '紧急', tag: 'danger' },
  high: { label: '高', tag: 'warning' },
  medium: { label: '中', tag: '' },
  low: { label: '低', tag: 'info' }
}
const statusMap = {
  pending: { label: '待处理', tag: 'warning' },
  processing: { label: '处理中', tag: 'primary' },
  review: { label: '待验收', tag: 'info' },
  closed: { label: '已关闭', tag: 'success' }
}

function statusCount(status) {
  return orders.value.filter(o => o.status === status).length
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN')
}

async function fetchOrders() {
  loading.value = true
  try {
    const params = {}
    if (filters.status) params.status = filters.status
    if (filters.priority) params.priority = filters.priority
    if (filters.type) params.type = filters.type
    const res = await getWorkOrders(params)
    if (res.code === 200) orders.value = res.data
  } finally { loading.value = false }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    form.value = { ...row }
  } else {
    editingId.value = null
    form.value = { title: '', type: 'fault', priority: 'medium', device_id: '', customer_id: null, assignee: '', description: '', result: '', status: 'pending' }
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.title) return ElMessage.warning('请填写工单标题')
  submitting.value = true
  try {
    if (editingId.value) {
      await updateWorkOrder(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      const res = await createWorkOrder(form.value)
      ElMessage.success(`工单 ${res.data.order_no} 创建成功`)
    }
    dialogVisible.value = false
    fetchOrders()
  } finally { submitting.value = false }
}

async function handleClose(row) {
  await ElMessageBox.confirm('确认关闭此工单？', '提示')
  await updateWorkOrder(row.id, { status: 'closed' })
  ElMessage.success('工单已关闭')
  fetchOrders()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除工单「${row.order_no}」？`, '提示')
  await deleteWorkOrder(row.id)
  ElMessage.success('已删除')
  fetchOrders()
}

onMounted(fetchOrders)
</script>
