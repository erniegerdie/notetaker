import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { VideoStatusResponse } from '@/lib/types'

interface UpdateVideoParams {
  videoId: string
  title?: string
}

interface DeleteVideoResponse {
  id: string
  deleted: boolean
  message: string
}

export function useUpdateVideo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ videoId, title }: UpdateVideoParams) => {
      const { data } = await api.patch<VideoStatusResponse>(
        `/api/videos/${videoId}`,
        { title }
      )
      return data
    },
    onSuccess: (data) => {
      // Invalidate video-related queries
      queryClient.invalidateQueries({ queryKey: ['video-status', data.id] })
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}

export function useDeleteVideo() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (videoId: string) => {
      const { data } = await api.delete<DeleteVideoResponse>(
        `/api/videos/${videoId}`
      )
      return data
    },
    onSuccess: () => {
      // Invalidate video list query
      queryClient.invalidateQueries({ queryKey: ['videos'] })
    },
  })
}
