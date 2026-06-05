import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  // 💡 新增 server 配置：设置跨域代理
  server: {
    proxy: {
      // 只要你请求的路径是以 /api 开头的，Vite 就会帮你拦截并转发给后端
      '/api': {
        target: 'https://baimeixiaofan.xyz', // ⚠️ 这里替换成你队友后端的真实本地 IP 或网址
        changeOrigin: true, // 允许跨域
        rewrite: (path) => path.replace(/^\/api/, ''), // 如果后端接口没有 /api 前缀，就把它砍掉
      },
    },
  },
})
