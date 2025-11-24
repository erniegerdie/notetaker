import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { VideoStatusResponse } from '@/lib/types'
import { STATUS_POLL_INTERVAL } from '@/lib/constants'

export function useVideoStatus(videoId: string | null) {
  return useQuery({
    queryKey: ['video-status', videoId],
    queryFn: async () => {
      if (!videoId) throw new Error('Video ID is required')

      const { data } = await api.get<VideoStatusResponse>(
        `/api/videos/${videoId}/status`
      )
      return data
    },
    enabled: !!videoId,
    refetchInterval: (query) => {
      const data = query.state.data
      // Poll every 2 seconds if processing or uploaded, stop if completed/failed
      if (data?.status === 'processing' || data?.status === 'uploaded') {
        return STATUS_POLL_INTERVAL
      }
      return false
    },
    refetchOnWindowFocus: true,
  })
}
