<template>
  <div class="page-container">
    <PageHeader title="设备管理" :subtitle="`共 ${tableData.length} 台设备`">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>添加设备
      </el-button>
    </PageHeader>

    <DashboardCard>
      <el-table :data="filteredData" v-loading="loading" stripe max-height="600">
        <el-table-column prop="device_id" label="设备编码" min-width="150" />
        <el-table-column prop="location" label="位置/名称" min-width="150">
          <template #default="{ row }">{{ row.location || row.name || '-' }}</template>
        </el-table-column>
        <el-table-column label="经纬度" width="180">
          <template #default="{ row }">
            <span v-if="row.latitude && row.longitude">{{ row.latitude }}, {{ row.longitude }}</span>
            <span v-else class="text-muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="在线状态" width="100" align="center">
          <template #default="{ row }">
            <span class="status-badge" :class="row.online ? 'status-badge--success' : 'status-badge--default'">
              <span class="status-dot" :class="{ 'status-dot--pulse': row.online }"></span>
              {{ row.online ? '在线' : '离线' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="90">
          <template #default="{ row }">
            <el-tag :type="row.source === 'config' ? '' : 'primary'" size="small">
              {{ row.source === 'config' ? '配置文件' : 'MySQL' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            <span v-if="row.created_at">{{ formatDateTime(row.created_at) }}</span>
            <span v-else class="text-muted">配置文件</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>

    <!-- 新增设备对话框 -->
    <el-dialog v-model="dialogVisible" title="添加设备" width="460px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="设备编码" required>
          <el-input v-model="form.device_id" placeholder="如：CQ_008" />
        </el-form-item>
        <el-form-item label="设备名称" required>
          <el-input v-model="form.name" placeholder="如：重庆-江北嘴" />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="form.latitude" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="form.longitude" :precision="2" style="width: 100%" />
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
import { ref, computed, onMounted } from 'vue'
import { getDevices, createDevice, deleteDevice } from '@/api/devices'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import { formatDateTime } from '@/utils/format'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const submitting = ref(false)

const filters = ref({ status: '', keyword: '' })

const form = ref({
  device_id: '',
  name: '',
  latitude: null,
  longitude: null
})

const filteredData = computed(() => {
  return tableData.value.filter(d => {
    if (filters.value.status === 'online' && !d.online) return false
    if (filters.value.status === 'offline' && d.online) return false
    if (filters.value.keyword && !d.device_id.includes(filters.value.keyword)) return false
    return true
  })
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getDevices()
    if (res.code === 200) {
      tableData.value = Array.isArray(res.data) ? res.data : (res.data?.list || [])
    }
  } finally { loading.value = false }
}

function handleAdd() {
  form.value = { device_id: '', name: '', latitude: null, longitude: null }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.device_id || !form.value.name) {
    return ElMessage.warning('请填写设备编码和名称')
  }
  submitting.value = true
  try {
    const res = await createDevice(form.value)
    if (res.code === 200) {
      ElMessage.success('设备已添加，已同步到 device_config.json')
      dialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(res.msg || '添加失败')
    }
  } finally { submitting.value = false }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除设备「${row.device_id}」？同时会从配置文件中移除。`, '提示')
    // 直接调 API 删除 JSON 中的设备
    const res = await deleteDevice(row.device_id)
    if (res.code === 200) {
      ElMessage.success('已删除')
      fetchData()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch { /* cancelled */ }
}

onMounted(fetchData)
</script>
