export const useAuthStore = defineStore('auth', () => {
  // 用戶狀態
  const user = ref(null)
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  
  // 模擬用戶數據
  const mockUsers = ref([
    {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      password: 'admin123',
      name: '管理員',
      role: 'admin',
      avatar: 'https://ui-avatars.com/api/?name=Admin&background=6366f1&color=fff',
      createdAt: new Date('2024-01-01'),
      lastLogin: new Date(),
      status: 'active'
    },
    {
      id: 2,
      username: 'user1',
      email: 'user1@example.com',
      password: 'user123',
      name: '使用者一',
      role: 'user',
      avatar: 'https://ui-avatars.com/api/?name=User1&background=22c55e&color=fff',
      createdAt: new Date('2024-01-15'),
      lastLogin: new Date(Date.now() - 86400000), // 1 day ago
      status: 'active'
    },
    {
      id: 3,
      username: 'user2',
      email: 'user2@example.com',
      password: 'user123',
      name: '使用者二',
      role: 'user',
      avatar: 'https://ui-avatars.com/api/?name=User2&background=f97316&color=fff',
      createdAt: new Date('2024-02-01'),
      lastLogin: new Date(Date.now() - 172800000), // 2 days ago
      status: 'inactive'
    }
  ])

  // 登入功能
  const login = async (credentials) => {
    try {
      // 模擬 API 延遲
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 查找用戶
      const foundUser = mockUsers.value.find(u => 
        (u.username === credentials.username || u.email === credentials.username) &&
        u.password === credentials.password
      )
      
      if (!foundUser) {
        throw new Error('用戶名或密碼錯誤')
      }
      
      if (foundUser.status === 'inactive') {
        throw new Error('帳戶已被停用')
      }
      
      // 更新最後登入時間
      foundUser.lastLogin = new Date()
      
      // 設定用戶資料 (不包含密碼)
      const { password, ...userWithoutPassword } = foundUser
      user.value = userWithoutPassword
      
      // 儲存到 localStorage
      if (process.client) {
        localStorage.setItem('admin-template-user', JSON.stringify(userWithoutPassword))
      }
      
      return { success: true, user: userWithoutPassword }
    } catch (error) {
      throw error
    }
  }

  // 註冊功能
  const register = async (userData) => {
    try {
      // 模擬 API 延遲
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 檢查用戶名和郵箱是否已存在
      const existingUser = mockUsers.value.find(u => 
        u.username === userData.username || u.email === userData.email
      )
      
      if (existingUser) {
        throw new Error('用戶名或郵箱已存在')
      }
      
      // 創建新用戶
      const newUser = {
        id: Math.max(...mockUsers.value.map(u => u.id)) + 1,
        username: userData.username,
        email: userData.email,
        password: userData.password,
        name: userData.name || userData.username,
        role: 'user',
        avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(userData.name || userData.username)}&background=6366f1&color=fff`,
        createdAt: new Date(),
        lastLogin: new Date(),
        status: 'active'
      }
      
      mockUsers.value.push(newUser)
      
      // 自動登入
      const { password, ...userWithoutPassword } = newUser
      user.value = userWithoutPassword
      
      // 儲存到 localStorage
      if (process.client) {
        localStorage.setItem('admin-template-user', JSON.stringify(userWithoutPassword))
      }
      
      return { success: true, user: userWithoutPassword }
    } catch (error) {
      throw error
    }
  }

  // 登出功能
  const logout = () => {
    user.value = null
    
    // 清除 localStorage
    if (process.client) {
      localStorage.removeItem('admin-template-user')
    }
    
    // 重定向到登入頁面
    navigateTo('/auth/login')
  }

  // 初始化用戶狀態
  const initializeAuth = () => {
    if (process.client) {
      const savedUser = localStorage.getItem('admin-template-user')
      if (savedUser) {
        try {
          user.value = JSON.parse(savedUser)
        } catch (error) {
          console.error('Failed to parse saved user data:', error)
          localStorage.removeItem('admin-template-user')
        }
      }
    }
  }

  // 用戶管理功能 (僅管理員)
  const getAllUsers = () => {
    if (!isAdmin.value) {
      throw new Error('權限不足')
    }
    return mockUsers.value.map(({ password, ...user }) => user)
  }

  const updateUser = (userId, updates) => {
    if (!isAdmin.value && user.value?.id !== userId) {
      throw new Error('權限不足')
    }
    
    const userIndex = mockUsers.value.findIndex(u => u.id === userId)
    if (userIndex === -1) {
      throw new Error('用戶不存在')
    }
    
    // 更新用戶資料
    Object.assign(mockUsers.value[userIndex], updates)
    
    // 如果更新的是當前用戶，同步更新 user 狀態
    if (user.value?.id === userId) {
      const { password, ...updatedUser } = mockUsers.value[userIndex]
      user.value = updatedUser
      
      if (process.client) {
        localStorage.setItem('admin-template-user', JSON.stringify(updatedUser))
      }
    }
    
    return mockUsers.value[userIndex]
  }

  const deleteUser = (userId) => {
    if (!isAdmin.value) {
      throw new Error('權限不足')
    }
    
    if (user.value?.id === userId) {
      throw new Error('無法刪除自己的帳戶')
    }
    
    const userIndex = mockUsers.value.findIndex(u => u.id === userId)
    if (userIndex === -1) {
      throw new Error('用戶不存在')
    }
    
    mockUsers.value.splice(userIndex, 1)
    return true
  }

  const toggleUserStatus = (userId) => {
    if (!isAdmin.value) {
      throw new Error('權限不足')
    }
    
    const userToUpdate = mockUsers.value.find(u => u.id === userId)
    if (!userToUpdate) {
      throw new Error('用戶不存在')
    }
    
    userToUpdate.status = userToUpdate.status === 'active' ? 'inactive' : 'active'
    return userToUpdate
  }

  const addUser = (newUser) => {
    if (!isAdmin.value) {
      throw new Error('權限不足')
    }
    
    // 檢查用戶名是否已存在
    const existingUser = mockUsers.value.find(u => u.username === newUser.username)
    if (existingUser) {
      throw new Error('用戶名已存在')
    }
    
    // 檢查郵箱是否已存在
    const existingEmail = mockUsers.value.find(u => u.email === newUser.email)
    if (existingEmail) {
      throw new Error('郵箱已存在')
    }
    
    // 添加預設密碼和其他屬性
    const userToAdd = {
      ...newUser,
      password: 'user123', // 預設密碼
      createdAt: new Date().toISOString()
    }
    
    mockUsers.value.push(userToAdd)
    return userToAdd
  }

  return {
    // 狀態
    user: readonly(user),
    isLoggedIn,
    isAdmin,
    mockUsers: readonly(mockUsers),
    
    // 方法
    login,
    register,
    logout,
    initializeAuth,
    
    // 用戶管理
    getAllUsers,
    updateUser,
    deleteUser,
    toggleUserStatus,
    addUser
  }
})