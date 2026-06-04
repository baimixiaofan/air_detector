<template>
  <div class="page-container">
    <PageHeader title="站点管理" :subtitle="`共 ${tableData.length} 个站点`">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>新增站点
      </el-button>
    </PageHeader>

    <FilterBar>
      <el-select v-model="filters.area" placeholder="选择区域" clearable>
        <el-option v-for="a in areas" :key="a" :label="a" :value="a" />
      </el-select>
      <el-select v-model="filters.siteType" placeholder="站点类型" clearable>
        <el-option v-for="t in siteTypes" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="搜索站点名称" clearable prefix-icon="Search" />
    </FilterBar>

    <DashboardCard>
      <el-table :data="filteredData" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="code" label="站点编码" width="120" />
        <el-table-column prop="name" label="站点名称" min-width="150" />
        <el-table-column prop="area" label="区域" width="100" />
        <el-table-column prop="site_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.site_type === 'national' ? 'warning' : ''">
              {{ siteTypeLabel(row.site_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="经纬度" width="180">
          <template #default="{ row }">
            <span v-if="row.latitude && row.longitude">{{ row.latitude }}, {{ row.longitude }}</span>
            <span v-else class="text-muted">未设置</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span class="status-badge" :class="row.status === 'active' ? 'status-badge--success' : 'status-badge--default'">
              <span class="status-dot"></span>
              {{ row.status === 'active' ? '运行中' : '已停用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="device_count" label="设备数" width="80" align="center" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button link type="danger">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="filteredData.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
        />
      </div>
    </DashboardCard>

    <!-- Create/Edit Drawer -->
    <el-drawer v-model="drawerVisible" :title="isEdit ? '编辑站点' : '新增站点'" size="420px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="站点编码" prop="code">
          <el-input v-model="form.code" placeholder="如：SITE001" />
        </el-form-item>
        <el-form-item label="站点名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入站点名称" />
        </el-form-item>
        <el-form-item label="区域" prop="area">
          <el-input v-model="form.area" placeholder="如：浦东新区" />
        </el-form-item>
        <el-form-item label="站点类型" prop="site_type">
          <el-select v-model="form.site_type" placeholder="选择类型" style="width: 100%">
            <el-option v-for="t in siteTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="纬度">
          <el-input-number v-model="form.latitude" :precision="6" :step="0.001" style="width: 100%" />
        </el-form-item>
        <el-form-item label="经度">
          <el-input-number v-model="form.longitude" :precision="6" :step="0.001" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" active-value="active" inactive-value="inactive" active-text="运行中" inactive-text="已停用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSites, createSite, updateSite, deleteSite } from '@/api/sites'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import { SITE_TYPES } from '@/utils/constants'
import { ElMessage } from 'element-plus'

const siteTypes = SITE_TYPES
const areas = ref([])
const loading = ref(false)
const tableData = ref([])
const drawerVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const filters = ref({ area: '', siteType: '', keyword: '' })
const pagination = ref({ page: 1, size: 20 })

const form = ref({
  id: null,
  code: '',
  name: '',
  area: '',
  site_type: 'enterprise',
  latitude: null,
  longitude: null,
  status: 'active'
})

const rules = {
  code: [{ required: true, message: '请输入站点编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入站点名称', trigger: 'blur' }],
  area: [{ required: true, message: '请输入区域', trigger: 'blur' }],
  site_type: [{ required: true, message: '请选择站点类型', trigger: 'change' }]
}

const filteredData = computed(() => {
  return tableData.value.filter(d => {
    if (filters.value.area && d.area !== filters.value.area) return false
    if (filters.value.siteType && d.site_type !== filters.value.siteType) return false
    if (filters.value.keyword && !d.name.includes(filters.value.keyword)) return false
    return true
  })
})

function siteTypeLabel(type) {
  return siteTypes.find(t => t.value === type)?.label || type
}

async function fetchData() {
  loading.value = true
  try {
    const res = await getSites()
    if (res.code === 200) {
      tableData.value = res.data || []
      areas.value = [...new Set(tableData.value.map(d => d.area).filter(Boolean))]
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  form.value = { id: null, code: '', name: '', area: '', site_type: 'enterprise', latitude: null, longitude: null, status: 'active' }
  drawerVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  form.value = { ...row }
  drawerVisible.value = true
}

async function handleSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateSite(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createSite(form.value)
      ElMessage.success('创建成功')
    }
    drawerVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteSite(id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(fetchData)
</script>

<style scoped>
.table-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.text-muted {
  color: var(--text-muted);
}
</style>
