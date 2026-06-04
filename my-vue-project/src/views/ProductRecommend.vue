<script setup>
import { ref, computed } from 'vue'

// 1. 模拟各地站点的实时监测数据
const siteData = ref([
  {
    id: 'S001',
    name: '朝阳区奥体中心站',
    readings: { pm25: 158, humidity: 45, noise: 55 },
    issue: '空气重度污染',
  },
  {
    id: 'S002',
    name: '海淀区万柳站',
    readings: { pm25: 35, humidity: 15, noise: 50 },
    issue: '环境极度干燥',
  },
  {
    id: 'S003',
    name: '东城区天坛站',
    readings: { pm25: 42, humidity: 50, noise: 85 },
    issue: '噪音严重超标',
  },
  {
    id: 'S004',
    name: '西城区万寿西宫站',
    readings: { pm25: 120, humidity: 20, noise: 40 },
    issue: '空气污染 且 气候干燥', // 复合问题
  },
  {
    id: 'S005',
    name: '顺义区中央别墅区',
    readings: { pm25: 25, humidity: 55, noise: 45 },
    issue: '各项指标优良',
  },
])

// 默认选中第一个站点
const selectedSiteId = ref('S001')

// 获取当前选中的站点信息
const currentSite = computed(() => {
  return siteData.value.find((site) => site.id === selectedSiteId.value)
})

// 💡 2. 核心智能推荐逻辑：根据当前站点的具体数值，动态生成推荐列表
const recommendedProducts = computed(() => {
  const readings = currentSite.value.readings
  const recs = []

  // 规则 1：如果 PM2.5 大于 75，推荐空气净化设备
  if (readings.pm25 > 75) {
    recs.push({
      id: 'p1',
      title: '工业级空气净化塔 (重型)',
      reason: `检测到该区域 PM2.5 高达 ${readings.pm25} μg/m³，存在重度扬尘/雾霾风险。`,
      desc: '专为室外和半开放空间设计，有效吸附颗粒物，快速降低局部 PM2.5 浓度。',
      price: '¥ 45,000',
      tag: '污染治理',
      gradient: 'linear-gradient(135deg, #ff4d4f, #ff7875)', // 红色系警告色
    })
  }

  // 规则 2：如果湿度低于 30%，推荐增湿设备
  if (readings.humidity < 30) {
    recs.push({
      id: 'p2',
      title: '高压微雾降尘增湿机',
      reason: `检测到该区域湿度仅为 ${readings.humidity}%，极度干燥，极易引发二次扬尘。`,
      desc: '采用超声波与高压微雾技术，大面积快速增加空气湿度，抑制粉尘扩散。',
      price: '¥ 12,800',
      tag: '气候调节',
      gradient: 'linear-gradient(135deg, #1890ff, #69c0ff)', // 蓝色系水润色
    })
  }

  // 规则 3：如果噪音大于 70dB，推荐降噪设备
  if (readings.noise > 70) {
    recs.push({
      id: 'p3',
      title: '智能主动声学屏障',
      reason: `检测到噪音值高达 ${readings.noise} dB，超出城市声环境标准。`,
      desc: '采用高分子吸音材料，配合反向声波发射器，可降低环境噪音 15-20 分贝。',
      price: '¥ 28,000',
      tag: '噪音控制',
      gradient: 'linear-gradient(135deg, #faad14, #ffd666)', // 橙色系警告色
    })
  }

  // 规则 4：如果数据全都正常，推荐常规保养服务
  if (recs.length === 0) {
    recs.push({
      id: 'p4',
      title: '绿盾白金维保服务包',
      reason: '当前区域各项环境指标均处于优良状态，设备运行负荷正常。',
      desc: '提供全套设备的年度深度清洁、传感器校准及固件升级服务，防患于未然。',
      price: '¥ 5,000 / 年',
      tag: '预防维护',
      gradient: 'linear-gradient(135deg, #52c41a, #95de64)', // 绿色系健康色
    })
  }

  return recs
})
</script>

