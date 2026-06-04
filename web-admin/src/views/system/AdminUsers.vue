<template>
  <div class="page-container">
    <PageHeader title="用户管理">
      <el-button type="primary" @click="handleAdd"><el-icon><Plus /></el-icon>新增用户</el-button>
    </PageHeader>

    <DashboardCard>
      <el-table :data="tableData" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="display_name" label="显示名称" width="140" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="160">
          <template #default="{ row }">{{ row.last_login ? formatDateTime(row.last_login) : '--' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)"><el-icon><Edit /></el-icon></el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
              <template #reference><el-button link type="danger"><el-icon><Delete /></el-icon></el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="440px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username"><el-input v-model="form.username" :disabled="isEdit" /></el-form-item>
        <el-form-item label="显示名" prop="display_name"><el-input v-model="form.display_name" /></el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password"><el-input v-model="form.password" type="password" show-password /></el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="运维" value="ops" />
            <el-option label="查看者" value="viewer" />
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
import { ref, onMounted } from 'vue'
import { getAdminUsers, createAdminUser, updateAdminUser, deleteAdminUser } from '@/api/system'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import { formatDateTime } from '@/utils/format'
import { ROLES } from '@/utils/constants'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const form = ref({ id: null, username: '', display_name: '', password: '', role: 'viewer' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入显示名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

function roleLabel(r) { return ROLES[r]?.label || r }
function roleTagType(r) { return ROLES[r]?.tagType || '' }

async function fetchData() {
  loading.value = true
  try { const res = await getAdminUsers(); if (res.code === 200) tableData.value = res.data || [] }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

function handleAdd() { isEdit.value = false; form.value = { id: null, username: '', display_name: '', password: '', role: 'viewer' }; dialogVisible.value = true }
function handleEdit(row) { isEdit.value = true; form.value = { ...row, password: '' }; dialogVisible.value = true }
async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    isEdit.value ? await updateAdminUser(form.value.id, form.value) : await createAdminUser(form.value)
    ElMessage.success('保存成功'); dialogVisible.value = false; fetchData()
  } catch (e) { ElMessage.error('操作失败') }
  finally { submitting.value = false }
}
async function handleDelete(id) {
  try { await deleteAdminUser(id); ElMessage.success('删除成功'); fetchData() }
  catch (e) { ElMessage.error('删除失败') }
}

onMounted(fetchData)
</script>
