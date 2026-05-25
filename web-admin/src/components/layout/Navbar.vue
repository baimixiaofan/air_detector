<template>
  <el-header class="navbar">
    <div class="navbar-left">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="title">{{ title }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="navbar-right">
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-info">
          <el-icon><User /></el-icon>
          {{ userStore.displayName || '管理员' }}
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>个人信息
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { logout as logoutApi } from '@/api/auth'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const title = ref('')

watch(() => route.meta, (meta) => {
  title.value = meta?.title || ''
}, { immediate: true })

function handleCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确认退出登录？', '提示').then(() => {
      logoutApi().finally(() => {
        userStore.clearAuth()
        router.push('/login')
      })
    }).catch(() => {})
  } else if (command === 'profile') {
    // TODO
  }
}
</script>

<style scoped>
.navbar { background: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; border-bottom: 1px solid #e4e7ed; height: 50px; }
.user-info { cursor: pointer; display: flex; align-items: center; gap: 4px; color: #606266; }
.user-info:hover { color: #409eff; }
</style>
