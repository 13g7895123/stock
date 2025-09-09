<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200 dark:border-gray-700">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {{ title }}
          </h3>
          <p v-if="subtitle" class="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {{ subtitle }}
          </p>
        </div>
        
        <!-- Search and Actions -->
        <div class="flex items-center gap-3">
          <!-- Search -->
          <div class="relative">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="t('common.search') + '...'"
              class="pl-10 pr-4 py-2 w-64 sm:w-48 lg:w-64 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
            />
          </div>
          
          <!-- Refresh Button -->
          <button
            @click="handleRefresh"
            :disabled="loading"
            class="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200 disabled:opacity-50"
          >
            <ArrowPathIcon class="h-5 w-5" :class="{ 'animate-spin': loading }" />
          </button>
          
          <!-- Additional Actions -->
          <div v-if="$slots.actions" class="flex items-center gap-2">
            <slot name="actions" />
          </div>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-700/50">
          <tr>
            <!-- Actions Column -->
            <th v-if="showActions" class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-16">
              {{ t('datatable.actions') }}
            </th>
            
            <!-- Dynamic Columns -->
            <th
              v-for="column in columns"
              :key="column.key"
              class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
              :class="column.headerClass"
            >
              <div class="flex items-center gap-2">
                {{ column.title }}
                <button
                  v-if="column.sortable"
                  @click="handleSort(column.key)"
                  class="hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                >
                  <ChevronUpDownIcon class="h-4 w-4" />
                </button>
              </div>
            </th>
          </tr>
        </thead>
        
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          <tr
            v-for="(item, index) in paginatedData"
            :key="getRowKey(item, index)"
            class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors duration-200"
          >
            <!-- Actions Column -->
            <td v-if="showActions" class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center space-x-2">
                <button
                  v-if="actions.includes('view')"
                  @click="handleAction('view', item)"
                  class="p-1.5 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition-colors duration-200"
                  :title="t('datatable.view')"
                >
                  <EyeIcon class="h-4 w-4" />
                </button>
                
                <button
                  v-if="actions.includes('edit')"
                  @click="handleAction('edit', item)"
                  class="p-1.5 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 rounded-lg transition-colors duration-200"
                  :title="t('datatable.edit')"
                >
                  <PencilIcon class="h-4 w-4" />
                </button>
                
                <button
                  v-if="actions.includes('delete')"
                  @click="handleAction('delete', item)"
                  class="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors duration-200"
                  :title="t('datatable.delete')"
                >
                  <TrashIcon class="h-4 w-4" />
                </button>
                
                <button
                  v-if="actions.includes('more')"
                  @click="handleAction('more', item)"
                  class="p-1.5 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200"
                  :title="t('datatable.more')"
                >
                  <EllipsisHorizontalIcon class="h-4 w-4" />
                </button>
              </div>
            </td>
            
            <!-- Dynamic Columns -->
            <td
              v-for="column in columns"
              :key="column.key"
              class="px-6 py-4 whitespace-nowrap"
              :class="column.cellClass"
            >
              <div v-if="column.component">
                <component
                  :is="column.component"
                  :data="item"
                  :value="getNestedValue(item, column.key)"
                />
              </div>
              <div v-else-if="column.formatter">
                {{ column.formatter(getNestedValue(item, column.key), item) }}
              </div>
              <div v-else class="text-sm text-gray-900 dark:text-white">
                {{ getNestedValue(item, column.key) }}
              </div>
            </td>
          </tr>
          
          <!-- Empty State -->
          <tr v-if="paginatedData.length === 0">
            <td :colspan="columns.length + (showActions ? 1 : 0)" class="px-6 py-12 text-center">
              <div class="flex flex-col items-center justify-center">
                <DocumentTextIcon class="h-12 w-12 text-gray-300 dark:text-gray-600 mb-3" />
                <p class="text-gray-500 dark:text-gray-400 text-sm">
                  {{ loading ? t('common.loading') : t('datatable.no_data') }}
                </p>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Footer with Pagination -->
    <div v-if="showPagination && paginatedData.length > 0" class="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <!-- Results Info -->
        <div class="text-sm text-gray-700 dark:text-gray-300">
          {{ t('datatable.showing') }} 
          <span class="font-medium">{{ (currentPage - 1) * pageSize + 1 }}</span> 
          {{ t('datatable.to') }} 
          <span class="font-medium">{{ Math.min(currentPage * pageSize, filteredData.length) }}</span> 
          {{ t('datatable.of') }} 
          <span class="font-medium">{{ filteredData.length }}</span> 
          {{ t('datatable.results') }}
        </div>
        
        <!-- Pagination -->
        <nav class="flex items-center gap-2">
          <!-- Previous -->
          <button
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage === 1"
            class="px-3 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {{ t('datatable.previous') }}
          </button>
          
          <!-- Page Numbers -->
          <button
            v-for="page in visiblePages"
            :key="page"
            @click="goToPage(page)"
            class="px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200"
            :class="page === currentPage 
              ? 'text-white bg-primary-500 hover:bg-primary-600' 
              : 'text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'"
          >
            {{ page }}
          </button>
          
          <!-- Next -->
          <button
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="px-3 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {{ t('datatable.next') }}
          </button>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  MagnifyingGlassIcon,
  ArrowPathIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  EllipsisHorizontalIcon,
  ChevronUpDownIcon,
  DocumentTextIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  data: {
    type: Array,
    default: () => []
  },
  columns: {
    type: Array,
    required: true
  },
  actions: {
    type: Array,
    default: () => ['view', 'edit', 'delete']
  },
  showActions: {
    type: Boolean,
    default: true
  },
  showPagination: {
    type: Boolean,
    default: true
  },
  pageSize: {
    type: Number,
    default: 10
  },
  loading: {
    type: Boolean,
    default: false
  },
  rowKey: {
    type: String,
    default: 'id'
  }
})

