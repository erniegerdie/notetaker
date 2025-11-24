"use client"

import React, { forwardRef } from 'react'
import { YouTubePlayer, VideoPlayerHandle as YouTubePlayerHandle } from './youtube-player'
import { HlsPlayer, VideoPlayerHandle as HlsPlayerHandle } from './hls-player'

interface VideoPlayerProps {
  sourceType: 'youtube' | 'upload'
  status: 'ready' | 'generating' | 'failed'
  youtubeVideoId?: string
  hlsUrl?: string
  onRetry?: () => void
  className?: string
  autoPlay?: boolean
}

export interface VideoPlayerHandle {
  seekTo: (seconds: number) => void
}

export const VideoPlayer = forwardRef<VideoPlayerHandle, VideoPlayerProps>(
  ({ sourceType, status, youtubeVideoId, hlsUrl, onRetry, className, autoPlay = false }, ref) => {
    if (sourceType === 'youtube' && youtubeVideoId) {
      return (
        <YouTubePlayer
          ref={ref}
          videoId={youtubeVideoId}
          className={className}
          autoPlay={autoPlay}
        />
      )
    }

    if (sourceType === 'upload') {
      return (
        <HlsPlayer
          ref={ref}
          src={hlsUrl}
          status={status}
          onRetry={onRetry}
          className={className}
          autoPlay={autoPlay}
        />
      )
    }

    return null
  }
)

VideoPlayer.displayName = 'VideoPlayer'
