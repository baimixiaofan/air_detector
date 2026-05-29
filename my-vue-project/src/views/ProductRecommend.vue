<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

// 模拟我们的环保硬件和软件增值产品数据
const products = ref([
  {
    id: 1,
    name: '微型空气监测站 V2.0',
    desc: '支持百米级网格化监测，高精度多参数，内置太阳能供电模块，免布线。',
    price: '¥ 12,800',
    tag: '热销爆款',
    tagType: 'danger',
    color: 'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)', // 模拟一张好看的产品主图
  },
  {
    id: 2,
    name: '工业粉尘在线分析仪',
    desc: '专为施工扬尘、矿山环境设计，抗恶劣环境，带自动除湿和自动清洗功能。',
    price: '¥ 8,500',
    tag: '本月新品',
    tagType: 'success',
    color: 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)',
  },
  {
    id: 3,
    name: '多参数水质自动监测仪',
    desc: '原位实时监测 pH、溶解氧、浊度、电导率等核心参数，支持一键校准。',
    price: '¥ 25,000',
    tag: '专业版',
    tagType: 'warning',
    color: 'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
  },
  {
    id: 4,
    name: '绿盾云平台 - 企业高级版',
    desc: '解锁 AI 污染趋势预测、历史数据永久存储、微信小程序多端协同等高级权益。',
    price: '¥ 3,600 / 年',
    tag: '软件服务',
    tagType: 'info',
    color: 'linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%)',
  },
])

const handleInquire = (productName) => {
  ElMessage.success(`您已成功提交关于【${productName}】的咨询意向，专属商务专员将很快联系您！`)
}
</script>

<template>
  <div class="product-container">
    <el-card shadow="never" class="header-card">
      <div class="header-title">
        <span>🎁 绿盾精选：增值产品与服务推荐</span>
        <span class="sub-title">为您的环保监测业务提供更强大的软硬件支持</span>
      </div>
    </el-card>

    <el-row :gutter="20" class="product-grid">
      <el-col v-for="item in products" :key="item.id" :xs="24" :sm="12" :md="12" :lg="6" :xl="6">
        <el-card class="product-card" shadow="hover" :body-style="{ padding: '0px' }">
          <div class="product-image" :style="{ background: item.color }">
            <el-tag :type="item.tagType" effect="dark" class="product-tag">{{ item.tag }}</el-tag>
          </div>

          <div class="product-info">
            <h3 class="product-name">{{ item.name }}</h3>
            <p class="product-desc">{{ item.desc }}</p>
            <div class="product-bottom">
              <span class="product-price">{{ item.price }}</span>
              <el-button type="primary" round size="small" @click="handleInquire(item.name)">
                获取报价
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.product-container {
  padding-bottom: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: bold;
  font-size: 16px;
}

.sub-title {
  font-size: 13px;
  color: #909399;
  font-weight: normal;
}

.product-grid {
  display: flex;
  flex-wrap: wrap;
}

/* 卡片整体样式 */
.product-card {
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
}

.product-card:hover {
  transform: translateY(-5px); /* 鼠标悬浮时卡片整体向上微移，增加高级感 */
}

/* 模拟图片区域 */
.product-image {
  height: 180px;
  width: 100%;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.product-tag {
  position: absolute;
  top: 10px;
  left: 10px;
}

/* 文字信息区域 */
.product-info {
  padding: 16px;
}

.product-name {
  margin: 0 0 10px 0;
  font-size: 16px;
  color: #303133;
}

.product-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  height: 40px; /* 固定高度，防止描述长短不一导致卡片不齐 */
  margin-bottom: 15px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2; /* 最多显示两行，超出显示省略号 */
  line-clamp: 2;
  overflow: hidden;
}

.product-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-price {
  font-size: 18px;
  font-weight: bold;
  color: #f56c6c;
}
</style>
