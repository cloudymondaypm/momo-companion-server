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
  // Retrieve shared configuration
  configStore.fetchPublicConfig().catch((error) => {
    console.error('Failed to retrieve shared configuration:', error)
  })
})
onShow(() => {
  console.log('App Show')
  // Delay with setTimeout to ensure tabBar is initialized
  setTimeout(() => {
    updateTabBarText()
  }, 100)
})

// Dynamically update tab bar labels
function updateTabBarText() {
  try {
    // Set Home tab label
    uni.setTabBarItem({
      index: 0,
      text: t('tabBar.home'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set Home tab label:', err)
      },
    })

    // Set Network Setup tab label
    uni.setTabBarItem({
      index: 1,
      text: t('tabBar.deviceConfig'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set Network Setup tab label:', err)
      },
    })

    // Set System tab label
    uni.setTabBarItem({
      index: 2,
      text: t('tabBar.settings'),
      success: () => {},
      fail: (err) => {
        console.log('Failed to set System tab label:', err)
      },
    })
  }
  catch (error) {
    console.log('Error updating tab bar labels:', error)
  }
}
// Listen for language switching events
onMounted(() => {
  // Listen for language changes and automatically update tab bar labels
  watch(() => langStore.currentLang, () => {
    console.log('Language changed; updating tab bar labels')
    // Immediately update tab bar labels after changing languages
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
