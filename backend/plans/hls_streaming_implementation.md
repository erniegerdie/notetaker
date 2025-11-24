# HLS Video Streaming Implementation Plan

## Overview
Implement production-ready HLS video streaming using FFmpeg → Cloudflare R2 → Next.js (hls.js), following the PRD in [video_streaming.md](video_streaming.md).

## Architecture Decisions

### **MVP Approach: Pragmatic & Cost-Effective**
- **Single bitrate HLS** (copy codec, no re-encoding) - Fast generation, ~30s for 1hr video
- **On-demand generation** (lazy) - Only process videos when first viewed, reduces costs
- **Presigned URL security** - 1-hour expiring URLs, validates user authentication
- **Browser-native caching** - Cloudflare CDN handles edge caching automatically

### **Storage Structure**
```
R2 Bucket:
videos/{user_id}/{video_id}.mp4              # Source (existing)
videos/{user_id}/{video_id}_hls/
  playlist.m3u8                               # Master playlist
  segment0.ts, segment1.ts, ...               # 6-second segments
```

### **Processing Flow**
1. User views video page → Frontend requests stream URL
2. Backend checks if HLS exists in R2 (`hls_playlist_key` field)
3. **If exists** → Return presigned URL → Player loads immediately
4. **If not exists** → Trigger background HLS generation → Return 202 Accepted
5. Frontend polls every 2s → Once ready → Load player with HLS URL

## Backend Implementation

### **1. Database Migration**
Add HLS tracking fields to Video model:
```python
hls_playlist_key: str | None      # R2 key for playlist.m3u8
hls_status: Enum | None           # null/generating/ready/failed
```

Migration: `alembic revision -m "add hls fields to videos"`

### **2. New Service: `services/hls_service.py`**
Functions:
- `generate_hls_for_video(video_id: str)` - Download from R2 → FFmpeg → Upload segments
- `check_hls_exists(video_id: str) → bool` - Check if playlist exists in R2
- `get_hls_playlist_url(video_id: str) → str` - Generate presigned URL (1hr expiry)
- `cleanup_hls_temp_files(temp_dir: str)` - Remove local temp files

**FFmpeg Command** (fast, no re-encode):
```bash
ffmpeg -i source.mp4 \
  -c:v copy -c:a copy \
  -start_number 0 \
  -hls_time 6 \
  -hls_list_size 0 \
  -hls_segment_filename "segment%d.ts" \
  -f hls playlist.m3u8
```

### **3. New API Endpoint: `api/videos.py`**
```python
@router.get("/{video_id}/stream")
async def get_video_stream(
    video_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
)
```

**Logic:**
- Validate user owns video
- If `hls_status == 'ready'` → Return presigned URL (200 OK)
- If `hls_status == 'generating'` → Return 202 Accepted with poll URL
- If `hls_status == null` → Start background generation → Return 202 Accepted
- If `hls_status == 'failed'` → Return 500 with error

**Response Schema:**
```python
class VideoStreamResponse(BaseModel):
    status: str  # "ready" | "generating" | "failed"
    hls_url: str | None  # Presigned URL if ready
    retry_after: int | None  # Seconds to wait before polling (if generating)
    error_message: str | None  # Error details if failed
```

### **4. Update `services/r2_service.py`**
Add HLS-specific functions:
- `upload_hls_segments(local_dir: str, r2_prefix: str)` - Batch upload .m3u8 + .ts files
- `delete_hls_directory(r2_prefix: str)` - Cleanup HLS assets on video deletion
- `list_hls_files(r2_prefix: str)` - Check what HLS files exist

## Frontend Implementation

### **1. Dependencies**
```bash
npm install hls.js
npm install --save-dev @types/hls.js
```

### **2. New Component: `components/hls-player.tsx`**
Features:
- hls.js for Chrome/Firefox
- Native HLS for Safari
- Standard HTML5 video controls
- Loading states (preparing video, buffering)
- Error states (generation failed, network error)
- Responsive sizing (16:9 aspect ratio)

**Key Features:**
```tsx
- Auto-detect HLS support (hls.js vs native)
- Loading spinner during generation
- Polling mechanism (2s interval) when status=generating
- Error fallback with retry button
- Clean event handling (play, pause, error, loaded)
- Playback speed controls
- Volume controls
- Fullscreen support
```

