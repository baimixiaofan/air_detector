import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 1. 当前登录人的状态
  const username = ref(localStorage.getItem('username') || '')
  const token = ref(localStorage.getItem('token') || '')
  const role = ref(localStorage.getItem('role') || '')

  // 💡 2. 全站用户名单 (如果缓存里没有，就用默认的三个测试账号)
  const defaultUsers = [
    {
      id: 101,
      username: 'admin',
      password: '123456',
      nickname: '超级管理员',
      role: 'admin',
      status: true,
      loginTime: '2026-05-28 10:00',
    },
    {
      id: 102,
      username: 'test',
      password: '123456',
      nickname: '测试操作员',
      role: 'operator',
      status: true,
      loginTime: '2026-05-27 15:30',
    },
    {
      id: 103,
      username: 'lisi',
      password: '123456',
      nickname: '李分析',
      role: 'operator',
      status: false,
      loginTime: '2026-05-20 09:12',
    },
  ]
  const userList = ref(JSON.parse(localStorage.getItem('userList')) || defaultUsers)

  // 💡 3. 监听魔法：只要 userList 发生改变，就立刻自动覆盖保存到本地缓存！
  watch(
    userList,
    (newList) => {
      localStorage.setItem('userList', JSON.stringify(newList))
    },
    { deep: true },
  ) // deep: true 表示深度监听数组内部对象的变化

  // 4. 登录动作 (接收传入的角色)
  const login = (newToken, newUsername, newRole) => {
    token.value = newToken
    username.value = newUsername
    role.value = newRole // 登录时存入真实的身份

    localStorage.setItem('token', newToken)
    localStorage.setItem('username', newUsername)
    localStorage.setItem('role', newRole)
  }

  const logout = () => {
    token.value = ''
    username.value = ''
    role.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }

  return {
    username,
    token,
    role,
    userList, // 把花名册暴露出去
    login,
    logout,
  }
})
