<template>
  <el-container class="app-layout">
    <SidebarMenu />
    <el-container>
      <Navbar />
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
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
}

.app-main {
  background: var(--page-bg);
  padding: 0;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
