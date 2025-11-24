import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import type { Transcription } from '@/lib/types'

export function useTranscription(videoId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['transcription', videoId],
    queryFn: async () => {
      if (!videoId) throw new Error('Video ID is required')

      const { data } = await api.get<Transcription>(
        `/api/videos/${videoId}/transcription`
      )
      return data
    },
    enabled: !!videoId && enabled,
    retry: false, // Don't retry if transcription isn't ready
    staleTime: Infinity, // Transcriptions don't change once completed
  })
}
