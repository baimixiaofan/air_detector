<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
// 💡 引入仓库，实现名字联动修改
import { useUserStore } from '../store/user'

const userStore = useUserStore()

// 1. 个人资料表单
const profileForm = reactive({
  nickname: userStore.username, // 默认显示仓库里的名字
  email: 'admin@green-shield.com',
  role: '厂商超级管理员',
  avatar: 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
})

// 2. 系统通知设置
const configForm = reactive({
  emailNotify: true,
  smsNotify: false,
  autoReport: true,
  theme: '清新绿',
})

// 保存个人资料
const handleSaveProfile = () => {
  // 💡 同步修改 Pinia 仓库里的名字，这样右上角会立刻跟着变！
  userStore.username = profileForm.nickname
  localStorage.setItem('username', profileForm.nickname) // 别忘了备份到缓存

  ElMessage.success('个人资料已更新！')
}

// 修改密码（模拟弹窗）
const handleChangePass = () => {
  ElMessage.warning('重置密码链接已发送至您的绑定邮箱，请查收。')
}
</script>

<template>
  <div class="settings-container">
    <el-tabs type="border-card">
      <el-tab-pane label="👤 个人资料">
        <div class="profile-section">
          <div class="avatar-box">
            <el-avatar :size="100" :src="profileForm.avatar" />
            <el-button size="small" style="margin-top: 10px">更换头像</el-button>
          </div>

          <el-form :model="profileForm" label-width="100px" style="max-width: 500px; flex: 1">
            <el-form-item label="登录账号">
              <el-input v-model="profileForm.nickname" placeholder="请输入昵称" />
            </el-form-item>
            <el-form-item label="电子邮箱">
              <el-input v-model="profileForm.email" />
            </el-form-item>
            <el-form-item label="当前角色">
              <el-tag type="success">{{ profileForm.role }}</el-tag>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSaveProfile">保存修改</el-button>
              <el-button type="danger" plain @click="handleChangePass">修改登录密码</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="⚙️ 系统配置">
        <el-form :model="configForm" label-width="150px" style="padding: 20px 0">
          <el-form-item label="邮件通知">
            <el-switch v-model="configForm.emailNotify" active-text="当设备告警时发送邮件" />
          </el-form-item>
          <el-form-item label="短信预警">
            <el-switch v-model="configForm.smsNotify" active-text="开启重要告警短信实时推送" />
          </el-form-item>
          <el-form-item label="自动生成报表">
            <el-switch v-model="configForm.autoReport" active-text="每日凌晨自动汇总前日数据" />
          </el-form-item>
          <el-form-item label="系统主题配色">
            <el-radio-group v-model="configForm.theme">
              <el-radio label="清新绿">清新绿</el-radio>
              <el-radio label="科技蓝">科技蓝</el-radio>
              <el-radio label="深邃黑">深邃黑</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="ElMessage.success('系统配置已保存')"
              >应用配置</el-button
            >
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.settings-container {
  padding-bottom: 20px;
}
.profile-section {
  display: flex;
  gap: 50px;
  padding: 30px;
  align-items: flex-start;
}
.avatar-box {
  display: flex;
  flex-direction: column;
  align-items: center;
}
/* 调整选项卡的高度，让它看起来更饱满 */
:deep(.el-tabs__content) {
  min-height: 400px;
}
</style>
