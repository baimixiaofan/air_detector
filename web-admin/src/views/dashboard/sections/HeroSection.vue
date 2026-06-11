<template>
  <section class="hero-section">
    <div class="hero-content">
      <div class="hero-badge">
        <span class="badge-dot"></span>
        <span>实时监测中</span>
      </div>
      <h1 class="hero-title">
        <span class="title-gradient">智能空气分析</span>
        <br />
        <span class="title-sub">让数据创造价值</span>
      </h1>
      <p class="hero-desc">
        通过 AI 深度分析家庭空气质量数据，为您生成个性化的健康建议、
        环境优化方案和商业洞察报告
      </p>
    </div>
    <div class="hero-visual">
      <div class="air-orb">
        <div class="orb-ring orb-ring-1"></div>
        <div class="orb-ring orb-ring-2"></div>
        <div class="orb-ring orb-ring-3"></div>
        <div class="orb-core">
          <span class="orb-value">{{ aqi }}</span>
          <span class="orb-label">AQI</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  aqi: {
    type: Number,
    default: 42
  }
})
</script>

<style scoped>
.hero-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 60px 40px;
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.08), rgba(88, 86, 214, 0.08));
  border-radius: var(--radius-xl);
  margin-bottom: 32px;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--glass-border);
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(0, 122, 255, 0.03) 0%, transparent 50%);
  animation: float 8s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(5deg); }
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 600px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(48, 209, 88, 0.12);
  border-radius: 20px;
  margin-bottom: 24px;
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.hero-badge span:last-child {
  font-size: var(--font-size-body);
  color: var(--color-success);
  font-weight: 500;
}

.hero-title {
  margin-bottom: 20px;
}

.title-gradient {
  font-size: 48px;
  font-weight: 700;
  background: linear-gradient(135deg, #007AFF, #5856D6, #FF6B9D);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient-shift 4s ease infinite;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.title-sub {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
  opacity: 0.9;
}

.hero-desc {
  font-size: var(--font-size-body);
  color: var(--text-secondary);
  line-height: 1.6;
}

.hero-visual {
  position: relative;
  z-index: 1;
}

.air-orb {
  position: relative;
  width: 200px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.orb-ring {
  position: absolute;
  border-radius: 50%;
  border: 2px solid;
  animation: orb-float 6s ease-in-out infinite;
}

@keyframes orb-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.orb-ring-1 {
  width: 200px;
  height: 200px;
  border-color: rgba(0, 122, 255, 0.15);
  animation-delay: 0s;
}

.orb-ring-2 {
  width: 160px;
  height: 160px;
  border-color: rgba(88, 86, 214, 0.15);
  animation-delay: -2s;
}

.orb-ring-3 {
  width: 120px;
  height: 120px;
  border-color: rgba(255, 107, 157, 0.15);
  animation-delay: -4s;
}

.orb-core {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  border-radius: 50%;
  box-shadow: 0 0 40px rgba(0, 122, 255, 0.3);
}

.orb-value {
  font-size: 36px;
  font-weight: 700;
  color: white;
  line-height: 1;
}

.orb-label {
  font-size: var(--font-size-caption);
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

@media (max-width: 1200px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
    padding: 40px 24px;
  }

  .title-gradient {
    font-size: 36px;
  }

  .title-sub {
    font-size: 24px;
  }
}
</style>
