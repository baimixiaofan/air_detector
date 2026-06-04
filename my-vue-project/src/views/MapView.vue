<script setup>
import { ref, shallowRef, onMounted, onUnmounted } from 'vue'
import AMapLoader from '@amap/amap-jsapi-loader'

// 💡 记得填入你自己的密钥和 Key！
window._AMapSecurityConfig = {
  securityJsCode: '993f672551490a9decd7a4fc0ca0d',
}
const AMAP_KEY = '728daa3f755a1214e038cc9962479bfc'

const mapRef = ref(null)
// 使用 shallowRef 存储地图实例，避免 Vue 深度劫持导致性能卡顿
const mapInstance = shallowRef(null)
let AMapObj = null // 存储 AMap 全局对象

// 当前选中的地区，默认北京
const currentRegion = ref('beijing')

// 💡 模拟各省份/直辖市的数据字典
// 💡 涵盖全国 34 个省级行政区的完整坐标数据字典
const regionData = {
  beijing: {
    name: '北京市',
    center: [116.407394, 39.904211],
    zoom: 10,
    stations: [
      { name: '奥体中心站', lnglat: [116.397228, 39.984102], status: 'normal' },
      { name: '万柳站', lnglat: [116.299059, 39.972328], status: 'alert' },
      { name: '天坛站', lnglat: [116.407394, 39.882111], status: 'normal' },
    ],
  },
  tianjin: { name: '天津市', center: [117.200983, 39.084158], zoom: 10, stations: [] },
  hebei: { name: '河北省', center: [114.51486, 38.042225], zoom: 7, stations: [] },
  shanxi: { name: '山西省', center: [112.548879, 37.87059], zoom: 7, stations: [] },
  neimenggu: { name: '内蒙古自治区', center: [111.765617, 40.817498], zoom: 6, stations: [] },
  liaoning: { name: '辽宁省', center: [123.431474, 41.805698], zoom: 7, stations: [] },
  jilin: { name: '吉林省', center: [125.323544, 43.817071], zoom: 7, stations: [] },
  heilongjiang: { name: '黑龙江省', center: [126.661669, 45.756967], zoom: 6, stations: [] },
  shanghai: {
    name: '上海市',
    center: [121.473662, 31.230372],
    zoom: 10,
    stations: [
      { name: '浦东张江站', lnglat: [121.603332, 31.203541], status: 'normal' },
      { name: '静安寺站', lnglat: [121.445214, 31.223483], status: 'normal' },
      { name: '徐家汇站', lnglat: [121.436525, 31.188522], status: 'alert' },
    ],
  },
  jiangsu: { name: '江苏省', center: [118.796877, 32.060255], zoom: 7, stations: [] },
  zhejiang: { name: '浙江省', center: [120.152791, 30.267446], zoom: 7, stations: [] },
  anhui: { name: '安徽省', center: [117.227239, 31.820586], zoom: 7, stations: [] },
  fujian: { name: '福建省', center: [119.296554, 26.074507], zoom: 7, stations: [] },
  jiangxi: { name: '江西省', center: [115.858198, 28.682892], zoom: 7, stations: [] },
  shandong: { name: '山东省', center: [117.020359, 36.66853], zoom: 7, stations: [] },
  henan: { name: '河南省', center: [113.625368, 34.746599], zoom: 7, stations: [] },
  hubei: { name: '湖北省', center: [114.341861, 30.546498], zoom: 7, stations: [] },
  hunan: { name: '湖南省', center: [112.938814, 28.228209], zoom: 7, stations: [] },
  guangdong: {
    name: '广东省',
    center: [113.264385, 23.129112],
    zoom: 7,
    stations: [
      { name: '广州天河站', lnglat: [113.324553, 23.106414], status: 'normal' },
      { name: '深圳南山站', lnglat: [113.93029, 22.53291], status: 'normal' },
      { name: '东莞松山湖站', lnglat: [113.883737, 22.906751], status: 'alert' },
    ],
  },
  guangxi: { name: '广西壮族自治区', center: [108.327546, 22.815478], zoom: 7, stations: [] },
  hainan: { name: '海南省', center: [110.329519, 20.035234], zoom: 8, stations: [] },
  chongqing: { name: '重庆市', center: [106.551556, 29.563009], zoom: 9, stations: [] },
  sichuan: {
    name: '四川省',
    center: [104.065735, 30.659462],
    zoom: 6,
    stations: [
      { name: '成都武侯站', lnglat: [104.04339, 30.641982], status: 'normal' },
      { name: '绵阳游仙站', lnglat: [104.757196, 31.46402], status: 'normal' },
    ],
  },
  guizhou: { name: '贵州省', center: [106.713478, 26.578343], zoom: 7, stations: [] },
  yunnan: { name: '云南省', center: [102.712251, 25.040609], zoom: 6, stations: [] },
  xizang: { name: '西藏自治区', center: [91.140856, 29.645554], zoom: 6, stations: [] },
  shaanxi: { name: '陕西省', center: [108.93984, 34.34127], zoom: 7, stations: [] },
  gansu: { name: '甘肃省', center: [103.826308, 36.059421], zoom: 6, stations: [] },
  qinghai: { name: '青海省', center: [101.780199, 36.620901], zoom: 6, stations: [] },
  ningxia: { name: '宁夏回族自治区', center: [106.230909, 38.487193], zoom: 7, stations: [] },
  xinjiang: { name: '新疆维吾尔自治区', center: [87.616848, 43.825592], zoom: 5, stations: [] },
  taiwan: { name: '台湾省', center: [121.509062, 25.044332], zoom: 7, stations: [] },
  hongkong: { name: '香港特别行政区', center: [114.16546, 22.275342], zoom: 10, stations: [] },
  macau: { name: '澳门特别行政区', center: [113.549134, 22.198751], zoom: 11, stations: [] },
}

