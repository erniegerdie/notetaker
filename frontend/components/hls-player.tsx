"use client"

import React, { forwardRef, useImperativeHandle, useRef, useEffect, useState } from 'react'
import Hls from 'hls.js'
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface HlsPlayerProps {
  src: string | undefined
  status: 'ready' | 'generating' | 'failed'
  onRetry?: () => void
  className?: string
  autoPlay?: boolean
  poster?: string
}

export interface VideoPlayerHandle {
  seekTo: (seconds: number) => void
}

export const HlsPlayer = forwardRef<VideoPlayerHandle, HlsPlayerProps>(({
  src,
  status,
  onRetry,
  className,
  autoPlay = false,
  poster
}, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useImperativeHandle(ref, () => ({
    seekTo: (seconds: number) => {
      if (videoRef.current) {
        videoRef.current.currentTime = seconds
        videoRef.current.play().catch(err => {
          console.error('Play failed after seek:', err)
        })
      }
    },
  }))

  useEffect(() => {
    const video = videoRef.current
    if (!video || !src || status !== 'ready') return

    setIsLoading(true)
    setError(null)

    // Detect if this is a direct video file (MP4) or HLS playlist (.m3u8)
    const isHlsPlaylist = src.includes('.m3u8')
    const isDirectVideo = !isHlsPlaylist

    console.log('Video player loading:', { src, isHlsPlaylist, isDirectVideo })

    // Direct MP4/video file - use native video element
    if (isDirectVideo) {
      console.log('Using native video playback for MP4')

      const handleLoadedMetadata = () => {
        console.log('Video metadata loaded')
        setIsLoading(false)
      }

      const handleError = (e: Event) => {
        console.error('Video error:', e)
        setError('Failed to load video')
        setIsLoading(false)
      }

      const handleCanPlay = () => {
        console.log('Video can play')
        setIsLoading(false)
      }

      video.addEventListener('loadedmetadata', handleLoadedMetadata)
      video.addEventListener('error', handleError)
      video.addEventListener('canplay', handleCanPlay)

      video.src = src
      video.load()

      return () => {
        video.removeEventListener('loadedmetadata', handleLoadedMetadata)
        video.removeEventListener('error', handleError)
        video.removeEventListener('canplay', handleCanPlay)
      }
    }

    // HLS playlist - use HLS.js or native HLS support
    // Check if browser supports native HLS (Safari)
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      console.log('Using native HLS playback (Safari)')
      video.src = src
      video.addEventListener('loadedmetadata', () => {
        setIsLoading(false)
      })
      video.addEventListener('error', () => {
        setError('Failed to load video')
        setIsLoading(false)
      })
    }
    // Use hls.js for other browsers
    else if (Hls.isSupported()) {
      console.log('Using HLS.js for HLS playback')
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
        backBufferLength: 90,
        xhrSetup: (xhr) => {
          // Enable CORS credentials if needed
          xhr.withCredentials = false
        }
      })

      hlsRef.current = hls

      hls.loadSource(src)
      hls.attachMedia(video)

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        console.log('HLS manifest parsed')
        setIsLoading(false)
        if (autoPlay) {
          video.play().catch(err => {
            console.error('Autoplay failed:', err)
          })
        }
      })

      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS error:', data)
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              setError('Network error - failed to load video')
              hls.startLoad()
              break
            case Hls.ErrorTypes.MEDIA_ERROR:
              setError('Media error - trying to recover')
              hls.recoverMediaError()
              break
            default:
              setError('Fatal error loading video')
              hls.destroy()
              setIsLoading(false)
              break
          }
        }
      })

      return () => {
        hls.destroy()
        hlsRef.current = null
      }
    } else {
      setError('HLS is not supported in your browser')
      setIsLoading(false)
    }
  }, [src, status, autoPlay])

  if (status === 'generating') {
    return (
      <div className={cn(
        'relative w-full bg-muted rounded-lg overflow-hidden',
        'aspect-video flex items-center justify-center',
        className
      )}>
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
          <div className="space-y-2">
            <p className="text-lg font-medium">Preparing video for streaming</p>
            <p className="text-sm text-muted-foreground">
              This may take a minute for the first view...
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (status === 'failed') {
    return (
      <div className={cn(
        'relative w-full bg-destructive/10 border border-destructive rounded-lg overflow-hidden',
        'aspect-video flex items-center justify-center',
        className
      )}>
        <div className="text-center space-y-4 px-4">
          <AlertCircle className="h-12 w-12 mx-auto text-destructive" />
          <div className="space-y-2">
            <p className="text-lg font-medium">Failed to prepare video</p>
            <p className="text-sm text-muted-foreground">
              Video streaming preparation failed
            </p>
          </div>
          {onRetry && (
            <Button onClick={onRetry} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={cn('relative w-full', className)}>
      {isLoading && (
        <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}

      {error && (
        <div className="absolute top-4 left-4 right-4 bg-destructive/90 text-destructive-foreground px-4 py-2 rounded-md z-20 flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{error}</span>
          {onRetry && (
            <Button
              onClick={onRetry}
              variant="secondary"
              size="sm"
              className="ml-auto"
            >
              Retry
            </Button>
          )}
        </div>
      )}

      <video
        ref={videoRef}
        controls
        poster={poster}
        className="w-full aspect-video rounded-lg bg-black"
        playsInline
      />
    </div>
  )
})

HlsPlayer.displayName = 'HlsPlayer'
