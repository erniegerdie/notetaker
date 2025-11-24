FROM python:3.11-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY uv.lock .

# Install uv
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY jobs ./jobs
COPY alembic.ini .

# Create uploads directory
RUN mkdir -p uploads

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run the application
# Cloud Run sets PORT env var, default to 8080 if not set
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
