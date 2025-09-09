<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <AppSidebar />
    <div 
      class="min-h-screen flex flex-col main-content-area"
      :class="{
        'sidebar-collapsed': sidebarCollapsed
      }"
    >
      <AppNavbar />
      <main class="flex-1 p-6 overflow-auto">
        <slot />
      </main>
      <AppFootbar v-if="showFootbar" />
    </div>
  </div>
</template>

<script setup>
const sidebarStore = useSidebarStore()
const { sidebarCollapsed } = storeToRefs(sidebarStore)

// Add footbar state from settings
const settingsStore = useSettingsStore()
const { showFootbar } = storeToRefs(settingsStore)
</script>