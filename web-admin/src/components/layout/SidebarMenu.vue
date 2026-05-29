<template>
  <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <el-icon :size="24" color="#e17055"><Monitor /></el-icon>
      </div>
      <span v-if="!isCollapse" class="sidebar-title">空气质量平台</span>
    </div>
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
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </template>
          <el-menu-item v-for="child in item.children" :key="child.path" :index="child.path">
            {{ child.title }}
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item v-else :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </template>
    </el-menu>

    <div class="sidebar-footer">
      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon :size="18"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
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
  { path: '/reports', title: '数据简报', icon: 'Document', roles: ['admin', 'ops', 'viewer'] },
  { path: '/sites', title: '站点管理', icon: 'Location', roles: ['admin', 'ops', 'viewer'] },
  { path: '/devices', title: '设备管理', icon: 'Cpu', roles: ['admin', 'ops', 'viewer'] },
  {
    path: '/monitoring', title: '实时监控', icon: 'TrendingUp', roles: ['admin', 'ops', 'viewer'],
    children: [
      { path: '/monitoring/list', title: '列表视图' },
      { path: '/monitoring/map', title: '地图视图' }
    ]
  },
  { path: '/rankings', title: '区域排行', icon: 'Trophy', roles: ['admin', 'ops', 'viewer'] },
  { path: '/recommendations', title: '产品推荐', icon: 'Present', roles: ['admin', 'ops', 'viewer'] },
  {
    path: '/history', title: '历史数据', icon: 'DataLine', roles: ['admin', 'ops', 'viewer'],
    children: [
      { path: '/history/query', title: '数据查询' },
      { path: '/history/comparison', title: '多站对比' },
      { path: '/history/report', title: '统计报表', roles: ['admin', 'ops'] }
    ]
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
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid var(--sidebar-border);
}

.sidebar-logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--color-primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  padding: 8px 0;
}

.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  color: var(--sidebar-text);
  height: 44px;
  margin: 2px 8px;
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

.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  padding-left: 48px !important;
  font-size: var(--font-size-body);
  height: 40px;
}

.sidebar-footer {
  border-top: 1px solid var(--sidebar-border);
  padding: 8px;
}

.collapse-btn {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.collapse-btn:hover {
  background: var(--sidebar-hover-bg);
  color: var(--color-primary);
}
</style>
