import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadVideoPresignedWithProgress } from '@/lib/api'
import { useState } from 'react'

interface UseVideoUploadOptions {
  onProgress?: (progress: number) => void
}

export function useVideoUpload(options?: UseVideoUploadOptions) {
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState(0)

  const mutation = useMutation({
    mutationFn: async (file: File) => {
      console.log('[useVideoUpload] Starting presigned upload:', file.name, file.size)

      // Use presigned URL upload with progress tracking
      const videoId = await uploadVideoPresignedWithProgress(file, (progress) => {
        setUploadProgress(Math.round(progress))
        options?.onProgress?.(Math.round(progress))
      })

      console.log('[useVideoUpload] Upload complete, video ID:', videoId)

      // Return response in expected format
      return { id: videoId }
    },
    onSuccess: (data) => {
      console.log('[useVideoUpload] onSuccess called with:', data)
      // Invalidate video list query to refetch
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      setUploadProgress(0)
    },
    onError: (error) => {
      console.error('[useVideoUpload] Upload error:', error)
      setUploadProgress(0)
    },
  })

  return {
    ...mutation,
    uploadProgress,
  }
}
