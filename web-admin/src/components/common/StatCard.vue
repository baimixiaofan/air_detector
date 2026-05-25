<template>
  <el-card shadow="hover" class="stat-card">
    <div class="stat-inner">
      <div class="stat-info">
        <p class="stat-label">{{ title }}</p>
        <p class="stat-value" :style="{ color: color }">{{ value }}</p>
        <p v-if="subtitle" class="stat-subtitle">{{ subtitle }}</p>
      </div>
      <div class="stat-icon" :style="{ background: iconBg || color + '18' }">
        <el-icon :size="28" :color="color"><component :is="icon" /></el-icon>
      </div>
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  title: String,
  value: [String, Number],
  subtitle: String,
  icon: [String, Object],
  color: { type: String, default: '#409eff' },
  iconBg: String
})
</script>

<style scoped>
.stat-card { flex: 1; min-width: 200px; }
.stat-inner { display: flex; justify-content: space-between; align-items: center; }
.stat-label { font-size: 14px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: bold; }
.stat-subtitle { font-size: 12px; color: #c0c4cc; margin-top: 4px; }
.stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
</style>
