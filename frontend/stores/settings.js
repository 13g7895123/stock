export const useSettingsStore = defineStore('settings', () => {
  const showFootbar = ref(true)
  const sidebarMenuItems = ref([
    {
      name: '控制台',
      icon: 'ChartBarIcon',
      children: [
        { name: '系統概覽', href: '/dashboard/overview' },
        { name: '數據監控', href: '/dashboard/monitoring' },
        { name: '效能統計', href: '/dashboard/performance' }
      ]
    },
    {
      name: '股票管理',
      icon: 'BuildingOfficeIcon',
      children: [
        { name: '股票清單', href: '/stocks/list' },
        { name: '股票更新', href: '/stocks/update' },
        { name: '分類管理', href: '/stocks/categories' }
      ]
    },
    {
      name: '資料管理',
      icon: 'CircleStackIcon',
      children: [
        { name: '歷史資料', href: '/data/historical' },
        { name: '資料更新', href: '/data/update' },
        { name: '資料品質', href: '/data/quality' }
      ]
    },
    {
      name: '技術分析',
      icon: 'PresentationChartLineIcon',
      children: [
        { name: '均線計算', href: '/analysis/moving-averages' },
        { name: '技術指標', href: '/analysis/indicators' },
        { name: '參數設定', href: '/analysis/parameters' }
      ]
    },
    {
      name: '選股結果',
      icon: 'StarIcon',
      children: [
        { name: '推薦股票', href: '/screening/recommendations' },
        { name: '篩選條件', href: '/screening/filters' },
        { name: '歷史記錄', href: '/screening/history' }
      ]
    },
    {
      name: '任務管理',
      icon: 'ClockIcon',
      children: [
        { name: '定時任務', href: '/tasks/scheduled' },
        { name: '手動執行', href: '/tasks/manual' },
        { name: '執行記錄', href: '/tasks/logs' }
      ]
    },
    {
      name: '系統設定',
      icon: 'CogIcon',
      children: [
        { name: '系統參數', href: '/settings/system' },
        { name: '數據來源', href: '/settings/datasource' },
        { name: '通知設定', href: '/settings/notifications' },
        { name: '用戶管理', href: '/settings/users' }
      ]
    }
  ])
  
  const toggleFootbar = () => {
    showFootbar.value = !showFootbar.value
  }
  
  const updateMenuItems = (newItems) => {
    sidebarMenuItems.value = newItems
  }
  
  return {
    showFootbar,
    sidebarMenuItems,
    toggleFootbar,
    updateMenuItems
  }
})