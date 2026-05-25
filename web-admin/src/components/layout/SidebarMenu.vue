<template>
  <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
    <div class="sidebar-header">
      <span v-if="!isCollapse" class="sidebar-title">空气质量平台</span>
      <span v-else class="sidebar-title-small">AQ</span>
    </div>
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapse"
      :collapse-transition="false"
      background-color="#001529"
      text-color="#ffffffa6"
      active-text-color="#fff"
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

    <div class="collapse-btn" @click="isCollapse = !isCollapse">
      <el-icon><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
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
.sidebar { background: #001529; display: flex; flex-direction: column; transition: width 0.3s; overflow: hidden; }
.sidebar-header { height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: bold; font-size: 16px; border-bottom: 1px solid #ffffff1a; }
.sidebar-title-small { font-size: 20px; }
.el-menu { border-right: none; flex: 1; }
.collapse-btn { height: 40px; display: flex; align-items: center; justify-content: center; color: #ffffffa6; cursor: pointer; border-top: 1px solid #ffffff1a; }
.collapse-btn:hover { color: #fff; }
</style>
