<template>
  <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
    <div class="flex flex-col space-y-2">
      <h4 class="font-medium text-gray-900 dark:text-white text-sm">{{ title }}</h4>
      <code class="text-xs text-gray-600 dark:text-gray-400 bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded">
        {{ endpoint }}
      </code>

      <ActionButton
        @click="$emit('test')"
        :loading="loading"
        :disabled="disabled"
        :icon="getStatusIcon()"
        :text="getButtonText()"
        :variant="getButtonVariant()"
        size="sm"
        class="w-full"
      />

      <!-- 結果顯示 -->
      <div v-if="result" class="mt-2 text-xs">
        <div :class="[
          'p-2 rounded',
          result.success ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
          'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
        ]">
          <div class="font-semibold mb-1">
            {{ result.success ? '✅ 成功' : '❌ 失敗' }}
          </div>
          <div v-if="result.success && result.data" class="text-xs opacity-75">
            <pre v-if="typeof result.data === 'object'" class="whitespace-pre-wrap">{{ JSON.stringify(getDisplayData(result.data), null, 2) }}</pre>
            <span v-else>{{ result.data }}</span>
          </div>
          <div v-if="!result.success && result.error" class="text-xs opacity-75">
            {{ result.error }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  PlayIcon,
  CheckIcon,
  XMarkIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'

// Props
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  endpoint: {
    type: String,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  result: {
    type: Object,
    default: null
  }
})

// Emits
defineEmits(['test'])

// 計算屬性
const getStatusIcon = () => {
  if (props.loading) return ClockIcon
  if (props.result?.success === true) return CheckIcon
  if (props.result?.success === false) return XMarkIcon
  return PlayIcon
}

const getButtonText = () => {
  if (props.loading) return '測試中...'
  if (props.result?.success === true) return '重新測試'
  if (props.result?.success === false) return '重試'
  return '測試'
}

const getButtonVariant = () => {
  if (props.result?.success === true) return 'success'
  if (props.result?.success === false) return 'error'
  return 'primary'
}

// 格式化顯示資料（限制大小）
const getDisplayData = (data) => {
  if (!data) return data

  // 如果是物件或陣列，只顯示前幾個項目
  if (Array.isArray(data)) {
    return data.length > 3 ? [...data.slice(0, 3), `... (${data.length} 項目)`] : data
  }

  if (typeof data === 'object') {
    const keys = Object.keys(data)
    if (keys.length > 5) {
      const limitedData = {}
      keys.slice(0, 5).forEach(key => {
        limitedData[key] = data[key]
      })
      limitedData[`... (${keys.length} 欄位)`] = '...'
      return limitedData
    }
  }

  return data
}
</script>