<template>
  <div class="dashboard">
    <!-- Header -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          <span>平台监控 · {{ now }}</span>
        </div>
        <h1 class="hero-title">平台运营看板</h1>
      </div>
      <div class="hero-actions">
        <el-button @click="fetchAll" :loading="loading" plain size="small">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <span class="update-tip" v-if="stats">最后更新：{{ lastUpdate }}</span>
      </div>
    </section>

    <!-- KPI 卡片: 设备 -->
    <section class="kpi-section">
      <div class="section-header"><h2>📟 设备概况</h2></div>
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon" style="background:linear-gradient(135deg,#0066CC,#5856D6)">
            <span class="icon-text">🏭</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats?.manufactured_devices ?? 0 }}</span>
            <span class="kpi-label">出厂设备</span>
          </div>
          <div class="kpi-sub">累计生产总量</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background:linear-gradient(135deg,#34C759,#30D158)">
            <span class="icon-text">✅</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats?.activated_devices ?? 0 }}</span>
            <span class="kpi-label">已激活</span>
          </div>
          <div class="kpi-sub">已部署上线运行</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background:linear-gradient(135deg,#007AFF,#5AC8FA)">
            <span class="icon-text">📶</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats?.online_rate ?? 0 }}%</span>
            <span class="kpi-label">在线率</span>
          </div>
          <div class="kpi-sub">{{ stats?.online_devices ?? 0 }}/{{ stats?.activated_devices ?? 0 }} 在线</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background:linear-gradient(135deg,#FF3B30,#FF9500)">
            <span class="icon-text">🔧</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats?.fault_rate ?? 0 }}%</span>
            <span class="kpi-label">故障率</span>
          </div>
          <div class="kpi-sub">待处理工单 / 总设备</div>
        </div>
      </div>
    </section>

    <!-- KPI 卡片: 业务 -->
    <section class="kpi-section">
      <div class="section-header"><h2>📊 业务概况</h2></div>
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon" style="background:linear-gradient(135deg,#5856D6,#AF52DE)">
            <span class="icon-text">🏢</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats?.enterprise_customers ?? 0 }}</span>
            <span class="kpi-label">企业客户</span>
          </div>
          <div class="kpi-sub">共 {{ stats?.total_customers ?? 0 }} 个客户</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background:linear-gradient(135deg,#FF9500,#FFCC00)">
            <span class="icon-text">📋</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats?.total_work_orders ?? 0 }}</span>
            <span class="kpi-label">售后工单</span>
          </div>
          <div class="kpi-sub">待处理 {{ stats?.pending_work_orders ?? 0 }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background:linear-gradient(135deg,#007AFF,#64D2FF)">
            <span class="icon-text">📦</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ formatNum(stats?.today_data_records ?? 0) }}</span>
            <span class="kpi-label">今日数据量</span>
          </div>
          <div class="kpi-sub">累计 {{ formatNum(stats?.total_data_records ?? 0) }} 条</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background:linear-gradient(135deg,#34C759,#30D158)">
            <span class="icon-text">📄</span>
          </div>
          <div class="kpi-content">
            <span class="kpi-value">{{ stats?.total_reports ?? 0 }}</span>
            <span class="kpi-label">生成报告</span>
          </div>
          <div class="kpi-sub">累计报告数量</div>
        </div>
      </div>
    </section>

    <!-- 待办事项 + 设备状态两列 -->
    <div class="two-col">
      <!-- 待办事项 -->
      <section class="alert-summary">
        <div class="section-header"><h2>⚠️ 待办事项</h2></div>
        <div class="alert-list">
          <div class="alert-item" v-if="(stats?.pending_alerts ?? 0) > 0">
            <span class="alert-icon" style="background:#FF3B30">!</span>
            <div class="alert-info">
              <span class="alert-title">{{ stats?.pending_alerts }} 条待处理告警</span>
              <span class="alert-desc">共 {{ stats?.total_alerts }} 条告警记录</span>
            </div>
          </div>
          <div class="alert-item" v-if="(stats?.pending_work_orders ?? 0) > 0">
            <span class="alert-icon" style="background:#FF9500">!</span>
            <div class="alert-info">
              <span class="alert-title">{{ stats?.pending_work_orders }} 个未完成工单</span>
              <span class="alert-desc">共 {{ stats?.total_work_orders }} 个售后工单</span>
            </div>
          </div>
          <div class="alert-item" v-if="(stats?.deactivated_devices ?? 0) > 0">
            <span class="alert-icon" style="background:#6e6e73">×</span>
            <div class="alert-info">
              <span class="alert-title">{{ stats?.deactivated_devices }} 台设备已注销</span>
              <span class="alert-desc">已从平台移除</span>
            </div>
          </div>
          <el-empty v-if="!pendingCount" description="暂无待办事项" :image-size="60" />
        </div>
      </section>

      <!-- 设备在线状态 -->
      <section class="status-section">
        <div class="section-header">
          <h2>📡 设备在线状态</h2>
          <span class="section-badge">{{ stats?.online_devices ?? 0 }}/{{ stats?.activated_devices ?? 0 }} 在线</span>
        </div>
        <div class="status-bar">
          <div class="bar-online" :style="{ width: onlinePct + '%' }"></div>
        </div>
        <div class="status-labels">
          <span class="label-online">在线 {{ stats?.online_devices ?? 0 }}</span>
          <span class="label-offline">离线 {{ stats?.offline_devices ?? 0 }}</span>
        </div>
      </section>
    </div>

    <!-- 设备列表 -->
    <section class="devices-section">
      <div class="section-header">
        <h2>设备列表</h2>
      </div>
      <el-table :data="deviceStatusList" v-loading="loading" stripe max-height="400" size="small">
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.online ? 'success' : 'info'" size="small">
              {{ row.online ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="设备名称" min-width="140" />
        <el-table-column prop="aqi" label="AQI" width="80" :formatter="(r) => r.aqi ?? '-'" />
        <el-table-column prop="location" label="位置" min-width="120" />
        <el-table-column prop="lastUpdate" label="最后更新" min-width="140" />
      </el-table>
    </section>

    <!-- AI 一句话总结 -->
    <section class="ai-summary" v-if="aiSummary">
      <span class="ai-icon">🤖</span>
      <span class="ai-text">{{ aiSummary }}</span>
    </section>

    <section class="system-health" v-if="sysHealth">
      <div class="section-header"><h2>🔧 系统状态</h2></div>
      <div class="health-grid">
        <div class="health-item">
          <span class="health-label">数据库</span>
          <span :class="'health-dot ' + (sysHealth.database?.mysql === 'OK' ? 'dot-green' : 'dot-red')"></span>
          <span>MySQL:{{ sysHealth.database?.mysql || '?' }} MongoDB:OK Redis:{{ sysHealth.database?.redis || '?' }}</span>
        </div>
        <div class="health-item">
          <span class="health-label">并发</span>
          <span>{{ sysHealth.concurrency?.active_threads }} 线程 · {{ sysHealth.concurrency?.active_sessions }} 在线 · 队列 {{ sysHealth.concurrency?.queue_depth }}</span>
        </div>
        <div class="health-item">
          <span class="health-label">连接池</span>
          <span>MySQL:20/30 · MongoDB:100 · Redis:50</span>
        </div>
        <div class="health-item">
          <span class="health-label">安全</span>
          <span>限流:5次/5min · 验证码:ON · HSTS:ON</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getDashboardStats, getDashboardTrend, getDashboardRealtime } from '@/api/dashboard'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const stats = ref(null)
const deviceStatusList = ref([])
const aiSummary = ref('')
const sysHealth = ref(null)
const now = ref('')
const lastUpdate = ref('')
let timer = null

const onlinePct = computed(() => {
  const act = stats.value?.activated_devices ?? 0
  if (act === 0) return 0
  return Math.round((stats.value?.online_devices ?? 0) / act * 100)
})

const pendingCount = computed(() => {
  return (stats.value?.pending_alerts ?? 0) + (stats.value?.pending_work_orders ?? 0) + (stats.value?.deactivated_devices ?? 0)
})

function formatNum(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return n.toString()
}

function updateTime() {
  now.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

async function fetchAll() {
  loading.value = true
  try {
    const statsRes = await getDashboardStats()
    if (statsRes.code === 200) {
      stats.value = statsRes.data
      lastUpdate.value = new Date().toLocaleString('zh-CN', { hour12: false })
    }

    // 设备列表异步加载，不阻塞看板
    getDashboardRealtime().then(res => {
      if (res.code === 200) deviceStatusList.value = Array.isArray(res.data) ? res.data.slice(0, 20) : []
    }).catch(() => {})

    // 系统健康异步加载，不阻塞看板
    request({ url: '/admin/system/health', method: 'get' }).then(res => {
      if (res.code === 200) sysHealth.value = res.data
    }).catch(() => {})

    // AI 一句话总结
    if (statsRes.code === 200) {
      const s = statsRes.data
      const online = s.online_rate ?? 0
      const fault = s.fault_rate ?? 0
      if (online >= 90 && fault < 5) {
        aiSummary.value = '平台运行状态良好，设备在线率' + online + '%，故障率仅' + fault + '%，建议继续保持。'
      } else if (online < 70) {
        aiSummary.value = '注意：设备在线率仅' + online + '%，建议检查离线设备网络连接。'
      } else if (fault >= 10) {
        aiSummary.value = '故障率' + fault + '%，偏高，建议优先处理待维修工单。'
      } else {
        aiSummary.value = '平台运行平稳，在线率' + online + '%，故障率' + fault + '%，各项指标正常。'
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAll()
  updateTime()
  timer = setInterval(updateTime, 60000)
})

onBeforeUnmount(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 24px; }

/* Hero */
.hero-section {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf4 100%);
  border-radius: 16px; padding: 32px;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(0,102,204,0.1); color: #0066CC;
  padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-bottom: 8px;
}
.badge-dot { width: 6px; height: 6px; border-radius: 50%; background: #34C759; }
.hero-title { font-size: 28px; font-weight: 700; color: #1d1d1f; margin: 0; }
.hero-actions { display: flex; align-items: center; gap: 16px; }
.update-tip { font-size: 12px; color: #aeaeb2; }

/* KPI */
.kpi-section { display: flex; flex-direction: column; gap: 16px; }
.section-header h2 { font-size: 16px; font-weight: 600; color: #1d1d1f; margin: 0; }
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.kpi-card {
  background: #fff; border: 1px solid rgba(0,0,0,0.06); border-radius: 14px;
  padding: 20px; display: flex; flex-direction: column; gap: 8px;
  transition: all 0.2s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
.kpi-icon {
  width: 40px; height: 40px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.icon-text { font-size: 18px; }
.kpi-content { display: flex; flex-direction: column; gap: 2px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #1d1d1f; line-height: 1.1; }
.kpi-label { font-size: 13px; color: #6e6e73; }
.kpi-sub { font-size: 12px; color: #aeaeb2; }

/* Two column layout */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

/* Alert summary */
.alert-summary, .status-section {
  background: #fff; border: 1px solid rgba(0,0,0,0.06); border-radius: 14px; padding: 20px;
}
.alert-list { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
.alert-item { display: flex; gap: 12px; align-items: center; }
.alert-icon {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 14px; flex-shrink: 0;
}
.alert-info { display: flex; flex-direction: column; gap: 2px; }
.alert-title { font-size: 14px; font-weight: 500; color: #1d1d1f; }
.alert-desc { font-size: 12px; color: #aeaeb2; }

/* Status bar */
.status-bar {
  height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; margin: 16px 0 8px;
}
.bar-online { height: 100%; background: linear-gradient(90deg, #34C759, #30D158); border-radius: 4px; transition: width 0.5s; }
.status-labels { display: flex; justify-content: space-between; font-size: 12px; }
.label-online { color: #34C759; }
.label-offline { color: #aeaeb2; }

/* Device table */
.devices-section {
  background: #fff; border: 1px solid rgba(0,0,0,0.06); border-radius: 14px; padding: 20px;
}

/* AI summary */
.ai-summary {
  background: linear-gradient(135deg, #f0f6ff, #f5f0ff);
  border: 1px solid #e0e8f5; border-radius: 12px; padding: 16px 20px;
  display: flex; align-items: center; gap: 10px;
}
.ai-icon { font-size: 18px; }
.ai-text { font-size: 13px; color: #333; line-height: 1.6; }

.system-health {
  background: #fff; border: 1px solid rgba(0,0,0,0.06); border-radius: 14px; padding: 20px;
}
.health-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 12px; }
.health-item { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #333; }
.health-label { font-weight: 500; color: #6e6e73; min-width: 60px; }
.health-dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-green { background: #34C759; }
.dot-red { background: #FF3B30; }
@media (max-width: 640px) { .health-grid { grid-template-columns: 1fr; } }

@media (max-width: 1024px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .kpi-grid { grid-template-columns: 1fr; }
}
</style>
