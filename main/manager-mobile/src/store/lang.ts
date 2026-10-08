import type { Ref } from 'vue'
import { defineStore } from 'pinia'
import { ref } from 'vue'

// Supported languages
export type Language = 'zh_CN' | 'en' | 'zh_TW' | 'de' | 'vi' | 'pt_BR'

export interface LangStore {
  currentLang: Ref<Language>
  changeLang: (lang: Language) => void
}

export const useLangStore = defineStore(
  'lang',
  (): LangStore => {
    // Load language preference from local storage or use the default
    const savedLang = uni.getStorageSync('app_language') as Language | null
    const currentLang = ref<Language>(savedLang || 'en')

    // Change language
    const changeLang = (lang: Language) => {
      currentLang.value = lang
      // Persist language preference in local storage
      uni.setStorageSync('app_language', lang)
    }

    return {
      currentLang,
      changeLang,
    }
  },
  {
    persist: {
      key: 'lang',
      serializer: {
        serialize: state => JSON.stringify(state.currentLang),
        deserialize: value => ({ currentLang: JSON.parse(value) }),
      },
    },
  },
)
