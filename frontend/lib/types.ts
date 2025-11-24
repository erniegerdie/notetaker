export type VideoStatus = 'uploaded' | 'processing' | 'completed' | 'failed'
export type SourceType = 'upload' | 'youtube'

export interface Video {
  id: string
  filename: string
  file_path: string
  file_size: number
  uploaded_at: string
  status: VideoStatus
  source_type?: SourceType
  youtube_url?: string
  note_summary?: string
  key_points_count?: number
  takeaways_count?: number
  tags_count?: number
  quotes_count?: number
}

export interface VideoUploadResponse {
  id: string
  filename: string
  status: VideoStatus
  status_url: string
}

export interface VideoStatusResponse {
  id: string
  status: VideoStatus
  uploaded_at: string
  duration_seconds?: number
  title?: string
  error_message?: string
}

export interface SentimentTimelineItem {
  timestamp_seconds: number
  sentiment: 'positive' | 'negative' | 'neutral'
  intensity: number
  description: string
}

export interface ThemeItem {
  theme: string
  frequency: number
  key_moments?: string[]
}

export interface TimestampedContent {
  content: string
  timestamp_seconds?: number
}

export interface GeneratedNote {
  summary: string
  key_points: TimestampedContent[]
  detailed_notes: string
  takeaways: TimestampedContent[]
  tags: string[]
  quotes?: TimestampedContent[]
  questions?: string[]
  participants?: string[]
  sentiment_timeline?: SentimentTimelineItem[]
  themes?: ThemeItem[]
  actionable_insights?: string[]
  model_used?: string
  processing_time_ms?: number
  generated_at?: string
}

export interface TranscriptSegment {
  start: number
  end: number
  text: string
}

export interface Transcription {
  video_id: string
  transcript_text: string
  transcript_segments?: TranscriptSegment[]
  model_used: string
  processing_time: string
  created_at: string
  audio_size?: number
  notes?: GeneratedNote
  notes_model_used?: string
  notes_processing_time?: string
}

export interface VideoWithTranscription extends VideoStatusResponse {
  transcription?: Transcription
}

export interface YouTubeSubmitRequest {
  url: string
}

export interface YouTubeSubmitResponse {
  id: string
  youtube_url: string
  title?: string
  status: VideoStatus
  source_type: SourceType
  status_url: string
}
