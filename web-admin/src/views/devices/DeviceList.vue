<template>
  <div class="page-container">
    <PageHeader title="设备管理" :subtitle="`共 ${tableData.length} 台设备`">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>添加设备
      </el-button>
    </PageHeader>

    <FilterBar>
      <el-select v-model="filters.status" placeholder="在线状态" clearable>
        <el-option label="在线" value="online" />
        <el-option label="离线" value="offline" />
      </el-select>
      <el-select v-model="filters.siteId" placeholder="绑定站点" clearable>
        <el-option v-for="s in sites" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="搜索设备编码" clearable prefix-icon="Search" />
    </FilterBar>

    <DashboardCard>
      <el-table :data="filteredData" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="device_id" label="设备编码" min-width="150" />
        <el-table-column prop="location" label="位置" min-width="150" />
        <el-table-column label="经纬度" width="180">
          <template #default="{ row }">
            <span v-if="row.latitude && row.longitude">{{ row.latitude }}, {{ row.longitude }}</span>
            <span v-else class="text-muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="在线状态" width="100">
          <template #default="{ row }">
            <span class="status-badge" :class="row.online ? 'status-badge--success' : 'status-badge--default'">
              <span class="status-dot" :class="{ 'status-dot--pulse': row.online }"></span>
              {{ row.online ? '在线' : '离线' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="绑定站点" width="140">
          <template #default="{ row }">
            <span v-if="row.site_name">{{ row.site_name }}</span>
            <span v-else class="text-muted">未绑定</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="filteredData.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
        />
      </div>
    </DashboardCard>

    <!-- Create/Edit Drawer -->
    <el-drawer v-model="drawerVisible" :title="isEdit ? '编辑设备' : '添加设备'" size="420px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="设备编码" prop="device_id">
          <el-input v-model="form.device_id" placeholder="如：192.168.1.100" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="form.location" placeholder="请输入设备位置" />
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="form.latitude" :precision="6" :step="0.001" style="width: 100%" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="form.longitude" :precision="6" :step="0.001" style="width: 100%" />
        </el-form-item>
        <el-form-item label="绑定站点">
          <el-select v-model="form.site_id" placeholder="选择站点" clearable style="width: 100%">
            <el-option v-for="s in sites" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDevices, createDevice, updateDevice, deleteDevice } from '@/api/devices'
import { getSites } from '@/api/sites'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import { formatDateTime } from '@/utils/format'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const sites = ref([])
const drawerVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const filters = ref({ status: '', siteId: '', keyword: '' })
const pagination = ref({ page: 1, size: 20 })

const form = ref({
  id: null,
  device_id: '',
  location: '',
  latitude: null,
  longitude: null,
  site_id: null
})

const rules = {
  device_id: [{ required: true, message: '请输入设备编码', trigger: 'blur' }],
  location: [{ required: true, message: '请输入位置', trigger: 'blur' }]
}

const filteredData = computed(() => {
  return tableData.value.filter(d => {
    if (filters.value.status === 'online' && !d.online) return false
    if (filters.value.status === 'offline' && d.online) return false
    if (filters.value.siteId && d.site_id !== filters.value.siteId) return false
    if (filters.value.keyword && !d.device_id.includes(filters.value.keyword)) return false
    return true
  })
})

async function fetchData() {
  loading.value = true
  try {
    const res = await getDevices()
    if (res.code === 200) {
      tableData.value = res.data || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchSites() {
  try {
    const res = await getSites()
    if (res.code === 200) {
      sites.value = res.data || []
    }
  } catch (e) {
    console.error(e)
  }
}

function handleAdd() {
  isEdit.value = false
  form.value = { id: null, device_id: '', location: '', latitude: null, longitude: null, site_id: null }
  drawerVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  form.value = { ...row }
  drawerVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateDevice(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createDevice(form.value)
      ElMessage.success('创建成功')
    }
    drawerVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteDevice(id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchData()
  fetchSites()
})
</script>

<style scoped>
.table-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.text-muted {
  color: var(--text-muted);
}
</style>
