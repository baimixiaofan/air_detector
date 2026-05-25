<template>
  <el-card>
    <template #header>{{ title }}</template>
    <el-empty :description="`${title}功能开发中...`" />
  </el-card>
</template>

<script setup>
defineProps({ title: { type: String, default: '' } })
</script>
