# Gemini Scribe

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Execute Tests](https://github.com/Gal-Gilor/gemini-scribe/actions/workflows/execute_main_tests.yaml/badge.svg)](https://github.com/Gal-Gilor/gemini-scribe/actions/workflows/execute_main_tests.yaml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Gal-Gilor/gemini-scribe)

A FastAPI service for converting PDF documents to clean Markdown using Google's Gemini AI. 

## Features

- **PDF to Markdown Conversion**: Advanced text extraction from PDF documents using Gemini AI
- **Google Cloud Integration**: Native support for Google Cloud Storage and Vertex AI
- **High Performance**: Async processing with FastAPI and optimized image handling
- **Production Ready**: Docker containerization, error handling, and comprehensive logging
- **Developer Friendly**: Full type hints, comprehensive tests, and development tooling

## Architecture

### Core Components
- **FastAPI Application**: CORS-enabled REST API with structured endpoints
- **Cloud Storage Service**: Google Cloud Storage integration for file operations
- **PDF Processing Engine**: Converts PDF pages to images using pdf2image
- **Text Extraction**: Gemini-powered image-to-markdown conversion
- **Configuration Management**: Environment-based settings with Pydantic validation

### Processing Flow
1. Client uploads PDF via `gs://` URI to `/extract_text` endpoint
2. Service downloads PDF from Google Cloud Storage
3. PDF converted to images using pdf2image
4. Images processed by Gemini with structured prompts
5. Response parsed to extract clean Markdown
6. Temporary files cleaned up and results returned

## Prerequisites

- Python 3.12+
- Poetry for dependency management
- Google Cloud Platform account
- Google Cloud Storage bucket
- Gemini API access (Vertex AI or direct API)

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/Gal-Gilor/gemini-scribe.git
cd gemini-scribe

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
git clone https://github.com/Gal-Gilor/gemini-scribe.git
cd gemini-scribe

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # Generate with: poetry export -f requirements.txt --output requirements.txt
```

## Configuration

### Environment Variables

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Set these variables in your `.env` file:

```bash
# Google Authentication
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Vertex AI (Optional)
GOOGLE_GENAI_USE_VERTEXAI=True
GEMINI_API_KEY=your-gemini-api-key

# Cloud Storage 
GOOGLE_CLOUD_BUCKET=your-bucket-name

# Application 
DEVELOPMENT=True
```

### Authentication

For Google Cloud services, authenticate using:

```bash
# Service account (production)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# OR user account (development)
gcloud auth application-default login
```

## Usage

### Start the Server

```bash
# Development
poetry run python gemini_scribe/main.py
# OR
python gemini_scribe/main.py

# Production with Uvicorn
uvicorn gemini_scribe.main:app --host 0.0.0.0 --port 8080
```

### API Endpoints

#### Extract Text from PDF

```bash
POST /extract_text
```

**Request:**
```json
{
  "uri": "gs://your-bucket/path/to/document.pdf"
}
```

**Response:**
```json
{
  "markdown": "# Extracted Document Content\n\nDocument text converted to markdown...",
  "pages_processed": 5,
  "processing_time_seconds": 12.34
}
```

#### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Example Usage

```python
import requests

# Extract text from PDF
response = requests.post(
    "http://localhost:8080/extract_text",
    json={"uri": "gs://my-bucket/document.pdf"}
)

if response.status_code == 200:
    result = response.json()
    print(f"Extracted {result['pages_processed']} pages")
    print(result["markdown"])
```

## Development

### Code Quality Tools

```bash
# Format code
black .
ruff format .

# Sort imports
isort .

# Lint and auto-fix
ruff check . --fix

# Type checking (if mypy is added)
mypy gemini_scribe/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gemini_scribe

# Run specific test file
pytest tests/test_text_extraction.py

# Run with verbose output
pytest -v
```

### Development Server

```bash
# Start with auto-reload
uvicorn gemini_scribe.main:app --reload --port 8080
```

## Deployment

### Docker

```bash
# Build image
docker build -t gemini-scribe .

# Run container
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=your-project \
  -e GOOGLE_CLOUD_BUCKET=your-bucket \
  -e GOOGLE_GENAI_USE_VERTEXAI=true \
  gemini-scribe
```

### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy gemini-scribe-service \
    --image gcr.io/your-project/gemini-scribe \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=your-project,GOOGLE_CLOUD_BUCKET=your-bucket,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=true
```

## Project Structure

```
gemini-scribe/
├── gemini_scribe/
│   ├── endpoints/          # API route handlers
│   ├── models/            # Pydantic data models
│   ├── services/          # Core business logic
│   ├── templates/         # AI prompt templates
│   ├── main.py           # FastAPI application
│   └── settings.py       # Configuration management
├── tests/                # Test suite
├── .env.example         # Environment configuration template
├── Dockerfile           # Container configuration
├── pyproject.toml      # Project dependencies
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes following code style guidelines
4. Run tests: `pytest`
5. Run code quality checks: `ruff check . --fix && black .`
6. Commit changes: `git commit -m "Description"`
7. Push branch: `git push origin feature-name`
8. Create a Pull Request

### Development Guidelines

- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Use meaningful commit messages
- Ensure all tests pass before submitting PR

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/Gal-Gilor/gemini-scribe/issues)
- **Author**: Gal Gilor
