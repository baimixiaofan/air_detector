<template>
  <el-header class="navbar">
    <div class="navbar-left">
      <h2 class="page-title">{{ title }}</h2>
    </div>
    <div class="navbar-right">
      <!-- Search -->
      <div class="search-wrapper">
        <el-icon class="search-icon"><Search /></el-icon>
        <input class="search-input" type="text" placeholder="搜索..." />
      </div>

      <!-- Date -->
      <span class="current-date">{{ currentDate }}</span>

      <!-- Notifications -->
      <el-badge :value="3" :max="99" class="notification-badge">
        <div class="icon-btn">
          <el-icon :size="20"><Bell /></el-icon>
        </div>
      </el-badge>

      <!-- User Dropdown -->
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-info">
          <div class="user-avatar">
            <span>{{ userStore.displayName?.charAt(0) || 'A' }}</span>
          </div>
          <span class="user-name">{{ userStore.displayName || '管理员' }}</span>
          <el-icon class="arrow-icon"><ArrowDown /></el-icon>
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
  backdrop-filter: var(--glass-blur);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  border-bottom: 1px solid var(--navbar-border);
  height: var(--navbar-height);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 5;
}

.navbar-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Search */
.search-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: #F5F5F7;
  border: 1px solid transparent;
  border-radius: 10px;
  transition: all var(--transition-fast);
}

.search-wrapper:focus-within {
  background: #FFFFFF;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
}

.search-icon {
  color: var(--text-muted);
  font-size: 16px;
}

.search-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: var(--font-size-body);
  width: 160px;
}

.search-input::placeholder {
  color: var(--text-muted);
}

/* Date */
.current-date {
  font-size: var(--font-size-body);
  color: var(--text-secondary);
}

/* Icon Button */
.icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.icon-btn:hover {
  background: #F5F5F7;
  color: var(--text-primary);
}

.notification-badge {
  cursor: pointer;
}

/* User */
.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-primary);
  padding: 6px 12px 6px 6px;
  border-radius: 12px;
  transition: all var(--transition-fast);
}

.user-info:hover {
  background: #F5F5F7;
}

.user-avatar {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: linear-gradient(135deg, #0066CC, #5856D6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  color: #fff;
}

.user-name {
  font-size: var(--font-size-body);
  font-weight: 500;
}

.arrow-icon {
  color: var(--text-muted);
  font-size: 14px;
}
</style>
