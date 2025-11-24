'use client'

import { use, useState, useRef } from 'react'
import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import { TopNav } from '@/components/top-nav'
import { UploadSheet } from '@/components/upload-sheet'
import { useVideoStatus } from '@/hooks/use-video-status'
import { useTranscription } from '@/hooks/use-transcription'
import { useUpdateVideo, useDeleteVideo } from '@/hooks/use-videos'
import { useVideoStream } from '@/hooks/use-video-stream'
import { VideoPlayer, VideoPlayerHandle } from '@/components/video-player'
import { TranscriptionViewer } from '@/components/transcription-viewer'
import { StatusBadge } from '@/components/status-badge'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowLeft, FileVideo, Loader2, BarChart3, FileText, MessageSquare, Copy, Download, Hash, Pencil, Check, X, Lightbulb, TrendingUp, Activity, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { formatDate, formatBytes } from '@/lib/utils'
import type { GeneratedNote } from '@/lib/types'
import { useQueryClient } from '@tanstack/react-query'
import { CollapsibleSection } from '@/components/collapsible-section'
import { SentimentTimeline } from '@/components/sentiment-timeline'
import { ThemesVisualization } from '@/components/themes-visualization'
import { ActionableInsights } from '@/components/actionable-insights'
import { StickyToc, createTocSections } from '@/components/sticky-toc'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useToast } from '@/hooks/use-toast'
import { useRouter } from 'next/navigation'

interface VideoPageProps {
  params: Promise<{ id: string }>
}

function formatNotesAsMarkdown(notes: GeneratedNote): string {
  let markdown = ''

  if (notes.summary) {
    markdown += `# Summary\n\n${notes.summary}\n\n`
  }

  if (notes.key_points && notes.key_points.length > 0) {
    markdown += `## Key Points\n\n`
    notes.key_points.forEach(point => {
      markdown += `- ${point}\n`
    })
    markdown += '\n'
  }

  if (notes.detailed_notes) {
    markdown += `## Detailed Notes\n\n${notes.detailed_notes}\n\n`
  }

  if (notes.takeaways && notes.takeaways.length > 0) {
    markdown += `## Takeaways\n\n`
    notes.takeaways.forEach(takeaway => {
      markdown += `- ${takeaway}\n`
    })
    markdown += '\n'
  }

  if (notes.tags && notes.tags.length > 0) {
    markdown += `## Tags\n\n`
    notes.tags.forEach(tag => {
      markdown += `- ${tag}\n`
    })
    markdown += '\n'
  }

  if (notes.quotes && notes.quotes.length > 0) {
    markdown += `## Notable Quotes\n\n`
    notes.quotes.forEach(quote => {
      markdown += `> ${quote}\n\n`
    })
  }

  if (notes.questions && notes.questions.length > 0) {
    markdown += `## Questions Raised\n\n`
    notes.questions.forEach(question => {
      markdown += `- ${question}\n`
    })
    markdown += '\n'
  }

  if (notes.participants && notes.participants.length > 0) {
    markdown += `## Participants\n\n`
    notes.participants.forEach(participant => {
      markdown += `- ${participant}\n`
    })
    markdown += '\n'
  }

  return markdown
}

function formatNotesAsText(notes: GeneratedNote): string {
  return formatNotesAsMarkdown(notes)
}

