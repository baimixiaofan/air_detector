<template>
  <div class="page-container monitoring-map-page">
    <PageHeader title="站点地图" />

    <div class="map-layout">
      <!-- Sidebar device list -->
      <div class="map-sidebar">
        <DashboardCard title="设备列表" :no-padding="true">
          <div class="device-list">
            <div
              v-for="device in devices"
              :key="device.device_id"
              class="device-list-item"
              :class="{ 'device-list-item--active': selectedDevice?.device_id === device.device_id }"
              @click="selectDevice(device)"
            >
              <span class="status-dot" :class="device.online !== false ? 'status-dot--pulse' : ''" :style="{ background: device.online !== false ? 'var(--color-success)' : 'var(--text-muted)' }"></span>
              <div class="device-info">
                <span class="device-id">{{ device.device_id }}</span>
                <span class="device-aqi" :style="{ color: aqiLevel(device.aqi).color }">AQI {{ device.aqi ?? '--' }}</span>
              </div>
            </div>
          </div>
        </DashboardCard>
      </div>

      <!-- Map -->
      <div class="map-container">
        <div ref="mapRef" class="leaflet-map"></div>
        <!-- AQI Legend -->
        <div class="map-legend">
          <div class="legend-item" v-for="l in legendItems" :key="l.label">
            <span class="legend-dot" :style="{ background: l.color }"></span>
            <span>{{ l.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { getRealtimeData } from '@/api/monitoring'
import PageHeader from '@/components/common/PageHeader.vue'
import DashboardCard from '@/components/common/DashboardCard.vue'
import { aqiLevel as aqiLevelFn } from '@/utils/format'
import L from 'leaflet'

const mapRef = ref(null)
const devices = ref([])
const selectedDevice = ref(null)
let map = null
let markers = []

const legendItems = [
  { label: '优 (0-50)', color: '#00b894' },
  { label: '良 (51-100)', color: '#fdcb6e' },
  { label: '轻度 (101-150)', color: '#e17055' },
  { label: '中度 (151-200)', color: '#d63031' }
]

function aqiLevel(aqi) {
  return aqiLevelFn(aqi)
}

function getMarkerColor(aqi) {
  if (!aqi) return '#b2bec3'
  if (aqi <= 50) return '#00b894'
  if (aqi <= 100) return '#fdcb6e'
  if (aqi <= 150) return '#e17055'
  return '#d63031'
}

function initMap() {
  if (!mapRef.value || map) return

  map = L.map(mapRef.value, {
    center: [31.2304, 121.4737],
    zoom: 12,
    zoomControl: false
  })

  L.control.zoom({ position: 'topright' }).addTo(map)

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19
  }).addTo(map)
}

function updateMarkers() {
  markers.forEach(m => map.removeLayer(m))
  markers = []

  const validDevices = devices.value.filter(d => d.latitude && d.longitude)
  if (!validDevices.length) return

  validDevices.forEach(d => {
    const color = getMarkerColor(d.aqi)
    const marker = L.circleMarker([d.latitude, d.longitude], {
      radius: 10,
      fillColor: color,
      color: '#fff',
      weight: 2,
      fillOpacity: 0.9
    }).addTo(map)

    marker.bindPopup(`
      <div style="font-size:13px;">
        <strong>${d.device_id}</strong><br/>
        AQI: <span style="color:${color};font-weight:bold;">${d.aqi ?? '--'}</span><br/>
        PM2.5: ${d.pm25 ?? '--'}
      </div>
    `)

    marker.on('click', () => selectDevice(d))
    markers.push(marker)
  })

  // Fit bounds
  const bounds = L.latLngBounds(validDevices.map(d => [d.latitude, d.longitude]))
  map.fitBounds(bounds, { padding: [50, 50] })
}

function selectDevice(device) {
  selectedDevice.value = device
  if (device.latitude && device.longitude) {
    map.setView([device.latitude, device.longitude], 14)
  }
}

async function fetchData() {
  try {
    const res = await getRealtimeData()
    if (res.code === 200 && res.data) {
      devices.value = res.data.devices || []
      await nextTick()
      updateMarkers()
    }
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  initMap()
  fetchData()
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.monitoring-map-page {
  height: calc(100vh - var(--navbar-height));
}
.map-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  height: calc(100vh - var(--navbar-height) - 120px);
}
.map-sidebar {
  overflow-y: auto;
}
.device-list {
  max-height: calc(100vh - var(--navbar-height) - 200px);
  overflow-y: auto;
}
.device-list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background var(--transition-fast);
  border-bottom: 1px solid #f0f2f5;
}
.device-list-item:hover {
  background: #f8f9fb;
}
.device-list-item--active {
  background: var(--color-primary-light);
}
.device-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.device-id {
  font-size: var(--font-size-body);
  color: var(--text-primary);
  font-weight: 500;
}
.device-aqi {
  font-size: var(--font-size-caption);
  font-weight: 600;
}
.map-container {
  position: relative;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}
.leaflet-map {
  width: 100%;
  height: 100%;
}
.map-legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: white;
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  box-shadow: var(--shadow-md);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-caption);
  color: var(--text-secondary);
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
</style>
