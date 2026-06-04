<template>
  <div class="stat-card" :class="`stat-card--${variant}`">
    <div class="stat-card__header">
      <span class="stat-card__title">{{ title }}</span>
      <el-icon class="stat-card__settings" :size="16"><Setting /></el-icon>
    </div>
    <div class="stat-card__body">
      <div class="stat-card__value-row">
        <span class="stat-card__value">{{ formattedValue }}</span>
        <div v-if="change !== undefined" class="stat-card__change" :class="changeClass">
          <el-icon :size="14">
            <Top v-if="change > 0" />
            <Bottom v-else-if="change < 0" />
          </el-icon>
          <span>{{ Math.abs(change) }}%</span>
        </div>
      </div>
      <p v-if="subtitle" class="stat-card__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="trendData && trendData.length" class="stat-card__trend">
      <svg :viewBox="`0 0 ${trendData.length * 10} 30`" preserveAspectRatio="none">
        <polyline
          :points="trendPoints"
          fill="none"
          :stroke="trendColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  value: [String, Number],
  subtitle: String,
  icon: [String, Object],
  variant: { type: String, default: 'light' },
  change: Number,
  changeLabel: String,
  trendData: { type: Array, default: () => [] },
  color: { type: String, default: '' }
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toLocaleString()
  }
  return props.value
})

const changeClass = computed(() => {
  if (props.change > 0) return 'stat-card__change--up'
  if (props.change < 0) return 'stat-card__change--down'
  return ''
})

const trendColor = computed(() => {
  if (props.color) return props.color
  if (props.variant === 'dark') return '#ffffff'
  if (props.variant === 'gradient') return '#ffffff'
  return '#e17055'
})

const trendPoints = computed(() => {
  if (!props.trendData.length) return ''
  const max = Math.max(...props.trendData)
  const min = Math.min(...props.trendData)
  const range = max - min || 1
  return props.trendData
    .map((v, i) => `${i * 10},${30 - ((v - min) / range) * 28}`)
    .join(' ')
})
</script>

<style scoped>
.stat-card {
  border-radius: var(--radius-md);
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-sizing: border-box;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* Light variant (default) */
.stat-card--light {
  background: var(--card-bg);
  box-shadow: var(--shadow-sm);
}

/* Dark variant */
.stat-card--dark {
  background: var(--kpi-dark-bg);
  color: var(--text-inverse);
}

/* Gradient variant */
.stat-card--gradient {
  background: var(--color-primary-gradient);
  color: var(--text-inverse);
}

.stat-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.stat-card__title {
  font-size: var(--font-size-card-title);
  font-weight: 500;
  opacity: 0.85;
}

.stat-card__settings {
  opacity: 0.5;
  cursor: pointer;
  transition: opacity var(--transition-fast);
}
.stat-card__settings:hover {
  opacity: 1;
}

.stat-card__body {
  position: relative;
  z-index: 1;
}

.stat-card__value-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.stat-card__value {
  font-size: var(--font-size-kpi);
  font-weight: 700;
  line-height: 1.1;
}

.stat-card__change {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: var(--font-size-caption);
  font-weight: 600;
}
.stat-card__change--up {
  color: #ff6b6b;
}
.stat-card__change--down {
  color: #51cf66;
}
.stat-card--dark .stat-card__change--up,
.stat-card--gradient .stat-card__change--up {
  color: #ff8787;
}
.stat-card--dark .stat-card__change--down,
.stat-card--gradient .stat-card__change--down {
  color: #69db7c;
}

.stat-card__subtitle {
  font-size: var(--font-size-caption);
  opacity: 0.6;
  margin-top: 8px;
}

.stat-card__trend {
  margin-top: 12px;
  height: 30px;
}
.stat-card__trend svg {
  width: 100%;
  height: 100%;
}
</style>
