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
  border-radius: var(--radius-md);
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
}
.filter-bar__items {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.filter-bar__items :deep(.el-select) {
  width: 160px;
}
.filter-bar__items :deep(.el-input) {
  width: 200px;
}
.filter-bar__items :deep(.el-date-editor) {
  width: 260px;
}
</style>
