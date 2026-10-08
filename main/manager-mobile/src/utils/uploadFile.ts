import { getEnvBaseUrl } from './index'
import { toast } from './toast'

/**
 * File upload hook usage example
 * @example
 * const { loading, error, data, progress, run } = useUpload<IUploadResult>(
 *   uploadUrl,
 *   {},
 *   {
 *     maxSize: 5, // 最大5MB
 *     sourceType: ['album'], // 仅支持从相册选择
 *     onProgress: (p) => console.log(`Upload progress：${p}%`),
 *     onSuccess: (res) => console.log('Upload succeeded', res),
 *     onError: (err) => console.error('Upload failed', err),
 *   },
 * )
 */

/**
 * Upload URL configuration
 */
export const uploadFileUrl = {
  /** Avatar upload URL (uses current BaseURL) */
  get USER_AVATAR() {
    return `${getEnvBaseUrl()}/user/avatar`
  },
}

/**
 * Generic file upload (supports file path)
 * @param url Upload URL
 * @param filePath Local file path
 * @param formData Extra form data
 * @param options 上传选项
 */
export function useFileUpload<T = string>(url: string, filePath: string, formData: Record<string, any> = {}, options: Omit<UploadOptions, 'sourceType' | 'sizeType' | 'count'> = {}) {
  return useUpload<T>(
    url,
    formData,
    {
      ...options,
      sourceType: ['album'],
      sizeType: ['original'],
    },
    filePath,
  )
}

export interface UploadOptions {
  /** Maximum image count (default 1) */
  count?: number
  /** Selected image quality: original or compressed */
  sizeType?: Array<'original' | 'compressed'>
  /** Image source: album or camera */
  sourceType?: Array<'album' | 'camera'>
  /** File size limit in MB */
  maxSize?: number //
  /** Progress callback */
  onProgress?: (progress: number) => void
  /** Success callback */
  onSuccess?: (res: Record<string, any>) => void
  /** Failure callback */
  onError?: (err: Error | UniApp.GeneralCallbackResult) => void
  /** Completion callback (always invoked) */
  onComplete?: () => void
}

/**
 * File upload hook
 * @template T Upload succeeded后返回的数据类型
 * @param url Upload URL
 * @param formData Extra form data
 * @param options 上传选项
 * @returns 上传状态和控制对象
 */
export function useUpload<T = string>(url: string, formData: Record<string, any> = {}, options: UploadOptions = {},
  /** 直接传入文件路径，跳过选择器 */
  directFilePath?: string) {
  /** Uploading state */
  const loading = ref(false)
  /** Upload error state */
  const error = ref(false)
  /** Successful upload response */
  const data = ref<T>()
  /** Upload progress（0-100） */
  const progress = ref(0)

  /** 解构上传选项，设置默认值 */
  const {
    /** Maximum image count */
    count = 1,
    /** 所选的图片的尺寸 */
    sizeType = ['original', 'compressed'],
    /** 选择图片的来源 */
    sourceType = ['album', 'camera'],
    /** File size limit (MB) */
    maxSize = 10,
    /** 进度回调 */
    onProgress,
    /** 成功回调 */
    onSuccess,
    /** 失败回调 */
    onError,
    /** 完成回调 */
    onComplete,
  } = options

  /**
   * Check file size limit
   * @param size File size（字节）
   * @returns 是否通过检查
   */
  const checkFileSize = (size: number) => {
    const sizeInMB = size / 1024 / 1024
    if (sizeInMB > maxSize) {
      toast.warning(`File size cannot exceed ${maxSize}MB`)
      return false
    }
    return true
  }
  /**
   * 触发文件选择和上传
   * Use a platform-specific picker：
   * - 微信小程序使用 chooseMedia
   * - 其他平台使用 chooseImage
   */
  const run = () => {
    if (directFilePath) {
      // 直接使用传入的文件路径
      loading.value = true
      progress.value = 0
      uploadFile<T>({
        url,
        tempFilePath: directFilePath,
        formData,
        data,
        error,
        loading,
        progress,
        onProgress,
        onSuccess,
        onError,
        onComplete,
      })
      return
    }

    // #ifdef MP-WEIXIN
    // Use chooseMedia on WeChat Mini Programs
    uni.chooseMedia({
      count,
      mediaType: ['image'], // 仅支持图片类型
      sourceType,
      success: (res) => {
        const file = res.tempFiles[0]
        // 检查File size是否符合限制
        if (!checkFileSize(file.size))
          return

        // 开始上传
        loading.value = true
        progress.value = 0
        uploadFile<T>({
          url,
          tempFilePath: file.tempFilePath,
          formData,
          data,
          error,
          loading,
          progress,
          onProgress,
          onSuccess,
          onError,
          onComplete,
        })
      },
      fail: (err) => {
        console.error('Failed to select media:', err)
        error.value = true
        onError?.(err)
      },
    })
    // #endif

    // #ifndef MP-WEIXIN
    // Use chooseImage on other platforms
    uni.chooseImage({
      count,
      sizeType,
      sourceType,
      success: (res) => {
        console.log('选择图片成功:', res)

        // 开始上传
        loading.value = true
        progress.value = 0
        uploadFile<T>({
          url,
          tempFilePath: res.tempFilePaths[0],
          formData,
          data,
          error,
          loading,
          progress,
          onProgress,
          onSuccess,
          onError,
          onComplete,
        })
      },
      fail: (err) => {
        console.error('Failed to select image:', err)
        error.value = true
        onError?.(err)
      },
    })
    // #endif
  }

  return { loading, error, data, progress, run }
}

