import type { Language } from '@/store/lang'
import { ref } from 'vue'
import { useLangStore } from '@/store/lang'

import de from './de'
import en from './en'
import pt_BR from './pt_BR'
import vi from './vi'
// Import language translations
import zh_CN from './zh_CN'
import zh_TW from './zh_TW'

// Translation map
const messages = {
  zh_CN,
  en,
  zh_TW,
  de,
  vi,
  pt_BR,
}

// Active language
const currentLang = ref<Language>('en')

// Initialize language
export function initI18n() {
  const langStore = useLangStore()
  currentLang.value = langStore.currentLang
}

// Switch language
export function changeLanguage(lang: Language) {
  currentLang.value = lang
  const langStore = useLangStore()
  langStore.changeLang(lang)
}

// Get translated text
export function t(key: string, params?: Record<string, string | number>): string {
  const langMessages = messages[currentLang.value]

  // Look up a flat translation key
  if (langMessages && typeof langMessages === 'object' && key in langMessages) {
    const value = langMessages[key]
    if (typeof value === 'string') {
      // Substitute template parameters
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

  return key // Return the key when no translation is found
}

// Get the active language
export function getCurrentLanguage(): Language {
  return currentLang.value
}

// List supported languages
export function getSupportedLanguages(): { code: Language, name: string }[] {
  return [
    { code: 'zh_CN', name: '简体中文' },
    { code: 'en', name: 'English' },
    { code: 'zh_TW', name: '繁體中文' },
    { code: 'de', name: 'Deutsch' },
    { code: 'vi', name: 'Tiếng Việt' },
    { code: 'pt_BR', name: 'Português (Brasil)' },
  ]
}
