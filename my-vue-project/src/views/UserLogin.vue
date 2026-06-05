<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
// 💡 1. 引入你组员写好的真实后端登录接口
import { login } from '@/api/auth'

const router = useRouter()

const username = ref('admin')
const password = ref('123456')
const loading = ref(false) // 增加一个 loading 状态，让点击时有转圈效果

const handleLogin = async () => {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  loading.value = true
  try {
    // 💡 2. 核心逻辑：向真实的后端发起请求！
    // 这行代码会带着账号密码跑到 admin_api.py 里去校验
    const res = await login(username.value, password.value)

    // 💡 3. 极其重要：把后端返回的真实 Token 存进浏览器的保险箱！
    // 名字必须叫 'admin_token'，因为你的 request.js 拦截器里就是找这个名字去拿的
    localStorage.setItem('admin_token', res.token)
    localStorage.setItem('admin_user', JSON.stringify(res.user))

    ElMessage.success(`欢迎回来，${res.user.display_name || res.user.username}！`)

    // 登录成功，跳转到大屏数据看板
    router.push('/admin/dataDashboard')
  } catch (error) {
    // 密码错误等拦截器已经自动弹窗提示了，这里只需接住异常防止代码崩溃
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
