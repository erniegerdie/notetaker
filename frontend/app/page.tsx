'use client'

import { TopNav } from '@/components/top-nav'
import { FilterTabs } from '@/components/filter-tabs'
import { NoteCard } from '@/components/note-card'
import { UploadSheet } from '@/components/upload-sheet'
import { ProtectedRoute } from '@/components/auth/protected-route'
import { useVideoList } from '@/hooks/use-video-list'
import { Loader2, Upload } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'

export default function HomePage() {
  return (
    <ProtectedRoute>
      <HomePageContent />
    </ProtectedRoute>
  )
}

function HomePageContent() {
  const { data: videos, isLoading } = useVideoList()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [startDate, setStartDate] = useState<string | null>(null)
  const [endDate, setEndDate] = useState<string | null>(null)
  const [uploadSheetOpen, setUploadSheetOpen] = useState(false)
  const router = useRouter()
  const queryClient = useQueryClient()

  const handleUploadSuccess = () => {
    setUploadSheetOpen(false)
    queryClient.invalidateQueries({ queryKey: ['videos'] })
  }

  // Extract all unique tags from videos
  const availableTags = Array.from(
    new Set(
      videos?.videos?.flatMap((video: any) =>
        video.note_summary ? [] : [] // TODO: Get actual tags from backend
      ) || []
    )
  )

  // Transform videos into notes format
  const notes = (videos?.videos || []).map((video: any) => ({
    id: video.id,
    year: new Date(video.uploaded_at).getFullYear().toString(),
    source: video.filename.split('.')[0].replace(/_/g, ' '),
    title: video.filename.replace(/\.[^/.]+$/, '').replace(/_/g, ' '),
    summary: video.note_summary
      ? video.note_summary
      : video.status === 'completed'
      ? 'Transcription completed. Click to view the full transcript and details.'
      : video.status === 'processing'
      ? 'Audio transcription in progress. Please wait while we process your video.'
      : video.status === 'failed'
      ? 'Transcription failed. Please try uploading again or contact support.'
      : 'Video uploaded successfully. Transcription will begin shortly.',
    category: 'other' as const,
    status: video.status,
    uploaded_at: video.uploaded_at,
    keyPointsCount: video.key_points_count,
    takeawaysCount: video.takeaways_count,
    tagsCount: video.tags_count,
    quotesCount: video.quotes_count,
  })) || []

  // Filter notes
  const filteredNotes = notes.filter((note: any) => {
    const matchesSearch = note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         note.summary.toLowerCase().includes(searchQuery.toLowerCase())

    // TODO: Tag filtering needs backend support to get video tags
    const matchesTags = selectedTags.length === 0 // || note.tags?.some(tag => selectedTags.includes(tag))

    // Date range filtering
    const noteDate = new Date(note.uploaded_at || Date.now())
    const matchesStartDate = !startDate || noteDate >= new Date(startDate)
    const matchesEndDate = !endDate || noteDate <= new Date(endDate)
    const matchesDateRange = matchesStartDate && matchesEndDate

    return matchesSearch && matchesTags && matchesDateRange
  })

  return (
    <div className="min-h-screen bg-white">
      {/* Top Navigation */}
      <TopNav
        onSearch={setSearchQuery}
        onCreateNew={() => setUploadSheetOpen(true)}
      />

      {/* Secondary Navigation - Filter Tabs */}
      <FilterTabs
        totalCount={filteredNotes.length}
        onSearch={setSearchQuery}
        onCreateNew={() => setUploadSheetOpen(true)}
        onTagFilter={setSelectedTags}
        onDateRangeFilter={(start, end) => {
          setStartDate(start)
          setEndDate(end)
        }}
        availableTags={availableTags}
      />

      {/* Notes Grid */}
      <div className="px-6 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : filteredNotes.length === 0 ? (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
              <Upload className="h-8 w-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No notes yet
            </h3>
            <p className="text-gray-500 mb-6">
              Upload your first video to create transcription notes
            </p>
            <Button onClick={() => router.push('/upload')}>
              <Upload className="h-4 w-4 mr-2" />
              Upload Video
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredNotes.map((note: any) => (
              <NoteCard key={note.id} {...note} />
            ))}
          </div>
        )}
      </div>

      {/* Upload Sheet */}
      <UploadSheet
        open={uploadSheetOpen}
        onOpenChange={setUploadSheetOpen}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  )
}
