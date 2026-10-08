import type { uniappRequestAdapter } from '@alova/adapter-uniapp'
import type { IResponse } from './types'
import type { Language } from '@/store/lang'
import AdapterUniapp from '@alova/adapter-uniapp'
import { createAlova } from 'alova'
import { createServerTokenAuthentication } from 'alova/client'
import VueHook from 'alova/vue'
import { getEnvBaseUrl } from '@/utils'
import { toast } from '@/utils/toast'
import { ContentTypeEnum, ResultEnum, ShowMessage } from './enum'

// Language mapping for the Accept-Language header
const langMap: Record<Language, string> = {
  zh_CN: 'zh-CN',
  en: 'en-US',
  zh_TW: 'zh-TW',
  de: 'de',
  vi: 'vi',
  pt_BR: 'pt-BR',
}

/**
 * Create request instance
 */
const { onAuthRequired, onResponseRefreshToken } = createServerTokenAuthentication<
  typeof VueHook,
  typeof uniappRequestAdapter
>({
  refreshTokenOnError: {
    isExpired: (error) => {
      return error.response?.status === ResultEnum.Unauthorized
    },
    handler: async () => {
      try {
        // await authLogin();
      }
      catch (error) {
        // Switch to login page
        await uni.reLaunch({ url: '/pages/login/index' })
        throw error
      }
    },
  },
})

/**
 * Alova request instance
 */
const alovaInstance = createAlova({
  baseURL: getEnvBaseUrl(),
  ...AdapterUniapp(),
  timeout: 5000,
  statesHook: VueHook,

  beforeRequest: onAuthRequired((method) => {
    // On H5, resolve the latest baseURL dynamically using the user's configured server
    const currentBaseUrl = getEnvBaseUrl()
    if (currentBaseUrl !== method.baseURL) {
      method.baseURL = currentBaseUrl
    }

    // Check for mixed content (HTTPS page requesting HTTP API)
    const currentProtocol = typeof window !== 'undefined' && window.location.protocol
    const requestProtocol = method.baseURL?.split(':')[0]
    const currentLang = langMap[uni.getStorageSync('app_language') as Language || 'zh_CN']
    if (currentProtocol === 'https:' && requestProtocol === 'http') {
      const errorMessage = 'Cannot configure an HTTP URL; check the API address'
      throw new Error(errorMessage)
    }

    // Set default Content-Type
    method.config.headers = {
      'Content-Type': ContentTypeEnum.JSON,
      'Accept': 'application/json, text/plain, */*',
      'Accept-language': currentLang,
      ...method.config.headers,
    }

    const { config } = method
    const ignoreAuth = config.meta?.ignoreAuth
    console.log('ignoreAuth===>', ignoreAuth)

    // Handle authentication information
    if (!ignoreAuth) {
      const authInfo = JSON.parse(uni.getStorageSync('token') || '{}')
      if (!authInfo.token) {
        // Redirect to login page
        uni.reLaunch({ url: '/pages/login/index' })
        throw new Error('[Request error]: Not logged in')
      }
      // Add Authorization header
      method.config.headers.Authorization = `Bearer ${authInfo.token}`
    }

    // Handle dynamic hostnames
    if (config.meta?.domain) {
      method.baseURL = config.meta.domain
      console.log('Current hostname', method.baseURL)
    }
  }),

  responded: onResponseRefreshToken((response, method) => {
    const { config } = method
    const { requestType } = config
    const {
      statusCode,
      data: rawData,
      errMsg,
    } = response as UniNamespace.RequestSuccessCallbackResult

    console.log(response)

    // Handle special request types (upload/download)
    if (requestType === 'upload' || requestType === 'download') {
      return response
    }

    // Handle HTTP status errors
    if (statusCode !== 200) {
      const errorMessage = ShowMessage(statusCode) || `HTTP request error[${statusCode}]`
      console.error('errorMessage===>', errorMessage)
      toast.error(errorMessage)
      throw new Error(`${errorMessage}：${errMsg}`)
    }

    // Handle application-level errors
    const { code, msg, data } = rawData as IResponse
    if (code !== ResultEnum.Success) {
      // Check whether token has expired
      if (code === ResultEnum.Unauthorized) {
        // Clear token and redirect to login page
        uni.removeStorageSync('token')
        uni.reLaunch({ url: '/pages/login/index' })
        throw new Error(`Request error[${code}]：${msg}`)
      }

      if (config.meta?.isExposeError) {
        return Promise.reject(msg)
      }

      if (config.meta?.toast !== false) {
        toast.warning(msg)
      }
      throw new Error(`Request error[${code}]：${msg}`)
    }
    // Handle successful responses and return application data
    return data
  }),
})

export const http = alovaInstance
