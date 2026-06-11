<template>
  <div class="dashboard-card" :class="{ 'dashboard-card--no-padding': noPadding }">
    <div v-if="title || $slots.actions" class="card-header">
      <div>
        <h3 class="card-header__title">{{ title }}</h3>
        <p v-if="subtitle" class="card-header__subtitle">{{ subtitle }}</p>
      </div>
      <div class="card-header__actions">
        <slot name="actions">
          <el-icon v-if="showSettings" class="card-action-btn" :size="18"><Setting /></el-icon>
        </slot>
      </div>
    </div>
    <div class="card-body">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  subtitle: String,
  noPadding: { type: Boolean, default: false },
  showSettings: { type: Boolean, default: false }
})
</script>

<style scoped>
.dashboard-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  backdrop-filter: var(--glass-blur);
  padding: 24px 28px;
  transition: all var(--transition-normal);
}

.dashboard-card:hover {
  background: var(--card-hover-bg);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: var(--shadow-md);
}

.dashboard-card--no-padding {
  padding: 0;
}

.dashboard-card--no-padding .card-body {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card-header__title {
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.card-header__subtitle {
  font-size: var(--font-size-caption);
  color: var(--text-muted);
  margin-top: 4px;
}

.card-header__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-action-btn {
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
  padding: 4px;
  border-radius: 6px;
}

.card-action-btn:hover {
  color: var(--color-primary);
  background: var(--color-primary-light);
}
</style>
