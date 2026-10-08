import smCrypto from 'sm-crypto'
import { pages, subPackages } from '@/pages.json'

import { isMpWeixin } from './platform'

/**
 * Storage key for runtime server address override
 */
export const SERVER_BASE_URL_OVERRIDE_KEY = 'server_base_url_override'

/**
 * Set, clear, or retrieve the runtime server address override
 */
export function setServerBaseUrlOverride(url: string) {
  uni.setStorageSync(SERVER_BASE_URL_OVERRIDE_KEY, url)
}

export function clearServerBaseUrlOverride() {
  uni.removeStorageSync(SERVER_BASE_URL_OVERRIDE_KEY)
}

export function getServerBaseUrlOverride(): string | null {
  const value = uni.getStorageSync(SERVER_BASE_URL_OVERRIDE_KEY)
  return value || null
}

export function getLastPage() {
  // getCurrentPages() always has at least one item; no extra guard is needed
  // const lastPage = getCurrentPages().at(-1)
  // The previous approach fails when building for older Android versions, so use the fallback below (despite src/interceptions/prototype.ts).
  const pages = getCurrentPages()
  return pages[pages.length - 1]
}

/**
 * Get the current route path and redirectPath
 * Example path: '/pages/login/index'
 * Example redirectPath: '/pages/demo/base/route-interceptor'
 */
export function currRoute() {
  const lastPage = getLastPage()
  const currRoute = (lastPage as any).$page
  // console.log('lastPage.$page:', currRoute)
  // console.log('lastPage.$page.fullpath:', currRoute.fullPath)
  // console.log('lastPage.$page.options:', currRoute.options)
  // console.log('lastPage.options:', (lastPage as any).options)
  // Cross-platform testing showed that only fullPath is reliable
  const { fullPath } = currRoute as { fullPath: string }
  // console.log(fullPath)
  // eg: /pages/login/index?redirect=%2Fpages%2Fdemo%2Fbase%2Froute-interceptor (mini program)
  // eg: /pages/login/index?redirect=%2Fpages%2Froute-interceptor%2Findex%3Fname%3Dfeige%26age%3D30(h5)
  return getUrlObj(fullPath)
}

function ensureDecodeURIComponent(url: string) {
  if (url.startsWith('%')) {
    return ensureDecodeURIComponent(decodeURIComponent(url))
  }
  return url
}
/**
 * Parse a URL into path and query
 * Example URL: /pages/login/index?redirect=%2Fpages%2Fdemo%2Fbase%2Froute-interceptor
 * Output: {path: /pages/login/index, query: {redirect: /pages/demo/base/route-interceptor}}
 */
export function getUrlObj(url: string) {
  const [path, queryStr] = url.split('?')
  // console.log(path, queryStr)

  if (!queryStr) {
    return {
      path,
      query: {},
    }
  }
  const query: Record<string, string> = {}
  queryStr.split('&').forEach((item) => {
    const [key, value] = item.split('=')
    // console.log(key, value)
    query[key] = ensureDecodeURIComponent(value) // Decode uniformly to support H5 and WeChat
  })
  return { path, query }
}
/**
 * Get all pages requiring login, including main and subpackages
 * Accept an optional key for filtering; defaults to needLogin and works with route-block
 * Without a key return all pages; otherwise filter by key
 */
export function getAllPages(key = 'needLogin') {
  // Handle main package
  const mainPages = pages
    .filter(page => !key || page[key])
    .map(page => ({
      ...page,
      path: `/${page.path}`,
    }))

  // Handle subpackages
  const subPages: any[] = []
  subPackages.forEach((subPageObj) => {
    // console.log(subPageObj)
    const { root } = subPageObj

    subPageObj.pages
      .filter(page => !key || page[key])
      .forEach((page: { path: string } & Record<string, any>) => {
        subPages.push({
          ...page,
          path: `/${root}/${page.path}`,
        })
      })
  })
  const result = [...mainPages, ...subPages]
  // console.log(`getAllPages by ${key} result: `, result)
  return result
}

/**
 * Get all pages requiring login, including main and subpackages
 * Return only the path array
 */
export const getNeedLoginPages = (): string[] => getAllPages('needLogin').map(page => page.path)

/**
 * Get all pages requiring login, including main and subpackages
 * Return only the path array
 */
export const needLoginPages: string[] = getAllPages('needLogin').map(page => page.path)

/**
 * Select base URL based on current WeChat mini program environment
 */
export function getEnvBaseUrl() {
  // Prefer the user-defined override, if set
  const override = getServerBaseUrlOverride()
  if (override)
    return override

  // Base request URL (defaults to environment configuration)
  let baseUrl = import.meta.env.VITE_SERVER_BASEURL

  // # Some deployments need different URLs for develop, trial, and release environments; see below.
  const VITE_SERVER_BASEURL__WEIXIN_DEVELOP = 'https://ukw0y1.laf.run'
  const VITE_SERVER_BASEURL__WEIXIN_TRIAL = 'https://ukw0y1.laf.run'
  const VITE_SERVER_BASEURL__WEIXIN_RELEASE = 'https://ukw0y1.laf.run'

  // Distinguish WeChat mini program environments
  if (isMpWeixin) {
    const {
      miniProgram: { envVersion },
    } = uni.getAccountInfoSync()

    switch (envVersion) {
      case 'develop':
        baseUrl = VITE_SERVER_BASEURL__WEIXIN_DEVELOP || baseUrl
        break
      case 'trial':
        baseUrl = VITE_SERVER_BASEURL__WEIXIN_TRIAL || baseUrl
        break
      case 'release':
        baseUrl = VITE_SERVER_BASEURL__WEIXIN_RELEASE || baseUrl
        break
    }
  }

  return baseUrl
}