**Component API:**
```tsx
interface HlsPlayerProps {
  src: string | undefined          // HLS playlist URL
  status: 'ready' | 'generating' | 'failed'
  onRetry?: () => void            // Retry callback for failed state
  className?: string              // Custom styling
  autoPlay?: boolean              // Auto-play on load
  poster?: string                 // Thumbnail image
}
```

### **3. Update `app/videos/[id]/page.tsx`**
**UI Layout Change:**
```
Before: [Title] → [Tabs: Notes/Transcription/Stats]
After:  [Title] → [VIDEO PLAYER] → [Tabs: Notes/Transcription/Stats]
```

**Player Placement:**
- Full-width video player above tabs
- Centered with max-width: 1200px
- 16:9 aspect ratio maintained
- Responsive: 100% width on mobile

**Integration:**
```tsx
const { data: streamData, isLoading: streamLoading, refetch } = useVideoStream(id)

{videoStatus.status === 'completed' && (
  <div className="mb-8">
    <HlsPlayer
      src={streamData?.hls_url}
      status={streamData?.status || 'generating'}
      onRetry={() => refetch()}
      className="w-full max-w-5xl mx-auto"
    />
  </div>
)}
```

### **4. New Hook: `hooks/use-video-stream.ts`**
```tsx
export function useVideoStream(videoId: string) {
  return useQuery({
    queryKey: ['video-stream', videoId],
    queryFn: () => fetchVideoStream(videoId),
    refetchInterval: (data) => {
      // Poll every 2s if generating, otherwise stop
      return data?.status === 'generating' ? 2000 : false
    },
    enabled: !!videoId,
  })
}
```

**API Client Function:**
```tsx
async function fetchVideoStream(videoId: string): Promise<VideoStreamResponse> {
  const response = await fetch(`/api/videos/${videoId}/stream`, {
    headers: { Authorization: `Bearer ${getToken()}` }
  })

  if (response.status === 202) {
    return { status: 'generating', hls_url: null, retry_after: 2 }
  }

  if (!response.ok) {
    throw new Error('Failed to load video stream')
  }

  return response.json()
}
```

## Configuration Updates

### **Backend `.env`**
No new variables needed (uses existing R2 config).
Ensure these are set:
```bash
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<key>
R2_SECRET_ACCESS_KEY=<secret>
R2_BUCKET_NAME=notetaker-videos
```

### **CORS Headers**
Ensure API allows HLS content types:
```python
# In main.py CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Content-Length"],
)
```

R2 bucket CORS (if using direct URLs):
```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "ExposeHeaders": ["Content-Length"],
    "MaxAgeSeconds": 3600
  }
]
```

## Database Schema Changes

### **New Enum: HlsStatus**
```python
class HlsStatus(str, enum.Enum):
    generating = "generating"
    ready = "ready"
    failed = "failed"
```

### **Video Model Updates**
```python
class Video(Base):
    # ... existing fields ...

    # HLS streaming fields
    hls_playlist_key = Column(String, nullable=True, index=True)
    hls_status = Column(Enum(HlsStatus), nullable=True, index=True)
    hls_generated_at = Column(DateTime(timezone=True), nullable=True)
    hls_error_message = Column(Text, nullable=True)
```

## File Changes Summary

### Backend Files
- ✏️ **app/models.py** - Add `hls_playlist_key`, `hls_status`, `hls_generated_at`, `hls_error_message`
- ➕ **app/services/hls_service.py** - NEW - HLS generation logic (FFmpeg + R2 upload)
- ✏️ **app/services/r2_service.py** - Add `upload_hls_segments()`, `delete_hls_directory()`, `list_hls_files()`
- ✏️ **app/api/videos.py** - Add `GET /{video_id}/stream` endpoint
- ✏️ **app/schemas.py** - Add `VideoStreamResponse` schema
- ➕ **alembic/versions/xxx_add_hls_fields.py** - NEW migration

### Frontend Files
- ➕ **components/hls-player.tsx** - NEW - Video player component with hls.js
- ➕ **hooks/use-video-stream.ts** - NEW - Stream API hook with polling
- ✏️ **app/videos/[id]/page.tsx** - Add video player above tabs
- ✏️ **package.json** - Add `hls.js` and `@types/hls.js`
- ➕ **lib/api.ts** - Add `fetchVideoStream()` API function

## Implementation Sequence

