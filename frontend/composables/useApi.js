/**
 * API基礎配置和通用函數
 */

export const useApi = () => {
  const config = useRuntimeConfig()
  
  // API基礎URL
  const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? config.public.apiUrl 
    : 'http://localhost:9121/api/v1'

  /**
   * 通用API請求函數
   */
  const apiRequest = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      ...options
    }

    try {
      const response = await $fetch(url, defaultOptions)
      return {
        success: true,
        data: response,
        error: null
      }
    } catch (error) {
      console.error('API請求失敗:', error)
      return {
        success: false,
        data: null,
        error: error.data?.detail || error.message || '請求失敗'
      }
    }
  }

  /**
   * GET請求
   */
  const get = async (endpoint, params = {}) => {
    const query = new URLSearchParams(params).toString()
    const url = query ? `${endpoint}?${query}` : endpoint
    return await apiRequest(url, { method: 'GET' })
  }

  /**
   * POST請求
   */
  const post = async (endpoint, data = {}) => {
    return await apiRequest(endpoint, {
      method: 'POST',
      body: data !== null ? JSON.stringify(data) : 'null'
    })
  }

  /**
   * PUT請求
   */
  const put = async (endpoint, data = {}) => {
    return await apiRequest(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  }

  /**
   * DELETE請求
   */
  const del = async (endpoint) => {
    return await apiRequest(endpoint, { method: 'DELETE' })
  }

  return {
    API_BASE_URL,
    apiRequest,
    get,
    post,
    put,
    delete: del
  }
}