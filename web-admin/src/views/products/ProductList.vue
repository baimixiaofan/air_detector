<template>
  <div class="page-container">
    <PageHeader title="产品型号" subtitle="管理监测设备的产品线和型号信息">
      <el-button type="primary" @click="openDialog()"><el-icon><Plus /></el-icon>新增型号</el-button>
    </PageHeader>

    <DashboardCard>
      <el-table :data="products" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="产品型号" min-width="160" />
        <el-table-column prop="product_line" label="产品线" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.product_line || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sensor_types" label="传感器" min-width="180" />
        <el-table-column prop="device_count" label="设备数" width="90" align="center">
          <template #default="{ row }">
            <span style="font-weight: 600; color: var(--color-primary);">{{ row.device_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
              {{ row.status === 1 ? '在售' : '停产' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openDialog(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑产品型号' : '新增产品型号'" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="产品型号" required>
          <el-input v-model="form.name" placeholder="如：AirMonitor Pro 2025" />
        </el-form-item>
        <el-form-item label="产品线">
          <el-select v-model="form.product_line" placeholder="选择产品线" allow-create style="width: 100%;">
            <el-option label="Pro 系列" value="Pro系列" />
            <el-option label="Lite 系列" value="Lite系列" />
            <el-option label="基础系列" value="基础系列" />
          </el-select>
        </el-form-item>
        <el-form-item label="传感器">
          <el-checkbox-group v-model="sensorList">
            <el-checkbox value="PM2.5" label="PM2.5" />
            <el-checkbox value="PM10" label="PM10" />
            <el-checkbox value="NO₂" label="NO₂" />
            <el-checkbox value="SO₂" label="SO₂" />
            <el-checkbox value="O₃" label="O₃" />
            <el-checkbox value="CO" label="CO" />
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="产品描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="产品特点和适用场景" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" :active-value="1" :inactive-value="0" active-text="在售" inactive-text="停产" />
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
import { getProducts, createProduct, updateProduct, deleteProduct } from '@/api/products'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'

const loading = ref(false)
const submitting = ref(false)
const products = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref({ name: '', product_line: '', sensor_types: '', description: '', status: 1 })
const sensorList = ref([])

const sensorStr = computed(() => sensorList.value.join(','))

async function fetchProducts() {
  loading.value = true
  try {
    const res = await getProducts()
    if (res.code === 200) products.value = res.data
  } finally { loading.value = false }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    form.value = { ...row }
    sensorList.value = row.sensor_types ? row.sensor_types.split(',') : []
  } else {
    editingId.value = null
    form.value = { name: '', product_line: '', sensor_types: '', description: '', status: 1 }
    sensorList.value = ['PM2.5', 'PM10', 'NO₂', 'SO₂', 'O₃']
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name) return ElMessage.warning('请填写产品型号')
  submitting.value = true
  form.value.sensor_types = sensorStr.value
  try {
    if (editingId.value) {
      await updateProduct(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createProduct(form.value)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    fetchProducts()
  } finally { submitting.value = false }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除产品型号「${row.name}」？`, '提示')
  await deleteProduct(row.id)
  ElMessage.success('已删除')
  fetchProducts()
}

onMounted(fetchProducts)
</script>
