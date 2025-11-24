'use client'

import { Card } from '@/components/ui/card'
import { FileText, Lightbulb, Hash, Quote, Loader2, Trash2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
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
import { Button } from '@/components/ui/button'
import { useDeleteVideo } from '@/hooks/use-videos'
import { useState } from 'react'
import { useToast } from '@/hooks/use-toast'

interface NoteCardProps {
  id: string
  year: string
  source: string
  title: string
  summary: string
  category?: 'theoretical' | 'empirical' | 'recent' | 'other'
  keyPointsCount?: number
  takeawaysCount?: number
  tagsCount?: number
  quotesCount?: number
  status?: 'uploaded' | 'processing' | 'completed' | 'failed'
}

const categoryColors = {
  theoretical: 'bg-red-100 text-red-700',
  empirical: 'bg-blue-100 text-blue-700',
  recent: 'bg-purple-100 text-purple-700',
  other: 'bg-gray-100 text-gray-700',
}

export function NoteCard({
  id,
  year,
  source,
  title,
  summary,
  category = 'other',
  keyPointsCount,
  takeawaysCount,
  tagsCount,
  quotesCount,
  status = 'completed',
}: NoteCardProps) {
  const router = useRouter()
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const deleteVideoMutation = useDeleteVideo()
  const { toast } = useToast()

  const isProcessing = status === 'uploaded' || status === 'processing'
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'

  const handleClick = () => {
    if (isCompleted || isFailed) {
      router.push(`/videos/${id}`)
    }
  }

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    setShowDeleteDialog(true)
  }

  const handleConfirmDelete = async () => {
    try {
      await deleteVideoMutation.mutateAsync(id)
      toast({
        title: 'Video deleted',
        description: 'The video and all associated data have been removed.',
      })
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

  return (
    <TooltipProvider>
      <Card
        onClick={handleClick}
        className={cn(
          'p-4 transition-shadow bg-white border border-gray-200 relative group',
          (isCompleted || isFailed) && 'hover:shadow-lg cursor-pointer',
          isProcessing && 'opacity-60 cursor-default'
        )}
      >
        {/* Delete Button - Top Right */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleDeleteClick}
          className="absolute top-2 right-2 h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50 hover:text-red-600 z-10"
        >
          <Trash2 className="h-4 w-4" />
        </Button>

      {/* Year Badge and Source */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className={cn(
            'px-2 py-1 rounded text-xs font-semibold',
            categoryColors[category]
          )}
        >
          {year}
        </span>
        <span className="text-xs text-gray-500 truncate">{source}</span>
      </div>

      {/* Title */}
      <h3 className="text-lg font-bold text-gray-900 mb-2 line-clamp-2">
        {title}
      </h3>

      {/* Summary */}
      <div className="text-sm text-gray-600 leading-relaxed line-clamp-4 mb-4">
        {isProcessing ? (
          <div className="flex items-center gap-2 text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Processing transcription...</span>
          </div>
        ) : isFailed ? (
          <span className="text-red-600">Transcription failed. Click to view details.</span>
        ) : (
          <p>{summary}</p>
        )}
      </div>

        {/* Footer Metadata */}
        <div className="flex items-center gap-3 text-xs text-gray-500">
          {keyPointsCount !== undefined && keyPointsCount > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 cursor-help">
                  <FileText className="h-3 w-3" />
                  <span>{keyPointsCount}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Key Points</p>
              </TooltipContent>
            </Tooltip>
          )}
          {takeawaysCount !== undefined && takeawaysCount > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 cursor-help">
                  <Lightbulb className="h-3 w-3" />
                  <span>{takeawaysCount}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Takeaways</p>
              </TooltipContent>
            </Tooltip>
          )}
          {tagsCount !== undefined && tagsCount > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 cursor-help">
                  <Hash className="h-3 w-3" />
                  <span>{tagsCount}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Tags</p>
              </TooltipContent>
            </Tooltip>
          )}
          {quotesCount !== undefined && quotesCount > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 cursor-help">
                  <Quote className="h-3 w-3" />
                  <span>{quotesCount}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Quotes</p>
              </TooltipContent>
            </Tooltip>
          )}
          {/* Status indicator */}
          <div className="ml-auto">
            {isProcessing && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Loader2 className="h-3 w-3 animate-spin text-blue-500 cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Processing</p>
                </TooltipContent>
              </Tooltip>
            )}
            {isCompleted && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="h-2 w-2 rounded-full bg-green-500 cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Completed</p>
                </TooltipContent>
              </Tooltip>
            )}
            {isFailed && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="h-2 w-2 rounded-full bg-red-500 cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Failed</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>
      </Card>

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
    </TooltipProvider>
  )
}
