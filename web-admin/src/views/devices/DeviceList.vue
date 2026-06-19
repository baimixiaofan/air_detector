<template>
  <div class="page-container">
    <PageHeader title="设备管理" :subtitle="`共 ${tableData.length} 台，已激活 ${statusCount('activated')} 台`">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>出厂添加设备
      </el-button>
    </PageHeader>

    <DashboardCard>
      <el-table :data="filteredData" v-loading="loading" stripe max-height="600">
        <el-table-column prop="device_id" label="设备编码" min-width="160" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.activation_status === 'manufactured'" type="info" size="small">已出厂未激活</el-tag>
            <el-tag v-else-if="row.activation_status === 'activated'" :type="row.online ? 'success' : 'warning'" size="small">
              {{ row.online ? '在线' : '已激活离线' }}
            </el-tag>
            <el-tag v-else type="danger" size="small">已注销</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="位置" min-width="140">
          <template #default="{ row }">
            {{ [row.district, roomMap[row.room_location]].filter(Boolean).join(' · ') || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="客户" width="120">
          <template #default="{ row }">{{ row.customer_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.activation_status === 'manufactured'" text type="success" size="small" @click="handleActivate(row)">激活</el-button>
            <el-button text type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">注销</el-button>
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑设备' : '出厂添加设备'" width="480px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="设备名称" required>
          <el-input v-model="form.name" placeholder="如：办公室监测仪" />
        </el-form-item>
        <div v-if="!isEdit" class="device-id-hint">
          保存后将自动生成设备编码（AQ-YYYYMMDD-NNN），用户可在小程序中绑定设备并获取位置信息
        </div>
        <template v-if="isEdit">
          <el-form-item label="位置">
            <el-input v-model="form.district" placeholder="区/县（用户绑定后自动填充）" />
          </el-form-item>
          <el-form-item label="房间">
            <el-select v-model="form.room_location" placeholder="选择位置" clearable style="width:100%">
              <el-option label="客厅" value="living_room" />
              <el-option label="卧室" value="bedroom" />
              <el-option label="厨房" value="kitchen" />
              <el-option label="书房" value="study" />
              <el-option label="阳台" value="balcony" />
              <el-option label="餐厅" value="dining_room" />
              <el-option label="卫生间" value="bathroom" />
              <el-option label="门厅" value="hall" />
            </el-select>
          </el-form-item>
          <el-form-item label="绑定客户">
            <el-select v-model="form.customer_id" placeholder="可选" clearable style="width:100%">
              <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="经纬度">
            <div style="display:flex;gap:8px">
              <el-input-number v-model="form.latitude" :precision="2" placeholder="纬度" style="flex:1" />
              <el-input-number v-model="form.longitude" :precision="2" placeholder="经度" style="flex:1" />
            </div>
          </el-form-item>
        </template>
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
import { getDevices, createDevice, updateDevice, deleteDevice } from '@/api/devices'
import { getCustomers } from '@/api/customers'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const submitting = ref(false)
const tableData = ref([])
const customers = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const filters = ref({ keyword: '' })

const form = ref({
  name: '', district: '', room_location: '',
  customer_id: null, latitude: null, longitude: null, _id: null
})

const roomMap = {
  living_room: '客厅', bedroom: '卧室', kitchen: '厨房',
  study: '书房', balcony: '阳台', dining_room: '餐厅', bathroom: '卫生间', hall: '门厅'
}

const filteredData = computed(() => {
  return tableData.value.filter(d => {
    if (filters.value.keyword && !d.device_id?.includes(filters.value.keyword) && !d.name?.includes(filters.value.keyword)) return false
    return true
  })
})

function statusCount(s) {
  return tableData.value.filter(d => d.activation_status === s).length
}

async function fetchData() {
  loading.value = true
  try {
    const [devRes, cusRes] = await Promise.all([getDevices(), getCustomers()])
    if (devRes.code === 200) {
      tableData.value = Array.isArray(devRes.data) ? devRes.data : (devRes.data?.list || [])
    }
    if (cusRes.code === 200) customers.value = cusRes.data || []
  } finally { loading.value = false }
}

function handleAdd() {
  isEdit.value = false
  form.value = { name: '', district: '', room_location: '', customer_id: null, latitude: null, longitude: null, _id: null }
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  form.value = {
    name: row.name || '', district: row.district || '',
    room_location: row.room_location || '', customer_id: row.customer_id || null,
    latitude: row.latitude, longitude: row.longitude, _id: row.id
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (isEdit.value) {
    if (!form.value.name) return ElMessage.warning('请填写名称')
    submitting.value = true
    try {
      const res = await updateDevice(form.value._id, form.value)
      if (res.code === 200) ElMessage.success('已更新')
      dialogVisible.value = false; fetchData()
    } finally { submitting.value = false }
    return
  }
  if (!form.value.name) return ElMessage.warning('请填写设备名称')
  submitting.value = true
  try {
    const res = await createDevice(form.value)
    if (res.code === 200) {
      ElMessage.success(`设备 ${res.data.device_id} 已添加（未激活）`)
      dialogVisible.value = false; fetchData()
    }
  } finally { submitting.value = false }
}

async function handleActivate(row) {
  await ElMessageBox.confirm(`确认激活「${row.device_id}」？`, '激活确认')
  const res = await updateDevice(row.id, { activation_status: 'activated' })
  if (res.code === 200) { ElMessage.success('已激活'); fetchData() }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认注销「${row.device_id}」？`, '提示')
  const res = await deleteDevice(row.device_id)
  if (res.code === 200) { ElMessage.success('已注销'); fetchData() }
}

onMounted(fetchData)
</script>

<style scoped>
.device-id-hint {
  margin: -8px 0 16px 100px;
  font-size: 12px;
  color: #aeaeb2;
  line-height: 1.5;
  padding: 10px 14px;
  background: #f5f5f7;
  border-radius: 8px;
}
</style>
