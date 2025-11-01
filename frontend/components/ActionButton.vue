<template>
  <button
    @click="handleClick"
    :disabled="loading || disabled"
    :class="[
      'px-4 py-2 rounded-lg transition-colors flex items-center',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      buttonClasses
    ]"
  >
    <component
      :is="icon"
      :class="['w-4 h-4', loading ? 'animate-spin' : '']"
      v-if="icon"
    />
    <!-- 支持 slot 或 text prop -->
    <slot v-if="!loading && $slots.default"></slot>
    <span v-else-if="!loading && text">{{ text }}</span>
    <span v-else>{{ loadingText }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'

// defineProps 和 defineEmits 是編譯器宏，不需要import

const props = defineProps({
  // 按鈕文字（可選，如果使用 slot 則不需要）
  text: {
    type: String,
    default: ''
  },
  // 載入中顯示的文字
  loadingText: {
    type: String,
    default: '載入中...'
  },
  // 按鈕圖示 (Heroicon 組件)
  icon: {
    type: [Object, String, Function],
    default: null
  },
  // 按鈕樣式類型
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'success', 'warning', 'danger', 'info', 'gray'].includes(value)
  },
  // 按鈕大小
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  // 載入狀態
  loading: {
    type: Boolean,
    default: false
  },
  // 禁用狀態
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const handleClick = () => {
  if (!props.loading && !props.disabled) {
    emit('click')
  }
}

// 計算按鈕樣式類別
const buttonClasses = computed(() => {
  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700',
    success: 'bg-green-600 text-white hover:bg-green-700',
    warning: 'bg-yellow-600 text-white hover:bg-yellow-700',
    danger: 'bg-red-600 text-white hover:bg-red-700',
    info: 'bg-blue-600 text-white hover:bg-blue-700',
    gray: 'bg-gray-500 text-white hover:bg-gray-600'
  }
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  }
  
  return `${variantClasses[props.variant]} ${sizeClasses[props.size]}`
})
</script>