# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy poetry files and README
COPY pyproject.toml poetry.lock* README.md ./

# Configure poetry: don't create virtual env, install deps
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-interaction --no-ansi --no-root

# Copy project files
COPY gemini_scribe/ ./gemini_scribe/

# Set Python path to include the app directory
ENV PYTHONPATH="/app"

# Expose the port that Cloud Run expects
EXPOSE 8080

# Set environment variable for production
ENV ENVIRONMENT=production

# Run the FastAPI application with uvicorn
CMD ["uvicorn", "gemini_scribe.main:app", "--host", "0.0.0.0", "--port", "8080"]