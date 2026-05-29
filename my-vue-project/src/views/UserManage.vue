<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'

const userStore = useUserStore()

// 状态切换时提示
const handleStatusChange = (row) => {
  const state = row.status ? '启用' : '禁用'
  ElMessage.info(`已将用户 ${row.username} 状态修改为：${state}`)
  // 因为我们在 store 里加了 watch 深度监听，这里开关状态一变，缓存会自动更新！
}

// 💡 编辑相关的逻辑
const dialogVisible = ref(false)
const editForm = ref({}) // 用来存放当前正在编辑的用户数据

// 点击编辑按钮
const handleEdit = (row) => {
  // 把当前行的数据“拷贝”一份给表单，避免还没点保存表格就跟着变
  editForm.value = { ...row }
  dialogVisible.value = true
}

// 点击弹窗里的“保存”
const saveEdit = () => {
  // 在仓库的用户名单里找到要修改的那个人，并把新数据覆盖过去
  const index = userStore.userList.findIndex((u) => u.id === editForm.value.id)
  if (index !== -1) {
    userStore.userList[index] = { ...editForm.value }
    ElMessage.success(`用户 ${editForm.value.username} 信息已更新！`)
  }
  dialogVisible.value = false
}
</script>

<template>
  <div class="user-manage-container">
    <el-card shadow="never">
      <template #header>
        <div class="header-box">
          <div class="left">
            <el-input placeholder="搜索用户名" style="width: 250px; margin-right: 15px" />
            <el-button type="primary">查询</el-button>
          </div>
          <el-button type="success" icon="Plus" @click="ElMessage.success('新增功能可自行挑战')"
            >新增成员</el-button
          >
        </div>
      </template>

      <el-table :data="userStore.userList" border stripe>
        <el-table-column prop="username" label="登录账号(用户名)" width="150" />
        <el-table-column prop="password" label="登录密码" width="120" />
        <el-table-column prop="nickname" label="人员昵称" width="150" />
        <el-table-column prop="role" label="系统角色">
          <template #default="scope">
            <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'">
              {{ scope.row.role === 'admin' ? '超级管理员' : '普通操作员' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="账号状态" width="100" align="center">
          <template #default="scope">
            <el-switch v-model="scope.row.status" @change="handleStatusChange(scope.row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center">
          <template #default="scope">
            <el-button type="primary" link @click="handleEdit(scope.row)">编辑</el-button>
            <el-button type="danger" link>删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="✏️ 编辑用户资料" width="400px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="登录密码">
          <el-input v-model="editForm.password" />
        </el-form-item>
        <el-form-item label="系统角色">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option label="超级管理员 (admin)" value="admin" />
            <el-option label="普通操作员 (operator)" value="operator" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">确认修改</el-button>
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
}
</style>