<template>
  <div class="recommend-container">
    <el-card shadow="never" class="diagnose-card">
      <template #header>
        <div class="header-toolbar">
          <span style="font-size: 16px; font-weight: bold; color: #0088ff">
            🧠 AI 智能环境诊断与解决方案
          </span>

          <div class="selector-box">
            <span class="label">选择目标站点：</span>
            <el-select v-model="selectedSiteId" style="width: 200px">
              <el-option
                v-for="site in siteData"
                :key="site.id"
                :label="site.name"
                :value="site.id"
              />
            </el-select>
          </div>
        </div>
      </template>

      <div class="site-status">
        <div class="status-title">当前监测概况</div>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="data-block">
              <div class="data-label">PM2.5 浓度</div>
              <div class="data-value" :class="{ 'text-danger': currentSite.readings.pm25 > 75 }">
                {{ currentSite.readings.pm25 }} <span class="unit">μg/m³</span>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="data-block">
              <div class="data-label">环境湿度</div>
              <div
                class="data-value"
                :class="{ 'text-warning': currentSite.readings.humidity < 30 }"
              >
                {{ currentSite.readings.humidity }} <span class="unit">%</span>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="data-block">
              <div class="data-label">噪音分贝</div>
              <div class="data-value" :class="{ 'text-orange': currentSite.readings.noise > 70 }">
                {{ currentSite.readings.noise }} <span class="unit">dB</span>
              </div>
            </div>
          </el-col>
        </el-row>
        <div class="ai-conclusion">
          <span class="icon">🤖</span> AI 诊断结论：<strong>{{ currentSite.issue }}</strong>
        </div>
      </div>
    </el-card>

    <div class="section-title">✨ 基于诊断结果的专属解决方案</div>

    <el-row :gutter="20">
      <transition-group name="list" tag="div" style="display: flex; flex-wrap: wrap; width: 100%">
        <el-col
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          v-for="item in recommendedProducts"
          :key="item.id"
          style="margin-bottom: 20px"
        >
          <el-card shadow="hover" class="product-card">
            <div class="product-cover" :style="{ background: item.gradient }">
              <el-tag
                effect="dark"
                class="product-tag"
                :color="'rgba(0,0,0,0.2)'"
                style="border: none"
              >
                {{ item.tag }}
              </el-tag>
            </div>
            <div class="product-info">
              <h3 class="product-title">{{ item.title }}</h3>
              <div class="reason-box">{{ item.reason }}</div>
              <p class="product-desc">{{ item.desc }}</p>
              <div class="product-bottom">
                <span class="price">{{ item.price }}</span>
                <el-button type="primary" size="small" plain>一键部署</el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </transition-group>
    </el-row>
  </div>
</template>

<style scoped>
.recommend-container {
  padding-bottom: 20px;
}

.header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.label {
  font-size: 14px;
  color: #64748b;
  margin-right: 10px;
}

/* 状态概况区域 */
.site-status {
  background: rgba(0, 162, 255, 0.03);
  border: 1px dashed rgba(0, 162, 255, 0.3);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 10px;
}
.status-title {
  font-size: 14px;
  font-weight: bold;
  color: #334155;
  margin-bottom: 15px;
}
.data-block {
  text-align: center;
}
.data-label {
  font-size: 13px;
  color: #94a3b8;
  margin-bottom: 5px;
}
.data-value {
  font-size: 32px;
  font-weight: 900;
  color: #10b981;
} /* 默认绿色 */
.unit {
  font-size: 14px;
  font-weight: normal;
}

/* 异常数据的高亮颜色 */
.text-danger {
  color: #ff4d4f !important;
}
.text-warning {
  color: #1890ff !important;
} /* 湿度低用蓝色警示 */
.text-orange {
  color: #faad14 !important;
}

.ai-conclusion {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 162, 255, 0.1);
  font-size: 15px;
  color: #1e293b;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #334155;
  margin: 25px 0 15px 5px;
}

/* 产品卡片样式 */
.product-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(0, 162, 255, 0.1) !important;
}
:deep(.el-card__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.product-cover {
  height: 120px;
  position: relative;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}
.product-tag {
  position: absolute;
  top: 12px;
  left: 12px;
}

.product-info {
  padding: 15px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}
.product-title {
  font-size: 16px;
  margin: 0 0 10px 0;
  color: #1e293b;
  font-weight: 900;
}
.reason-box {
  background: rgba(255, 77, 79, 0.05);
  border-left: 3px solid #ff4d4f;
  padding: 8px 10px;
  font-size: 12px;
  color: #d4380d;
  margin-bottom: 10px;
  border-radius: 0 4px 4px 0;
}
.product-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  margin-bottom: 20px;
  flex-grow: 1;
}
.product-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.price {
  font-size: 18px;
  font-weight: bold;
  color: #ff4d4f;
}

/* 动画过渡 */
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
</style>
