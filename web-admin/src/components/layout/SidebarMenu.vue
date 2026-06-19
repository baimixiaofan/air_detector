<template>
  <el-aside :width="isCollapse ? '72px' : '260px'" class="sidebar">
    <!-- Logo -->
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <span class="logo-emoji">🌬️</span>
      </div>
      <transition name="fade">
        <div v-if="!isCollapse" class="sidebar-brand">
          <span class="brand-name">AirInsight</span>
          <span class="brand-tag">Pro</span>
        </div>
      </transition>
    </div>

    <!-- Menu -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      :collapse-transition="false"
      class="sidebar-menu"
      router
    >
      <template v-for="item in menuItems" :key="item.path">
        <el-sub-menu v-if="item.children" :index="item.path">
          <template #title>
            <div class="menu-icon-wrapper">
              <el-icon :size="20"><component :is="item.icon" /></el-icon>
            </div>
            <span>{{ item.title }}</span>
          </template>
          <el-menu-item v-for="child in item.children" :key="child.path" :index="child.path">
            <span class="submenu-dot"></span>
            {{ child.title }}
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item v-else :index="item.path">
          <div class="menu-icon-wrapper">
            <el-icon :size="20"><component :is="item.icon" /></el-icon>
          </div>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </template>
    </el-menu>

    <!-- Collapse Button -->
    <div class="sidebar-footer">
      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon :size="18">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
        <span v-if="!isCollapse" class="collapse-text">收起菜单</span>
      </div>
    </div>
  </el-aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)
const activeMenu = computed(() => route.path)

const role = computed(() => userStore.role)

const allMenuItems = [
  { path: '/dashboard', title: '数据看板', icon: 'Monitor', roles: ['admin', 'ops', 'viewer'] },
  { path: '/map', title: '全国分布', icon: 'MapLocation', roles: ['admin', 'ops', 'viewer'] },
  { path: '/customers', title: '客户管理', icon: 'UserFilled', roles: ['admin', 'ops'] },
  { path: '/devices', title: '设备管理', icon: 'Cpu', roles: ['admin', 'ops', 'viewer'] },
  { path: '/workorders', title: '售后工单', icon: 'Tickets', roles: ['admin', 'ops'] },
  { path: '/analytics', title: '数据分析', icon: 'DataAnalysis', roles: ['admin', 'ops'] },
  { path: '/reports', title: '数据报告', icon: 'Document', roles: ['admin', 'ops', 'viewer'] },
  { path: '/rankings', title: '区域排行', icon: 'Trophy', roles: ['admin', 'ops', 'viewer'] },
  {
    path: '/history', title: '历史数据', icon: 'DataLine', roles: ['admin', 'ops', 'viewer'],
  },
  {
    path: '/alerts', title: '告警管理', icon: 'Warning', roles: ['admin', 'ops', 'viewer'],
    children: [
      { path: '/alerts/records', title: '告警记录' },
      { path: '/alerts/rules', title: '告警规则', roles: ['admin', 'ops'] }
    ]
  },
  {
    path: '/settings', title: '系统设置', icon: 'Setting', roles: ['admin'],
    children: [
      { path: '/settings/company', title: '企业信息' },
      { path: '/settings/users', title: '用户管理' },
      { path: '/settings/logs', title: '操作日志' }
    ]
  }
]

const menuItems = computed(() => {
  return allMenuItems
    .filter(item => item.roles.includes(role.value))
    .map(item => {
      if (item.children) {
        return {
          ...item,
          children: item.children.filter(c => !c.roles || c.roles.includes(role.value))
        }
      }
      return item
    })
})
</script>

<style scoped>
.sidebar {
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  z-index: 10;
}

/* Header */
.sidebar-header {
  height: 72px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 20px;
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.sidebar-logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #0066CC, #5856D6);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-emoji {
  font-size: 20px;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.brand-tag {
  padding: 2px 8px;
  background: linear-gradient(135deg, #0066CC, #5856D6);
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.05em;
}

/* Menu */
.sidebar-menu {
  flex: 1;
  border-right: none;
  padding: 12px 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  color: var(--sidebar-text);
  height: 48px;
  margin: 4px 12px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  padding-left: 16px !important;
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background: var(--sidebar-hover-bg);
  color: var(--text-primary);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 500;
}

.sidebar-menu :deep(.el-sub-menu .el-menu) {
  background: transparent !important;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  padding-left: 52px !important;
  font-size: var(--font-size-body);
  height: 42px;
}

.menu-icon-wrapper {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 4px;
}

.submenu-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  margin-right: 10px;
  transition: all var(--transition-fast);
}

.el-menu-item.is-active .submenu-dot {
  background: var(--color-primary);
}

/* Footer */
.sidebar-footer {
  border-top: 1px solid var(--sidebar-border);
  padding: 12px;
  flex-shrink: 0;
}

.collapse-btn {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.collapse-btn:hover {
  background: var(--sidebar-hover-bg);
  color: var(--color-primary);
}

.collapse-text {
  font-size: var(--font-size-caption);
}

/* Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
