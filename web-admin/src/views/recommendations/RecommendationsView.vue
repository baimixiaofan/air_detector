<template>
  <div class="page-container">
    <PageHeader title="产品推荐">
      <el-button type="primary" @click="handleAdd"><el-icon><Plus /></el-icon>添加推荐</el-button>
    </PageHeader>

    <div class="recommendation-grid">
      <DashboardCard v-for="item in recommendations" :key="item.id" class="recommendation-card">
        <div class="rec-icon">
          <el-icon :size="32" color="#e17055"><Present /></el-icon>
        </div>
        <h4 class="rec-name">{{ item.name }}</h4>
        <p class="rec-desc">{{ item.description }}</p>
        <div class="rec-footer">
          <el-tag size="small" type="info">{{ item.target_audience }}</el-tag>
          <span class="rec-price">{{ item.price_range }}</span>
        </div>
        <div class="rec-actions">
          <el-button link type="primary" size="small">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(item.id)">
            <template #reference><el-button link type="danger" size="small">删除</el-button></template>
          </el-popconfirm>
        </div>
      </DashboardCard>
      <el-empty v-if="!recommendations.length" description="暂无产品推荐" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import { ElMessage } from 'element-plus'

const recommendations = ref([])

async function fetchData() {
  // Placeholder - needs backend API
  recommendations.value = []
}

function handleAdd() { ElMessage.info('功能开发中') }
function handleDelete(id) { ElMessage.info('功能开发中') }

onMounted(fetchData)
</script>

<style scoped>
.recommendation-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.recommendation-card { text-align: center; }
.rec-icon { margin-bottom: 12px; }
.rec-name { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.rec-desc { font-size: var(--font-size-body); color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px; min-height: 48px; }
.rec-footer { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.rec-price { font-size: var(--font-size-body); font-weight: 600; color: var(--color-primary); }
.rec-actions { border-top: 1px solid #f0f2f5; padding-top: 10px; display: flex; justify-content: center; gap: 16px; }
</style>
