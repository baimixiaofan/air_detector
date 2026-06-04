<template>
  <div class="page-container">
    <PageHeader title="告警规则">
      <el-button type="primary" @click="handleAdd"><el-icon><Plus /></el-icon>添加规则</el-button>
    </PageHeader>

    <DashboardCard>
      <el-table :data="tableData" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="name" label="规则名称" min-width="150" />
        <el-table-column prop="pollutant" label="监测指标" width="100" />
        <el-table-column label="阈值条件" width="140">
          <template #default="{ row }">{{ row.operator }} {{ row.threshold }}</template>
        </el-table-column>
        <el-table-column label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="alertSeverityType(row.severity)" size="small">{{ alertSeverityLabel(row.severity) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)"><el-icon><Edit /></el-icon></el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
              <template #reference><el-button link type="danger"><el-icon><Delete /></el-icon></el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </DashboardCard>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑规则' : '添加规则'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="规则名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="监测指标" prop="pollutant">
          <el-select v-model="form.pollutant" style="width: 100%">
            <el-option label="AQI" value="aqi" />
            <el-option label="PM2.5" value="pm25" />
            <el-option label="PM10" value="pm10" />
            <el-option label="NO₂" value="no2" />
            <el-option label="SO₂" value="so2" />
            <el-option label="O₃" value="o3" />
          </el-select>
        </el-form-item>
        <el-form-item label="阈值条件" required>
          <el-col :span="10"><el-select v-model="form.operator" style="width: 100%"><el-option label=">" value=">" /><el-option label=">=" value=">=" /><el-option label="=" value="=" /></el-select></el-col>
          <el-col :span="2" style="text-align:center">—</el-col>
          <el-col :span="12"><el-input-number v-model="form.threshold" :min="0" style="width: 100%" /></el-col>
        </el-form-item>
        <el-form-item label="严重程度" prop="severity">
          <el-select v-model="form.severity" style="width: 100%">
            <el-option label="严重" value="critical" />
            <el-option label="警告" value="warning" />
            <el-option label="提示" value="info" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAlertRules, createAlertRule, updateAlertRule, deleteAlertRule } from '@/api/alerts'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import { ALERT_SEVERITY } from '@/utils/constants'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const form = ref({ id: null, name: '', pollutant: 'aqi', operator: '>', threshold: 100, severity: 'warning', enabled: true })
const rules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  pollutant: [{ required: true, message: '请选择指标', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }]
}

function alertSeverityLabel(s) { return ALERT_SEVERITY[s]?.label || s }
function alertSeverityType(s) { return ALERT_SEVERITY[s]?.tagType || '' }

async function fetchData() {
  loading.value = true
  try { const res = await getAlertRules(); if (res.code === 200) tableData.value = res.data || [] }
  catch (e) { console.error(e) }
  finally { loading.value = false }
}

function handleAdd() {
  isEdit.value = false
  form.value = { id: null, name: '', pollutant: 'aqi', operator: '>', threshold: 100, severity: 'warning', enabled: true }
  dialogVisible.value = true
}
function handleEdit(row) {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}
async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    isEdit.value ? await updateAlertRule(form.value.id, form.value) : await createAlertRule(form.value)
    ElMessage.success('保存成功')
    dialogVisible.value = false
    fetchData()
  } catch (e) { ElMessage.error('操作失败') }
  finally { submitting.value = false }
}
async function handleToggle(row) {
  try { await updateAlertRule(row.id, { enabled: row.enabled }) }
  catch (e) { row.enabled = !row.enabled }
}
async function handleDelete(id) {
  try { await deleteAlertRule(id); ElMessage.success('删除成功'); fetchData() }
  catch (e) { ElMessage.error('删除失败') }
}

onMounted(fetchData)
</script>
