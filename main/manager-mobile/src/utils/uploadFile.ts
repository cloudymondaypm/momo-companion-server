import { getEnvBaseUrl } from './index'
import { toast } from './toast'

/**
 * File upload hook usage example
 * @example
 * const { loading, error, data, progress, run } = useUpload<IUploadResult>(
 *   uploadUrl,
 *   {},
 *   {
 *     maxSize: 5, // Maximum 5 MB
 *     sourceType: ['album'], // Select only from album
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
 * @param options Upload options
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
 * @template T Successful upload response type
 * @param url Upload URL
 * @param formData Extra form data
 * @param options Upload options
 * @returns Upload state and controls
 */
export function useUpload<T = string>(url: string, formData: Record<string, any> = {}, options: UploadOptions = {},
  /** Provide file path to skip picker */
  directFilePath?: string) {
  /** Uploading state */
  const loading = ref(false)
  /** Upload error state */
  const error = ref(false)
  /** Successful upload response */
  const data = ref<T>()
  /** Upload progress（0-100） */
  const progress = ref(0)

  /** Destructure options and apply defaults */
  const {
    /** Maximum image count */
    count = 1,
    /** Selected image dimensions */
    sizeType = ['original', 'compressed'],
    /** Image source */
    sourceType = ['album', 'camera'],
    /** File size limit (MB) */
    maxSize = 10,
    /** Progress callback */
    onProgress,
    /** Success callback */
    onSuccess,
    /** Failure callback */
    onError,
    /** Completion callback */
    onComplete,
  } = options

  /**
   * Check file size limit
   * @param size File size in bytes
   * @returns Whether validation passed
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
   * Select and upload a file
   * Use a platform-specific picker：
   * - WeChat Mini Programs use chooseMedia
   * - Other platforms use chooseImage
   */
  const run = () => {
    if (directFilePath) {
      // Use provided file path
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
      mediaType: ['image'], // Only image files are supported
      sourceType,
      success: (res) => {
        const file = res.tempFiles[0]
        // Check file size limit
        if (!checkFileSize(file.size))
          return

        // Start upload
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
        console.log('Image selected:', res)

        // Start upload
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
 * @template T Successful upload response type
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
  /** Upload progress callback */
  onProgress?: (progress: number) => void
  /** Upload success callback */
  onSuccess?: (res: Record<string, any>) => void
  /** Upload failure callback */
  onError?: (err: Error | UniApp.GeneralCallbackResult) => void
  /** Upload completion callback */
  onComplete?: () => void
}

/**
 * Execute file upload
 * @template T Successful upload response type
 * @param options Upload options
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
      name: 'file', // Form field key for file
      formData,
      header: {
        // Allow browser to set multipart Content-Type on H5
        // #ifndef H5
        'Content-Type': 'multipart/form-data',
        // #endif
      },
      // Validate file name
      success: (uploadFileRes) => {
        console.log('File uploaded successfully:', uploadFileRes)
        try {
          // Parse response data
          const { data: _data } = JSON.parse(uploadFileRes.data)
          // Upload succeeded
          data.value = _data as T
          onSuccess?.(_data)
        }
        catch (err) {
          // Response parsing error
          console.error('Failed to parse upload response:', err)
          error.value = true
          onError?.(new Error('Failed to parse upload response'))
        }
      },
      fail: (err) => {
        // Upload request failed
        console.error('Failed to upload file:', err)
        error.value = true
        onError?.(err)
      },
      complete: () => {
        // Run regardless of outcome
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
