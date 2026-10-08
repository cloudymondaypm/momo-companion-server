/**
 * by Feige on 2024-03-06
 * Route interception, usually for authentication
 * Use a route allowlist or blocklist based on application requirements
 * Use a blocklist here because most pages are accessible without authentication
 */
import { useUserStore } from '@/store'
import { needLoginPages as _needLoginPages, getLastPage, getNeedLoginPages } from '@/utils'

// TODO Check
const loginRoute = import.meta.env.VITE_LOGIN_URL

function isLogined() {
  const userStore = useUserStore()
  return !!userStore.userInfo.username
}

const isDev = import.meta.env.DEV

// Blocklist-based login guard (most pages do not require authentication)
const navigateToInterceptor = {
  // Note: URLs here start with '/', unlike paths in pages.json
  // Add relative-path support, thanks to contributor @ideal
  invoke({ url }: { url: string }) {
    // console.log(url) // /pages/route-interceptor/index?name=feige&age=30
    let path = url.split('?')[0]
    console.log('Page changed')

    // Handle relative paths
    if (!path.startsWith('/')) {
      const currentPath = getLastPage().route
      const normalizedCurrentPath = currentPath.startsWith('/') ? currentPath : `/${currentPath}`
      const baseDir = normalizedCurrentPath.substring(0, normalizedCurrentPath.lastIndexOf('/'))
      path = `${baseDir}/${path}`
    }

    let needLoginPages: string[] = []
    // Fetch on every call to avoid development issues; moving this outside the function improves production performance
    if (isDev) {
      needLoginPages = getNeedLoginPages()
    }
    else {
      needLoginPages = _needLoginPages
    }
    const isNeedLogin = needLoginPages.includes(path)
    if (!isNeedLogin) {
      return true
    }
    const hasLogin = isLogined()
    if (hasLogin) {
      return true
    }
    const redirectRoute = `${loginRoute}?redirect=${encodeURIComponent(url)}`
    uni.navigateTo({ url: redirectRoute })
    return false
  },
}

export const routeInterceptor = {
  install() {
    uni.addInterceptor('navigateTo', navigateToInterceptor)
    uni.addInterceptor('reLaunch', navigateToInterceptor)
    uni.addInterceptor('redirectTo', navigateToInterceptor)
    uni.addInterceptor('switchTab', navigateToInterceptor)
  },
}