/**
 * File upload options interface
 * @template T Upload succeeded后返回的数据类型
 */
interface UploadFileOptions<T> {
  /** Upload URL */
  url: string
  /** Temporary file path */
  tempFilePath: string
  /** Extra form data */
  formData: Record<string, any>
  /** Successful upload response */
  data: Ref<T | undefined>
  /** Upload error state */
  error: Ref<boolean>
  /** Uploading state */
  loading: Ref<boolean>
  /** Upload progress（0-100） */
  progress: Ref<number>
  /** Upload progress回调 */
  onProgress?: (progress: number) => void
  /** Upload succeeded回调 */
  onSuccess?: (res: Record<string, any>) => void
  /** Upload failed回调 */
  onError?: (err: Error | UniApp.GeneralCallbackResult) => void
  /** 上传完成回调 */
  onComplete?: () => void
}

/**
 * Execute file upload
 * @template T Upload succeeded后返回的数据类型
 * @param options 上传选项
 */
function uploadFile<T>({
  url,
  tempFilePath,
  formData,
  data,
  error,
  loading,
  progress,
  onProgress,
  onSuccess,
  onError,
  onComplete,
}: UploadFileOptions<T>) {
  try {
    // Create upload task
    const uploadTask = uni.uploadFile({
      url,
      filePath: tempFilePath,
      name: 'file', // 文件对应的 key
      formData,
      header: {
        // Allow browser to set multipart Content-Type on H5
        // #ifndef H5
        'Content-Type': 'multipart/form-data',
        // #endif
      },
      // 确保文件名称合法
      success: (uploadFileRes) => {
        console.log('File uploaded successfully:', uploadFileRes)
        try {
          // 解析响应数据
          const { data: _data } = JSON.parse(uploadFileRes.data)
          // Upload succeeded
          data.value = _data as T
          onSuccess?.(_data)
        }
        catch (err) {
          // 响应解析错误
          console.error('Failed to parse upload response:', err)
          error.value = true
          onError?.(new Error('Failed to parse upload response'))
        }
      },
      fail: (err) => {
        // Upload request失败
        console.error('Failed to upload file:', err)
        error.value = true
        onError?.(err)
      },
      complete: () => {
        // 无论成功失败都执行
        loading.value = false
        onComplete?.()
      },
    })

    // Listen for upload progress
    uploadTask.onProgressUpdate((res) => {
      progress.value = res.progress
      onProgress?.(res.progress)
    })
  }
  catch (err) {
    // Failed to create upload task
    console.error('Failed to create upload task:', err)
    error.value = true
    loading.value = false
    onError?.(new Error('Failed to create upload task'))
  }
}
