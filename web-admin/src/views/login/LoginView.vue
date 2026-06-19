<template>
  <div class="login-page">
    <div class="login-left">
      <div class="left-content">
        <div class="brand-logo"><span class="logo-emoji">🌬️</span></div>
        <h1 class="brand-title"><span class="title-main">AirInsight</span><span class="title-sub">智能空气分析平台</span></h1>
        <p class="brand-desc">通过 AI 深度分析空气质量数据<br />为企业创造健康、舒适的环境</p>
      </div>
      <div class="decor-circles">
        <div class="circle circle-1"></div><div class="circle circle-2"></div><div class="circle circle-3"></div>
      </div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <div class="card-header"><h2>欢迎回来</h2><p>登录您的账户以继续</p></div>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" class="login-input" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password class="login-input" />
          </el-form-item>
          <el-form-item prop="captcha">
            <div class="captcha-row">
              <el-input v-model="form.captcha" placeholder="验证码" :prefix-icon="Lock" style="flex: 1" />
              <span class="captcha-math" @click="refreshCaptcha" title="点击刷新">{{ captchaExpr }}</span>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">{{ loading ? '登录中...' : '登录' }}</el-button>
          </el-form-item>
        </el-form>

        <div class="login-footer">
          <p class="hint-text">默认账号: <span class="hint-highlight">admin</span> / <span class="hint-highlight">admin123</span></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { login, getCaptcha } from '@/api/auth'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)
const captchaId = ref('')
const captchaExpr = ref('?')

const form = reactive({ username: 'admin', password: 'admin123', captcha: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    if (res.code === 200) {
      captchaId.value = res.data.captcha_id
      captchaExpr.value = res.data.expression
    }
  } catch (e) { /* ignore */ }
}

async function handleLogin() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login(form.username, form.password, captchaId.value, form.captcha)
    if (res.code === 200) {
      userStore.setToken(res.data.token)
      userStore.setUser(res.data.user)
      ElMessage.success('登录成功')
      router.push(route.query.redirect || '/dashboard')
    } else {
      ElMessage.error(res.msg || '登录失败')
      refreshCaptcha()
    }
  } catch (e) {
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(refreshCaptcha)
</script>

<style scoped>
.login-page { display: flex; min-height: 100vh; }
.login-left { flex: 1; background: linear-gradient(135deg, #0066CC 0%, #5856D6 100%); display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; }
.left-content { position: relative; z-index: 1; text-align: center; color: #fff; padding: 60px; }
.brand-logo { width: 80px; height: 80px; border-radius: 20px; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; margin: 0 auto 24px; }
.logo-emoji { font-size: 40px; }
.brand-title { margin-bottom: 16px; }
.title-main { font-size: 36px; font-weight: 700; display: block; }
.title-sub { font-size: 16px; opacity: 0.8; margin-top: 4px; display: block; }
.brand-desc { font-size: 14px; opacity: 0.7; line-height: 1.6; }
.decor-circles { position: absolute; inset: 0; pointer-events: none; }
.circle { position: absolute; border-radius: 50%; border: 2px solid rgba(255,255,255,0.1); }
.circle-1 { width: 400px; height: 400px; top: -100px; right: -100px; }
.circle-2 { width: 300px; height: 300px; bottom: -50px; left: -50px; }
.circle-3 { width: 200px; height: 200px; bottom: 100px; right: 150px; }
.login-right { flex: 1; display: flex; align-items: center; justify-content: center; background: #f5f5f7; }
.login-card { width: 400px; background: #fff; border-radius: 20px; padding: 48px 40px; box-shadow: 0 4px 24px rgba(0,0,0,0.06); }
.card-header { text-align: center; margin-bottom: 32px; }
.card-header h2 { font-size: 24px; font-weight: 700; color: #1d1d1f; margin: 0 0 8px; }
.card-header p { font-size: 14px; color: #6e6e73; margin: 0; }
.login-btn { width: 100%; height: 48px; border-radius: 12px; font-size: 16px; font-weight: 600; }
.login-input :deep(.el-input__wrapper) { border-radius: 10px; }
.login-footer { text-align: center; margin-top: 16px; }
.hint-text { font-size: 13px; color: #aeaeb2; }
.hint-highlight { color: #007AFF; font-weight: 500; }
.captcha-row { display: flex; gap: 12px; align-items: center; }
.captcha-math { flex-shrink: 0; padding: 8px 16px; background: #f5f5f7; border-radius: 10px; font-size: 18px; font-weight: 700; font-family: 'Courier New', monospace; color: #1d1d1f; cursor: pointer; user-select: none; min-width: 100px; text-align: center; }
.captcha-math:hover { background: #e8e8ed; }
@media (max-width: 768px) { .login-left { display: none; } .login-card { width: 90%; padding: 32px 24px; } }
</style>
