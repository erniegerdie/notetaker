import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Video } from '@/lib/types'
import { BACKGROUND_REFETCH_INTERVAL, STATUS_POLL_INTERVAL } from '@/lib/constants'

interface VideoListResponse {
  videos: Video[]
}

interface UseVideoListOptions {
  enabled?: boolean
}

export function useVideoList(options?: UseVideoListOptions) {
  return useQuery({
    queryKey: ['videos'],
    queryFn: async () => {
      const { data } = await api.get<VideoListResponse>('/api/videos')
      // Sort by uploaded_at descending (newest first)
      return {
        ...data,
        videos: data.videos.sort((a, b) =>
          new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime()
        )
      }
    },
    // Dynamic refetch interval: poll faster if any videos are processing
    refetchInterval: (query) => {
      const hasProcessingVideos = query.state.data?.videos.some(
        video => video.status === 'uploaded' || video.status === 'processing'
      )
      return hasProcessingVideos ? STATUS_POLL_INTERVAL : BACKGROUND_REFETCH_INTERVAL
    },
    refetchOnWindowFocus: true,
    enabled: options?.enabled !== false, // Default to true if not specified
  })
}
