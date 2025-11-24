import Link from 'next/link'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { StatusBadge } from '@/components/status-badge'
import { FileVideo } from 'lucide-react'
import { formatDate, formatBytes } from '@/lib/utils'
import type { Video } from '@/lib/types'

interface VideoCardProps {
  video: Video
}

export function VideoCard({ video }: VideoCardProps) {
  return (
    <Link href={`/videos/${video.id}`}>
      <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="rounded-lg bg-primary/10 p-3">
              <FileVideo className="h-8 w-8 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold truncate mb-1">{video.filename}</h3>
              <p className="text-sm text-muted-foreground">
                {formatBytes(video.file_size)}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                {formatDate(video.uploaded_at)}
              </p>
            </div>
          </div>
        </CardContent>
        <CardFooter className="px-6 pb-6 pt-0">
          <StatusBadge status={video.status} />
        </CardFooter>
      </Card>
    </Link>
  )
}
