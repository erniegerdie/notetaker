'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileVideo, X, Link as LinkIcon, CheckCircle2, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useVideoUpload } from '@/hooks/use-video-upload'
import { useYoutubeSubmit } from '@/hooks/use-youtube-submit'
import { useToast } from '@/hooks/use-toast'
import { ALLOWED_VIDEO_FORMATS, MAX_FILE_SIZE_MB, VIDEO_MIME_TYPES } from '@/lib/constants'
import { formatBytes } from '@/lib/utils'
import { cn } from '@/lib/utils'
import { validateYoutubeUrl } from '@/lib/validators'

interface VideoUploadProps {
  onUploadSuccess?: (videoId: string) => void
}

export function VideoUpload({ onUploadSuccess }: VideoUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [activeTab, setActiveTab] = useState<'file' | 'youtube'>('file')

  const { mutate: uploadVideo, isPending: isUploading, uploadProgress } = useVideoUpload()
  const { mutate: submitYoutube, isPending: isSubmittingYoutube } = useYoutubeSubmit()
  const { toast } = useToast()

  const urlValidation = validateYoutubeUrl(youtubeUrl)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0]
      let errorMessage = 'Invalid file'

      if (rejection.errors?.[0]?.code === 'file-too-large') {
        errorMessage = `File size must be less than ${MAX_FILE_SIZE_MB}MB`
      } else if (rejection.errors?.[0]?.code === 'file-invalid-type') {
        errorMessage = `File type must be one of: ${ALLOWED_VIDEO_FORMATS.join(', ')}`
      }

      toast({
        title: 'Upload failed',
        description: errorMessage,
        variant: 'destructive',
      })
      return
    }

    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
    }
  }, [toast])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: VIDEO_MIME_TYPES,
    maxSize: MAX_FILE_SIZE_MB * 1024 * 1024,
    multiple: false,
    disabled: isUploading,
  })

  const handleFileUpload = () => {
    if (!selectedFile) return

    console.log('Starting video upload:', selectedFile.name)

    uploadVideo(selectedFile, {
      onSuccess: (data) => {
        console.log('Upload successful! Video ID:', data.id)
        toast({
          title: 'Upload successful',
          description: `${selectedFile.name} is being processed`,
        })
        onUploadSuccess?.(data.id)
        setSelectedFile(null)
      },
      onError: (error) => {
        console.error('Upload failed:', error)
        toast({
          title: 'Upload failed',
          description: error.message,
          variant: 'destructive',
        })
      },
    })
  }

  const handleYoutubeSubmit = () => {
    if (!urlValidation.valid) return

    submitYoutube(
      { url: youtubeUrl },
      {
        onSuccess: (data) => {
          toast({
            title: 'YouTube video submitted',
            description: data.title || 'Video is being downloaded and processed',
          })
          onUploadSuccess?.(data.id)
          setYoutubeUrl('')
        },
        onError: (error) => {
          toast({
            title: 'YouTube submission failed',
            description: error.message,
            variant: 'destructive',
          })
        },
      }
    )
  }

  const handleClearFile = () => {
    setSelectedFile(null)
  }

  return (
    <Card>
      <CardContent className="p-6">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'file' | 'youtube')}>
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="file">
              <Upload className="h-4 w-4 mr-2" />
              Upload File
            </TabsTrigger>
            <TabsTrigger value="youtube">
              <LinkIcon className="h-4 w-4 mr-2" />
              YouTube URL
            </TabsTrigger>
          </TabsList>

          {/* File Upload Tab */}
          <TabsContent value="file" className="mt-0">
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors',
                isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50',
                isUploading && 'opacity-50 cursor-not-allowed'
              )}
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center gap-2">
                <Upload className="h-12 w-12 text-muted-foreground" />
                <div>
                  <p className="text-lg font-medium">
                    {isDragActive ? 'Drop video here' : 'Drag & drop video here'}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    or click to browse files
                  </p>
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Supported formats: {ALLOWED_VIDEO_FORMATS.join(', ')} • Max size: {MAX_FILE_SIZE_MB}MB
                </p>
              </div>
            </div>

            {selectedFile && (
              <div className="mt-4">
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileVideo className="h-8 w-8 text-primary" />
                    <div>
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatBytes(selectedFile.size)}
                      </p>
                    </div>
                  </div>
                  {!isUploading && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={handleClearFile}
                      className="h-8 w-8"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {isUploading && (
                  <div className="mt-4 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Uploading...</span>
                      <span className="font-medium">{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} />
                  </div>
                )}

                {!isUploading && (
                  <Button
                    onClick={handleFileUpload}
                    className="w-full mt-4"
                    size="lg"
                  >
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Video
                  </Button>
                )}
              </div>
            )}
          </TabsContent>

          {/* YouTube URL Tab */}
          <TabsContent value="youtube" className="mt-0">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="youtube-url">YouTube URL or Video ID</Label>
                <div className="relative">
                  <Input
                    id="youtube-url"
                    type="text"
                    placeholder="https://www.youtube.com/watch?v=..."
                    value={youtubeUrl}
                    onChange={(e) => setYoutubeUrl(e.target.value)}
                    disabled={isSubmittingYoutube}
                    className="pr-10"
                  />
                  {youtubeUrl && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      {urlValidation.valid ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                    </div>
                  )}
                </div>
                {youtubeUrl && !urlValidation.valid && (
                  <p className="text-sm text-red-500">{urlValidation.error}</p>
                )}
                <p className="text-xs text-muted-foreground">
                  Supports: youtube.com/watch?v=ID, youtu.be/ID, or 11-character video ID
                </p>
              </div>

              {isSubmittingYoutube && (
                <div className="p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                    <div>
                      <p className="font-medium">Downloading from YouTube...</p>
                      <p className="text-sm text-muted-foreground">
                        This may take a few moments
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <Button
                onClick={handleYoutubeSubmit}
                disabled={!urlValidation.valid || isSubmittingYoutube}
                className="w-full"
                size="lg"
              >
                <LinkIcon className="mr-2 h-4 w-4" />
                Submit YouTube Video
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
