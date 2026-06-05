<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getCompanyInfo, updateCompanyInfo } from '@/api/system'

const enterprise = ref({
  name: '',
  logo_url: '',
  address: '',
  contact_name: '',
  contact_phone: '',
  contact_email: '',
  description: '',
})
const loading = ref(false)
const editing = ref(false)

const fetchInfo = async () => {
  loading.value = true
  try {
    const res = await getCompanyInfo()
    if (res && res.id) {
      enterprise.value = res
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  try {
    await updateCompanyInfo(enterprise.value)
    ElMessage.success('企业信息已更新')
    editing.value = false
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  fetchInfo()
})
</script>

<template>
  <div class="enterprise-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>🏢 企业主体基本信息</span>
          <div>
            <el-button v-if="!editing" type="primary" size="small" @click="editing = true">编辑信息</el-button>
            <template v-else>
              <el-button type="success" size="small" @click="handleSave">保存</el-button>
              <el-button size="small" @click="editing = false; fetchInfo()">取消</el-button>
            </template>
          </div>
        </div>
      </template>

      <el-form :model="enterprise" label-width="120px" :disabled="!editing">
        <el-form-item label="企业名称">
          <el-input v-model="enterprise.name" />
        </el-form-item>
        <el-form-item label="企业地址">
          <el-input v-model="enterprise.address" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="enterprise.contact_name" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="enterprise.contact_phone" />
        </el-form-item>
        <el-form-item label="联系邮箱">
          <el-input v-model="enterprise.contact_email" />
        </el-form-item>
        <el-form-item label="企业简介">
          <el-input v-model="enterprise.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.enterprise-container {
  padding-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