### Phase 1: Backend Foundation (3-4 hours)
1. Database migration - Add HLS fields to Video model
2. Create `hls_service.py` - FFmpeg conversion logic
3. Update `r2_service.py` - HLS upload functions
4. Create `/stream` API endpoint
5. Add `VideoStreamResponse` schema
6. Test HLS generation manually with sample video

### Phase 2: Frontend Player (3-4 hours)
1. Install hls.js dependency
2. Create `HlsPlayer` component
3. Create `useVideoStream` hook with polling
4. Update video detail page layout
5. Add loading/error states
6. Test cross-browser (Chrome, Safari, Firefox)

### Phase 3: Integration & Testing (2-3 hours)
1. End-to-end testing (upload → view → stream)
2. Test on-demand generation flow
3. Test polling mechanism
4. Test error handling (FFmpeg fails, R2 fails)
5. Test user authorization (can't view others' videos)
6. Mobile responsive testing
7. Network error recovery testing

### Phase 4: Polish & Optimization (1-2 hours)
1. Add video player keyboard shortcuts (space = play/pause, arrows = seek)
2. Optimize presigned URL expiry times
3. Add analytics logging (generation time, success rate)
4. Documentation updates
5. Performance testing (large videos, slow networks)

## Success Criteria

✅ User can watch videos with instant seeking/scrubbing
✅ Works across all browsers (Chrome, Firefox, Safari)
✅ Videos only generate HLS on first view (cost optimization)
✅ Secure: Users can only stream their own videos
✅ Smooth UX: Loading states during generation, polling for readiness
✅ Production-ready: Error handling, cleanup, presigned URLs
✅ Fast generation: <1 min for typical meeting recordings
✅ Reliable: Handles network errors, retries gracefully

## Error Handling Strategy

### FFmpeg Failures
- Log error to `hls_error_message` field
- Set `hls_status = 'failed'`
- Frontend shows error with retry button
- User can trigger manual retry

### R2 Upload Failures
- Retry with exponential backoff (3 attempts)
- If all fail, mark as failed
- Clean up partial uploads

### Network Failures (Frontend)
- hls.js auto-retries segment loading
- If retries exhausted, show network error message
- User can refresh or retry

### Missing Source Video
- If R2 source video deleted, show error
- Suggest re-uploading video

## Performance Optimization

### HLS Generation
- Use `-c:v copy -c:a copy` (no transcoding) - **~30s for 1hr video**
- Process in temp directory with SSD
- Parallel upload of segments to R2
- Clean up temp files immediately after upload

### Streaming
- 6-second segments (good balance for seeking)
- Cloudflare CDN edge caching (automatic)
- Presigned URLs valid for 1 hour (reduce API calls)
- Browser automatically caches segments

### Database Queries
- Index on `hls_status` for filtering
- Index on `hls_playlist_key` for lookups

## Cost Analysis

### R2 Storage
- Source MP4: varies (e.g., 100MB for 1hr meeting)
- HLS segments: ~same size as source (copy codec)
- Total per video: ~2x source size
- At $0.015/GB: 1000 videos (100MB each) = $3/month

### R2 Operations
- Class A (write): $4.50 per million operations
- Class B (read): $0.36 per million operations
- HLS generation: ~20 writes per video (playlist + segments)
- Viewing: ~1 read per video (cached by CDN)

### Cloudflare CDN
- **Egress: $0** (included with R2)
- Bandwidth savings vs direct download: massive

### Total Cost Estimate
- 1000 users, 10 videos each, 2 views per video
- Storage: $30/month
- Operations: ~$1/month
- **Total: ~$31/month for 10,000 videos**

Compare to video hosting platforms: **$200-500/month** for same usage.

## Security Considerations

### User Authorization
- Every stream request validates user owns video
- Presigned URLs include video_id in path
- URLs expire after 1 hour

### R2 Access Control
- Bucket is private (no public access)
- Only presigned URLs work
- Each URL is unique and time-limited

### Content Protection
- URLs are not guessable (UUID-based)
- No direct listing of bucket contents
- User authentication required for all API calls

### HTTPS Only
- All stream URLs use HTTPS
- Cloudflare enforces TLS 1.2+

## Monitoring & Logging

### Metrics to Track
- HLS generation success rate
- Average generation time
- HLS file size distribution
- Stream request volume
- Error types and frequency
- User video watch completion rate

