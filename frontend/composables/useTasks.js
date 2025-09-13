/**
 * 任務管理相關API組合式函數
 */

export const useTasks = () => {
  const { get, post, del } = useApi()

  // 響應式資料
  const tasks = ref([])
  const runningTasks = ref([])
  const taskHistory = ref([])
  const loading = ref(false)
  const error = ref(null)
  
  /**
   * 獲取手動執行任務列表
   */
  const getManualTasks = async () => {
    loading.value = true
    error.value = null
    
    try {
      // 獲取執行中的任務
      const runningResult = await get('/task-execution/running')
      const runningTasksData = runningResult.success ? runningResult.data.running_tasks || [] : []
      
      // 獲取最近任務歷史
      const recentResult = await get('/task-execution/recent?limit=50')
      const taskHistoryData = recentResult.success ? recentResult.data.tasks || [] : []
      
      // 格式化執行中的任務
      runningTasks.value = runningTasksData.map(task => ({
        id: task.id,
        name: task.task_name,
        description: task.task_name,
        status: task.status,
        startTime: task.start_time ? new Date(task.start_time).toLocaleString('zh-TW') : '-',
        executionTime: task.duration_seconds ? `${task.duration_seconds.toFixed(0)}秒` : '計算中...',
        estimatedRemaining: '計算中...',
        currentStep: task.result_summary || '執行中...',
        progress: {
          current: task.processed_count || 0,
          total: task.total_count || 0,
          percent: task.progress || 0
        },
        recentItems: []
      }))
      
      // 格式化歷史任務
      taskHistory.value = taskHistoryData.map(task => ({
        id: task.id,
        name: task.task_name,
        description: task.task_name,
        status: task.status,
        taskType: task.task_type || 'manual',
        startTime: task.start_time ? new Date(task.start_time).toLocaleString('zh-TW') : '-',
        executionTime: task.duration_seconds ? `${task.duration_seconds.toFixed(0)}秒` : '-',
        processedCount: task.processed_count || 0,
        successCount: task.success_count || 0,
        failureCount: task.error_count || 0,
        errorMessage: task.error_message
      }))
      
      return {
        running_tasks: runningTasks.value,
        task_history: taskHistory.value
      }
    } catch (err) {
      error.value = err.message
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 創建股票爬蟲任務
   */
  const createStockCrawlTask = async (symbols = null) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await post('/tasks/manual/stock-crawl', symbols)
      
      if (result.success) {
        // 重新獲取任務列表以顯示新任務
        await getManualTasks()
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 取消執行中的任務
   */
  const cancelTask = async (taskId) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await post(`/task-execution/cancel/${taskId}`, { reason: '用戶取消' })
      
      if (result.success) {
        // 重新獲取任務列表
        await getManualTasks()
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 獲取任務詳情
   */
  const getTaskDetails = async (taskId) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await get(`/task-execution/status/${taskId}`)
      
      if (result.success) {
        const task = result.task
        return {
          id: task.id,
          name: task.task_name,
          type: task.task_type,
          status: task.status,
          progress: task.progress,
          startTime: task.start_time,
          endTime: task.end_time,
          duration: task.duration_seconds,
          processedCount: task.processed_count,
          totalCount: task.total_count,
          successCount: task.success_count,
          errorCount: task.error_count,
          parameters: task.parameters,
          resultSummary: task.result_summary,
          errorMessage: task.error_message,
          createdBy: task.created_by
        }
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 清除已完成的任務記錄
   */
  const clearCompletedTasks = async () => {
    loading.value = true
    error.value = null
    
    try {
      const result = await post('/tasks/manual/clear-completed')
      
      if (result.success) {
        // 重新獲取任務列表
        await getManualTasks()
        return result.data
      } else {
        error.value = result.error
        return null
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 輪詢更新執行中的任務狀態
   * @param {Object} callbacks - 回調函數集合
   * @param {Function} callbacks.onTaskCompleted - 當任務完成時調用
   */
  const startTaskPolling = (callbacks = {}) => {
    let previousRunningTaskIds = new Set(runningTasks.value.map(t => t.id))
    
    const pollInterval = setInterval(async () => {
      if (runningTasks.value.length > 0 || previousRunningTaskIds.size > 0) {
        try {
          const previousTasks = new Set(runningTasks.value.map(t => t.id))
          await getManualTasks()
          const currentTasks = new Set(runningTasks.value.map(t => t.id))
          
          // 檢測完成的任務
          const completedTaskIds = [...previousTasks].filter(id => !currentTasks.has(id))
          
          if (completedTaskIds.length > 0 && callbacks.onTaskCompleted) {
            console.log(`檢測到 ${completedTaskIds.length} 個任務完成:`, completedTaskIds)
            // 調用任務完成回調
            await callbacks.onTaskCompleted(completedTaskIds)
          }
          
          previousRunningTaskIds = currentTasks
        } catch (err) {
          console.error('Task polling error:', err)
        }
      } else {
        // 如果沒有執行中的任務，停止輪詢
        clearInterval(pollInterval)
      }
    }, 3000) // 每3秒更新一次

    // 返回清理函數
    return () => clearInterval(pollInterval)
  }

  return {
    // 響應式資料
    tasks: readonly(tasks),
    runningTasks: readonly(runningTasks),
    taskHistory: readonly(taskHistory),
    loading: readonly(loading),
    error: readonly(error),
    
    // 方法
    getManualTasks,
    createStockCrawlTask,
    cancelTask,
    getTaskDetails,
    clearCompletedTasks,
    startTaskPolling
  }
}