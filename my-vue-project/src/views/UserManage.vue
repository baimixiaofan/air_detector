<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAdminUsers, createAdminUser, updateAdminUser, deleteAdminUser } from '@/api/system'

const userList = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)

const dialogVisible = ref(false)
const dialogTitle = ref('新增管理员')
const form = ref({ username: '', password: '', display_name: '', role: 'viewer', status: 1 })
const isEdit = ref(false)
const editId = ref(null)

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await getAdminUsers({ page: page.value, size: 20 })
    userList.value = res.list || []
    total.value = res.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  form.value = { username: '', password: '', display_name: '', role: 'viewer', status: 1 }
  dialogTitle.value = '新增管理员'
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    username: row.username,
    password: '',
    display_name: row.display_name || '',
    role: row.role || 'viewer',
    status: row.status ?? 1
  }
  dialogTitle.value = '编辑管理员'
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!isEdit.value && !form.value.password) {
    ElMessage.warning('请输入密码')
    return
  }
  try {
    if (isEdit.value) {
      const data = { ...form.value }
      if (!data.password) delete data.password
      await updateAdminUser(editId.value, data)
      ElMessage.success('管理员已更新')
    } else {
      await createAdminUser(form.value)
      ElMessage.success('管理员已添加')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch (e) {
    console.error(e)
  }
}

const handleDelete = (row) => {
  if (row.username === 'admin') {
    ElMessage.warning('不能删除默认管理员')
    return
  }
  ElMessageBox.confirm(`确定要删除管理员 "${row.username}" 吗？`, '删除确认', { type: 'warning' })
    .then(async () => {
      await deleteAdminUser(row.id)
      ElMessage.success('管理员已删除')
      fetchUsers()
    })
    .catch(() => {})
}

const roleMap = { admin: '超级管理员', ops: '运维人员', viewer: '查看者' }
const getRoleLabel = (r) => roleMap[r] || r
const getRoleType = (r) => r === 'admin' ? 'danger' : r === 'ops' ? 'warning' : 'info'

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div class="user-manage-container">
    <el-card shadow="never">
      <template #header>
        <div class="header-box">
          <span>👥 管理员管理</span>
          <el-button type="success" icon="Plus" @click="handleAdd">新增管理员</el-button>
        </div>
      </template>

      <el-table :data="userList" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="display_name" label="显示名称" width="150" />
        <el-table-column label="角色" width="120">
          <template #default="scope">
            <el-tag :type="getRoleType(scope.row.role)" effect="dark">
              {{ getRoleLabel(scope.row.role) }}
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
        <el-table-column prop="last_login" label="最后登录" width="180" />
        <el-table-column label="操作" width="150" align="center">
          <template #default="scope">
            <el-button type="primary" link @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > 20">
        <el-pagination background layout="prev, pager, next" :total="total" :page-size="20" :current-page="page" @current-change="(p) => { page = p; fetchUsers() }" />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password :placeholder="isEdit ? '留空则不修改' : '请输入密码'" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="超级管理员" value="admin" />
            <el-option label="运维人员" value="ops" />
            <el-option label="查看者" value="viewer" />
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
.user-manage-container {
  padding-bottom: 20px;
}
.header-box {
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
