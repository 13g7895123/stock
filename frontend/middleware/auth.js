export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()
  
  // 初始化認證狀態
  authStore.initializeAuth()
  
  // 如果未登入，重定向到登入頁面
  if (!authStore.isLoggedIn) {
    return navigateTo('/auth/login')
  }
})