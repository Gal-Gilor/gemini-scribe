from unittest.mock import AsyncMock

import pytest
from PIL import Image

from gemini_scribe.services.cloud_storage import AsyncStorageBucket
from gemini_scribe.services.cloud_storage import Storage


@pytest.fixture
def sample_images():
    """Create sample PIL Image objects for testing."""
    # Create simple test images
    return [Image.new("RGB", (100, 100), color=(255, i * 50, 0)) for i in range(3)]


@pytest.fixture
def mock_storage_client():
    """Create a mock for the async Google Cloud Storage client."""
    mock_client = AsyncMock(spec=Storage)

    # Configure common mock responses
    mock_client.list_objects = AsyncMock(return_value={"items": []})
    mock_client.upload = AsyncMock(return_value={"name": "test-blob"})
    mock_client.download = AsyncMock(return_value=b"test file content")
    mock_client.delete = AsyncMock()
    mock_client.download_metadata = AsyncMock(return_value={"size": "1024"})

    return mock_client


@pytest.fixture
def mock_storage_bucket():
    """Create a proper mock for the AsyncStorageBucket."""
    mock_bucket = AsyncMock(spec=AsyncStorageBucket)
    mock_bucket.name = "test-bucket"
    mock_bucket.exists = AsyncMock(return_value=True)
    mock_bucket.list_blobs = AsyncMock(return_value=[])
    mock_bucket.upload_blob = AsyncMock(return_value={"name": "test-blob"})
    mock_bucket.download_blob = AsyncMock(return_value=None)
    mock_bucket.delete_blob = AsyncMock(return_value=None)
    mock_bucket.get_blob_metadata = AsyncMock(return_value={"size": "1024"})

    return mock_bucket


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for upload/download testing."""
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("This is test content")
    return file_path


@pytest.fixture
def mock_genai_client():
    """Create a mock for the Google Gemini AI client."""
    mock_client = AsyncMock()
    mock_model = AsyncMock()

    # Configure the response
    mock_response = AsyncMock()
    mock_response.text = "```markdown\n# Extracted Content\nThis is sample text\n```"

    # Set up the chain of calls
    mock_model.generate_content = AsyncMock(return_value=mock_response)
    mock_client.aio = AsyncMock()
    mock_client.aio.models = mock_model

    return mock_client


@pytest.fixture
def mock_text_extractor(monkeypatch):
    """Mock the code block extraction function."""
    async_mock = AsyncMock(return_value="Extracted markdown content")
    monkeypatch.setattr(
        "gemini_scribe.services.text_extraction.extract_and_concatenate_code_blocks",
        async_mock,
    )
    return async_mock
