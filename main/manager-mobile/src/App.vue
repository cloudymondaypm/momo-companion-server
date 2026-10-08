<script setup lang="ts">
import { onHide, onLaunch, onShow } from '@dcloudio/uni-app'
import { onMounted, watch } from 'vue'
import { usePageAuth } from '@/hooks/usePageAuth'
import { t } from '@/i18n'
import { useConfigStore } from '@/store'
import { useLangStore } from '@/store/lang'
import 'abortcontroller-polyfill/dist/abortcontroller-polyfill-only'

usePageAuth()

const configStore = useConfigStore()
const langStore = useLangStore()

onLaunch(() => {
  console.log('App Launch')
  // Load public configuration
  configStore.fetchPublicConfig().catch((error) => {
    console.error('Failed to load public configuration:', error)
  })
})
onShow(() => {
  console.log('App Show')
  // Delay with setTimeout to ensure the tab bar has initialized
  setTimeout(() => {
    updateTabBarText()
  }, 100)
})

// Update tab bar labels dynamically
function updateTabBarText() {
  try {
    // Set Home tab bar label
    uni.setTabBarItem({
      index: 0,
      text: t('tabBar.home'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set Home tab bar label:', err)
      },
    })

    // Set Provisioning tab bar label
    uni.setTabBarItem({
      index: 1,
      text: t('tabBar.deviceConfig'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set Provisioning tab bar label:', err)
      },
    })

    // Set System tab bar label
    uni.setTabBarItem({
      index: 2,
      text: t('tabBar.settings'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set System tab bar label:', err)
      },
    })
  }
  catch (error) {
    console.log('Error updating tab bar labels:', error)
  }
}
// Listen for language-change events
onMounted(() => {
  // Watch language changes and update tab bar labels automatically
  watch(() => langStore.currentLang, () => {
    console.log('Language changed; updating tab bar labels')
    // Update tab bar labels immediately after language change
    updateTabBarText()
  })
})

onHide(() => {
  console.log('App Hide')
})
</script>

<style lang="scss">
swiper,
scroll-view {
  flex: 1;
  height: 100%;
  overflow: hidden;
}

image {
  width: 100%;
  height: 100%;
  vertical-align: middle;
}
</style>
