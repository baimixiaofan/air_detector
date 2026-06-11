<template>
  <div class="filter-bar">
    <div class="filter-bar__items">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  backdrop-filter: var(--glass-blur);
  padding: 18px 24px;
  margin-bottom: 20px;
  transition: all var(--transition-normal);
}

.filter-bar:hover {
  border-color: rgba(255, 255, 255, 0.1);
}

.filter-bar__items {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
}

.filter-bar__items :deep(.el-select) {
  width: 180px;
}

.filter-bar__items :deep(.el-input) {
  width: 220px;
}

.filter-bar__items :deep(.el-date-editor) {
  width: 280px;
}
</style>
