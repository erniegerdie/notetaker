import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

interface VideoStreamResponse {
  status: 'ready' | 'generating' | 'failed'
  source_type: 'youtube' | 'upload'
  hls_url?: string | null
  youtube_video_id?: string | null
  youtube_url?: string | null
  retry_after?: number | null
  error_message?: string | null
}

async function fetchVideoStream(videoId: string): Promise<VideoStreamResponse> {
  const response = await api.get<VideoStreamResponse>(`/api/videos/${videoId}/stream`)
  return response.data
}

export function useVideoStream(videoId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ['video-stream', videoId],
    queryFn: () => fetchVideoStream(videoId),
    refetchInterval: (query) => {
      // Poll every 2s if generating, otherwise stop
      const data = query.state.data
      return data?.status === 'generating' ? 2000 : false
    },
    enabled: enabled && !!videoId,
    retry: (failureCount, error) => {
      // Don't retry on 400/404 errors
      const message = error?.message || ''
      if (message.includes('400') || message.includes('404')) {
        return false
      }
      // Retry network errors up to 3 times
      return failureCount < 3
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}
