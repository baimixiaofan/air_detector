<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'

// 获取地图容器的引用
const mapRef = ref(null)
// 保存地图实例
let map = null

// 模拟的站点数据（加上了经纬度，大概在北京市区）
const siteData = [
  { id: 'ST-001', name: '朝阳区奥体中心站', lnglat: [116.397428, 39.98923], status: '正常' },
  { id: 'ST-002', name: '海淀区万柳站', lnglat: [116.288968, 39.967817], status: '告警' },
  { id: 'ST-003', name: '东城区天坛站', lnglat: [116.410886, 39.881949], status: '正常' },
  { id: 'ST-004', name: '西城区万寿西宫站', lnglat: [116.363943, 39.880521], status: '离线' },
]

const initMap = () => {
  // 1. 设置安全密钥（必须写在 load 之前）
  window._AMapSecurityConfig = {
    securityJsCode: '993f672551490a9decd7a4fc0ca0db29', // 👈 替换成你的真实安全密钥
  }

  // 2. 加载高德地图 API
  AMapLoader.load({
    key: '728daa3f755a1214e038cc9962479bfc', // 👈 替换成你的真实 Key
    version: '2.0', // 指定要加载的 JSAPI 的版本
    plugins: ['AMap.Marker', 'AMap.InfoWindow'], // 需要使用的插件列表
  })
    .then((AMap) => {
      // 3. 初始化地图
      map = new AMap.Map(mapRef.value, {
        viewMode: '2D', // 是否为3D地图模式
        zoom: 11, // 初始化地图级别
        center: [116.397428, 39.90923], // 初始化地图中心点位置（北京）
      })

      // 4. 遍历数据，在地图上打点（Marker）
      siteData.forEach((site) => {
        // 根据状态决定标记点的颜色图标 (b:蓝, r:红)
        let iconLetter = 'b'
        if (site.status === '告警') {
          iconLetter = 'r'
        } else if (site.status === '离线') {
          iconLetter = 'bs' // 高德默认图标库没灰色，我们用 bs(带阴影的蓝) 代替一下
        }

        const marker = new AMap.Marker({
          position: new AMap.LngLat(site.lnglat[0], site.lnglat[1]), // 经纬度对象
          title: site.name,
          // 💡 关键修复：把写死的 _b 换成动态变量 ${iconLetter}
          icon: `//webapi.amap.com/theme/v1.3/markers/n/mark_${iconLetter}.png`,
        })

        // 可以给点加上文字标签
        marker.setLabel({
          offset: new AMap.Pixel(20, 20),
          content: `<div class='info'>${site.name}</div>`,
          direction: 'right',
        })

        // 将标记添加到地图上
        map.add(marker)
      })
    })
    .catch((e) => {
      console.error('高德地图加载失败:', e)
    })
}

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  // 离开页面时销毁地图实例，释放内存
  if (map) {
    map.destroy()
  }
})
</script>

<template>
  <div class="map-container">
    <el-card shadow="never" class="map-card" :body-style="{ padding: '0px', height: '100%' }">
      <template #header>
        <div class="card-header">
          <span>📍 站点实时地图分布</span>
        </div>
      </template>
      <div ref="mapRef" class="real-map"></div>
    </el-card>
  </div>
</template>

<style scoped>
.map-container {
  height: calc(100vh - 120px); /* 让地图卡片撑满屏幕剩余高度 */
}

.map-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.real-map {
  width: 100%;
  height: 100%; /* 占据卡片的全部剩余空间 */
}

/* 高德地图标签文字的样式（全局穿透） */
:deep(.amap-marker-label) {
  border: none;
  background-color: transparent;
}
:deep(.info) {
  background: white;
  padding: 4px 8px;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  font-size: 12px;
  font-weight: bold;
}
</style>
