<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

const username = ref('admin')
const password = ref('123456')

const handleLogin = () => {
  // 💡 核心逻辑：去花名册里找有没有账号和密码完全匹配的人
  const targetUser = userStore.userList.find(
    (u) => u.username === username.value && u.password === password.value,
  )

  if (targetUser) {
    // 找到了人，还要看看他有没有被拉黑（状态是否为 false）
    if (!targetUser.status) {
      ElMessage.error('🚫 该账号已被禁用，请联系超级管理员！')
      return
    }

    // 校验全部通过，存入 Token、名字和权限角色！
    userStore.login('mock-token-123456', targetUser.username, targetUser.role)

    ElMessage.success(`欢迎回来，${targetUser.nickname}！`)
    router.push('/admin/dataDashboard')
  } else {
    // 找不到人，或者密码不对
    ElMessage.error('❌ 账号或密码错误！')
  }
}
</script>

<template>
  <div class="login-container">
    <el-card class="login-box">
      <h2>🌍 绿盾环境监测 - 厂商平台</h2>
      <el-input v-model="username" placeholder="请输入厂商账号" class="input-field" />
      <el-input
        v-model="password"
        type="password"
        placeholder="请输入密码"
        show-password
        class="input-field"
      />
      <el-button type="primary" class="login-btn" @click="handleLogin">登 录</el-button>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1f2d3d 0%, #304156 100%);
}
.login-box {
  width: 400px;
  text-align: center;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}
.login-box h2 {
  color: #304156;
  margin-bottom: 30px;
  font-size: 20px;
}
.input-field {
  margin-bottom: 20px;
}
.login-btn {
  width: 100%;
  font-size: 16px;
  padding: 12px;
}
</style>
