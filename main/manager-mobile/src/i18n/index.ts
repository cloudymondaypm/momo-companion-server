import type { Language } from '@/store/lang'
import { ref } from 'vue'
import { useLangStore } from '@/store/lang'

import de from './de'
import en from './en'
import pt_BR from './pt_BR'
import vi from './vi'
// Import translation files
import zh_CN from './zh_CN'
import zh_TW from './zh_TW'

// Translation dictionaries
const messages = {
  zh_CN,
  en,
  zh_TW,
  de,
  vi,
  pt_BR,
}

// Current language
const currentLang = ref<Language>('en')

// Initialize language
export function initI18n() {
  const langStore = useLangStore()
  currentLang.value = langStore.currentLang
}

// Change language
export function changeLanguage(lang: Language) {
  currentLang.value = lang
  const langStore = useLangStore()
  langStore.changeLang(lang)
}

// Get translated text
export function t(key: string, params?: Record<string, string | number>): string {
  const langMessages = messages[currentLang.value]

  // Look up flattened translation keys
  if (langMessages && typeof langMessages === 'object' && key in langMessages) {
    const value = langMessages[key]
    if (typeof value === 'string') {
      // Replace template parameters
      if (params) {
        let result = value
        Object.entries(params).forEach(([paramKey, paramValue]) => {
          const regex = new RegExp(`\{${paramKey}\}`, 'g')
          result = result.replace(regex, String(paramValue))
        })
        return result
      }
      return value
    }
    return key
  }

  return key // Return the key if no translation is found
}

// Get current language
export function getCurrentLanguage(): Language {
  return currentLang.value
}

// List supported languages
export function getSupportedLanguages(): { code: Language, name: string }[] {
  return [
    { code: 'zh_CN', name: 'Simplified Chinese' },
    { code: 'en', name: 'English' },
    { code: 'zh_TW', name: 'Traditional Chinese' },
    { code: 'de', name: 'Deutsch' },
    { code: 'vi', name: 'Tiếng Việt' },
    { code: 'pt_BR', name: 'Português (Brasil)' },
  ]
}
