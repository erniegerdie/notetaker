# Presigned URL Upload Architecture Implementation Plan

## Overview
Refactor video upload flow to use R2 presigned URLs, eliminating API file handling and delegating compression/transcription to a single worker service.

## Architecture Changes

### Current Flow (Deployed)

**Visual Diagram**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ CURRENT (Deployed - Single Worker)                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Frontend → API (receives file) → Upload to R2 (uncompressed)      │
│             ↓                      ↓                                │
│          Multipart              r2_key stored                       │
│          Upload                 in database                         │
│                                    ↓                                │
│                            Cloud Task created                       │
│                                    ↓                                │
│                         Worker downloads from R2                    │
│                                    ↓                                │
│                         Compress video (ffmpeg)                     │
│                                    ↓                                │
│                         Re-upload compressed to R2                  │
│                                    ↓                                │
│                         Delete original uncompressed                │
│                                    ↓                                │
│                         Extract audio → Transcribe                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Code References** ([backend/app/api/videos.py:51-120](../backend/app/api/videos.py)):
1. **Line 63**: `temp_path, original_size = await save_upload_file(file)` - API saves uploaded file
2. **Line 67**: `r2_key, file_size = upload_local_file(temp_path, user_id=user_id)` - API uploads uncompressed to R2
3. **Line 89**: `create_video_processing_task(str(video.id), r2_key, user_id)` - Cloud Task triggered

**Worker Flow** ([backend/app/worker.py:89-161](../backend/app/worker.py)):
1. **Line 90**: `local_file_path, _ = download_video(r2_key)` - Download from R2
2. **Line 100-127**: Compress video with ffmpeg
3. **Line 131**: `final_r2_key, file_size = upload_local_file(...)` - Re-upload compressed
4. **Line 147-152**: `delete_video(r2_key)` - Delete original uncompressed
5. **Line 157**: `await process_video(...)` - Start transcription

### Proposed Flow (Presigned URL)

**Visual Diagram**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ PROPOSED (Presigned URL - Same Worker)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Frontend → API (generates presigned URL) → Return URL to frontend │
│             ↓                                ↓                      │
│          Creates DB record              Frontend uploads            │
│          (status: uploading)            directly to R2              │
│             ↓                                ↓                      │
│          Returns video_id            Frontend notifies API          │
│                                             ↓                       │
│                                    API verifies upload              │
│                                             ↓                       │
│                                    Cloud Task created               │
│                                             ↓                       │
│                         Worker downloads from R2 (SAME AS BEFORE)   │
│                                             ↓                       │
│                         Compress → Re-upload → Delete → Transcribe  │
│                                    (NO CHANGES)                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Difference**: Frontend uploads directly to R2 instead of through API. Worker logic unchanged.

## Cost Comparison

### Current Deployed Architecture (100 videos/month @ 200MB avg)

| Component | Calculation | Monthly Cost |
|-----------|-------------|--------------|
| **Cloud Run API** | 100 videos × 10s upload handling × $0.000029/s | ~$0.50 |
| **Cloud Run Worker** | 100 videos × 360s (download + compress + upload + transcribe) × $0.000029/s | ~$2.50 |
| **GCP Egress (Worker → R2)** | 8GB compressed uploads × $0.12/GB | ~$0.96 |
| **GCP Egress (Worker → OpenAI)** | 5GB audio × $0.12/GB | ~$0.60 |
| **R2 Storage** | 8GB × $0.015/GB | ~$0.12 |
| **Cloud SQL (db-f1-micro)** | Fixed monthly cost | ~$8.00 |
| **Cloud Tasks** | 100 tasks (free tier) | $0.00 |
| **Artifact Registry** | Docker images | ~$0.10 |
| **TOTAL** | | **~$12.78/month** |

### Presigned URL Architecture (100 videos/month @ 200MB avg)

| Component | Calculation | Monthly Cost |
|-----------|-------------|--------------|
| **Cloud Run API** | 100 videos × 2s (just generate presigned URLs) × $0.000029/s | ~$0.20 |
| **Cloud Run Worker** | UNCHANGED (same compression/transcription work) | ~$2.50 |
| **GCP Egress (Worker → R2)** | UNCHANGED (8GB compressed) | ~$0.96 |
| **GCP Egress (Worker → OpenAI)** | UNCHANGED (5GB audio) | ~$0.60 |
| **R2 Storage** | UNCHANGED (8GB) | ~$0.12 |
| **Cloud SQL** | UNCHANGED | ~$8.00 |
| **Cloud Tasks** | UNCHANGED | $0.00 |
| **Artifact Registry** | UNCHANGED | ~$0.10 |
| **TOTAL** | | **~$12.48/month** |

