<template>
  <div class="space-y-6">
    <!-- Access Denied for Non-Admin -->
    <div v-if="!authStore.isAdmin" class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-12 text-center">
      <ShieldExclamationIcon class="w-12 h-12 text-red-500 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">{{ t('auth.access_denied') }}</h3>
      <p class="text-gray-600 dark:text-gray-400">{{ t('auth.admin_only_feature') }}</p>
    </div>

    <!-- DataTable Implementation -->
    <DataTable
      v-else
      :title="t('nav.user_management')"
      :subtitle="t('datatable.user_management_subtitle')"
      :data="users"
      :columns="userColumns"
      :actions="['view', 'edit', 'delete']"
      :loading="loading"
      :show-actions="true"
      :show-pagination="true"
      :page-size="10"
      row-key="id"
      @action="handleUserAction"
      @refresh="refreshUsers"
      @sort="handleSort"
    >
      <template #actions>
        <button
          @click="showAddUserDialog = true"
          class="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white font-medium rounded-lg transition-colors duration-200 flex items-center gap-2"
        >
          <UserPlusIcon class="h-4 w-4" />
          {{ t('datatable.add_user') }}
        </button>
      </template>
    </DataTable>

    <!-- Edit User Modal -->
    <div v-if="showEditModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
          {{ t('auth.edit_user') }}
        </h3>
        
        <div class="space-y-4">
          <!-- Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.full_name') }}
            </label>
            <input
              v-model="editForm.name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <!-- Email -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.email') }}
            </label>
            <input
              v-model="editForm.email"
              type="email"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>

          <!-- Role -->
          <div v-if="editForm.id !== authStore.user?.id">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.role') }}
            </label>
            <select
              v-model="editForm.role"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            >
              <option value="user">{{ t('auth.role_user') }}</option>
              <option value="admin">{{ t('auth.role_admin') }}</option>
            </select>
          </div>
        </div>

        <!-- Modal Actions -->
        <div class="flex justify-end space-x-3 mt-6">
          <button
            @click="showEditModal = false"
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            @click="saveUser"
            class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors duration-200"
          >
            {{ t('common.save') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Add User Dialog -->
    <div v-if="showAddUserDialog" class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
          {{ t('datatable.add_user') }}
        </h3>
        
        <div class="space-y-4">
          <!-- Username -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.username') }}
            </label>
            <input
              v-model="addForm.username"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <!-- Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.full_name') }}
            </label>
            <input
              v-model="addForm.name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <!-- Email -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.email') }}
            </label>
            <input
              v-model="addForm.email"
              type="email"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>

          <!-- Role -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ t('auth.role') }}
            </label>
            <select
              v-model="addForm.role"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            >
              <option value="user">{{ t('auth.role_user') }}</option>
              <option value="admin">{{ t('auth.role_admin') }}</option>
            </select>
          </div>
        </div>

        <!-- Modal Actions -->
        <div class="flex justify-end space-x-3 mt-6">
          <button
            @click="cancelAddUser"
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            @click="addUser"
            class="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors duration-200"
          >
            {{ t('common.add') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ShieldExclamationIcon,
  UserPlusIcon
} from '@heroicons/vue/24/outline'

definePageMeta({
  middleware: 'auth'
})

const { t } = useI18n()
const authStore = useAuthStore()

const loading = ref(false)
const showEditModal = ref(false)
const showAddUserDialog = ref(false)
const editForm = ref({})
const addForm = ref({
  username: '',
  name: '',
  email: '',
  role: 'user'
})

// Get all users (only for admins)
const users = computed(() => {
  try {
    return authStore.isAdmin ? authStore.getAllUsers() : []
  } catch {
    return []
  }
})

// Define table columns for DataTable
const userColumns = [
  {
    key: 'name',
    title: t('auth.user'),
    sortable: true,
    component: markRaw(defineComponent({
      props: ['data', 'value'],
      template: `
        <div class="flex items-center">
          <img :src="data.avatar" :alt="data.name" class="w-10 h-10 rounded-full" />
          <div class="ml-4">
            <div class="text-sm font-medium text-gray-900 dark:text-white">{{ data.name }}</div>
            <div class="text-sm text-gray-500 dark:text-gray-400">{{ data.email }}</div>
          </div>
        </div>
      `
    }))
  },
  {
    key: 'role',
    title: t('auth.role'),
    sortable: true,
    component: markRaw(defineComponent({
      props: ['data', 'value'],
      setup(props) {
        const { t } = useI18n()
        return { t }
      },
      template: `
        <span 
          class="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
          :class="{
            'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400': data.role === 'admin',
            'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400': data.role === 'user'
          }"
        >
          {{ t(\`auth.role_\${data.role}\`) }}
        </span>
      `
    }))
  },
  {
    key: 'status',
    title: t('auth.status'),
    sortable: true,
    component: markRaw(defineComponent({
      props: ['data', 'value'],
      setup(props) {
        const { t } = useI18n()
        return { t }
      },
      template: `
        <span 
          class="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
          :class="{
            'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400': data.status === 'active',
            'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400': data.status === 'inactive'
          }"
        >
          {{ t(\`auth.status_\${data.status}\`) }}
        </span>
      `
    }))
  },
  {
    key: 'lastLogin',
    title: t('auth.last_login'),
    sortable: true,
    formatter: (value) => {
      return new Date(value).toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
]

// Handle DataTable actions
const handleUserAction = ({ action, item }) => {
  switch (action) {
    case 'view':
      // Handle view action
      break
    case 'edit':
      editUser(item)
      break
    case 'delete':
      deleteUser(item)
      break
  }
}

// Refresh users
const refreshUsers = () => {
  loading.value = true
  // Simulate loading
  setTimeout(() => {
    loading.value = false
  }, 1000)
}

// Handle sorting
const handleSort = ({ key, order }) => {
  // Sorting is handled by DataTable component internally
  console.log('Sort:', key, order)
}

// Edit user
const editUser = (user) => {
  editForm.value = { ...user }
  showEditModal.value = true
}

// Save user changes
const saveUser = () => {
  try {
    authStore.updateUser(editForm.value.id, {
      name: editForm.value.name,
      email: editForm.value.email,
      role: editForm.value.role
    })
    showEditModal.value = false
  } catch (error) {
    console.error('Failed to update user:', error)
  }
}

// Delete user
const deleteUser = (user) => {
  if (confirm(t('auth.confirm_delete_user'))) {
    try {
      authStore.deleteUser(user.id)
    } catch (error) {
      console.error('Failed to delete user:', error)
    }
  }
}

// Add user
const addUser = () => {
  try {
    const newUser = {
      id: Date.now(),
      ...addForm.value,
      status: 'active',
      lastLogin: new Date().toISOString(),
      avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(addForm.value.name)}&background=6366f1&color=fff`
    }
    
    authStore.addUser(newUser)
    cancelAddUser()
  } catch (error) {
    console.error('Failed to add user:', error)
  }
}

// Cancel add user
const cancelAddUser = () => {
  showAddUserDialog.value = false
  addForm.value = {
    username: '',
    name: '',
    email: '',
    role: 'user'
  }
}
</script>