// 初始化地图
const initMap = async () => {
  try {
    AMapObj = await AMapLoader.load({
      key: AMAP_KEY,
      version: '2.0',
      plugins: ['AMap.Marker'],
    })

    const initialConfig = regionData[currentRegion.value]

    mapInstance.value = new AMapObj.Map(mapRef.value, {
      zoom: initialConfig.zoom,
      center: initialConfig.center,
      // 💡 核心魔法：强制使用极客深蓝主题！
      mapStyle: 'amap://styles/darkblue',
      pitch: 45, // 开启 3D 俯视视角，更有科技感
      viewMode: '3D',
    })

    // 初始化时画出点位
    renderStations(initialConfig.stations)
  } catch (e) {
    console.error('地图加载失败', e)
  }
}

// 渲染站点标记
const renderStations = (stations) => {
  if (!mapInstance.value || !AMapObj) return

  // 先清除地图上已有的所有旧标记
  mapInstance.value.clearMap()

  stations.forEach((item) => {
    // 根据状态给标记不同颜色：正常是青色，告警是红色
    const color = item.status === 'normal' ? '#00f5ff' : '#ff4d4f'
    const shadow = item.status === 'normal' ? '0 0 15px #00f5ff' : '0 0 20px #ff4d4f'

    // 💡 自定义发光 HTML 圆点标记
    const markerContent = `
      <div style="
        width: 14px; 
        height: 14px; 
        background: ${color}; 
        border-radius: 50%; 
        border: 2px solid #fff;
        box-shadow: ${shadow};
        animation: pulse 2s infinite;
      "></div>
      <div style="
        color: ${color}; 
        font-size: 12px; 
        font-weight: bold; 
        margin-top: 5px; 
        text-shadow: 0 0 5px #000;
        white-space: nowrap;
        transform: translateX(-30%);
      ">${item.name}</div>
    `

    const marker = new AMapObj.Marker({
      position: item.lnglat,
      content: markerContent,
      offset: new AMapObj.Pixel(-7, -7), // 让圆点中心对准坐标
    })

    mapInstance.value.add(marker)
  })
}

// 当下拉框选项改变时触发
const handleRegionChange = (val) => {
  const config = regionData[val]
  if (!mapInstance.value || !config) return

  // 💡 让地图平滑飞到新省份的中心点
  mapInstance.value.setZoomAndCenter(config.zoom, config.center, false, 1000)

  // 重新渲染该省份的点位
  renderStations(config.stations)
}

onMounted(() => {
  initMap()
})

onUnmounted(() => {
  if (mapInstance.value) {
    mapInstance.value.destroy()
  }
})
</script>

<template>
  <div class="map-view-container">
    <el-card shadow="never" class="cyber-map-card">
      <template #header>
        <div class="header-toolbar">
          <span class="title">📍 区域站点监控态势</span>

          <div class="control-box">
            <span style="font-size: 13px; color: #94a3b8; margin-right: 10px">当前监控区域:</span>
            <el-select v-model="currentRegion" @change="handleRegionChange" style="width: 160px">
              <el-option
                v-for="(data, key) in regionData"
                :key="key"
                :label="data.name"
                :value="key"
              />
            </el-select>
          </div>
        </div>
      </template>

      <div ref="mapRef" class="map-box"></div>
    </el-card>
  </div>
</template>

<style scoped>
.map-view-container {
  padding-bottom: 20px;
}

.header-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  color: #00f5ff;
  font-weight: bold;
  text-shadow: 0 0 8px rgba(0, 245, 255, 0.4);
}

.map-box {
  width: 100%;
  /* 让地图铺满剩下的高度 */
  height: calc(100vh - 220px);
  min-height: 500px;
  border-radius: 4px;
}

/* 全局动画：让地图上的监控点像呼吸一样闪烁 */
@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.4);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 覆盖 el-select 的默认白底，让下拉框也变高级 */
:deep(.el-input__wrapper) {
  background-color: rgba(10, 25, 50, 0.8) !important;
  box-shadow: 0 0 0 1px rgba(0, 245, 255, 0.3) inset !important;
}
:deep(.el-input__inner) {
  color: #00f5ff !important;
  font-weight: bold;
}
</style>
