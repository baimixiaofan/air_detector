<template>
  <el-container class="app-layout">
    <SidebarMenu />
    <el-container>
      <Navbar />
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import SidebarMenu from './SidebarMenu.vue'
import Navbar from './Navbar.vue'
</script>

<style scoped>
.app-layout { height: 100vh; }
.app-main { background: #f0f2f5; padding: 20px; overflow-y: auto; }
</style>
