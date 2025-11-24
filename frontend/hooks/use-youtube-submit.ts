import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import type { YouTubeSubmitRequest, YouTubeSubmitResponse } from '@/lib/types'

export function useYoutubeSubmit() {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async (request: YouTubeSubmitRequest) => {
      const { data } = await api.post<YouTubeSubmitResponse>(
        '/api/videos/youtube',
        request,
        {
          timeout: 5 * 60 * 1000, // 5 minutes for YouTube download
        }
      )
      return data
    },
    onSuccess: () => {
      // Invalidate video list query to refetch
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })

  return mutation
}
