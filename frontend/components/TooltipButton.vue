<template>
  <div class="relative inline-block">
    <button 
      @mouseenter="showTooltip = true"
      @mouseleave="showTooltip = false"
      :class="buttonClass"
      v-bind="$attrs"
    >
      <slot />
      <component 
        :is="tooltipIcon" 
        class="w-4 h-4 ml-1 opacity-60 hover:opacity-100 transition-opacity"
        v-if="tooltipIcon"
      />
    </button>
    
    <!-- 工具提示 -->
    <div
      v-if="showTooltip && tooltip"
      class="absolute z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg max-w-xs"
      :class="tooltipPosition"
    >
      <div class="relative">
        {{ tooltip }}
        <!-- 箭頭 -->
        <div 
          class="absolute w-2 h-2 bg-gray-900 rotate-45"
          :class="arrowPosition"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { QuestionMarkCircleIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  // 工具提示文字
  tooltip: {
    type: String,
    required: true
  },
  // 工具提示位置
  position: {
    type: String,
    default: 'top',
    validator: (value) => ['top', 'bottom', 'left', 'right'].includes(value)
  },
  // 工具提示圖示
  tooltipIcon: {
    type: [Object, String, Function],
    default: () => QuestionMarkCircleIcon
  },
  // 按鈕樣式類別
  buttonClass: {
    type: String,
    default: 'inline-flex items-center'
  }
})

const showTooltip = ref(false)

// 計算工具提示位置類別
const tooltipPosition = computed(() => {
  switch (props.position) {
    case 'top':
      return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2'
    case 'bottom':
      return 'top-full left-1/2 transform -translate-x-1/2 mt-2'
    case 'left':
      return 'right-full top-1/2 transform -translate-y-1/2 mr-2'
    case 'right':
      return 'left-full top-1/2 transform -translate-y-1/2 ml-2'
    default:
      return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2'
  }
})

// 計算箭頭位置類別
const arrowPosition = computed(() => {
  switch (props.position) {
    case 'top':
      return 'top-full left-1/2 transform -translate-x-1/2 -mt-1'
    case 'bottom':
      return 'bottom-full left-1/2 transform -translate-x-1/2 -mb-1'
    case 'left':
      return 'left-full top-1/2 transform -translate-y-1/2 -ml-1'
    case 'right':
      return 'right-full top-1/2 transform -translate-y-1/2 -mr-1'
    default:
      return 'top-full left-1/2 transform -translate-x-1/2 -mt-1'
  }
})
</script>