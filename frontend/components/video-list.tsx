'use client'

import { useVideoList } from '@/hooks/use-video-list'
import { VideoCard } from '@/components/video-card'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import { FileVideo } from 'lucide-react'

export function VideoList() {
  const { data, isLoading, error } = useVideoList()

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <Skeleton className="h-14 w-14 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="p-6">
          <p className="text-destructive">Error loading videos: {error.message}</p>
        </CardContent>
      </Card>
    )
  }

  if (!data?.videos.length) {
    return (
      <Card className="border-dashed">
        <CardContent className="p-12 text-center">
          <FileVideo className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No videos yet</h3>
          <p className="text-muted-foreground">
            Upload your first video to get started
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {data.videos.map((video) => (
        <VideoCard key={video.id} video={video} />
      ))}
    </div>
  )
}
