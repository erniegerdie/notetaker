# Presigned URL Upload - Testing Guide

Quick guide for testing the new presigned URL upload implementation.

## Prerequisites

- Backend running with R2 credentials configured
- Frontend dev server running
- Valid authentication (logged in user)

## Local Testing Steps

### 1. Start Backend

```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**Verify**:
- Server starts without errors
- Check logs for: "Application startup complete"
- Visit http://localhost:8000/docs to see new endpoints

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

**Verify**:
- Dev server starts on port 3000
- No TypeScript errors
- Open http://localhost:3000

### 3. Test Upload Flow

#### Test Case 1: Small Video (< 50MB)

1. Navigate to upload page
2. Select a small video file (e.g., 10MB mp4)
3. Click "Upload Video"

**Expected Behavior**:
- Progress bar appears and fills
- Console logs show:
  ```
  [API] Requesting presigned URL for video.mp4 (10.00MB)
  [API] Got presigned URL for video <uuid> (expires in 3600s)
  [API] Uploading to R2: videos/<user_id>/<uuid>.mp4
  [API] R2 upload successful for video <uuid>
  [API] Notifying backend of upload completion
  [API] Upload complete for video <uuid>
  ```
- Success toast: "Upload successful"
- Video appears in list with "uploading" → "uploaded" → "processing" status

#### Test Case 2: Large Video (> 100MB)

1. Select a larger video file (e.g., 200MB)
2. Upload and monitor progress

**Expected Behavior**:
- Smooth progress updates (0% → 100%)
- No timeout errors
- Upload completes successfully
- Same status transitions as small file

#### Test Case 3: Error Handling

**Invalid File Type**:
1. Try uploading a .txt file
2. **Expected**: Error toast with "Invalid file type" message

**File Too Large**:
1. Try uploading a file > 500MB
2. **Expected**: Error toast with "File size exceeds maximum" message

**Network Interruption** (advanced):
1. Start upload
2. Disconnect network mid-upload
3. **Expected**: Error toast with "R2 upload network error"

### 4. Verify Backend Processing

After successful upload, check that processing happens:

1. Video status changes: `uploading` → `uploaded` → `processing` → `completed`
2. Check backend logs for:
   ```
   [Worker] Starting processing for video <uuid>
   [Worker] Downloading video from R2: videos/<user_id>/<uuid>.mp4
   [Worker] Compressing video...
   [Worker] Uploaded to R2: videos/<user_id>/<uuid>_compressed.mp4
   [Worker] Deleted original video from R2
   [Worker] Starting transcription
   ```

3. Transcription completes with notes generated

### 5. Check R2 Storage

Verify R2 behavior (optional, requires R2 dashboard access):

1. After upload: Original uncompressed video in R2
2. After worker compression: Compressed video in R2
3. After worker cleanup: Only compressed video remains

**Expected R2 keys**:
- Temporary: `videos/<user_id>/<uuid>.mp4` (deleted by worker)
- Final: `videos/<user_id>/<uuid>_compressed.mp4` (kept)

## Browser DevTools Checks

### Network Tab

**During Upload**:
1. `POST /api/videos/upload/presigned` → 201 Created
   - Response includes: `upload_url`, `video_id`, `r2_key`, `expires_in`

2. `PUT https://<r2-endpoint>/<bucket>/<key>?X-Amz-...` → 200 OK
   - This is the direct R2 upload (bypasses your API)
   - Large payload (video file)
   - Should show upload progress

3. `POST /api/videos/<uuid>/upload/complete` → 200 OK
   - Response: `{ id: uuid, filename: "...", status: "uploaded" }`

### Console Tab

**Expected Logs**:
```
[API] Requesting presigned URL for video.mp4 (200.00MB)
[API] Got presigned URL for video abc-123 (expires in 3600s)
[API] Uploading to R2: videos/user123/abc-123.mp4
[API] R2 upload successful for video abc-123
[API] Notifying backend of upload completion
[API] Upload complete for video abc-123
[useVideoUpload] Upload complete, video ID: abc-123
```

**No Errors** - Check for:
- ❌ CORS errors (R2 presigned URLs should have correct CORS headers)
- ❌ 401/403 errors (authentication issues)
- ❌ Network errors (connectivity issues)

## Comparison: Old vs New Flow

### Old Flow (Multipart)
```
Frontend → API (200MB) → R2 upload → Cloud Task
         ↑ blocking
Time: ~15-20 seconds (includes API processing)
```

### New Flow (Presigned)
```
Frontend → API (metadata) → Presigned URL returned
         ↓ (immediate)
Frontend → R2 (200MB direct) → API completion → Cloud Task
                              ↑ (2 seconds)
Time: ~10-12 seconds (R2 direct upload)
```

**Performance Improvement**: ~30-40% faster, API never blocks

## Troubleshooting

### Upload Fails at Step 1 (Presigned URL Generation)

**Symptoms**: Error toast immediately when clicking upload

**Possible Causes**:
- Backend not running
- R2 credentials not configured in backend `.env`
- File validation failed (size/type)

**Fix**:
- Check backend logs for error details
- Verify `R2_*` environment variables are set
- Check file meets size/format requirements

### Upload Fails at Step 2 (R2 Upload)

**Symptoms**: Progress bar starts, then fails mid-upload

**Possible Causes**:
- Invalid presigned URL (expired or incorrect signature)
- Network connectivity issues
- CORS configuration on R2 bucket

**Fix**:
- Check presigned URL expiration (default 1 hour)
- Verify R2 bucket has CORS configured for PUT requests
- Check browser network tab for specific error

### Upload Fails at Step 3 (Completion)

**Symptoms**: Upload progress reaches 100%, then error

**Possible Causes**:
- File not actually in R2 (upload claimed success but failed)
- Backend can't verify R2 object exists
- Authentication token expired

**Fix**:
- Check backend logs for `verify_r2_object_exists` errors
- Verify R2 credentials have `head_object` permission
- Refresh authentication if token expired

### Worker Not Processing

**Symptoms**: Video stuck in "uploaded" status forever

**Possible Causes**:
- Cloud Tasks not configured (GCP deployment)
- BackgroundTasks not running (local dev)
- Worker service not running (GCP deployment)

**Fix**:
- Local dev: Check backend logs for worker processing
- GCP: Check Cloud Tasks queue and worker logs
- Verify `WORKER_SERVICE_URL` set correctly (GCP)

## Success Criteria

✅ **All tests pass**:
- Small video uploads successfully
- Large video uploads successfully
- Progress bar updates smoothly
- Error handling shows appropriate messages
- Video processing completes end-to-end
- Worker compresses and re-uploads
- Transcription generates successfully

✅ **Performance verified**:
- Upload faster than old multipart flow
- API responds immediately (< 2 seconds)
- No timeout errors on large files

✅ **No regressions**:
- YouTube upload still works
- Old `/upload` endpoint still works (if kept)
- Video list displays correctly
- Status polling works

## Next Steps After Testing

1. **If all tests pass**: Ready for staging deployment
2. **If issues found**: Document in GitHub issue, fix, re-test
3. **After staging validation**: Production deployment
4. **After production**: Monitor for 1-2 weeks, then remove old endpoint

---

**Testing Complete?** Mark tests in [presigned-url-implementation-status.md](presigned-url-implementation-status.md) and proceed to deployment!