/**
 * Select upload URL based on current WeChat mini program environment
 */
export function getEnvBaseUploadUrl() {
  // Base request URL
  let baseUploadUrl = import.meta.env.VITE_UPLOAD_BASEURL

  const VITE_UPLOAD_BASEURL__WEIXIN_DEVELOP = 'https://ukw0y1.laf.run/upload'
  const VITE_UPLOAD_BASEURL__WEIXIN_TRIAL = 'https://ukw0y1.laf.run/upload'
  const VITE_UPLOAD_BASEURL__WEIXIN_RELEASE = 'https://ukw0y1.laf.run/upload'

  // Distinguish WeChat mini program environments
  if (isMpWeixin) {
    const {
      miniProgram: { envVersion },
    } = uni.getAccountInfoSync()

    switch (envVersion) {
      case 'develop':
        baseUploadUrl = VITE_UPLOAD_BASEURL__WEIXIN_DEVELOP || baseUploadUrl
        break
      case 'trial':
        baseUploadUrl = VITE_UPLOAD_BASEURL__WEIXIN_TRIAL || baseUploadUrl
        break
      case 'release':
        baseUploadUrl = VITE_UPLOAD_BASEURL__WEIXIN_RELEASE || baseUploadUrl
        break
    }
  }

  return baseUploadUrl
}

/**
 * Generate an SM2 keypair (hexadecimal)
 * @returns {object} Object containing public and private keys
 */
export function generateSm2KeyPairHex() {
  // Generate an SM2 keypair with sm-crypto
  const sm2 = smCrypto.sm2
  const keypair = sm2.generateKeyPairHex()

  return {
    publicKey: keypair.publicKey,
    privateKey: keypair.privateKey,
    clientPublicKey: keypair.publicKey, // Client public key
    clientPrivateKey: keypair.privateKey, // Client private key
  }
}

/**
 * SM2 public-key encryption
 * @param {string} publicKey Public key (hexadecimal)
 * @param {string} plainText Plaintext
 * @returns {string} Encrypted ciphertext (hexadecimal)
 */
export function sm2Encrypt(publicKey: string, plainText: string): string {
  if (!publicKey) {
    throw new Error('Public key cannot be null or undefined')
  }

  if (!plainText) {
    throw new Error('Plaintext must not be empty')
  }

  const sm2 = smCrypto.sm2
  // For SM2 encryption, prefix an uncompressed public key with 04
  const encrypted = sm2.doEncrypt(plainText, publicKey, 1)
  // Convert to hexadecimal to match backend formatting (add 04 prefix)
  const result = `04${encrypted}`

  return result
}

/**
 * SM2 private-key decryption
 * @param {string} privateKey Private key (hexadecimal)
 * @param {string} cipherText Ciphertext (hexadecimal)
 * @returns {string} Decrypted plaintext
 */
export function sm2Decrypt(privateKey: string, cipherText: string): string {
  const sm2 = smCrypto.sm2
  // Remove the 04 prefix to match backend formatting
  const dataWithoutPrefix = cipherText.startsWith('04') ? cipherText.substring(2) : cipherText
  // SM2 decryption
  return sm2.doDecrypt(dataWithoutPrefix, privateKey, 1)
}

type AnyFunction = (...args: any[]) => any

interface DebouncedFunction extends AnyFunction {
  cancel: () => void
}

/**
 * Debounce function
 * @param fn Function to debounce
 * @param delay Delay in milliseconds; defaults to 500ms
 * @param immediate Whether to execute immediately; defaults to false
 * @returns Debounced function
 */
export function debounce<T extends AnyFunction>(
  fn: T,
  delay = 500,
  immediate = false,
): DebouncedFunction {
  let timer: ReturnType<typeof setTimeout> | null = null

  const debounced = function (this: any, ...args: Parameters<T>) {
    if (timer) {
      clearTimeout(timer)
    }

    if (immediate && !timer) {
      fn.apply(this, args)
    }

    timer = setTimeout(() => {
      if (!immediate) {
        fn.apply(this, args)
      }
      timer = null
    }, delay)
  } as DebouncedFunction

  debounced.cancel = () => {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  return debounced
}

type DeepCloneTarget = string | number | boolean | null | undefined | object

/**
 * Deep clone function
 * @param target Target to clone
 * @returns New cloned object
 */
export function deepClone<T extends DeepCloneTarget>(target: T): T {
  if (target === null || typeof target !== 'object') {
    return target
  }

  if (target instanceof Date) {
    return new Date(target.getTime()) as any
  }

  if (Array.isArray(target)) {
    return target.map(item => deepClone(item)) as any
  }

  if (target instanceof Object) {
    const clonedObj = {} as T
    for (const key in target) {
      if (Object.prototype.hasOwnProperty.call(target, key)) {
        (clonedObj as any)[key] = deepClone((target as any)[key])
      }
    }
    return clonedObj
  }

  return target
}