**Savings**: ~$0.30/month (2.4%)

**Real Benefits** (beyond cost):
- ✅ API handles zero large file uploads (no timeout risk, no memory pressure)
- ✅ Faster uploads for users (direct R2, one less network hop)
- ✅ Lower API compute usage (80% reduction in execution time per upload)
- ✅ Better scalability (API is truly stateless)

## Benefits Summary

✅ **Worker Already Ready**: Current [backend/app/worker.py](../backend/app/worker.py) already implements the complete download → compress → re-upload → delete flow (lines 89-161)
✅ **Minimal Code Changes**: Only API endpoints need updating, worker remains completely unchanged
✅ **API Simplicity**: Never handles large files (stateless, faster, no timeout risk)
✅ **User Experience**: Direct R2 upload (faster, one less network hop)
✅ **Storage Efficiency**: Worker already compresses before final storage (current implementation)
✅ **Scalability**: Lower API memory usage (no 200MB uploads through Cloud Run)

## Implementation Steps

### 1. Backend API Changes

#### New Endpoint: `POST /api/videos/upload/presigned`

**Purpose**: Generate presigned R2 upload URL

**Request**:
```json
{
  "filename": "my-video.mp4",
  "file_size": 209715200,
  "content_type": "video/mp4"
}
```

**Response**:
```json
{
  "video_id": "uuid",
  "upload_url": "https://r2.cloudflarestorage.com/...",
  "r2_key": "videos/user_id/uuid.mp4",
  "expires_in": 3600,
  "status_url": "/api/videos/{video_id}/status"
}
```

**Implementation**:
```python
@router.post("/upload/presigned", response_model=PresignedUploadResponse)
async def generate_presigned_upload_url(
    request: PresignedUploadRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    # Validate file
    validate_video_file_metadata(request.filename, request.file_size)

    # Generate unique R2 key
    r2_key = generate_r2_key(request.filename, user_id)

    # Generate presigned upload URL
    upload_url = generate_presigned_upload_url(
        r2_key,
        content_type=request.content_type,
        expires_in=settings.presigned_url_expiration_seconds
    )

    # Create video record with uploading status
    video = Video(
        filename=request.filename,
        file_path=r2_key,
        r2_key=r2_key,
        file_size=request.file_size,
        status=VideoStatus.uploading,
        source_type=SourceType.upload,
        user_id=user_id
    )
    db.add(video)
    await db.commit()

    return PresignedUploadResponse(...)
```

#### New Endpoint: `POST /api/videos/{video_id}/upload/complete`

**Purpose**: Trigger processing after frontend uploads to R2

**Request**:
```json
{
  "success": true
}
```

**Response**:
```json
{
  "video_id": "uuid",
  "status": "uploaded",
  "status_url": "/api/videos/{video_id}/status"
}
```

**Implementation**:
```python
@router.post("/{video_id}/upload/complete", response_model=VideoUploadResponse)
async def complete_upload(
    video_id: UUID,
    request: UploadCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    # Get video record
    video = await get_video_or_404(db, video_id, user_id)

    if not request.success:
        # Frontend reported upload failure
        video.status = VideoStatus.failed
        await db.commit()
        raise HTTPException(status_code=400, detail="Upload failed")

    # Verify file exists in R2
    verify_r2_object_exists(video.r2_key)

    # Update status
    video.status = VideoStatus.uploaded
    await db.commit()

    # Queue processing task (Cloud Tasks or BackgroundTasks)
    if CLOUD_TASKS_AVAILABLE:
        create_video_processing_task(str(video.id), video.r2_key, user_id)
    else:
        # Fallback to BackgroundTasks
        background_tasks.add_task(process_video_wrapper, str(video.id))

    return VideoUploadResponse(...)
```

#### Files to Modify

**backend/app/api/videos.py**:
- Add `POST /upload/presigned` endpoint
- Add `POST /{video_id}/upload/complete` endpoint
- Keep existing `POST /upload` for backward compatibility (optional)

**backend/app/services/r2_service.py**:
- Add `generate_presigned_upload_url()` function
- Add `verify_r2_object_exists()` function

