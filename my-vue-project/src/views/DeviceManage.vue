<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDevices, createDevice, updateDevice, deleteDevice } from '@/api/devices'
import { getSites } from '@/api/sites'

const tableData = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const loading = ref(false)
const keyword = ref('')
const siteList = ref([])

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新增设备')
const form = ref({ name: '', device_id: '', site_id: null, status: 1 })
const isEdit = ref(false)
const editId = ref(null)

const fetchDevices = async () => {
  loading.value = true
  try {
    const res = await getDevices({ page: page.value, size: size.value, keyword: keyword.value })
    tableData.value = res.list || []
    total.value = res.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const fetchSites = async () => {
  try {
    const res = await getSites({ page: 1, size: 100 })
    siteList.value = res.list || []
  } catch (e) {
    console.error(e)
  }
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  form.value = { name: '', device_id: '', site_id: null, status: 1 }
  dialogTitle.value = '新增设备'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    name: row.name || '',
    device_id: row.device_id || '',
    site_id: row.site?.site_id || null,
    status: row.status ?? 1
  }
  dialogTitle.value = '编辑设备'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.name || !form.value.device_id) {
    ElMessage.warning('请填写设备名称和设备ID')
    return
  }
  try {
    if (isEdit.value) {
      await updateDevice(editId.value, form.value)
      ElMessage.success('设备已更新')
    } else {
      await createDevice(form.value)
      ElMessage.success('设备已添加')
    }
    dialogVisible.value = false
    fetchDevices()
  } catch (e) {
    console.error(e)
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除设备 "${row.name}" 吗？`, '删除确认', { type: 'warning' })
    .then(async () => {
      await deleteDevice(row.id)
      ElMessage.success('设备已删除')
      fetchDevices()
    })
    .catch(() => {})
}

const handlePageChange = (newPage) => {
  page.value = newPage
  fetchDevices()
}

const handleSearch = () => {
  page.value = 1
  fetchDevices()
}

onMounted(() => {
  fetchDevices()
  fetchSites()
})
</script>

<template>
  <div class="device-manage-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>⚙️ 设备状态监控</span>
          <div>
            <el-input v-model="keyword" placeholder="搜索设备名称/ID" style="width: 200px; margin-right: 10px" clearable @clear="handleSearch" @keyup.enter="handleSearch" />
            <el-button type="primary" @click="handleAdd">新增设备</el-button>
          </div>
        </div>
      </template>

      <el-table :data="tableData" border style="width: 100%" v-loading="loading">
        <el-table-column prop="device_id" label="设备编号" width="150" />
        <el-table-column prop="name" label="设备名称" min-width="150" />
        <el-table-column label="所属站点" min-width="150">
          <template #default="scope">
            {{ scope.row.site?.site_name || '未绑定' }}
          </template>
        </el-table-column>
        <el-table-column label="在线状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.online ? 'success' : 'info'" effect="dark" size="small">
              {{ scope.row.online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'" size="small">
              {{ scope.row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="scope">
            <el-button type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > size">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="size"
          :current-page="page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="设备名称">
          <el-input v-model="form.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备ID">
          <el-input v-model="form.device_id" placeholder="请输入设备ID" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="所属站点">
          <el-select v-model="form.site_id" placeholder="选择站点" clearable style="width: 100%">
            <el-option v-for="s in siteList" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
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
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
