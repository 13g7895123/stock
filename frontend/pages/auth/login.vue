<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- Logo & Title -->
      <div class="text-center">
        <h2 class="mt-6 text-3xl font-bold text-gray-900 dark:text-white">
          {{ t('auth.login_title') }}
        </h2>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
          {{ t('auth.login_subtitle') }}
        </p>
      </div>

      <!-- Login Form -->
      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <div class="space-y-4">
          <!-- Username/Email -->
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.username_email') }}
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              required
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              :placeholder="t('auth.username_email_placeholder')"
            />
          </div>

          <!-- Password -->
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.password') }}
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              required
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              :placeholder="t('auth.password_placeholder')"
            />
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p class="text-sm text-red-700 dark:text-red-400">{{ error }}</p>
        </div>

        <!-- Demo Accounts Info -->
        <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 class="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">{{ t('auth.demo_accounts') }}</h4>
          <div class="space-y-1 text-xs text-blue-700 dark:text-blue-400">
            <p><strong>{{ t('auth.admin_account') }}:</strong> admin / admin123</p>
            <p><strong>{{ t('auth.user_account') }}:</strong> user1 / user123</p>
          </div>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
        >
          <span v-if="!loading">{{ t('auth.login') }}</span>
          <span v-else class="flex items-center">
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ t('auth.logging_in') }}
          </span>
        </button>

        <!-- Register Link -->
        <div class="text-center">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ t('auth.no_account') }}
            <NuxtLink to="/auth/register" class="font-medium text-primary-500 hover:text-primary-600 transition-colors duration-200">
              {{ t('auth.register') }}
            </NuxtLink>
          </p>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
  middleware: 'guest'
})

const { t } = useI18n()
const authStore = useAuthStore()

const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  try {
    loading.value = true
    error.value = ''
    
    await authStore.login(form.value)
    
    // 重定向到首頁
    await navigateTo('/')
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// 如果已經登入，重定向到首頁
onMounted(() => {
  if (authStore.isLoggedIn) {
    navigateTo('/')
  }
})
</script>