**backend/app/schemas.py**:
- Add `PresignedUploadRequest` schema
- Add `PresignedUploadResponse` schema
- Add `UploadCompleteRequest` schema

**backend/app/config.py**:
- Add `presigned_url_expiration_seconds: int = 3600`

**backend/app/utils/file_handler.py**:
- Add `validate_video_file_metadata()` for pre-upload validation
- Add `generate_r2_key()` for consistent key generation

### 2. Worker Service Changes

**✅ NO CHANGES NEEDED** - Worker already implements the exact flow needed for presigned URLs!

**Current Implementation** ([backend/app/worker.py:43-203](../backend/app/worker.py)):

The worker already:
1. **Line 90**: Downloads video from R2 - `local_file_path, _ = download_video(r2_key)`
2. **Lines 100-127**: Compresses video with ffmpeg (CRF, resolution, FPS limits)
3. **Line 131**: Re-uploads compressed version - `final_r2_key, file_size = upload_local_file(...)`
4. **Lines 147-152**: Deletes original uncompressed file - `delete_video(r2_key)`
5. **Line 157**: Triggers transcription - `await process_video(...)`

**Why this works perfectly for presigned URLs:**
- Worker doesn't care HOW the file got to R2 (API upload vs direct upload)
- Worker just needs the `r2_key` to download and process
- Same compression → re-upload → delete → transcribe flow applies

**Zero worker changes required!** 🎉

### 3. Frontend Changes

#### New Upload Flow

**Current**:
```typescript
// Upload file directly to API
const formData = new FormData()
formData.append('file', file)
const response = await api.post('/api/videos/upload', formData)
```

**New**:
```typescript
// 1. Get presigned URL
const presignedResponse = await api.post('/api/videos/upload/presigned', {
  filename: file.name,
  file_size: file.size,
  content_type: file.type
})

// 2. Upload directly to R2
await fetch(presignedResponse.upload_url, {
  method: 'PUT',
  body: file,
  headers: {
    'Content-Type': file.type
  }
})

// 3. Notify backend upload complete
await api.post(`/api/videos/${presignedResponse.video_id}/upload/complete`, {
  success: true
})

// 4. Poll status as usual
pollVideoStatus(presignedResponse.video_id)
```

#### Files to Modify

**frontend/lib/api.ts**:
```typescript
export async function uploadVideoPresigned(file: File) {
  // 1. Get presigned URL
  const { data } = await api.post('/api/videos/upload/presigned', {
    filename: file.name,
    file_size: file.size,
    content_type: file.type
  })

  // 2. Upload to R2
  const uploadResponse = await fetch(data.upload_url, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type
    }
  })

  if (!uploadResponse.ok) {
    throw new Error('R2 upload failed')
  }

  // 3. Complete upload
  await api.post(`/api/videos/${data.video_id}/upload/complete`, {
    success: true
  })

  return data.video_id
}
```

**Frontend upload component** (need to locate):
- Replace direct API upload with `uploadVideoPresigned()`
- Add upload progress tracking (R2 supports progress events)
- Handle errors at each step (presigned generation, R2 upload, completion)

### 4. Database Schema

**No changes needed** - existing schema supports this flow:

```sql
-- Video lifecycle for presigned URL flow:
-- 1. POST /upload/presigned → status='uploading', r2_key set
-- 2. Frontend uploads to R2
-- 3. POST /upload/complete → status='uploaded'
-- 4. Worker processes → status='processing'
-- 5. Transcription complete → status='completed'
```

### 5. Error Handling

**Scenario 1: Frontend fails to upload to R2**
- Frontend calls `/upload/complete` with `success: false`
- Video status set to `failed`
- User can retry

**Scenario 2: Frontend uploads to R2 but crashes before completing**
- Video stuck in `uploading` status
- Background cleanup job (future enhancement) can detect and clean up
- Or: presigned URL expiration (1 hour) prevents abandoned uploads

**Scenario 3: Worker fails to compress**
- Worker falls back to original file (existing logic)
- Continues with transcription

**Scenario 4: R2 upload succeeds but file not found**
- `/upload/complete` calls `verify_r2_object_exists()`
- Returns 400 error if not found
- Frontend can retry

## Migration Strategy

### Option A: Immediate Cutover (Recommended)

