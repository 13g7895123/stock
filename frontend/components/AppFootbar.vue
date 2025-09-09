<template>
  <footer class="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3">
    <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
      <!-- Left side - Version -->
      <div class="flex items-center space-x-4">
        <span>{{ t('common.version') }} 1.0.0</span>
      </div>
      
      <!-- Center - Copyright -->
      <div class="flex items-center">
        <span>{{ t('footer.copyright') }}</span>
      </div>
      
      <!-- Right side - Links -->
      <div class="flex items-center space-x-4">
        <a 
          href="#" 
          class="hover:text-primary-500 transition-colors duration-200"
          @click.prevent="$emit('privacy')"
        >
          {{ t('footer.privacy_policy') }}
        </a>
        <span class="w-px h-4 bg-gray-300 dark:bg-gray-600"></span>
        <a 
          href="#" 
          class="hover:text-primary-500 transition-colors duration-200"
          @click.prevent="$emit('terms')"
        >
          {{ t('footer.terms_of_service') }}
        </a>
      </div>
    </div>
  </footer>
</template>

<script setup>
const { t } = useI18n()
defineEmits(['privacy', 'terms'])
</script>