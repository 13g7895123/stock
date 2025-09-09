<template>
  <div class="space-y-6">
    <!-- Welcome Section -->
    <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        歡迎回來！
      </h2>
      <p class="text-gray-600 dark:text-gray-300">
        這是一個現代化的後台管理系統模板，具有響應式設計和暗色模式支持。
      </p>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <div
        v-for="stat in stats"
        :key="stat.name"
        class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6"
      >
        <div class="flex items-center">
          <div class="p-3 rounded-lg bg-primary-100 dark:bg-primary-900">
            <component :is="getIcon(stat.icon)" class="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div class="ml-4">
            <p class="text-sm font-medium text-gray-600 dark:text-gray-400">{{ stat.name }}</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stat.value }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Chart Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          數據趨勢
        </h3>
        <div class="h-64 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
          <p class="text-gray-500 dark:text-gray-400">圖表區域 (可整合圖表庫)</p>
        </div>
      </div>

      <!-- Activity Feed -->
      <div class="bg-white dark:bg-gray-800 rounded-lg-custom shadow-sm p-6">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          最新活動
        </h3>
        <div class="space-y-4">
          <div
            v-for="activity in activities"
            :key="activity.id"
            class="flex items-start space-x-3"
          >
            <div class="w-2 h-2 mt-2 bg-primary-500 rounded-full"></div>
            <div class="flex-1">
              <p class="text-sm text-gray-900 dark:text-white">{{ activity.description }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ activity.time }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  UsersIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'

const stats = [
  { name: '總用戶數', value: '1,234', icon: 'UsersIcon' },
  { name: '總收入', value: '$12,345', icon: 'CurrencyDollarIcon' },
  { name: '轉換率', value: '12.5%', icon: 'ChartBarIcon' },
  { name: '平均時間', value: '2.4m', icon: 'ClockIcon' }
]

const activities = [
  { id: 1, description: '新用戶註冊', time: '2分鐘前' },
  { id: 2, description: '系統備份完成', time: '15分鐘前' },
  { id: 3, description: '收到新訂單', time: '1小時前' },
  { id: 4, description: '服務器維護完成', time: '2小時前' }
]

const iconComponents = {
  UsersIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ClockIcon
}

const getIcon = (iconName) => {
  return iconComponents[iconName] || ChartBarIcon
}
</script>