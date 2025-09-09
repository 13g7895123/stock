<template>
  <div class="relative">
    <button
      @click="toggleItem"
      class="w-full flex items-center px-3 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200 group"
      :class="{ 'justify-center': collapsed }"
    >
      <!-- Icon -->
      <component 
        :is="getIcon(item.icon)" 
        class="w-5 h-5 text-gray-500 group-hover:text-primary-500 transition-colors duration-200" 
      />
      
      <!-- Text and Arrow (desktop) -->
      <div v-if="!collapsed" class="flex items-center justify-between flex-1 ml-3">
        <span class="font-medium">{{ item.name }}</span>
        <ChevronDownIcon 
          v-if="item.children"
          class="w-4 h-4 transition-transform duration-200"
          :class="{ 'rotate-180': isExpanded }"
        />
      </div>
    </button>

    <!-- Tooltip for collapsed state -->
    <div
      v-if="collapsed"
      class="absolute left-full top-0 ml-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50 whitespace-nowrap"
    >
      {{ item.name }}
    </div>

    <!-- Submenu -->
    <transition
      enter-active-class="transition-all duration-200 ease-out"
      enter-from-class="opacity-0 max-h-0"
      enter-to-class="opacity-100 max-h-96"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 max-h-96"
      leave-to-class="opacity-0 max-h-0"
    >
      <div v-if="isExpanded && !collapsed && item.children" class="ml-8 mt-2 space-y-1 overflow-hidden">
        <NuxtLink
          v-for="child in item.children"
          :key="child.name"
          :to="child.href"
          class="block px-3 py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-primary-500 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-all duration-200"
        >
          {{ child.name }}
        </NuxtLink>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { 
  ChartBarIcon,
  CogIcon,
  QuestionMarkCircleIcon,
  ChevronDownIcon 
} from '@heroicons/vue/24/outline'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const isExpanded = ref(false)

const toggleItem = () => {
  if (props.item.children && !props.collapsed) {
    isExpanded.value = !isExpanded.value
  } else if (props.item.children && props.collapsed) {
    // For collapsed state, we could show a popover menu here in the future
  }
}

const iconComponents = {
  ChartBarIcon,
  CogIcon,
  QuestionMarkCircleIcon
}

const getIcon = (iconName) => {
  return iconComponents[iconName] || ChartBarIcon
}
</script>