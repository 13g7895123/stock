<template>
  <div>
    <!-- Desktop Sidebar -->
    <aside
      class="fixed top-0 left-0 h-full bg-white dark:bg-gray-800 shadow-lg transition-all duration-300 z-40 hidden lg:flex flex-col"
      :class="[
        sidebarCollapsed ? 'w-20' : 'w-70'
      ]"
    >
      <!-- Logo/Brand -->
      <div class="h-16 flex items-center justify-center border-b border-gray-200 dark:border-gray-700">
        <div v-if="!sidebarCollapsed" class="text-xl font-bold text-gray-800 dark:text-white">
          股票分析系統
        </div>
        <div v-else class="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
          <span class="text-white font-bold text-sm">股</span>
        </div>
      </div>

      <!-- Navigation Menu -->
      <nav class="flex-1 px-4 py-6 space-y-2">
        <SidebarMenuItem
          v-for="item in menuItems"
          :key="item.name"
          :item="item"
          :collapsed="sidebarCollapsed"
        />
      </nav>

      <!-- Logout Button -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          class="w-full flex items-center px-3 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200"
          :class="{ 'justify-center': sidebarCollapsed }"
        >
          <ArrowRightOnRectangleIcon class="w-5 h-5" />
          <span v-if="!sidebarCollapsed" class="ml-3">登出</span>
        </button>
      </div>

      <!-- Collapse Toggle -->
      <button
        @click="toggleSidebar"
        class="absolute -right-3 top-6 w-6 h-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
      >
        <ChevronLeftIcon 
          class="w-4 h-4 text-gray-500 transition-transform duration-200"
          :class="{ 'rotate-180': sidebarCollapsed }"
        />
      </button>
    </aside>

    <!-- Mobile Sidebar Overlay -->
    <div
      v-if="sidebarMobileOpen"
      class="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
      @click="closeMobileSidebar"
    />

    <!-- Mobile Sidebar -->
    <aside
      class="fixed top-0 left-0 h-full w-70 bg-white dark:bg-gray-800 shadow-lg transition-transform duration-300 z-50 lg:hidden flex flex-col"
      :class="[
        sidebarMobileOpen ? 'translate-x-0' : '-translate-x-full'
      ]"
    >
      <!-- Logo/Brand -->
      <div class="h-16 flex items-center justify-between px-4 border-b border-gray-200 dark:border-gray-700">
        <div class="text-xl font-bold text-gray-800 dark:text-white">
          股票分析系統
        </div>
        <button
          @click="closeMobileSidebar"
          class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
        >
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Navigation Menu -->
      <nav class="flex-1 px-4 py-6 space-y-2">
        <SidebarMenuItem
          v-for="item in menuItems"
          :key="item.name"
          :item="item"
          :collapsed="false"
          @click="closeMobileSidebar"
        />
      </nav>

      <!-- Logout Button -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          class="w-full flex items-center px-3 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200"
          @click="closeMobileSidebar"
        >
          <ArrowRightOnRectangleIcon class="w-5 h-5" />
          <span class="ml-3">登出</span>
        </button>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { 
  ChevronLeftIcon,
  XMarkIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/vue/24/outline'

const sidebarStore = useSidebarStore()
const { sidebarCollapsed, sidebarMobileOpen } = storeToRefs(sidebarStore)
const { toggleSidebar, closeMobileSidebar } = sidebarStore

const settingsStore = useSettingsStore()
const { sidebarMenuItems } = storeToRefs(settingsStore)

const menuItems = computed(() => sidebarMenuItems.value)
</script>

<style scoped>
.w-70 {
  width: 280px;
}
</style>