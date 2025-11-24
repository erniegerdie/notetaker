import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Collection {
  id: string
  name: string
  description?: string
}

export interface CreateCollectionData {
  name: string
  description?: string
}

export function useCollections() {
  return useQuery<Collection[]>({
    queryKey: ['collections'],
    queryFn: async () => {
      const { data } = await api.get('/api/collections')
      return data
    },
  })
}

export function useCreateCollection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (collectionData: CreateCollectionData) => {
      const { data } = await api.post('/api/collections', collectionData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export function useDeleteCollection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (collectionId: string) => {
      await api.delete(`/api/collections/${collectionId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}
