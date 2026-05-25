<template>
  <div class="error-page">
    <h1>403</h1>
    <p>抱歉，您没有权限访问此页面</p>
    <el-button type="primary" @click="$router.push('/dashboard')">返回首页</el-button>
  </div>
</template>
<style scoped>
.error-page { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
h1 { font-size: 80px; color: #f56c6c; margin: 0; }
p { font-size: 18px; color: #909399; margin: 16px 0; }
</style>
