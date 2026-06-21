import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import AppLayout from '@/components/layout/AppLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { noAuth: true }
  },
  {
    path: '/',
    component: AppLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { roles: ['admin', 'ops', 'viewer'], title: '数据看板', icon: 'Monitor' }
      },
      {
        path: 'map',
        name: 'ChinaMap',
        component: () => import('@/views/map/ChinaMapView.vue'),
        meta: { roles: ['admin', 'ops', 'viewer'], title: '全国分布', icon: 'MapLocation' }
      },
      {
        path: 'sites',
        name: 'Sites',
        component: () => import('@/views/sites/SiteList.vue'),
        meta: { roles: ['admin', 'ops', 'viewer'], title: '站点管理', icon: 'Location' }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/views/devices/DeviceList.vue'),
        meta: { roles: ['admin', 'ops', 'viewer'], title: '设备管理', icon: 'Cpu' }
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/views/history/HistoryQuery.vue'),
        meta: { roles: ['admin', 'ops', 'viewer'], title: '历史数据', icon: 'DataLine' }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@/views/users/UserManagement.vue'),
        meta: { roles: ['admin', 'ops'], title: '用户管理', icon: 'UserFilled' }
      },
      { path: 'customers', redirect: '/users?tab=customers' },
      { path: 'wechat-users', redirect: '/users?tab=wechat' },
      {
        path: 'workorders',
        name: 'WorkOrders',
        component: () => import('@/views/workorders/WorkOrderList.vue'),
        meta: { roles: ['admin', 'ops'], title: '售后工单', icon: 'Tickets' }
      },
      {
        path: 'rankings',
        name: 'Rankings',
        component: () => import('@/views/rankings/RankingsView.vue'),
        meta: { roles: ['admin', 'ops', 'viewer'], title: '区域排行', icon: 'Trophy' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/analytics/PoorAirUsers.vue'),
        meta: { roles: ['admin', 'ops'], title: '数据分析', icon: 'DataAnalysis' }
      },
      {
        path: 'reports',
        name: 'Reports',
        component: () => import('@/views/reports/ReportsView.vue'),
        meta: { roles: ['admin', 'ops', 'viewer'], title: '数据报告', icon: 'Document' }
      },
      {
        path: 'alerts',
        redirect: '/alerts/records',
        meta: { roles: ['admin', 'ops', 'viewer'], title: '告警管理', icon: 'Warning' },
        children: [
          {
            path: 'records',
            name: 'AlertRecords',
            component: () => import('@/views/alerts/AlertRecords.vue'),
            meta: { roles: ['admin', 'ops', 'viewer'], title: '告警记录' }
          },
          {
            path: 'rules',
            name: 'AlertRules',
            component: () => import('@/views/alerts/AlertRules.vue'),
            meta: { roles: ['admin', 'ops'], title: '告警规则' }
          }
        ]
      },
      {
        path: 'settings',
        redirect: '/settings/company',
        meta: { roles: ['admin'], title: '系统设置', icon: 'Setting' },
        children: [
          {
            path: 'company',
            name: 'CompanyInfo',
            component: () => import('@/views/system/CompanyInfo.vue'),
            meta: { roles: ['admin'], title: '企业信息' }
          },
          {
            path: 'users',
            name: 'AdminUsers',
            component: () => import('@/views/system/AdminUsers.vue'),
            meta: { roles: ['admin'], title: '用户管理' }
          },
          {
            path: 'logs',
            name: 'OperationLogs',
            component: () => import('@/views/system/OperationLogs.vue'),
            meta: { roles: ['admin'], title: '操作日志' }
          }
        ]
      }
    ]
  },
  { path: '/403', name: 'Forbidden', component: () => import('@/views/error/Page403.vue') },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/views/error/Page404.vue') }
]

const router = createRouter({
  history: createWebHashHistory('/admin/'),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  if (to.meta.noAuth) {
    next()
    return
  }

  const token = localStorage.getItem('admin_token')
  if (!token) {
    next(`/login?redirect=${to.path}`)
    return
  }

  const userStore = useUserStore()
  if (!userStore.user) {
    userStore.fetchProfile().then(() => {
      if (to.meta.roles && !to.meta.roles.includes(userStore.user?.role)) {
        next('/403')
      } else {
        next()
      }
    }).catch(() => {
      localStorage.removeItem('admin_token')
      next('/login')
    })
  } else {
    if (to.meta.roles && !to.meta.roles.includes(userStore.user.role)) {
      next('/403')
    } else {
      next()
    }
  }
})

export default router
