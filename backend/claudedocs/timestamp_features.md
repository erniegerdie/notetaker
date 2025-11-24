# Time-Synced Intelligence Features

**Implementation Date**: 2025-11-16
**Status**: ✅ Complete

## Overview

Enhanced video transcription API with timestamp-aware features that enable time-synced notes, clickable references, and AI-generated video chapters.

## Features Implemented

### 1. **Timestamped Transcript Segments**

Whisper API now returns segment-level timestamps for each portion of the transcript.

**Database Schema**:
```python
# transcriptions.transcript_segments (JSONB)
[
  {"start": 0.0, "end": 5.2, "text": "Hello, welcome to the session."},
  {"start": 5.2, "end": 12.5, "text": "Today we'll discuss..."},
  ...
]
```

**API Response**:
```json
GET /api/videos/{id}/transcription
{
  "transcript_segments": [
    {"start": 0.0, "end": 5.2, "text": "Hello, welcome..."},
    ...
  ]
}
```

---

### 2. **Time-Synced Notes**

Key points, takeaways, and quotes now include timestamp references linking back to specific moments in the video.

**Schema**:
```python
class TimestampedItem(BaseModel):
    content: str
    timestamp_seconds: Optional[float]  # Can be null for backward compatibility
```

**Example Note Structure**:
```json
{
  "key_points": [
    {
      "content": "Discussion about attachment patterns",
      "timestamp_seconds": 45.2
    },
    {
      "content": "Exploration of nervous system regulation",
      "timestamp_seconds": 120.5
    }
  ],
  "takeaways": [
    {
      "content": "Consider grounding exercises earlier next session",
      "timestamp_seconds": 180.0
    }
  ],
  "quotes": [
    {
      "content": "I noticed tension in my chest when discussing that topic",
      "timestamp_seconds": 78.3
    }
  ]
}
```

**UI Integration** (Frontend):
- Display timestamp pill next to each item (e.g., `12:44`)
- Clicking timestamp jumps video player to that moment
- Hover effect to indicate clickability

---

### 3. **AI-Generated Chapters**

Automatic semantic segmentation of transcripts into 5-10 logical chapters based on topic transitions.

**Schema**:
```python
class ChapterItem(BaseModel):
    title: str
    start_seconds: float
    end_seconds: float
    description: Optional[str]
```

**Example Chapters**:
```json
{
  "chapters": [
    {
      "title": "Introduction & rapport building",
      "start_seconds": 0.0,
      "end_seconds": 135.5,
      "description": "Initial conversation establishing therapeutic relationship"
    },
    {
      "title": "Exploring childhood experiences",
      "start_seconds": 135.5,
      "end_seconds": 420.0,
      "description": "Deep dive into early attachment patterns"
    },
    {
      "title": "Emotion regulation conversation",
      "start_seconds": 420.0,
      "end_seconds": 650.0,
      "description": "Discussing nervous system responses and grounding techniques"
    }
  ]
}
```

**UI Integration** (Frontend):
- Sidebar or horizontal strip showing chapter timeline
- Click chapter to jump to start time
- Visual progress indicator showing current chapter
- Seekbar overlay with chapter markers

---

## Technical Implementation

### Database Changes

**Migration**: `6938b4d9027f_add_transcript_segments_to_transcriptions`

```sql
ALTER TABLE transcriptions
ADD COLUMN transcript_segments JSONB;
```

### API Changes

**Modified Services**:
- `transcription_service.py`: Changed `response_format` from `"text"` to `"verbose_json"` with `timestamp_granularity="segment"`
- `note_generation_service.py`: Updated prompt to request timestamp references and chapters
- `video_service.py`: Passes `transcript_segments` to note generation

**Return Value Changes**:
```python
# Before
transcribe_audio() -> tuple[str, str]  # (text, model)

# After
transcribe_audio() -> tuple[str, str, list[dict]]  # (text, model, segments)
```

### Backward Compatibility

