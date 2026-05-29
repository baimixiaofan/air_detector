<script setup>
import { reactive } from 'vue'

const enterprise = reactive({
  name: '绿盾环境科技（北京）有限公司',
  code: '91110108MA01XXXXXX',
  type: '有限责任公司',
  address: '北京市海淀区中关村软件园 1 号楼 402 室',
  date: '2020-05-20',
  scope: '环境监测设备研发、空气质量数据分析、环保工程咨询等。',
  status: '正常经营',
})
</script>

<template>
  <div class="enterprise-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>🏢 企业主体基本信息</span>
          <el-button type="primary" size="small">申请资料变更</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="企业名称">{{ enterprise.name }}</el-descriptions-item>
        <el-descriptions-item label="统一社会信用代码">{{ enterprise.code }}</el-descriptions-item>
        <el-descriptions-item label="企业类型">{{ enterprise.type }}</el-descriptions-item>
        <el-descriptions-item label="成立日期">{{ enterprise.date }}</el-descriptions-item>
        <el-descriptions-item label="经营状态">
          <el-tag type="success">{{ enterprise.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册地址">{{ enterprise.address }}</el-descriptions-item>
        <el-descriptions-item label="经营范围" :span="2">{{
          enterprise.scope
        }}</el-descriptions-item>
      </el-descriptions>

      <div class="cert-section">
        <h4>🎖️ 企业资质证书</h4>
        <el-row :gutter="20">
          <el-col :span="6" v-for="i in 3" :key="i">
            <div class="cert-placeholder">高新技术企业证书-202{{ i }}</div>
          </el-col>
        </el-row>
      </div>
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
.cert-section {
  margin-top: 30px;
}
.cert-placeholder {
  height: 150px;
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  border-radius: 8px;
  font-size: 13px;
}
</style>
