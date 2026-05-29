import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login', // 只要用户访问根目录，强制一脚踢到登录页
    },
    {
      path: '/login',
      name: 'Login',
      // 这里引入我们将要写的登录页
      component: () => import('../views/UserLogin.vue'),
    },
    {
      path: '/admin',
      name: 'Admin',
      // 这里引入我们将要写的后台主骨架
      component: () => import('../views/AdminLayout.vue'),
      redirect: '/admin/dataDashboard',
      children: [
        {
          path: 'dataDashboard', // 子路由路径前面不用加斜杠
          name: 'DataDashboard',
          // 引入我们刚刚写的画作
          component: () => import('../views/DataDashboard.vue'),
        },
        {
          path: 'siteManage',
          name: 'SiteManage',
          component: () => import('../views/SiteManage.vue'),
        },
        {
          path: 'deviceManage',
          name: 'DeviceManage',
          component: () => import('../views/DeviceManage.vue'),
        },
        {
          path: 'mapView',
          name: 'MapView',
          component: () => import('../views/MapView.vue'),
        },
        {
          path: 'regionRanking',
          name: 'RegionRanking',
          component: () => import('../views/RegionRanking.vue'),
        },
        {
          path: 'dataReport',
          name: 'DataReport',
          component: () => import('../views/DataReport.vue'),
        },
        {
          path: 'listView',
          name: 'ListView',
          component: () => import('../views/ListView.vue'),
        },
        {
          path: 'productRecommend',
          name: 'ProductRecommend',
          component: () => import('../views/ProductRecommend.vue'),
        },
        {
          path: 'historyData',
          name: 'HistoryData',
          component: () => import('../views/HistoryData.vue'),
        },
        {
          path: 'alertManage',
          name: 'AlertManage',
          component: () => import('../views/AlertManage.vue'),
        },
        {
          path: 'systemSettings',
          name: 'SystemSettings',
          component: () => import('../views/SystemSettings.vue'),
        },
        {
          path: 'multiCompare',
          name: 'MultiCompare',
          component: () => import('../views/MultiCompare.vue'),
        },
        {
          path: 'statReport',
          name: 'StatReport',
          component: () => import('../views/StatReport.vue'),
        },
        {
          path: 'enterpriseInfo',
          name: 'EnterpriseInfo',
          component: () => import('../views/EnterpriseInfo.vue'),
        },
        {
          path: 'userManage',
          name: 'UserManage',
          component: () => import('../views/UserManage.vue'),
        },
      ],
    },
  ],
})
// 添加路由全局前置守卫（也就是我们的“系统保安”）
router.beforeEach((to, from, next) => {
  // 1. 去浏览器的本地存储里看一眼，有没有登录成功时存下的“钥匙” (token)
  const token = localStorage.getItem('token')

  // 2. 检查用户要去的地方，是不是后台管理页面（看路径是不是以 /admin 开头）
  if (to.path.startsWith('/admin')) {
    if (token) {
      // 有钥匙，保安挥挥手放行，允许进入页面
      next()
    } else {
      // 没钥匙还想白嫖？保安一脚把你踹回登录页！
      next('/login')
    }
  } else {
    // 如果去的是登录页本身，不需要钥匙，直接放行，否则会陷入死循环
    next()
  }
})
export default router
