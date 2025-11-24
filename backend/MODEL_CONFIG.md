# Model Configuration Guide

All AI models used in the backend are configurable via environment variables.

## Environment Variables

### Required API Keys

```env
OPENAI_API_KEY=sk-your-key                    # For transcription
OPENROUTER_API_KEY=sk-or-v1-your-key          # For note generation
```

### Model Selection

```env
# Transcription Model (OpenAI)
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
TRANSCRIPTION_FALLBACK_MODEL=whisper-1

# Note Generation Model (OpenRouter)
NOTES_MODEL=openrouter/google/gemini-2.0-flash-exp
```

## Available Models

### Transcription Models (OpenAI)

**Primary Models:**
- `gpt-4o-mini-transcribe` - Fast, cost-effective (recommended)
- `gpt-4o-transcribe` - Higher quality, more expensive
- `gpt-4o-transcribe-diarize` - Speaker diarization support

**Fallback Models:**
- `whisper-1` - Classic Whisper model (reliable fallback)

**Configuration Example:**
```env
TRANSCRIPTION_MODEL=gpt-4o-transcribe
TRANSCRIPTION_FALLBACK_MODEL=gpt-4o-mini-transcribe
```

### Note Generation Models (via OpenRouter)

**Recommended Models:**
- `openrouter/google/gemini-2.0-flash-exp` - Fast, high quality (default)
- `openrouter/google/gemini-2.5-flash` - Latest Gemini Flash
- `openrouter/anthropic/claude-3.5-sonnet` - Excellent for structured notes
- `openrouter/openai/gpt-4o-mini` - OpenAI alternative

**Configuration Example:**
```env
NOTES_MODEL=openrouter/anthropic/claude-3.5-sonnet
```

## Model Pricing Considerations

### Transcription (OpenAI)
- `gpt-4o-mini-transcribe`: ~$0.10 per hour of audio
- `gpt-4o-transcribe`: ~$0.60 per hour of audio
- `whisper-1`: ~$0.006 per minute of audio

### Note Generation (OpenRouter)
- `gemini-2.0-flash-exp`: Free during preview
- `gemini-2.5-flash`: Pay per token
- `claude-3.5-sonnet`: Higher quality, higher cost

Check current pricing:
- OpenAI: https://openai.com/api/pricing/
- OpenRouter: https://openrouter.ai/models

## How Models Are Used

### 1. Transcription Flow

```python
# Primary attempt
model = settings.transcription_model  # From .env
response = openai.audio.transcriptions.create(model=model, ...)

# If primary fails, automatic fallback
if error:
    model = settings.transcription_fallback_model  # From .env
    response = openai.audio.transcriptions.create(model=model, ...)
```

### 2. Note Generation Flow

```python
model = settings.notes_model  # From .env
response = litellm.completion(
    model=model,
    messages=[...],
    extra_body={"reasoning": {"exclude": True}}  # Disable thinking tokens
)
```

## Reasoning Tokens

For models that support reasoning tokens (like o1, Gemini Flash Thinking):

```python
# Disabled by default for all notes generation
extra_body={
    "reasoning": {
        "exclude": True  # Don't generate or return reasoning tokens
    }
}
```

This is hardcoded in the note generation service to keep costs predictable.

## Changing Models at Runtime

Models are loaded from environment variables at startup. To change models:

1. **Update .env file:**
   ```env
   TRANSCRIPTION_MODEL=gpt-4o-transcribe
   NOTES_MODEL=openrouter/anthropic/claude-3.5-sonnet
   ```

2. **Restart the API server:**
   ```bash
   # Stop (Ctrl+C) and restart
   uv run uvicorn app.main:app --reload
   ```

3. **Test with new models:**
   ```bash
   curl -X POST "http://localhost:8000/api/videos/upload" -F "file=@test.mp4"
   ```

## Model Capabilities

### Transcription Models

| Feature | gpt-4o-mini | gpt-4o | gpt-4o-diarize | whisper-1 |
|---------|-------------|---------|----------------|-----------|
| Speed | Fast | Medium | Medium | Fast |
| Quality | High | Very High | Very High | Good |
| Diarization | No | No | Yes | No |
| Prompting | Yes | Yes | No | Yes |
| Streaming | Yes | Yes | Yes | No |
| Cost | Low | High | High | Very Low |

### Note Generation Models

| Feature | Gemini Flash | Claude 3.5 | GPT-4o-mini |
|---------|--------------|------------|-------------|
| Speed | Very Fast | Fast | Fast |
| Quality | Excellent | Excellent | Good |
| Context | 1M tokens | 200K tokens | 128K tokens |
| Reasoning | Available | Available | No |
| Cost | Free* | Medium | Low |

*During preview period

## Troubleshooting

### "Model not found" Error

**Transcription:**
```bash
# Check OpenAI API has access to model
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | grep transcribe
```

**Note Generation:**
```bash
# Verify model name format for OpenRouter
# Should be: openrouter/{provider}/{model}
NOTES_MODEL=openrouter/google/gemini-2.0-flash-exp
```

### High Costs

1. Switch to cheaper models:
   ```env
   TRANSCRIPTION_MODEL=whisper-1
   NOTES_MODEL=openrouter/google/gemini-2.0-flash-exp
   ```

2. Monitor usage:
   - OpenAI: https://platform.openai.com/usage
   - OpenRouter: https://openrouter.ai/activity

## Testing Different Models

```bash
# Test transcription model
TRANSCRIPTION_MODEL=gpt-4o-transcribe uv run uvicorn app.main:app

# Test notes model
NOTES_MODEL=openrouter/anthropic/claude-3.5-sonnet uv run uvicorn app.main:app
```

## Recommendations

**For Production:**
```env
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
TRANSCRIPTION_FALLBACK_MODEL=whisper-1
NOTES_MODEL=openrouter/google/gemini-2.0-flash-exp
```

**For Development/Testing:**
```env
TRANSCRIPTION_MODEL=whisper-1
TRANSCRIPTION_FALLBACK_MODEL=whisper-1
NOTES_MODEL=openrouter/google/gemini-2.0-flash-exp
```

**For Best Quality (Higher Cost):**
```env
TRANSCRIPTION_MODEL=gpt-4o-transcribe
TRANSCRIPTION_FALLBACK_MODEL=gpt-4o-mini-transcribe
NOTES_MODEL=openrouter/anthropic/claude-3.5-sonnet
```