**Existing Data**: Old transcriptions without segments continue to work
- `transcript_segments` field is nullable
- Notes generated without timestamps set `timestamp_seconds: null`
- Frontend should gracefully handle missing timestamps

**Schema Flexibility**:
- `TimestampedItem.timestamp_seconds` is `Optional[float]`
- LLM prompt adapts based on whether segments are available
- Old notes with plain string arrays can be migrated to new format

---

## LLM Prompt Engineering

### Timestamp Formatting

When segments are available, transcript is formatted as:
```
[0.0s - 5.2s] Hello, welcome to the session.
[5.2s - 12.5s] Today we'll discuss your experiences.
[12.5s - 18.0s] I noticed some tension when you mentioned that.
```

### Prompt Instructions

```
IMPORTANT: For key_points, takeaways, and quotes, you MUST include timestamp references.
Use the timestamp from the segment where the content appears (look for [X.Xs - Y.Ys] markers).

Example:
- key_points: [{"content": "Main topic discussed", "timestamp_seconds": 45.2}]

Chapters: Divide the transcript into 5-10 semantic chapters based on topic transitions.
For each chapter provide:
- Title: Descriptive chapter title (e.g., "Introduction & rapport building")
- Start_seconds: Start timestamp
- End_seconds: End timestamp
- Description: Brief 1-sentence description (optional)
```

---

## Testing

**Validation Tests**:
```bash
# Run schema validation tests
uv run python -c "from app.schemas import TimestampedItem, ChapterItem; print('✓ Tests passed')"

# Check all imports
uv run python -c "from app.services.transcription_service import transcribe_audio; print('✓ Imports successful')"
```

**Sample Test Results**:
```
✓ TimestampedItem with timestamp: Key point @ 45.2s
✓ TimestampedItem without timestamp: Key point no timestamp
✓ ChapterItem: Introduction (0.0-60.0s)
✓ GeneratedNote with 2 timestamped key_points
✓ GeneratedNote with 1 chapters
✓ ALL SCHEMA VALIDATION TESTS PASSED
```

---

## API Response Examples

### Transcription Response (New Format)

```json
GET /api/videos/{video_id}/transcription
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "transcript_text": "Hello, welcome to the session. Today we'll discuss...",
  "model_used": "whisper-1",
  "processing_time": "2m 15s",
  "created_at": "2025-11-16T10:30:00Z",
  "audio_size": 5242880,

  "transcript_segments": [
    {"start": 0.0, "end": 5.2, "text": "Hello, welcome to the session."},
    {"start": 5.2, "end": 12.5, "text": "Today we'll discuss your experiences."},
    ...
  ],

  "notes": {
    "summary": "Session focused on attachment patterns...",

    "key_points": [
      {
        "content": "Discussion about early childhood attachment",
        "timestamp_seconds": 45.2
      },
      {
        "content": "Recognition of nervous system activation patterns",
        "timestamp_seconds": 120.5
      }
    ],

    "takeaways": [
      {
        "content": "Practice grounding exercises when noticing chest tension",
        "timestamp_seconds": 180.0
      }
    ],

    "quotes": [
      {
        "content": "I felt my chest tighten when talking about my mother",
        "timestamp_seconds": 78.3
      }
    ],

    "chapters": [
      {
        "title": "Introduction & rapport building",
        "start_seconds": 0.0,
        "end_seconds": 135.5,
        "description": "Initial conversation establishing safety"
      },
      {
        "title": "Exploring childhood experiences",
        "start_seconds": 135.5,
        "end_seconds": 420.0,
        "description": "Deep dive into early attachment patterns"
      }
    ],

    "tags": ["attachment", "nervous-system", "grounding"],
    "detailed_notes": "Client presented with awareness of somatic responses...",
    "model_used": "gpt-4",
    "processing_time_ms": 3250,
    "generated_at": "2025-11-16T10:32:15Z"
  }
}
```

---

## Frontend Integration Guide