1. Deploy new backend with presigned endpoints
2. Update frontend to use new flow
3. Keep old `/upload` endpoint for 1-2 weeks (deprecation period)
4. Monitor for issues
5. Remove old endpoint after validation

### Option B: Gradual Migration

1. Deploy both endpoints
2. Frontend uses feature flag: `USE_PRESIGNED_UPLOAD`
3. Roll out to 10% → 50% → 100% of users
4. Deprecate old endpoint after 100% migration

### Recommended: Option A
- Simpler codebase (no feature flags)
- Clear cutover date
- Presigned URL pattern is industry standard

## Testing Checklist

### Backend
- [ ] Generate presigned URL successfully
- [ ] Presigned URL has correct expiration
- [ ] R2 key generated with user_id prefix
- [ ] Video record created with `uploading` status
- [ ] Upload complete verifies R2 object exists
- [ ] Cloud Task created on completion
- [ ] Error handling for invalid file types
- [ ] Error handling for file size limits

### Worker
- [ ] Downloads from R2 successfully
- [ ] Compresses video correctly
- [ ] Re-uploads compressed version
- [ ] Deletes original uncompressed file
- [ ] Transcription starts after compression
- [ ] Fallback to original if compression fails

### Frontend
- [ ] Presigned URL request succeeds
- [ ] Direct R2 upload works (PUT request)
- [ ] Upload progress tracking works
- [ ] Completion notification succeeds
- [ ] Status polling works
- [ ] Error handling for each step
- [ ] Large file handling (>200MB)
- [ ] Network failure recovery

### End-to-End
- [ ] Upload 50MB video → compressed → transcribed
- [ ] Upload 200MB video → compressed → transcribed
- [ ] YouTube flow still works (unchanged)
- [ ] Multiple concurrent uploads work
- [ ] Error scenarios handled gracefully

## Rollback Plan

If critical issues arise:

1. **Frontend rollback**: Revert to old `/upload` endpoint (1-line change)
2. **Backend**: Keep both endpoints running (no removal needed)
3. **Database**: No migrations = no rollback needed
4. **Worker**: Unchanged logic = no rollback needed

**Risk**: LOW - Presigned URLs are standard pattern, worker logic unchanged

## Timeline

**Estimated effort**: 1-2 days

- Backend implementation: 4 hours
- Frontend implementation: 2 hours
- Testing: 2 hours
- Documentation: 1 hour
- Deployment: 1 hour

## Success Metrics

- [ ] API memory usage reduced by ~80% (no 200MB file handling)
- [ ] Upload success rate ≥99%
- [ ] Average upload time reduced (direct R2 vs API hop)
- [ ] Worker processing time unchanged (same logic)
- [ ] Cost reduced from ~$12.78 to ~$12.48/month for 100 videos
- [ ] Zero data loss during migration
- [ ] API execution time per upload reduced from ~10s to ~2s

## Future Enhancements

1. **Multipart uploads**: For files >5GB (R2 supports multipart)
2. **Resume uploads**: Handle network interruptions gracefully
3. **Upload cleanup job**: Delete abandoned uploads (stuck in `uploading` >24h)
4. **Progress websocket**: Real-time upload progress to frontend
5. **CDN integration**: Use R2 custom domain for presigned URLs

---

## Summary

**Decision**: Implement presigned URL upload flow

**Why**:
- **Minimal changes required**: Worker already has the exact logic needed (zero changes!)
- **Cost savings**: ~$0.30/month reduction ($12.78 → $12.48)
- **API performance**: 80% reduction in execution time per upload (10s → 2s)
- **Better scalability**: API never handles large files (stateless, no memory pressure)
- **Faster user experience**: Direct R2 upload (one less network hop)
- **Low risk**: Presigned URLs are industry standard, worker logic unchanged

**Current Architecture Advantage**:
The current implementation already has the worker doing compress → re-upload → delete, which is exactly what's needed for presigned URLs. This means we're 90% of the way there - we just need to change the initial upload mechanism from API → R2 to Frontend → R2.

**Next Steps**:
1. Implement backend presigned endpoints ([backend/app/api/videos.py](../backend/app/api/videos.py))
2. Add R2 presigned URL generation ([backend/app/services/r2_service.py](../backend/app/services/r2_service.py))
3. Update frontend upload component
4. Test end-to-end flow
5. Deploy with fallback to old endpoint
6. Monitor for 1 week
7. Remove old `/upload` endpoint after validation
