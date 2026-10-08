import { createPinia } from 'pinia'
import { createPersistedState } from 'pinia-plugin-persistedstate' // State persistence

const store = createPinia()
store.use(
  createPersistedState({
    storage: {
      getItem: uni.getStorageSync,
      setItem: uni.setStorageSync,
    },
  }),
)

export default store

export * from './config'
export * from './plugin'
export * from './provider'
export * from './speedPitch'
// Central module exports
export * from './user'
