/**
 * Tab bar state: persist with storageSync to retain the selected tab on browser refresh
 * Use simple reactive state instead of global Pinia state
 */
export const tabbarStore = reactive({
  curIdx: uni.getStorageSync('app-tabbar-index') || 0,
  setCurIdx(idx: number) {
    this.curIdx = idx
    uni.setStorageSync('app-tabbar-index', idx)
  },
})
