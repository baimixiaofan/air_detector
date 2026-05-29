<template>
  <el-header class="navbar">
    <div class="navbar-left">
      <h2 class="page-title">{{ title }}</h2>
    </div>
    <div class="navbar-right">
      <span class="current-date">{{ currentDate }}</span>
      <el-badge :value="3" :max="99" class="notification-badge">
        <el-icon :size="20" class="nav-icon"><Bell /></el-icon>
      </el-badge>
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-info">
          <el-avatar :size="32" class="user-avatar">
            {{ userStore.displayName?.charAt(0) || 'A' }}
          </el-avatar>
          <span class="user-name">{{ userStore.displayName || '管理员' }}</span>
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
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { logout as logoutApi } from '@/api/auth'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const title = ref('')

const currentDate = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

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
.navbar {
  background: var(--navbar-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid var(--navbar-border);
  height: var(--navbar-height);
  box-shadow: var(--shadow-sm);
}

.navbar-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--text-primary);
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.current-date {
  font-size: var(--font-size-body);
  color: var(--text-secondary);
}

.nav-icon {
  color: var(--text-secondary);
  cursor: pointer;
  transition: color var(--transition-fast);
}
.nav-icon:hover {
  color: var(--color-primary);
}

.notification-badge {
  cursor: pointer;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
  transition: color var(--transition-fast);
}
.user-info:hover {
  color: var(--color-primary);
}

.user-avatar {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 600;
  font-size: 14px;
}

.user-name {
  font-size: var(--font-size-body);
  font-weight: 500;
}
</style>
