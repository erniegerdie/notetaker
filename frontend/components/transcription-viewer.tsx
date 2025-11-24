'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Copy, Download, Check, Clock } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { formatDate, formatBytes } from '@/lib/utils'
import type { Transcription } from '@/lib/types'
import { useState } from 'react'

interface TranscriptionViewerProps {
  transcription: Transcription
  filename: string
  onTimestampClick?: (seconds: number) => void
}

function formatTimestamp(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`
}

export function TranscriptionViewer({ transcription, filename, onTimestampClick }: TranscriptionViewerProps) {
  const { toast } = useToast()
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(transcription.transcript_text)
      setCopied(true)
      toast({ title: 'Copied to clipboard' })
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      toast({
        title: 'Failed to copy',
        description: 'Please try again',
        variant: 'destructive',
      })
    }
  }

  const handleDownload = () => {
    try {
      const blob = new Blob([transcription.transcript_text], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${filename.replace(/\.[^/.]+$/, '')}_transcript.txt`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast({ title: 'Transcription downloaded' })
    } catch (error) {
      toast({
        title: 'Download failed',
        description: 'Please try again',
        variant: 'destructive',
      })
    }
  }

  const hasSegments = transcription.transcript_segments && transcription.transcript_segments.length > 0

  // Group segments into paragraphs (approximately every 5-8 segments or when there's a longer pause)
  const groupIntoParagraphs = (segments: typeof transcription.transcript_segments) => {
    if (!segments) return []

    const paragraphs: Array<{ startTime: number; segments: typeof segments }> = []
    let currentParagraph: typeof segments = []
    let paragraphStartTime = 0

    segments.forEach((segment, index) => {
      if (currentParagraph.length === 0) {
        paragraphStartTime = segment.start
      }

      currentParagraph.push(segment)

      // Start new paragraph if:
      // 1. We have 5-8 segments already, OR
      // 2. There's a pause longer than 2 seconds before next segment, OR
      // 3. This is the last segment
      const nextSegment = segments[index + 1]
      const shouldBreak =
        currentParagraph.length >= 6 ||
        (nextSegment && (nextSegment.start - segment.end) > 2) ||
        index === segments.length - 1

      if (shouldBreak) {
        paragraphs.push({
          startTime: paragraphStartTime,
          segments: [...currentParagraph]
        })
        currentParagraph = []
      }
    })

    return paragraphs
  }

  const paragraphs = hasSegments ? groupIntoParagraphs(transcription.transcript_segments!) : []

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>Transcription</CardTitle>
            <p className="text-sm text-muted-foreground mt-2">
              Model: {transcription.model_used} • Processing time: {transcription.processing_time}
              {transcription.audio_size && ` • Audio: ${formatBytes(transcription.audio_size)}`} • {formatDate(transcription.created_at)}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleCopy}>
              {copied ? (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy
                </>
              )}
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="mr-2 h-4 w-4" />
              Download
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-lg bg-muted p-6">
          {hasSegments ? (
            <div className="space-y-4">
              {paragraphs.map((paragraph, pIndex) => (
                <div key={pIndex} className="grid grid-cols-[auto,1fr] gap-4 group">
                  <button
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono text-cyan-600 hover:text-cyan-700 hover:bg-cyan-50 transition-colors h-fit"
                    onClick={() => {
                      if (onTimestampClick) {
                        onTimestampClick(paragraph.startTime)
                      } else {
                        toast({
                          title: 'Video player not ready',
                          description: 'Please wait for the video to load',
                        })
                      }
                    }}
                  >
                    <Clock className="w-3 h-3" />
                    {formatTimestamp(paragraph.startTime)}
                  </button>
                  <p className="text-sm leading-relaxed text-gray-900">
                    {paragraph.segments.map(seg => seg.text).join(' ')}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="prose prose-sm max-w-none">
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {transcription.transcript_text}
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
