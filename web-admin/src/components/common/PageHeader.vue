<template>
  <div class="page-header">
    <div class="page-header__left">
      <h2 class="page-header__title">{{ title }}</h2>
      <p v-if="subtitle" class="page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div class="page-header__right">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  subtitle: String
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-header__title {
  font-size: var(--font-size-h2);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.page-header__subtitle {
  font-size: var(--font-size-body);
  color: var(--text-muted);
  margin-top: 6px;
}

.page-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
