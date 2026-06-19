<template>
  <el-container class="app-layout">
    <SidebarMenu />
    <el-container class="app-layout__main">
      <Navbar />
      <el-main class="app-main">
        <router-view v-slot="{ Component, route }">
          <transition name="page-content" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import SidebarMenu from './SidebarMenu.vue'
import Navbar from './Navbar.vue'
</script>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}

.app-layout__main {
  flex-direction: column;
  overflow: hidden;
}

.app-main {
  background: var(--page-bg);
  padding: 28px 32px;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}

/* Page Content Transition */
.page-content-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-content-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-content-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.page-content-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