export default function VideoPage({ params }: VideoPageProps) {
  const { id } = use(params)
  const [uploadSheetOpen, setUploadSheetOpen] = useState(false)
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editedTitle, setEditedTitle] = useState('')
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const router = useRouter()
  const queryClient = useQueryClient()
  const playerRef = useRef<VideoPlayerHandle>(null)

  const { data: videoStatus, isLoading: statusLoading, error: statusError } = useVideoStatus(id)
  const {
    data: transcription,
    isLoading: transcriptionLoading,
    error: transcriptionError
  } = useTranscription(id, videoStatus?.status === 'completed')

  // HLS streaming hook - only enabled when video is completed
  const {
    data: streamData,
    isLoading: streamLoading,
    refetch: refetchStream
  } = useVideoStream(id, videoStatus?.status === 'completed')

  const updateVideoMutation = useUpdateVideo()
  const deleteVideoMutation = useDeleteVideo()
  const { toast } = useToast()

  const handleUploadSuccess = () => {
    setUploadSheetOpen(false)
    queryClient.invalidateQueries({ queryKey: ['videos'] })
  }

  const getDisplayTitle = () => {
    if (videoStatus?.title) return videoStatus.title
    return `Weekly Team Standup - ${formatDate(videoStatus?.uploaded_at || '')}`
  }

  const handleStartEdit = () => {
    setEditedTitle(getDisplayTitle())
    setIsEditingTitle(true)
  }

  const handleSaveTitle = async () => {
    try {
      await updateVideoMutation.mutateAsync({
        videoId: id,
        title: editedTitle
      })
      setIsEditingTitle(false)
    } catch (error) {
      console.error('Failed to update title:', error)
    }
  }

  const handleCancelEdit = () => {
    setIsEditingTitle(false)
    setEditedTitle('')
  }

  const handleTimestampClick = (seconds: number) => {
    playerRef.current?.seekTo(seconds)
    // Optional: scroll to player
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleDeleteClick = () => {
    setShowDeleteDialog(true)
  }

  const handleConfirmDelete = async () => {
    try {
      await deleteVideoMutation.mutateAsync(id)
      toast({
        title: 'Video deleted',
        description: 'The video and all associated data have been removed.',
      })
      router.push('/') 
    } catch (error) {
      toast({
        title: 'Delete failed',
        description: error instanceof Error ? error.message : 'Failed to delete video',
        variant: 'destructive',
      })
    } finally {
      setShowDeleteDialog(false)
    }
  }

  if (statusLoading) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
        <div className="container mx-auto px-4 py-12">
          <Skeleton className="h-10 w-32 mb-8" />
          <Skeleton className="h-64 w-full" />
        </div>
      </main>
    )
  }

  if (statusError || !videoStatus) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
        <div className="container mx-auto px-4 py-12">
          <Link href="/">
            <Button variant="ghost" className="mb-8">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Videos
            </Button>
          </Link>
          <Card className="border-destructive">
            <CardContent className="p-6">
              <p className="text-destructive">Error: {statusError?.message || 'Video not found'}</p>
            </CardContent>
          </Card>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <TopNav
        onCreateNew={() => setUploadSheetOpen(true)}
        showSearch={true}
      />

      <div className="container mx-auto px-8 py-8">
        {/* Title */}
        <div className="mb-8">
          {isEditingTitle ? (
            <div className="flex items-center gap-2 mb-3">
              <input
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                className="flex-1 text-3xl font-bold text-gray-900 border-b-2 border-blue-600 focus:outline-none bg-transparent"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSaveTitle()
                  if (e.key === 'Escape') handleCancelEdit()
                }}
              />
              <Button
                size="sm"
                variant="ghost"
                onClick={handleSaveTitle}
                className="h-8 w-8 p-0 hover:bg-green-100"
              >
                <Check className="h-4 w-4 text-green-600" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleCancelEdit}
                className="h-8 w-8 p-0 hover:bg-red-100"
              >
                <X className="h-4 w-4 text-red-600" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 mb-3 group">
              <h1 className="text-3xl font-bold text-gray-900">
                {getDisplayTitle()}
              </h1>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleStartEdit}
                className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 p-0 hover:bg-gray-100"
              >
                <Pencil className="h-4 w-4 text-gray-500" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDeleteClick}
                className="opacity-0 group-hover:opacity-100 transition-opacity h-8 w-8 p-0 hover:bg-red-50 hover:text-red-600"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}
          {/* Tag Badges */}
          {transcription?.notes?.tags && transcription.notes.tags.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              {transcription.notes.tags.map((tag, index) => (
                <Badge key={index} variant="secondary" className="bg-gray-100 text-gray-700 hover:bg-gray-200">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>

        {videoStatus.error_message && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700 font-medium">Error:</p>
            <p className="text-sm text-red-600 mt-1">{videoStatus.error_message}</p>
          </div>
        )}

        {/* Processing State */}
        {(videoStatus.status === 'uploaded' || videoStatus.status === 'processing') && (
          <Card>
            <CardContent className="p-12 text-center">
              <Loader2 className="h-12 w-12 text-primary animate-spin mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Processing Video</h3>
              <p className="text-muted-foreground">
                Your video is being transcribed. This may take a few minutes.
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Status: {videoStatus.status === 'uploaded' ? 'Queued' : 'Processing...'}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Failed State */}
        {videoStatus.status === 'failed' && !videoStatus.error_message && (
          <Card className="border-destructive">
            <CardContent className="p-12 text-center">
              <div className="rounded-full bg-destructive/10 h-16 w-16 flex items-center justify-center mx-auto mb-4">
                <FileVideo className="h-8 w-8 text-destructive" />
              </div>
              <h3 className="text-lg font-semibold mb-2">Processing Failed</h3>
              <p className="text-muted-foreground">
                We encountered an error while processing your video.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Video Player */}
        {videoStatus.status === 'completed' && streamData && (
          <div className="mb-8">
            <VideoPlayer
              ref={playerRef}
              sourceType={streamData.source_type}
              status={streamData.status}
              youtubeVideoId={streamData.youtube_video_id || undefined}
              hlsUrl={streamData.hls_url || undefined}
              onRetry={() => refetchStream()}
              className="w-full max-w-5xl mx-auto"
            />
          </div>
        )}

        {/* Tabs with Content */}
        {videoStatus.status === 'completed' && (
          <Tabs defaultValue="notes" className="w-full -mx-8">
            {/* Secondary Navigation - Tab Bar */}
            <div className="bg-white border-b sticky top-[73px] z-30">
              <div className="container mx-auto px-8 max-w-6xl">
                <TabsList className="grid w-full grid-cols-3 bg-transparent border-none rounded-none h-auto p-0">
                  <TabsTrigger
                    value="notes"
                    className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-gray-900 rounded-none py-3 font-medium"
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    Notes
                  </TabsTrigger>
                  <TabsTrigger
                    value="transcription"
                    className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-gray-900 rounded-none py-3 font-medium"
                  >
                    <MessageSquare className="mr-2 h-4 w-4" />
                    Transcription
                  </TabsTrigger>
                  <TabsTrigger
                    value="stats"
                    className="data-[state=active]:bg-transparent data-[state=active]:border-b-2 data-[state=active]:border-gray-900 rounded-none py-3 font-medium"
                  >
                    <BarChart3 className="mr-2 h-4 w-4" />
                    Stats
                  </TabsTrigger>
                </TabsList>
              </div>
            </div>

            {/* Tab Content Area */}
            <div className="px-8 py-8">
              <TabsContent value="notes" className="mt-0">
                {transcriptionLoading && (
                  <div className="space-y-4">
                    <Skeleton className="h-32 w-full" />
                    <Skeleton className="h-64 w-full" />
                  </div>
                )}
                {transcriptionError && (
                  <Card className="border-red-200 bg-red-50">
                    <CardContent className="p-6">
                      <p className="text-red-700">
                        Failed to load notes: {transcriptionError.message}
                      </p>
                    </CardContent>
                  </Card>
                )}
                {transcription && transcription.notes && (
                  <div className="flex gap-8">
                    {/* Sticky TOC - Desktop only */}
                    <div className="hidden lg:block w-64 flex-shrink-0">
                      <StickyToc
                        sections={createTocSections(
                          !!transcription.notes.themes,
                          !!transcription.notes.sentiment_timeline,
                          !!transcription.notes.actionable_insights
                        )}
                      />
                    </div>

                    {/* Main Content */}
                    <div className="flex-1 space-y-6">
                      {/* Stats Cards */}
                      <div className="grid grid-cols-3 gap-4">
                        <Card className="border border-gray-200">
                          <CardContent className="p-6">
                            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                              <svg className="w-5 h-5 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <circle cx="12" cy="12" r="10" strokeWidth="2"/>
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6l4 2"/>
                              </svg>
                              <span>Duration</span>
                            </div>
                            <div className="text-3xl font-bold">
                              {videoStatus.duration_seconds
                                ? (() => {
                                    const hours = Math.floor(videoStatus.duration_seconds / 3600)
                                    const minutes = Math.floor((videoStatus.duration_seconds % 3600) / 60)
                                    const seconds = videoStatus.duration_seconds % 60
                                    return hours > 0
                                      ? `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
                                      : `${minutes}:${String(seconds).padStart(2, '0')}`
                                  })()
                                : '--:--'}
                            </div>
                          </CardContent>
                        </Card>
                        <Card className="border border-gray-200">
                          <CardContent className="p-6">
                            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                              <svg className="w-5 h-5 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                              </svg>
                              <span>Words</span>
                            </div>
                            <div className="text-3xl font-bold">
                              {transcription?.transcript_text?.split(/\s+/).length.toLocaleString() || '0'}
                            </div>
                          </CardContent>
                        </Card>
                        <Card className="border border-gray-200">
                          <CardContent className="p-6">
                            <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                              <svg className="w-5 h-5 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                              </svg>
                              <span>Key Points</span>
                            </div>
                            <div className="text-3xl font-bold">
                              {transcription.notes.key_points?.length || 0}
                            </div>
                          </CardContent>
                        </Card>
                      </div>

                      {/* Summary */}
                      {transcription.notes.summary && (
                        <CollapsibleSection id="summary" title="Summary" icon={<FileText className="w-5 h-5 text-gray-500" />}>
                          <p className="text-gray-700 leading-relaxed">
                            {transcription.notes.summary}
                          </p>
                        </CollapsibleSection>
                      )}

                      {/* Key Points */}
                      {transcription.notes.key_points && transcription.notes.key_points.length > 0 && (
                        <CollapsibleSection id="key-points" title="Key Points" icon={<Hash className="w-5 h-5 text-gray-500" />}>
                          <ul className="space-y-2">
                            {transcription.notes.key_points.map((point, index) => {
                              const colors = ['text-cyan-500', 'text-green-500', 'text-orange-500', 'text-pink-500']
                              const bulletColor = colors[index % colors.length]
                              const content = typeof point === 'string' ? point : point.content
                              const timestamp = typeof point === 'object' && point.timestamp_seconds
                              return (
                                <li key={index} className="flex gap-2">
                                  <span className={`flex-shrink-0 ${bulletColor} text-lg leading-6`}>•</span>
                                  <span className="text-gray-900 leading-relaxed flex-1">
                                    {content}
                                    {timestamp && (
                                      <button
                                        onClick={() => handleTimestampClick(timestamp)}
                                        className="ml-2 text-sm text-cyan-600 hover:text-cyan-700 hover:underline cursor-pointer"
                                      >
                                        [{Math.floor(timestamp / 60)}:{String(Math.floor(timestamp % 60)).padStart(2, '0')}]
                                      </button>
                                    )}
                                  </span>
                                </li>
                              )
                            })}
                          </ul>
                        </CollapsibleSection>
                      )}

                      {/* Detailed Notes */}
                      {transcription.notes.detailed_notes && (
                        <CollapsibleSection id="detailed-notes" title="Detailed Notes" icon={<MessageSquare className="w-5 h-5 text-gray-500" />}>
                          <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                            {transcription.notes.detailed_notes}
                          </div>
                        </CollapsibleSection>
                      )}

                      {/* Takeaways */}
                      {transcription.notes.takeaways && transcription.notes.takeaways.length > 0 && (
                        <CollapsibleSection id="takeaways" title="Takeaways" icon={<Lightbulb className="w-5 h-5 text-gray-500" />}>
                          <ul className="space-y-2">
                            {transcription.notes.takeaways.map((takeaway, index) => {
                              const content = typeof takeaway === 'string' ? takeaway : takeaway.content
                              const timestamp = typeof takeaway === 'object' && takeaway.timestamp_seconds
                              return (
                                <li key={index} className="flex gap-2 text-gray-900">
                                  <span className="text-cyan-500 text-lg leading-6">•</span>
                                  <span className="leading-relaxed">
                                    {content}
                                    {timestamp && (
                                      <button
                                        onClick={() => handleTimestampClick(timestamp)}
                                        className="ml-2 text-sm text-cyan-600 hover:text-cyan-700 hover:underline cursor-pointer"
                                      >
                                        [{Math.floor(timestamp / 60)}:{String(Math.floor(timestamp % 60)).padStart(2, '0')}]
                                      </button>
                                    )}
                                  </span>
                                </li>
                              )
                            })}
                          </ul>
                        </CollapsibleSection>
                      )}

                      {/* Themes & Patterns */}
                      {transcription.notes.themes && transcription.notes.themes.length > 0 && (
                        <CollapsibleSection id="themes" title="Themes & Patterns" icon={<TrendingUp className="w-5 h-5 text-gray-500" />}>
                          <ThemesVisualization themes={transcription.notes.themes} />
                        </CollapsibleSection>
                      )}

                      {/* Sentiment Timeline */}
                      {transcription.notes.sentiment_timeline && transcription.notes.sentiment_timeline.length > 0 && (
                        <CollapsibleSection id="sentiment" title="Sentiment Timeline" icon={<Activity className="w-5 h-5 text-gray-500" />}>
                          <SentimentTimeline timeline={transcription.notes.sentiment_timeline} />
                        </CollapsibleSection>
                      )}

                      {/* Actionable Insights */}
                      {transcription.notes.actionable_insights && transcription.notes.actionable_insights.length > 0 && (
                        <CollapsibleSection id="insights" title="Actionable Insights" icon={<Lightbulb className="w-5 h-5 text-gray-500" />}>
                          <ActionableInsights insights={transcription.notes.actionable_insights} />
                        </CollapsibleSection>
                      )}

                      {/* Important Quotes */}
                      {transcription.notes.quotes && transcription.notes.quotes.length > 0 && (
                        <CollapsibleSection id="quotes" title="Important Quotes" icon={<MessageSquare className="w-5 h-5 text-gray-500" />}>
                          <div className="space-y-3">
                            {transcription.notes.quotes.map((quote, index) => {
                              const content = typeof quote === 'string' ? quote : quote.content
                              const timestamp = typeof quote === 'object' && quote.timestamp_seconds
                              return (
                                <div key={index} className="border-l-4 border-cyan-500 pl-4 py-1">
                                  <p className="text-gray-700 italic leading-relaxed">
                                    &ldquo;{content}&rdquo;
                                    {timestamp && (
                                      <button
                                        onClick={() => handleTimestampClick(timestamp)}
                                        className="ml-2 text-sm text-cyan-600 hover:text-cyan-700 hover:underline cursor-pointer not-italic"
                                      >
                                        [{Math.floor(timestamp / 60)}:{String(Math.floor(timestamp % 60)).padStart(2, '0')}]
                                      </button>
                                    )}
                                  </p>
                                </div>
                              )
                            })}
                          </div>
                        </CollapsibleSection>
                      )}

                      {/* Questions */}
                      {transcription.notes.questions && transcription.notes.questions.length > 0 && (
                        <CollapsibleSection id="questions" title="Questions Raised" icon={<MessageSquare className="w-5 h-5 text-gray-500" />}>
                          <ul className="space-y-2">
                            {transcription.notes.questions.map((question, index) => (
                              <li key={index} className="flex gap-2 text-gray-900">
                                <span className="text-cyan-500 text-lg leading-6">•</span>
                                <span className="leading-relaxed">{question}</span>
                              </li>
                            ))}
                          </ul>
                        </CollapsibleSection>
                      )}
                    </div>
                  </div>
                )}
                {transcription && !transcription.notes && (
                  <Card>
                    <CardContent className="p-12 text-center">
                      <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold mb-2">Notes Not Generated</h3>
                      <p className="text-gray-500">
                        AI-generated notes are not available for this video yet.
                      </p>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              <TabsContent value="stats" className="mt-0">
                {transcriptionLoading && (
                  <Card>
                  <CardContent className="p-6">
                    <Skeleton className="h-64 w-full" />
                  </CardContent>
                </Card>
              )}
              {transcriptionError && (
                <Card className="border-destructive">
                  <CardContent className="p-6">
                    <p className="text-destructive">
                      Failed to load stats: {transcriptionError.message}
                    </p>
                  </CardContent>
                </Card>
              )}
              {transcription && (
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold mb-4">Processing Statistics</h3>
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Model Used</p>
                        <p className="text-lg font-medium">{transcription.model_used}</p>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Processing Time</p>
                        <p className="text-lg font-medium">{transcription.processing_time}</p>
                      </div>
                      {transcription.audio_size && (
                        <div className="space-y-2">
                          <p className="text-sm text-muted-foreground">Audio Size</p>
                          <p className="text-lg font-medium">{formatBytes(transcription.audio_size)}</p>
                        </div>
                      )}
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Completed At</p>
                        <p className="text-lg font-medium">{formatDate(transcription.created_at)}</p>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Transcript Length</p>
                        <p className="text-lg font-medium">{transcription?.transcript_text?.length.toLocaleString() || 0} characters</p>
                      </div>
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">Word Count</p>
                        <p className="text-lg font-medium">{transcription?.transcript_text?.split(/\s+/).length.toLocaleString() || 0} words</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
              </TabsContent>

              <TabsContent value="transcription" className="mt-0">
              {transcriptionLoading && (
                <Card>
                  <CardContent className="p-6">
                    <Skeleton className="h-8 w-48 mb-4" />
                    <Skeleton className="h-64 w-full" />
                  </CardContent>
                </Card>
              )}
              {transcriptionError && (
                <Card className="border-destructive">
                  <CardContent className="p-6">
                    <p className="text-destructive">
                      Failed to load transcription: {transcriptionError.message}
                    </p>
                  </CardContent>
                </Card>
              )}
              {transcription && (
                <TranscriptionViewer
                  transcription={transcription}
                  filename={`video_${id}`}
                  onTimestampClick={handleTimestampClick}
                />
              )}
              </TabsContent>
            </div>
          </Tabs>
        )}
      </div>

      {/* Upload Sheet */}
      <UploadSheet
        open={uploadSheetOpen}
        onOpenChange={setUploadSheetOpen}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Video</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this video? This will permanently remove the video file,
              transcription, and all associated notes. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteVideoMutation.isPending}
            >
              {deleteVideoMutation.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  )
}
