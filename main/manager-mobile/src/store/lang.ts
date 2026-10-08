import type { Ref } from 'vue'
import { defineStore } from 'pinia'
import { ref } from 'vue'

// Supported language codes
export type Language = 'zh_CN' | 'en' | 'zh_TW' | 'de' | 'vi' | 'pt_BR'

export interface LangStore {
  currentLang: Ref<Language>
  changeLang: (lang: Language) => void
}

export const useLangStore = defineStore(
  'lang',
  (): LangStore => {
    // Load the saved language, defaulting to English
    const savedLang = uni.getStorageSync('app_language') as Language | null
    const currentLang = ref<Language>(savedLang || 'en')

    // Switch language
    const changeLang = (lang: Language) => {
      currentLang.value = lang
      // Save the selected language locally
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
