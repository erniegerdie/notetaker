'use client'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { VideoUpload } from '@/components/video-upload'
import { useRouter } from 'next/navigation'

interface UploadSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onUploadSuccess?: () => void
}

export function UploadSheet({
  open,
  onOpenChange,
  onUploadSuccess,
}: UploadSheetProps) {
  const router = useRouter()

  const handleUploadSuccess = (videoId: string) => {
    // Close the dialog
    onOpenChange(false)

    // Call the optional callback
    onUploadSuccess?.()

    // Navigate to the video detail page to show processing progress
    router.push(`/videos/${videoId}`)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add Video</DialogTitle>
          <DialogDescription>
            Upload a video file or submit a YouTube URL to generate a transcription note. Supported formats include MP4, AVI, MOV, and more.
          </DialogDescription>
        </DialogHeader>
        <div className="mt-6">
          <VideoUpload onUploadSuccess={handleUploadSuccess} />
        </div>
      </DialogContent>
    </Dialog>
  )
}
