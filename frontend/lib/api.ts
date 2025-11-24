import axios from 'axios'
import { supabase } from './supabase'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for authentication and logging
api.interceptors.request.use(
  async (config) => {
    // Add Supabase JWT token to requests (with timeout to prevent hanging)
    try {
      const sessionPromise = supabase.auth.getSession()
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Auth timeout')), 2000)
      )

      const { data: { session } } = await Promise.race([
        sessionPromise,
        timeoutPromise
      ]) as any

      if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`
      }
    } catch (error) {
      console.warn('[API] Auth check failed, continuing without token:', error)
      // Continue without auth token rather than failing the request
    }

    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const message = error.response?.data?.detail || error.message || 'Unknown error'
    console.error(`[API Error] ${error.config?.url}:`, message)

    // Handle 401/403 authentication errors - sign out and redirect to login
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.warn(`[API] ${error.response?.status} - clearing session and redirecting to login`)
      try {
        await supabase.auth.signOut()
      } catch (signOutError) {
        console.error('[API] Error signing out:', signOutError)
      }
      // Redirect to login page
      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(new Error(message))
  }
)

// Presigned URL upload flow
export async function uploadVideoPresigned(
  file: File,
  onProgress?: (progress: number) => void
): Promise<string> {
  try {
    // 1. Get presigned URL from backend
    console.log(`[API] Requesting presigned URL for ${file.name} (${(file.size / (1024*1024)).toFixed(2)}MB)`)

    const { data: presignedData } = await api.post('/api/videos/upload/presigned', {
      filename: file.name,
      file_size: file.size,
      content_type: file.type || 'video/mp4'
    })

    const { video_id, upload_url, r2_key, expires_in } = presignedData

    console.log(`[API] Got presigned URL for video ${video_id} (expires in ${expires_in}s)`)

    // 2. Upload directly to R2 using presigned URL
    console.log(`[API] Uploading to R2: ${r2_key}`)

    const uploadResponse = await fetch(upload_url, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type || 'video/mp4'
      }
    })

    if (!uploadResponse.ok) {
      const errorText = await uploadResponse.text()
      console.error(`[API] R2 upload failed:`, errorText)
      throw new Error(`R2 upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`)
    }

    console.log(`[API] R2 upload successful for video ${video_id}`)

    // 3. Notify backend that upload is complete
    console.log(`[API] Notifying backend of upload completion`)

    await api.post(`/api/videos/${video_id}/upload/complete`, {
      success: true
    })

    console.log(`[API] Upload complete for video ${video_id}`)

    return video_id
  } catch (error: any) {
    console.error('[API] Presigned upload failed:', error)

    // Attempt to notify backend of failure if we have video_id
    // This is best-effort cleanup

    throw error
  }
}

// Upload with XMLHttpRequest for progress tracking
export async function uploadVideoPresignedWithProgress(
  file: File,
  onProgress: (progress: number) => void
): Promise<string> {
  try {
    // 1. Get presigned URL from backend
    console.log(`[API] Requesting presigned URL for ${file.name} (${(file.size / (1024*1024)).toFixed(2)}MB)`)

    const { data: presignedData } = await api.post('/api/videos/upload/presigned', {
      filename: file.name,
      file_size: file.size,
      content_type: file.type || 'video/mp4'
    })

    const { video_id, upload_url, r2_key, expires_in } = presignedData

    console.log(`[API] Got presigned URL for video ${video_id} (expires in ${expires_in}s)`)

    // 2. Upload to R2 with progress tracking
    console.log(`[API] Uploading to R2 with progress: ${r2_key}`)

    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest()

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = (e.loaded / e.total) * 100
          onProgress(progress)
        }
      })

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          console.log(`[API] R2 upload successful for video ${video_id}`)
          resolve()
        } else {
          console.error(`[API] R2 upload failed:`, xhr.responseText)
          reject(new Error(`R2 upload failed: ${xhr.status} ${xhr.statusText}`))
        }
      })

      xhr.addEventListener('error', (e) => {
        console.error(`[API] R2 upload network error:`, {
          status: xhr.status,
          statusText: xhr.statusText,
          responseText: xhr.responseText,
          readyState: xhr.readyState,
          event: e
        })
        reject(new Error(`R2 upload network error (status: ${xhr.status})`))
      })

      xhr.addEventListener('abort', () => {
        console.error(`[API] R2 upload aborted`)
        reject(new Error('R2 upload aborted'))
      })

      xhr.open('PUT', upload_url)
      xhr.setRequestHeader('Content-Type', file.type || 'video/mp4')
      xhr.send(file)
    })

    // 3. Notify backend that upload is complete
    console.log(`[API] Notifying backend of upload completion`)

    await api.post(`/api/videos/${video_id}/upload/complete`, {
      success: true
    })

    console.log(`[API] Upload complete for video ${video_id}`)

    return video_id
  } catch (error: any) {
    console.error('[API] Presigned upload with progress failed:', error)
    throw error
  }
}

export default api