### Logging Strategy
```python
logger.info(f"HLS generation started: video_id={video.id}")
logger.info(f"HLS generation complete: video_id={video.id}, time={elapsed}s, segments={count}")
logger.error(f"HLS generation failed: video_id={video.id}, error={error}")
```

## Future Enhancements (Not in MVP)

### Phase 2 Features
- ⏭️ **Adaptive bitrate (ABR)** - Multi-quality streaming (1080p, 720p, 480p)
- ⏭️ **Thumbnail previews** - Generate thumbnails for scrubbing bar
- ⏭️ **Timestamp sync** - Click note timestamp → jump to video time
- ⏭️ **Playback speed** - 0.5x to 2x speed controls
- ⏭️ **Watch analytics** - Track completion rate, rewind patterns
- ⏭️ **Subtitle overlay** - Generate .vtt from transcript for captions

### Advanced Features
- ⏭️ **Cloudflare Worker auth** - More sophisticated access control
- ⏭️ **Video chapters** - Auto-detect chapters from transcript
- ⏭️ **Sharing links** - Generate temporary share links with expiry
- ⏭️ **Download option** - Allow downloading HLS or source MP4
- ⏭️ **Picture-in-picture** - Continue watching while browsing notes

## Testing Checklist

### Functional Testing
- [ ] Upload video → HLS generates automatically on first view
- [ ] HLS playlist URL is presigned and time-limited
- [ ] Video plays in Chrome (hls.js)
- [ ] Video plays in Safari (native HLS)
- [ ] Video plays in Firefox (hls.js)
- [ ] Seeking works instantly (no buffering delay)
- [ ] User can only stream their own videos (403 for others)
- [ ] Polling works when status=generating
- [ ] Error state shows when generation fails
- [ ] Retry button works after failure

### Performance Testing
- [ ] 5min video generates HLS in <30s
- [ ] 1hr video generates HLS in <2min
- [ ] Segments load quickly from CDN
- [ ] No memory leaks in player component
- [ ] Multiple videos can play sequentially without issues

### Error Handling
- [ ] FFmpeg failure → shows error message
- [ ] R2 upload failure → retries then shows error
- [ ] Network failure → hls.js auto-retries
- [ ] Missing source video → shows helpful error
- [ ] Invalid video format → shows format error

### Security Testing
- [ ] Unauthenticated request → 401 Unauthorized
- [ ] User A can't stream User B's video → 403 Forbidden
- [ ] Presigned URL expires after 1 hour
- [ ] Direct R2 URL without signing → Access Denied

## Estimated Effort

### Development Time
- **Backend**: 4-6 hours (HLS service, API endpoint, migration, testing)
- **Frontend**: 3-4 hours (Player component, UI integration, polling, testing)
- **Integration & Testing**: 2-3 hours (E2E, cross-browser, security, error states)
- **Documentation**: 1 hour (Update README, API docs)

**Total: 10-14 hours for complete MVP**

### Deployment Checklist
- [ ] Run database migration on production
- [ ] Verify R2 credentials in production .env
- [ ] Test FFmpeg is installed on production server
- [ ] Configure CORS headers on API
- [ ] Deploy frontend with hls.js dependency
- [ ] Monitor HLS generation for first 10 videos
- [ ] Check Cloudflare CDN cache hit rate
- [ ] Verify presigned URLs work across regions

## Success Metrics (After Launch)

### Week 1 Goals
- ✅ 100% of videos successfully generate HLS
- ✅ Average generation time <2 minutes
- ✅ CDN cache hit rate >90%
- ✅ Zero security incidents
- ✅ User feedback: positive playback experience

### Month 1 Goals
- ✅ 1000+ videos with HLS streaming
- ✅ 95% generation success rate
- ✅ Average playback start time <2 seconds
- ✅ <1% error rate on streaming
- ✅ User retention: watch >50% of video content

---

## References

- [Original PRD: video_streaming.md](video_streaming.md)
- [FFmpeg HLS Documentation](https://ffmpeg.org/ffmpeg-formats.html#hls-2)
- [hls.js GitHub](https://github.com/video-dev/hls.js)
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [MDN: Video and Audio APIs](https://developer.mozilla.org/en-US/docs/Web/Media)

---

**Status**: ✅ Ready for implementation
**Priority**: High (core feature for video platform)
**Risk Level**: Low (proven tech stack, clear requirements)
