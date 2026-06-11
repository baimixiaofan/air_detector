<template>
  <div class="page-container">
    <PageHeader title="客户管理" subtitle="管理 B 端客户信息（地产商/酒店/学校/医院）">
      <el-button type="primary" @click="openDialog()"><el-icon><Plus /></el-icon>新增客户</el-button>
    </PageHeader>

    <FilterBar>
      <el-select v-model="filters.type" placeholder="客户类型" clearable style="width: 140px;">
        <el-option label="企业客户" value="enterprise" />
        <el-option label="个人客户" value="individual" />
      </el-select>
      <el-select v-model="filters.industry" placeholder="行业" clearable style="width: 140px;">
        <el-option label="地产" value="地产" />
        <el-option label="酒店" value="酒店" />
        <el-option label="学校" value="学校" />
        <el-option label="医院" value="医院" />
        <el-option label="办公" value="办公" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px;">
        <el-option label="活跃" value="active" />
        <el-option label="停用" value="inactive" />
      </el-select>
      <el-button @click="fetchCustomers"><el-icon><Search /></el-icon>查询</el-button>
    </FilterBar>

    <DashboardCard>
      <el-table :data="customers" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="客户名称" min-width="160" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'enterprise' ? 'primary' : 'success'" size="small">
              {{ row.type === 'enterprise' ? '企业' : '个人' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业" width="90">
          <template #default="{ row }">{{ row.industry || '-' }}</template>
        </el-table-column>
        <el-table-column prop="contact_name" label="联系人" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="device_count" label="设备数" width="80" align="center">
          <template #default="{ row }">
            <span style="font-weight: 600; color: var(--color-primary);">{{ row.device_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '活跃' : '停用' }}
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
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑客户' : '新增客户'" width="560px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="客户名称" required>
          <el-input v-model="form.name" placeholder="如：XX地产集团" />
        </el-form-item>
        <el-form-item label="客户类型">
          <el-radio-group v-model="form.type">
            <el-radio value="enterprise">企业客户</el-radio>
            <el-radio value="individual">个人客户</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="行业">
          <el-select v-model="form.industry" placeholder="选择行业" allow-create style="width: 100%;">
            <el-option label="地产" value="地产" />
            <el-option label="酒店" value="酒店" />
            <el-option label="学校" value="学校" />
            <el-option label="医院" value="医院" />
            <el-option label="办公" value="办公" />
            <el-option label="工厂" value="工厂" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_name" placeholder="联系人姓名" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" placeholder="联系电话" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="邮箱地址" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" placeholder="客户地址" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" active-value="active" inactive-value="inactive" active-text="活跃" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="备注信息" />
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
import { ref, reactive, onMounted } from 'vue'
import { getCustomers, createCustomer, updateCustomer, deleteCustomer } from '@/api/customers'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'

const loading = ref(false)
const submitting = ref(false)
const customers = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const filters = reactive({ type: '', industry: '', status: '' })
const form = ref({
  name: '', type: 'enterprise', contact_name: '', phone: '', email: '',
  address: '', industry: '', status: 'active', notes: ''
})

async function fetchCustomers() {
  loading.value = true
  try {
    const params = {}
    if (filters.type) params.type = filters.type
    if (filters.industry) params.industry = filters.industry
    if (filters.status) params.status = filters.status
    const res = await getCustomers(params)
    if (res.code === 200) customers.value = res.data
  } finally { loading.value = false }
}

function openDialog(row) {
  if (row) {
    editingId.value = row.id
    form.value = { ...row }
  } else {
    editingId.value = null
    form.value = { name: '', type: 'enterprise', contact_name: '', phone: '', email: '', address: '', industry: '', status: 'active', notes: '' }
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name) return ElMessage.warning('请填写客户名称')
  submitting.value = true
  try {
    if (editingId.value) {
      await updateCustomer(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createCustomer(form.value)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    fetchCustomers()
  } finally { submitting.value = false }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除客户「${row.name}」？`, '提示')
  await deleteCustomer(row.id)
  ElMessage.success('已删除')
  fetchCustomers()
}

onMounted(fetchCustomers)
</script>
