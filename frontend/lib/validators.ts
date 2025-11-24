import { z } from 'zod'
import { MAX_FILE_SIZE_BYTES, ALLOWED_VIDEO_FORMATS } from './constants'

export const fileUploadSchema = z.object({
  file: z.custom<File>((file) => {
    if (!(file instanceof File)) {
      return false
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      throw new Error(`File size must be less than ${MAX_FILE_SIZE_BYTES / 1024 / 1024}MB`)
    }

    // Check file extension
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!extension || !ALLOWED_VIDEO_FORMATS.includes(extension)) {
      throw new Error(`File type must be one of: ${ALLOWED_VIDEO_FORMATS.join(', ')}`)
    }

    return true
  }, {
    message: 'Invalid file'
  })
})

export type FileUploadInput = z.infer<typeof fileUploadSchema>

/**
 * Validates YouTube URL format.
 * Accepts:
 * - https://www.youtube.com/watch?v=VIDEO_ID
 * - https://youtu.be/VIDEO_ID
 * - VIDEO_ID (11-character alphanumeric string)
 */
export function validateYoutubeUrl(url: string): { valid: boolean; error?: string } {
  if (!url || url.trim().length === 0) {
    return { valid: false, error: 'URL cannot be empty' }
  }

  const trimmedUrl = url.trim()

  // Check if it's a raw video ID (11 characters)
  const videoIdPattern = /^[a-zA-Z0-9_-]{11}$/
  if (videoIdPattern.test(trimmedUrl)) {
    return { valid: true }
  }

  // Check for youtube.com/watch?v=ID format
  const youtubeWatchPattern = /(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})/
  if (youtubeWatchPattern.test(trimmedUrl)) {
    return { valid: true }
  }

  // Check for youtu.be/ID format
  const youtubeShortPattern = /(?:youtu\.be\/)([a-zA-Z0-9_-]{11})/
  if (youtubeShortPattern.test(trimmedUrl)) {
    return { valid: true }
  }

  return {
    valid: false,
    error: 'Invalid YouTube URL. Use youtube.com/watch?v=ID, youtu.be/ID, or 11-character video ID'
  }
}

export const youtubeUrlSchema = z.string().refine(
  (url) => validateYoutubeUrl(url).valid,
  {
    message: 'Invalid YouTube URL format'
  }
)

export type YouTubeUrlInput = z.infer<typeof youtubeUrlSchema>
