<template>
  <div class="page-container">
    <PageHeader title="企业信息" />

    <DashboardCard>
      <el-form ref="formRef" :model="form" label-width="100px" style="max-width: 600px;">
        <el-form-item label="企业名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入企业名称" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" placeholder="请输入企业地址" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact_person">
          <el-input v-model="form.contact_person" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
        </el-form-item>
      </el-form>
    </DashboardCard>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCompanyInfo, updateCompanyInfo } from '@/api/system'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import { ElMessage } from 'element-plus'

const formRef = ref(null)
const saving = ref(false)
const form = ref({ name: '', address: '', contact_person: '', phone: '', email: '' })

async function fetchData() {
  try { const res = await getCompanyInfo(); if (res.code === 200 && res.data) form.value = res.data }
  catch (e) { console.error(e) }
}

async function handleSave() {
  saving.value = true
  try { await updateCompanyInfo(form.value); ElMessage.success('保存成功') }
  catch (e) { ElMessage.error('保存失败') }
  finally { saving.value = false }
}

onMounted(fetchData)
</script>
