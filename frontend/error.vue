<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
    <div class="max-w-md w-full text-center">
      <!-- Error Icon -->
      <div class="mb-8">
        <div class="mx-auto flex items-center justify-center h-24 w-24 rounded-full bg-red-100 dark:bg-red-900/30">
          <ExclamationTriangleIcon class="h-12 w-12 text-red-600 dark:text-red-400" />
        </div>
      </div>

      <!-- Error Code -->
      <h1 class="text-6xl font-bold text-gray-900 dark:text-white mb-4">
        {{ error.statusCode }}
      </h1>

      <!-- Error Message -->
      <h2 class="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-6">
        {{ getErrorTitle() }}
      </h2>

      <p class="text-gray-600 dark:text-gray-400 mb-8">
        {{ getErrorMessage() }}
      </p>

      <!-- Action Buttons -->
      <div class="space-y-4">
        <button
          @click="handleError"
          class="w-full bg-primary-500 hover:bg-primary-600 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200"
        >
          {{ t('error.back_home') }}
        </button>
        
        <button
          @click="refresh"
          class="w-full border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium py-3 px-6 rounded-lg transition-colors duration-200"
        >
          {{ t('error.refresh_page') }}
        </button>
      </div>

      <!-- Additional Info -->
      <div class="mt-8 text-sm text-gray-500 dark:text-gray-400">
        {{ t('error.error_id') }}: {{ generateErrorId() }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

const props = defineProps(['error'])
const { t } = useI18n()

const getErrorTitle = () => {
  switch (props.error?.statusCode) {
    case 404:
      return t('error.page_not_found')
    case 500:
      return t('error.internal_server_error')
    case 403:
      return t('error.access_forbidden')
    default:
      return t('error.something_went_wrong')
  }
}

const getErrorMessage = () => {
  switch (props.error?.statusCode) {
    case 404:
      return t('error.page_not_found_message')
    case 500:
      return t('error.internal_server_error_message')
    case 403:
      return t('error.access_forbidden_message')
    default:
      return t('error.generic_error_message')
  }
}

const generateErrorId = () => {
  return Math.random().toString(36).substring(2, 15)
}

const handleError = async () => {
  await clearError({ redirect: '/' })
}

const refresh = () => {
  window.location.reload()
}

// Set page meta
useHead({
  title: `${props.error?.statusCode} - ${getErrorTitle()}`,
})
</script>