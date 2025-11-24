from loguru import logger
from app.config import settings
from app.schemas import GeneratedNote
from app.services.llm import chat


class NoteGenerationError(Exception):
    """Raised when note generation fails."""

    pass


async def generate_notes(
    transcript_text: str,
    transcript_segments: list[dict] = None,
    model: str = None
) -> tuple[GeneratedNote, str]:
    """
    Generate structured notes from transcript with timestamp references using LiteLLM.

    Args:
        transcript_text: Transcribed text to generate notes from
        transcript_segments: Optional timestamped segments from Whisper API
        model: Model to use for note generation (defaults to settings.notes_model)

    Returns:
        tuple: (GeneratedNote object, model_used)

    Raises:
        NoteGenerationError: If note generation fails
    """
    if not transcript_text or not transcript_text.strip():
        raise NoteGenerationError("Cannot generate notes from empty transcript")

    # Use configured model if not specified
    if model is None:
        model = settings.notes_model

    # Format transcript with timestamps if available
    if transcript_segments:
        formatted_transcript = "\n".join([
            f"[{segment['start']:.1f}s - {segment['end']:.1f}s] {segment['text']}"
            for segment in transcript_segments
        ])
        timestamp_instruction = """
IMPORTANT: For key_points, takeaways, and quotes, you MUST include timestamp references.
Use the timestamp from the segment where the content appears (look for [X.Xs - Y.Ys] markers).
For each item, include the timestamp_seconds field with the start time of the relevant segment.

Example format:
- key_points: [{"content": "Main topic discussed", "timestamp_seconds": 45.2}]
- takeaways: [{"content": "Important insight", "timestamp_seconds": 120.5}]
- quotes: [{"content": "Direct quote", "timestamp_seconds": 78.3}]
"""
    else:
        formatted_transcript = transcript_text
        timestamp_instruction = """
Note: Timestamp data is not available for this transcript.
For key_points, takeaways, and quotes, set timestamp_seconds to null.
"""

    note_prompt = f"""Generate comprehensive, structured notes from the following transcript.

{timestamp_instruction}

Extract and organize the following information:
- Summary: Executive summary (2-3 sentences)
- Key Points: Main points with timestamp references (list of objects with 'content' and 'timestamp_seconds')
- Detailed Notes: Important details and context
- Takeaways: Main takeaways and insights with timestamp references (list of objects)
- Topics: Main topics covered (max 4, plain strings)
- Quotes: Notable quotes from authors, specialists, or experts with timestamps (if any, list of objects)
- Questions: Questions raised or to follow up on (if any, plain strings)
- Participants: Authors, specialists, or participants mentioned (if any, plain strings)
- Chapters: Divide the transcript into 5-10 semantic chapters/segments based on topic transitions. For each chapter:
  * Title: Descriptive chapter title (e.g., "Introduction & rapport building")
  * Start_seconds: Start timestamp of the chapter
  * End_seconds: End timestamp of the chapter
  * Description: Brief 1-sentence description of what's covered (optional)
- Sentiment Timeline: Analyze emotional tone throughout the transcript. Identify 5-8 key moments where emotional intensity shifts. For each moment:
  * Timestamp_seconds: Exact timestamp (integer)
  * Sentiment: 'positive', 'negative', or 'neutral'
  * Intensity: -100 (very negative) to +100 (very positive)
  * Description: Brief explanation of the emotional shift
- Themes: Identify 3-6 recurring themes or patterns. For each theme:
  * Theme name
  * Frequency: How many times discussed
  * Key moments: Optional specific quotes or examples
- Actionable Insights: 3-5 clinical, professional, or educational recommendations (plain strings)

Transcript:
{formatted_transcript}"""

    try:
        note_object = await chat(
            messages=[{"role": "user", "content": note_prompt}],
            response_model=GeneratedNote,
        )

        if not note_object:
            raise NoteGenerationError("Empty notes returned")

        return note_object, model

    except Exception as e:
        error_msg = str(e)
        raise NoteGenerationError(f"Note generation failed: {error_msg}")
