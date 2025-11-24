"use client"

import React, { forwardRef, useImperativeHandle, useRef, useState } from 'react'
import YouTube, { YouTubeProps, YouTubePlayer as YouTubePlayerType } from 'react-youtube'
import { Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface YouTubePlayerProps {
  videoId: string
  className?: string
  autoPlay?: boolean
}

export interface VideoPlayerHandle {
  seekTo: (seconds: number) => void
}

export const YouTubePlayer = forwardRef<VideoPlayerHandle, YouTubePlayerProps>(
  ({ videoId, className, autoPlay = false }, ref) => {
    const playerRef = useRef<YouTubePlayerType | null>(null)
    const [isReady, setIsReady] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useImperativeHandle(ref, () => ({
      seekTo: (seconds: number) => {
        if (playerRef.current) {
          playerRef.current.seekTo(seconds, true)
          playerRef.current.playVideo()
        }
      },
    }))

    const onReady: YouTubeProps['onReady'] = (event) => {
      playerRef.current = event.target
      setIsReady(true)
      if (autoPlay) {
        event.target.playVideo()
      }
    }

    const onError: YouTubeProps['onError'] = (event) => {
      const errorMessages: Record<number, string> = {
        2: 'Invalid video ID',
        5: 'HTML5 player error',
        100: 'Video not found or private',
        101: 'Video not allowed to be embedded',
        150: 'Video not allowed to be embedded',
      }
      setError(errorMessages[event.data] || 'Failed to load video')
      setIsReady(true)
    }

    const opts: YouTubeProps['opts'] = {
      height: '100%',
      width: '100%',
      playerVars: {
        autoplay: autoPlay ? 1 : 0,
        modestbranding: 1,
        rel: 0,
      },
    }

    if (error) {
      return (
        <div className={cn(
          'relative w-full bg-destructive/10 border border-destructive rounded-lg overflow-hidden',
          'aspect-video flex items-center justify-center',
          className
        )}>
          <div className="text-center space-y-4 px-4">
            <AlertCircle className="h-12 w-12 mx-auto text-destructive" />
            <div className="space-y-2">
              <p className="text-lg font-medium">Failed to load YouTube video</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        </div>
      )
    }

    return (
      <div className={cn('relative w-full', className)}>
        {!isReady && (
          <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}

        <div className="w-full aspect-video rounded-lg overflow-hidden bg-black">
          <YouTube
            videoId={videoId}
            opts={opts}
            onReady={onReady}
            onError={onError}
            className="w-full h-full"
          />
        </div>
      </div>
    )
  }
)

YouTubePlayer.displayName = 'YouTubePlayer'
