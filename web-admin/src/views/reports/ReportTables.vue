<template>
  <div class="tables-container">
    <!-- 设备逐台分析表 -->
    <div class="table-card" v-if="tableData.device_breakdown?.length">
      <h3>📊 设备逐台分析表</h3>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th class="rank">#</th>
              <th>设备名称</th>
              <th>位置</th>
              <th>平均 AQI</th>
              <th>最高 AQI</th>
              <th>PM2.5</th>
              <th>NO₂</th>
              <th>达标率</th>
              <th>超标次数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in sortedDevices" :key="d.device_id">
              <td class="rank">{{ d.rank }}</td>
              <td><strong>{{ d.device_name || d.device_id }}</strong></td>
              <td>{{ d.district || '-' }}</td>
              <td>
                <span :class="'aqi-tag ' + aqiLevel(d.avg_aqi)">{{ d.avg_aqi }}</span>
              </td>
              <td>{{ d.max_aqi }}</td>
              <td>{{ d.avg_pm25 }}</td>
              <td>{{ d.avg_no2 }}</td>
              <td>
                <span :style="{ color: d.compliance_pct >= 90 ? '#34C759' : d.compliance_pct >= 80 ? '#FF9500' : '#FF3B30' }">
                  {{ d.compliance_pct }}%
                </span>
              </td>
              <td>{{ d.exceed_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 日均值对比表 -->
    <div class="table-card" v-if="tableData.daily_breakdown?.length">
      <h3>📅 日均值对比表</h3>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>AQI</th>
              <th>最高 AQI</th>
              <th>PM2.5</th>
              <th>NO₂</th>
              <th>SO₂</th>
              <th>O₃</th>
              <th>数据量</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in tableData.daily_breakdown" :key="d.date">
              <td>{{ d.date }}</td>
              <td>
                <span :class="'aqi-tag ' + aqiLevel(d.avg_aqi)">{{ d.avg_aqi }}</span>
              </td>
              <td>{{ d.max_aqi }}</td>
              <td>{{ d.avg_pm25 }}</td>
              <td>{{ d.avg_no2 }}</td>
              <td>{{ d.avg_so2 }}</td>
              <td>{{ d.avg_o3 }}</td>
              <td>{{ d.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 污染物超标统计表 -->
    <div class="table-card" v-if="tableData.exceedance_summary?.length">
      <h3>⚠️ 污染物超标统计</h3>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>污染物</th>
              <th>阈值</th>
              <th>超标次数</th>
              <th>超标率</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in tableData.exceedance_summary" :key="e.pollutant">
              <td><strong>{{ e.pollutant }}</strong></td>
              <td>{{ e.threshold }}</td>
              <td>{{ e.exceed_count }}</td>
              <td>{{ e.exceed_rate }}%</td>
              <td>
                <span :class="'status-tag ' + (e.exceed_rate > 10 ? 'bad' : e.exceed_rate > 5 ? 'warn' : 'good')">
                  {{ e.exceed_rate > 10 ? '超标严重' : e.exceed_rate > 5 ? '轻度超标' : '正常' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 环比对比表 -->
    <div class="table-card" v-if="tableData.previous_period">
      <h3>📈 环比对比表</h3>
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>指标</th>
              <th>本期</th>
              <th>上期</th>
              <th>变化</th>
              <th>趋势</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>平均 AQI</td>
              <td>{{ tableData.previous_period.avg_aqi }}</td>
              <td>{{ tableData.previous_period.avg_aqi }}</td>
              <td v-if="tableData.comparison?.aqi_change !== undefined">
                {{ tableData.comparison.aqi_change > 0 ? '+' : '' }}{{ tableData.comparison.aqi_change }}%
              </td>
              <td v-else>-</td>
              <td v-if="tableData.comparison?.aqi_change !== undefined">
                <span :class="'trend-icon ' + (tableData.comparison.aqi_change <= 0 ? 'up' : 'down')">
                  {{ tableData.comparison.aqi_change <= 0 ? '↓ 改善' : '↑ 恶化' }}
                </span>
              </td>
              <td v-else>-</td>
            </tr>
            <tr>
              <td>PM2.5</td>
              <td>{{ tableData.previous_period.avg_pm25 }}</td>
              <td>{{ tableData.previous_period.avg_pm25 }}</td>
              <td v-if="tableData.comparison?.pm25_change !== undefined">
                {{ tableData.comparison.pm25_change > 0 ? '+' : '' }}{{ tableData.comparison.pm25_change }}%
              </td>
              <td v-else>-</td>
              <td v-if="tableData.comparison?.pm25_change !== undefined">
                <span :class="'trend-icon ' + (tableData.comparison.pm25_change <= 0 ? 'up' : 'down')">
                  {{ tableData.comparison.pm25_change <= 0 ? '↓ 改善' : '↑ 恶化' }}
                </span>
              </td>
              <td v-else>-</td>
            </tr>
            <tr>
              <td>达标率</td>
              <td>{{ tableData.previous_period.compliance_rate }}%</td>
              <td>{{ tableData.previous_period.compliance_rate }}%</td>
              <td v-if="tableData.comparison?.compliance_change !== undefined">
                {{ tableData.comparison.compliance_change > 0 ? '+' : '' }}{{ tableData.comparison.compliance_change }}%
              </td>
              <td v-else>-</td>
              <td v-if="tableData.comparison?.compliance_change !== undefined">
                <span :class="'trend-icon ' + (tableData.comparison.compliance_change >= 0 ? 'up' : 'down')">
                  {{ tableData.comparison.compliance_change >= 0 ? '↑ 提升' : '↓ 下降' }}
                </span>
              </td>
              <td v-else>-</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tableData: { type: Object, default: () => ({}) }
})

const sortedDevices = computed(() => {
  const list = [...(props.tableData.device_breakdown || [])]
  return list.sort((a, b) => b.avg_aqi - a.avg_aqi)
})

function aqiLevel(aqi) {
  if (aqi <= 50) return 'level-good'
  if (aqi <= 100) return 'level-moderate'
  if (aqi <= 150) return 'level-unhealthy'
  if (aqi <= 200) return 'level-bad'
  return 'level-danger'
}
</script>

<style scoped>
.tables-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin: 24px 0;
}

.table-card {
  background: #fff;
  border: 1px solid #e8e8ed;
  border-radius: 12px;
  padding: 20px;
}

.table-card h3 {
  font-size: 15px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0 0 16px 0;
}

.table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table th {
  background: #f5f5f7;
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
  color: #6e6e73;
  font-size: 12px;
  white-space: nowrap;
  border-bottom: 1px solid #e8e8ed;
}

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f0f0f0;
  color: #1d1d1f;
}

.data-table tr:hover td {
  background: #fafafa;
}

.rank {
  width: 40px;
  text-align: center;
  color: #aeaeb2;
  font-weight: 500;
}

.aqi-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 12px;
}

.level-good { background: rgba(52,199,89,0.15); color: #34C759; }
.level-moderate { background: rgba(0,122,255,0.12); color: #007AFF; }
.level-unhealthy { background: rgba(255,149,0,0.15); color: #FF9500; }
.level-bad { background: rgba(255,59,48,0.12); color: #FF3B30; }
.level-danger { background: rgba(175,82,222,0.15); color: #AF52DE; }

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.good { background: rgba(52,199,89,0.12); color: #34C759; }
.status-tag.warn { background: rgba(255,149,0,0.12); color: #FF9500; }
.status-tag.bad { background: rgba(255,59,48,0.12); color: #FF3B30; }

.trend-icon {
  font-size: 12px;
  font-weight: 500;
}

.trend-icon.up { color: #34C759; }
.trend-icon.down { color: #FF3B30; }
</style>
