<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
// 💡 1. 引入你组员写好的真实后端登录接口
import { login } from '@/api/auth'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()

const username = ref('admin')
const password = ref('admin123')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  loading.value = true
  try {
    const res = await login(username.value, password.value)

    // 用 store 统一管理 token 和用户信息
    userStore.login(res.token, res.user.username, res.user.role)

    ElMessage.success(`欢迎回来，${res.user.display_name || res.user.username}！`)
    router.push('/admin/dataDashboard')
  } catch (error) {
    console.error('登录异常:', error)
  } finally {
    loading.value = false
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
