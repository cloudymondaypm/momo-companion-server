import type { TabBar } from '@uni-helper/vite-plugin-uni-pages'

type FgTabBarItem = TabBar['list'][0] & {
  icon: string
  iconType: 'uiLib' | 'unocss' | 'iconfont'
}

/**
 * Tab bar strategy; see tabbar.md
 * 0: 'NO_TABBAR' `No tab bar`
 * 1: 'NATIVE_TABBAR'  `Native tab bar`
 * 2: 'CUSTOM_TABBAR_WITH_CACHE' `Custom cached tab bar`
 * 3: 'CUSTOM_TABBAR_WITHOUT_CACHE' `Custom tab bar without cache`
 *
 * Restart after editing this file to regenerate pages.json
 */
export const TABBAR_MAP = {
  NO_TABBAR: 0,
  NATIVE_TABBAR: 1,
  CUSTOM_TABBAR_WITH_CACHE: 2,
  CUSTOM_TABBAR_WITHOUT_CACHE: 3,
}
// TODO: Select tab bar strategy here
export const selectedTabbarStrategy = TABBAR_MAP.NATIVE_TABBAR

// selectedTabbarStrategy==NATIVE_TABBAR(1) requires iconPath and selectedIconPath
// selectedTabbarStrategy==CUSTOM_TABBAR(2,3) requires icon and iconType
// selectedTabbarStrategy==NO_TABBAR(0) disables tabbarList
export const tabbarList: FgTabBarItem[] = [
  {
    iconPath: 'static/tabbar/robot.png',
    selectedIconPath: 'static/tabbar/robot_activate.png',
    pagePath: 'pages/index/index',
    text: 'Home',
    icon: 'home',
    // Use iconType uiLib for UI framework icons
    iconType: 'uiLib',
  },
  {
    iconPath: 'static/tabbar/network.png',
    selectedIconPath: 'static/tabbar/network_activate.png',
    pagePath: 'pages/device-config/index',
    text: 'Network Setup',
    icon: 'i-carbon-network-3',
    iconType: 'uiLib',
  },
  {
    iconPath: 'static/tabbar/system.png',
    selectedIconPath: 'static/tabbar/system_activate.png',
    pagePath: 'pages/settings/index',
    text: 'System',
    icon: 'i-carbon-settings',
    iconType: 'uiLib',
  },
]

// NATIVE_TABBAR(1) and CUSTOM_TABBAR_WITH_CACHE(2) require tab bar caching
export const cacheTabbarEnable = selectedTabbarStrategy === TABBAR_MAP.NATIVE_TABBAR
  || selectedTabbarStrategy === TABBAR_MAP.CUSTOM_TABBAR_WITH_CACHE

const _tabbar: TabBar = {
  // Only WeChat Mini Programs support custom (not App or H5)
  custom: selectedTabbarStrategy === TABBAR_MAP.CUSTOM_TABBAR_WITH_CACHE,
  color: '#e6e6e6',
  selectedColor: '#667dea',
  backgroundColor: '#fff',
  borderStyle: 'black',
  height: '50px',
  fontSize: '10px',
  iconWidth: '24px',
  spacing: '3px',
  list: tabbarList as unknown as TabBar['list'],
}

// Strategies 0 and 1 need bottom tab bar configuration for caching
export const tabBar = cacheTabbarEnable ? _tabbar : undefined
