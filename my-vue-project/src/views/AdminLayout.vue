<script setup>
// 不需要 onMounted 了，Pinia 会自动响应式更新
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'
import { useDark } from '@vueuse/core'

const router = useRouter()
const userStore = useUserStore() // 💡 实例化仓库
const isDark = useDark()

const handleLogout = () => {
  // 💡 调用仓库的 logout 方法
  userStore.logout()

  ElMessage.warning('已安全退出系统')
  router.push('/login')
}
</script>

<template>
  <div class="common-layout">
    <el-container class="main-container">
      <el-aside width="220px" class="aside-menu">
        <div class="logo">空气质量平台</div>
        <el-menu
          router
          :default-active="$route.path"
          class="custom-menu"
          background-color="#192433"
          text-color="#a4b0be"
          active-text-color="#ffffff"
        >
          <el-menu-item index="/admin/dataDashboard">📊 数据看板</el-menu-item>
          <el-menu-item index="/admin/dataReport">📄 数据简报</el-menu-item>
          <el-menu-item index="/admin/siteManage">📍 站点管理</el-menu-item>
          <el-menu-item index="/admin/deviceManage">⚙️ 设备管理</el-menu-item>

          <el-sub-menu index="5">
            <template #title><span>👁️ 实时监控</span></template>
            <el-menu-item index="/admin/listView">列表视图</el-menu-item>
            <el-menu-item index="/admin/mapView">地图视图</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/admin/regionRanking">🏆 区域排行</el-menu-item>
          <el-menu-item index="/admin/productRecommend">🎁 产品推荐</el-menu-item>

          <el-sub-menu index="8">
            <template #title><span>📈 历史数据</span></template>
            <el-menu-item index="/admin/historyData">数据查询</el-menu-item>
            <el-menu-item index="/admin/multiCompare">多站对比</el-menu-item>
            <el-menu-item index="/admin/statReport">统计报表</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="9">
            <template #title><span>⚠️ 告警管理</span></template>
            <el-menu-item index="/admin/alertManage">告警列表</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="10" v-if="userStore.role === 'admin'">
            <template #title><span>⚙️ 系统设置</span></template>
            <el-menu-item index="/admin/systemSettings">个人设置</el-menu-item>
            <el-menu-item index="/admin/enterpriseInfo">企业信息</el-menu-item>
            <el-menu-item index="/admin/userManage">用户管理</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="logo">🍃 绿盾环境监测中心</div>
          <div class="user-profile">
            <el-switch
              v-model="isDark"
              inline-prompt
              active-text="🌙"
              inactive-text="☀️"
              style="margin-right: 20px"
            />

            <span>👤 {{ userStore.username || '未知用户' }}</span>
            <el-button type="danger" text @click="handleLogout">退出登录</el-button>
          </div>
        </el-header>

        <el-main class="main-content">
          <router-view v-slot="{ Component }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
.common-layout,
.main-container {
  height: 100vh;
}

/* 侧边栏复刻截图颜色 */
.aside-menu {
  /* 侧边栏：白昼玻璃态 */
  background: rgba(255, 255, 255, 0.8) !important;
  border-right: 1px solid rgba(0, 162, 255, 0.2);
  box-shadow: 2px 0 15px rgba(0, 100, 200, 0.05);
  backdrop-filter: blur(15px);
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 18px;
  font-weight: bold;
  color: white;
  border-bottom: 1px solid #101722;
}

.custom-menu {
  border-right: none;
}

/* 激活状态的菜单加上背景色 */
.el-menu-item.is-active {
  background-color: #0d1620 !important;
}

.header {
  /* 顶部栏：纯净白 */
  background-color: rgba(255, 255, 255, 0.9) !important;
  border-bottom: 1px solid rgba(0, 162, 255, 0.2);
  box-shadow: 0 2px 15px rgba(0, 100, 200, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 100;
  color: #1e293b;
}

/* 左侧菜单文字变深，选中状态变成亮蓝色 */
:deep(.el-menu) {
  background-color: transparent !important;
  border-right: none !important;
}
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: #334155 !important;
}
:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(0, 162, 255, 0.1) 0%, transparent 100%) !important;
  color: #00a2ff !important;
  border-left: 3px solid #00a2ff;
  font-weight: bold;
}

.breadcrumb {
  font-size: 14px;
  color: #666;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 15px;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
/* 💡 页面切换的丝滑过渡动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px); /* 新页面从右侧滑入并淡入 */
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px); /* 老页面向左侧滑出并淡出 */
}
</style>
