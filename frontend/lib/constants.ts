export const ALLOWED_VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm']
export const MAX_FILE_SIZE_MB = 500
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

export const STATUS_POLL_INTERVAL = 2000 // 2 seconds
export const BACKGROUND_REFETCH_INTERVAL = 30000 // 30 seconds

export const VIDEO_MIME_TYPES = {
  'video/mp4': ['.mp4'],
  'video/x-msvideo': ['.avi'],
  'video/quicktime': ['.mov'],
  'video/x-matroska': ['.mkv'],
  'video/webm': ['.webm']
}