const emit = defineEmits(['action', 'refresh', 'sort'])

const { t } = useI18n()
const searchQuery = ref('')
const currentPage = ref(1)
const sortKey = ref('')
const sortOrder = ref('asc')

// Computed properties
const filteredData = computed(() => {
  if (!searchQuery.value) return props.data

  const query = searchQuery.value.toLowerCase()
  return props.data.filter(item => {
    return props.columns.some(column => {
      const value = getNestedValue(item, column.key)
      return String(value).toLowerCase().includes(query)
    })
  })
})

const sortedData = computed(() => {
  if (!sortKey.value) return filteredData.value

  return [...filteredData.value].sort((a, b) => {
    const aVal = getNestedValue(a, sortKey.value)
    const bVal = getNestedValue(b, sortKey.value)
    
    let comparison = 0
    if (aVal > bVal) comparison = 1
    if (aVal < bVal) comparison = -1
    
    return sortOrder.value === 'desc' ? -comparison : comparison
  })
})

const paginatedData = computed(() => {
  if (!props.showPagination) return sortedData.value
  
  const start = (currentPage.value - 1) * props.pageSize
  const end = start + props.pageSize
  return sortedData.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredData.value.length / props.pageSize)
})

const visiblePages = computed(() => {
  const pages = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// Methods
const getNestedValue = (obj, path) => {
  return path.split('.').reduce((current, prop) => current?.[prop], obj) ?? ''
}

const getRowKey = (item, index) => {
  return props.rowKey ? getNestedValue(item, props.rowKey) : index
}

const handleAction = (action, item) => {
  emit('action', { action, item })
}

const handleRefresh = () => {
  emit('refresh')
}

const handleSort = (key) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
  
  emit('sort', { key: sortKey.value, order: sortOrder.value })
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// Watch for data changes to reset pagination
watch(() => props.data, () => {
  currentPage.value = 1
})

watch(searchQuery, () => {
  currentPage.value = 1
})
</script>