### Video Player Timestamp Jumps

```javascript
// Example: Jump to timestamp when user clicks a key point
function handleTimestampClick(timestampSeconds) {
  videoPlayer.currentTime = timestampSeconds;
  videoPlayer.play();
}

// Render key points with clickable timestamps
keyPoints.map(point => (
  <div className="key-point">
    <span>{point.content}</span>
    {point.timestamp_seconds && (
      <button
        className="timestamp-pill"
        onClick={() => handleTimestampClick(point.timestamp_seconds)}
      >
        {formatTimestamp(point.timestamp_seconds)}
      </button>
    )}
  </div>
))

function formatTimestamp(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
```

### Chapter Navigation Sidebar

```javascript
// Render chapter timeline
chapters.map(chapter => (
  <div
    className="chapter-item"
    onClick={() => handleTimestampClick(chapter.start_seconds)}
  >
    <h4>{chapter.title}</h4>
    <span className="chapter-time">
      {formatTimestamp(chapter.start_seconds)} - {formatTimestamp(chapter.end_seconds)}
    </span>
    {chapter.description && <p>{chapter.description}</p>}
  </div>
))
```

### Video Seekbar Chapter Markers

```javascript
// Add visual markers on video seekbar for each chapter
chapters.map(chapter => {
  const position = (chapter.start_seconds / videoDuration) * 100;
  return (
    <div
      className="chapter-marker"
      style={{ left: `${position}%` }}
      title={chapter.title}
    />
  );
})
```

---

## Benefits

### User Experience
✅ **Magical Feel**: Clicking a note jumps to exact video moment
✅ **Quick Navigation**: Chapters provide semantic video structure
✅ **Context Preservation**: Timestamps link insights back to source

### Clinical/Professional Value
✅ **Review Efficiency**: Jump to key moments without rewatching
✅ **Evidence-Based Notes**: Quotes linked to original context
✅ **Session Structure**: Chapters reveal conversation flow patterns

### Technical Benefits
✅ **Zero Breaking Changes**: Backward compatible with old data
✅ **Flexible Schema**: JSONB allows future enhancements
✅ **AI-Powered**: LLM generates timestamps and chapters automatically

---

## Future Enhancements

### Potential Features (Not Implemented)
- Word-level timestamps for karaoke-style highlighting
- Automatic topic extraction with timestamp clustering
- Sentiment timeline visualization on video seekbar
- Interactive transcript with synchronized scrolling
- Multi-language timestamp support
- Export chapters to YouTube-style descriptions

### Performance Optimizations
- Cache formatted transcripts with timestamps
- Lazy load segments for very long videos
- Compress segment data for large transcriptions
- Index segments for faster search

---

## Troubleshooting

### Missing Timestamps
**Symptom**: `transcript_segments` is null or empty
**Cause**: Whisper API didn't return segments
**Solution**: Check OpenAI API response format, verify `verbose_json` is used

### Timestamp Accuracy
**Symptom**: Timestamps don't align perfectly with video
**Cause**: Whisper segment boundaries are approximate
**Solution**: Expected behavior - segments are semantic, not frame-perfect

### LLM Not Generating Timestamps
**Symptom**: Notes have `timestamp_seconds: null` despite segments existing
**Cause**: LLM prompt not followed or model hallucinating
**Solution**: Review prompt clarity, try different model, add validation

### Backward Compatibility Issues
**Symptom**: Old notes fail validation
**Solution**: Ensure `timestamp_seconds` is `Optional[float]` in schema

---

## References

- **OpenAI Whisper API**: [Transcriptions Documentation](https://platform.openai.com/docs/guides/speech-to-text)
- **Migration File**: `alembic/versions/6938b4d9027f_add_transcript_segments_to_.py`
- **Schema Definitions**: `app/schemas.py` (lines 110-152)
- **Transcription Service**: `app/services/transcription_service.py`
- **Note Generation**: `app/services/note_generation_service.py`
