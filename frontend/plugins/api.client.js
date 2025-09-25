/**
 * API plugin - 提供全域的 $api 函數
 */

export default defineNuxtPlugin(() => {
  const { apiRequest } = useApi()

  // 提供一個簡化的 API 函數，自動處理方法和資料
  const $api = async (endpoint, options = {}) => {
    const { method = 'GET', ...restOptions } = options

    // 根據方法類型處理請求
    if (method === 'GET') {
      return await apiRequest(endpoint, { method: 'GET', ...restOptions })
    } else if (method === 'POST') {
      const body = options.body || options.data
      return await apiRequest(endpoint, {
        method: 'POST',
        body: body ? JSON.stringify(body) : undefined,
        ...restOptions
      })
    } else if (method === 'PUT') {
      const body = options.body || options.data
      return await apiRequest(endpoint, {
        method: 'PUT',
        body: body ? JSON.stringify(body) : undefined,
        ...restOptions
      })
    } else if (method === 'DELETE') {
      return await apiRequest(endpoint, { method: 'DELETE', ...restOptions })
    } else {
      return await apiRequest(endpoint, options)
    }
  }

  // 將 $api 函數註冊到 Nuxt app
  return {
    provide: {
      api: $api
    }
  }
})