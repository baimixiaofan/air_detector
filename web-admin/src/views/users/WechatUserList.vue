<template>
  <div class="page-container">
    <PageHeader title="微信用户管理" subtitle="管理小程序端用户（昵称/头像/设备/收藏）">
      <el-button @click="fetchList"><el-icon><Refresh /></el-icon>刷新</el-button>
    </PageHeader>

    <FilterBar>
      <el-input v-model="filters.keyword" placeholder="昵称 / open_id / 手机 / 邮箱" clearable style="width: 280px;" @keyup.enter="handleSearch" />
      <el-select v-model="filters.has_profile" placeholder="资料状态" clearable style="width: 140px;">
        <el-option label="已完善" value="1" />
        <el-option label="未完善" value="0" />
      </el-select>
      <el-button type="primary" @click="handleSearch"><el-icon><Search /></el-icon>查询</el-button>
    </FilterBar>

    <DashboardCard>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column label="头像/昵称" min-width="200">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :src="row.avatar_url" :size="36" :alt="row.nickname || '未完善'">
                {{ (row.nickname || '?').charAt(0) }}
              </el-avatar>
              <div class="user-info">
                <div class="nickname">{{ row.nickname || '未完善资料' }}</div>
                <div class="open-id">{{ row.open_id }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="gender" label="性别" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.gender === 1" type="primary" size="small">男</el-tag>
            <el-tag v-else-if="row.gender === 2" type="danger" size="small">女</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机" width="130">
          <template #default="{ row }">
            <span :class="{ muted: !row.phone }">{{ row.phone || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180">
          <template #default="{ row }">
            <span :class="{ muted: !row.email }">{{ row.email || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="设备/收藏/告警" width="170" align="center">
          <template #default="{ row }">
            <div class="counts">
              <span class="count-pill primary">设备 {{ row.device_count }}</span>
              <span class="count-pill warn">收藏 {{ row.favorite_count }}</span>
              <span class="count-pill danger">告警 {{ row.alert_count }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="160">
          <template #default="{ row }">{{ formatDate(row.last_login_at) }}</template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" width="160">
          <template #default="{ row }">{{ formatDate(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="openDetail(row)">详情</el-button>
            <el-button text type="warning" size="small" @click="openEdit(row)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px; justify-content: flex-end;"
        @size-change="fetchList"
        @current-change="fetchList"
      />
    </DashboardCard>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="微信用户详情" width="720px" top="6vh">
      <div v-loading="detailLoading">
        <div v-if="detail" class="detail-header">
          <el-avatar :src="detail.avatar_url" :size="64">
            {{ (detail.nickname || '?').charAt(0) }}
          </el-avatar>
          <div class="detail-meta">
            <div class="detail-name">{{ detail.nickname || '未完善资料' }}</div>
            <div class="detail-sub">
              <span>open_id: {{ detail.open_id }}</span>
              <el-divider direction="vertical" />
              <span>性别: {{ genderText(detail.gender) }}</span>
              <el-divider direction="vertical" />
              <span>设备 {{ detail.device_count }} / 收藏 {{ detail.favorite_count }} / 告警 {{ detail.alert_count }}</span>
            </div>
          </div>
        </div>
        <el-descriptions v-if="detail" :column="2" border size="small" class="detail-desc">
          <el-descriptions-item label="手机">{{ detail.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ detail.email || '-' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatDate(detail.create_time) }}</el-descriptions-item>
          <el-descriptions-item label="最后登录">{{ formatDate(detail.last_login_at) }} ({{ detail.last_login_ip || '-' }})</el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">绑定设备 ({{ detail?.devices?.length || 0 }})</el-divider>
        <el-table v-if="detail?.devices?.length" :data="detail.devices" size="small" stripe>
          <el-table-column prop="device_id" label="设备ID" min-width="160" />
          <el-table-column prop="device_name" label="名称" min-width="120">
            <template #default="{ row }">{{ row.device_name || '-' }}</template>
          </el-table-column>
          <el-table-column prop="room_location" label="位置" width="100">
            <template #default="{ row }">{{ roomText(row.room_location) }}</template>
          </el-table-column>
          <el-table-column label="地区" min-width="200">
            <template #default="{ row }">
              {{ [row.province, row.city, row.district].filter(Boolean).join(' ') || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="bind_time" label="绑定时间" width="160">
            <template #default="{ row }">{{ formatDate(row.bind_time) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无绑定设备" :image-size="80" />

        <el-divider content-position="left">收藏设备 ({{ detail?.favorites?.length || 0 }})</el-divider>
        <el-table v-if="detail?.favorites?.length" :data="detail.favorites" size="small" stripe>
          <el-table-column prop="device_id" label="设备ID" min-width="200" />
          <el-table-column prop="create_time" label="收藏时间" width="180">
            <template #default="{ row }">{{ formatDate(row.create_time) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无收藏" :image-size="80" />
      </div>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editVisible" :title="`编辑用户 #${editingId}`" width="520px" @closed="resetForm">
      <el-form :model="form" label-width="80px">
        <el-form-item label="头像">
          <div class="avatar-edit">
            <el-avatar :src="form.avatar_url" :size="56">
              {{ (form.nickname || '?').charAt(0) }}
            </el-avatar>
            <el-input v-model="form.avatar_url" placeholder="头像 URL" style="margin-left: 12px; flex: 1;" />
          </div>
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="用户昵称" maxlength="20" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio :value="0">未知</el-radio>
            <el-radio :value="1">男</el-radio>
            <el-radio :value="2">女</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="form.phone" placeholder="手机号" maxlength="20" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="邮箱" maxlength="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getWechatUsers, getWechatUser, updateWechatUser, deleteWechatUser } from '@/api/wechatUsers'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'

const loading = ref(false)
const submitting = ref(false)
const list = ref([])
const filters = reactive({ keyword: '', has_profile: '' })
const pagination = reactive({ page: 1, size: 20, total: 0 })

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)

const editVisible = ref(false)
const editingId = ref(null)
const form = ref({ nickname: '', avatar_url: '', gender: 0, phone: '', email: '' })

function formatDate(s) {
  if (!s) return '-'
  const d = new Date(s)
  if (isNaN(d.getTime())) return s
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function genderText(g) {
  return g === 1 ? '男' : g === 2 ? '女' : '未知'
}

function roomText(r) {
  return { living_room: '客厅', bedroom: '卧室', kitchen: '厨房', study: '书房', office: '办公室' }[r] || r || '-'
}

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pagination.page, size: pagination.size }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.has_profile) params.has_profile = filters.has_profile
    const res = await getWechatUsers(params)
    if (res.code === 200) {
      list.value = res.data.list || []
      pagination.total = res.data.total || 0
    }
  } finally { loading.value = false }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

async function openDetail(row) {
  detailVisible.value = true
  detailLoading.value = true
  detail.value = null
  try {
    const res = await getWechatUser(row.id)
    if (res.code === 200) detail.value = res.data
  } finally { detailLoading.value = false }
}

function openEdit(row) {
  editingId.value = row.id
  form.value = {
    nickname: row.nickname || '',
    avatar_url: row.avatar_url || '',
    gender: row.gender || 0,
    phone: row.phone || '',
    email: row.email || ''
  }
  editVisible.value = true
}

function resetForm() {
  editingId.value = null
  form.value = { nickname: '', avatar_url: '', gender: 0, phone: '', email: '' }
}

async function handleSubmit() {
  submitting.value = true
  try {
    await updateWechatUser(editingId.value, form.value)
    ElMessage.success('保存成功')
    editVisible.value = false
    fetchList()
  } finally { submitting.value = false }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(
    `确认删除用户「${row.nickname || row.open_id}」？\n将一并删除其收藏、告警设置，并解绑所有设备。`,
    '危险操作',
    { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' }
  )
  await deleteWechatUser(row.id)
  ElMessage.success('已删除')
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped>
.user-cell { display: flex; align-items: center; gap: 12px; }
.user-info .nickname { font-weight: 600; color: var(--text-primary); }
.user-info .open-id { font-size: 12px; color: var(--text-secondary); font-family: monospace; margin-top: 2px; }
.muted { color: var(--text-secondary); }
.counts { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; }
.count-pill { font-size: 12px; padding: 2px 8px; border-radius: 10px; background: #F5F5F7; color: #6E6E73; }
.count-pill.primary { background: #E3F2FD; color: #0066CC; }
.count-pill.warn { background: #FFF3E0; color: #FF9500; }
.count-pill.danger { background: #FFEBEE; color: #FF3B30; }
.detail-header { display: flex; gap: 16px; align-items: center; margin-bottom: 16px; }
.detail-name { font-size: 18px; font-weight: 600; color: var(--text-primary); }
.detail-sub { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.detail-desc { margin-bottom: 16px; }
.avatar-edit { display: flex; align-items: center; width: 100%; }
</style>
