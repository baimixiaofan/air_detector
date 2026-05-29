<template>
  <div class="error-page">
    <div class="error-card">
      <div class="error-icon">
        <el-icon :size="64" color="#e17055"><Lock /></el-icon>
      </div>
      <h1 class="error-code">403</h1>
      <p class="error-message">抱歉，您没有权限访问此页面</p>
      <el-button type="primary" class="error-btn" @click="$router.push('/dashboard')">返回首页</el-button>
    </div>
  </div>
</template>

<style scoped>
.error-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--page-bg);
}
.error-card {
  text-align: center;
}
.error-icon {
  margin-bottom: 20px;
}
.error-code {
  font-size: 72px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}
.error-message {
  font-size: 16px;
  color: var(--text-muted);
  margin: 0 0 32px;
}
.error-btn {
  height: 44px;
  padding: 0 32px;
  font-size: 15px;
  border-radius: var(--radius-sm);
}
</style>
