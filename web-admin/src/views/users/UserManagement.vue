<template>
  <div style="margin: -24px -32px;">
    <el-tabs v-model="activeTab" class="user-tabs" @tab-change="onTabChange">
      <el-tab-pane label="企业客户" name="customers">
        <CustomerList />
      </el-tab-pane>
      <el-tab-pane label="微信用户" name="wechat">
        <WechatUserList />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CustomerList from '@/views/customers/CustomerList.vue'
import WechatUserList from '@/views/users/WechatUserList.vue'

const route = useRoute()
const router = useRouter()
const activeTab = ref(route.query.tab === 'wechat' ? 'wechat' : 'customers')

function onTabChange(tab) {
  router.replace({ query: { tab } })
}
</script>

<style scoped>
.user-tabs { margin: 0; }
.user-tabs :deep(.el-tabs__header) {
  padding: 0 32px;
  margin: 0;
  background: var(--card-bg);
  box-shadow: 0 1px 0 var(--card-border);
  position: sticky;
  top: 0;
  z-index: 9;
}
.user-tabs :deep(.el-tabs__content) { padding: 0; }
.user-tabs :deep(.el-tab-pane) { padding: 0; }
.user-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }
</style>
