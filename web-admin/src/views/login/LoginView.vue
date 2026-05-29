<template>
  <div class="login-container">
    <div class="login-left">
      <div class="login-brand">
        <div class="brand-icon">
          <el-icon :size="40" color="#fff"><Monitor /></el-icon>
        </div>
        <h1 class="brand-title">空气质量监测</h1>
        <p class="brand-subtitle">企业级环境数据管理平台</p>
      </div>
      <div class="brand-features">
        <div class="feature-item">
          <el-icon :size="20" color="rgba(255,255,255,0.8)"><TrendCharts /></el-icon>
          <span>实时数据监控</span>
        </div>
        <div class="feature-item">
          <el-icon :size="20" color="rgba(255,255,255,0.8)"><Warning /></el-icon>
          <span>智能告警分析</span>
        </div>
        <div class="feature-item">
          <el-icon :size="20" color="rgba(255,255,255,0.8)"><Document /></el-icon>
          <span>数据报表生成</span>
        </div>
      </div>
    </div>
    <div class="login-right">
      <div class="login-card">
        <div class="login-header">
          <div class="login-logo">
            <el-icon :size="28" color="#e17055"><Monitor /></el-icon>
          </div>
          <h2 class="login-title">欢迎回来</h2>
          <p class="login-desc">请登录您的管理账号</p>
        </div>
        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>
        <p class="login-hint">默认账号: admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { login } from '@/api/auth'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: 'admin', password: 'admin123' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login(form.username, form.password)
    if (res.code === 200) {
      userStore.setToken(res.data.token)
      userStore.setUser(res.data.user)
      ElMessage.success('登录成功')
      router.push(route.query.redirect || '/dashboard')
    } else {
      ElMessage.error(res.msg || '登录失败')
    }
  } catch (e) {
    // 错误已在 request.js 拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
}

.login-left {
  flex: 1;
  background: var(--color-primary-gradient);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px;
  position: relative;
  overflow: hidden;
}
.login-left::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
}
.login-left::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: -10%;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
}

.login-brand {
  position: relative;
  z-index: 1;
}
.brand-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}
.brand-title {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 8px;
}
.brand-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
}

.brand-features {
  position: relative;
  z-index: 1;
  margin-top: 48px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
}

.login-right {
  width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}

.login-card {
  width: 360px;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}
.login-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--color-primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}
.login-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.login-desc {
  font-size: 14px;
  color: var(--text-muted);
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  border-radius: var(--radius-sm);
}

.login-hint {
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .login-left { display: none; }
  .login-right { width: 100%; }
}
</style>
