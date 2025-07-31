import os
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PIL import Image

from gemini_scribe.services.image_to_markdown import GeminiParserAsync


@pytest.mark.asyncio
async def test_extract_text_from_image_success(
    mock_genai_client, monkeypatch, mock_text_extractor, tmp_path
):
    """Test successful text extraction from an image."""
    # Create a test image file
    image_path = tmp_path / "test_image.png"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(image_path)

    # Create the mock directly in the test
    mock_template = AsyncMock()
    mock_template.render_async = AsyncMock(return_value="Template instructions")

    mock_env = AsyncMock()
    mock_env.get_template = MagicMock(return_value=mock_template)

    # Patch both jinja and the text extractor
    monkeypatch.setattr("gemini_scribe.services.image_to_markdown.jinja2_env_async", mock_env)
    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.extract_and_concatenate_code_blocks",
        mock_text_extractor,
    )

    # Execute the method
    result = await GeminiParserAsync._extract_text_from_image(mock_genai_client, image_path)

    # Verify interactions and results
    mock_env.get_template.assert_called_once_with("extract_text_from_image.txt")
    mock_genai_client.aio.models.generate_content.assert_called_once()
    mock_text_extractor.assert_called_once()
    assert result == "Extracted markdown content"


@pytest.mark.asyncio
async def test_extract_text_from_image_error_handling(mock_genai_client, tmp_path):
    """Test error handling during image processing."""
    # Test with non-existent file
    result1 = await GeminiParserAsync._extract_text_from_image(
        mock_genai_client, Path("/nonexistent/file.png")
    )
    assert result1 == ""

    # Test with API error
    image_path = tmp_path / "test_image.png"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(image_path)

    mock_genai_client.aio.models.generate_content.side_effect = Exception("API error")
    result2 = await GeminiParserAsync._extract_text_from_image(mock_genai_client, image_path)
    assert result2 == ""


@pytest.mark.asyncio
async def test_extract_text_from_images(monkeypatch, tmp_path):
    """Test extracting text from multiple images."""
    # Create test image files
    image_paths = [tmp_path / f"test_image_{i}.png" for i in range(3)]
    for path in image_paths:
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(path)

    # Mock the client creation
    mock_client = AsyncMock()
    mock_client_constructor = MagicMock(return_value=mock_client)
    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.genai.Client", mock_client_constructor
    )

    # Mock the _extract_text_from_image method to return results for different images
    expected_results = [f"Content from image {i}" for i in range(3)]

    async def mock_extract(client, file_path, **kwargs):
        # Return different content based on the image number
        idx = int(file_path.stem.split("_")[-1])
        return expected_results[idx]

    monkeypatch.setattr(GeminiParserAsync, "_extract_text_from_image", mock_extract)

    # Execute the method
    results = await GeminiParserAsync.extract_text_from_images(image_paths)

    # Verify the client was created with expected parameters
    mock_client_constructor.assert_called_once()

    # Verify results
    assert results == expected_results


@pytest.mark.asyncio
async def test_save_markdown(tmp_path):
    """Test saving markdown content to a file."""
    # Test data
    markdown_content = "# Test Heading\n\nTest content"
    original_file = Path("/path/to/original/document.pdf")
    destination_dir = tmp_path / "output" / "nested"  # Test nested directory creation

    # Execute the method
    await GeminiParserAsync._save_markdown(markdown_content, original_file, destination_dir)

    # Verify the directory was created
    assert destination_dir.exists()
    assert destination_dir.is_dir()

    # Verify the file was created with correct name and content
    output_file = destination_dir / "document.md"
    assert output_file.exists()
    assert output_file.read_text() == markdown_content


@pytest.mark.asyncio
async def test_save_markdown_existing_directory(tmp_path):
    """Test saving markdown when the directory already exists."""
    # Create the directory in advance
    destination_dir = tmp_path / "existing_dir"
    destination_dir.mkdir()

    # Test data
    markdown_content = "# Test Content"
    original_file = Path("test.pdf")

    # Execute the method - should not raise exceptions
    await GeminiParserAsync._save_markdown(markdown_content, original_file, destination_dir)

    # Verify the file was created
    output_file = destination_dir / "test.md"
    assert output_file.exists()
    assert output_file.read_text() == markdown_content


@pytest.mark.asyncio
async def test_save_markdown_file_path_types(tmp_path):
    """Test saving markdown with different path types."""
    # Test data
    markdown_content = "# Test Content"

    # Test with string paths for destination, but Path for the file_path
    await GeminiParserAsync._save_markdown(
        markdown_content, Path("document.pdf"), str(tmp_path)
    )

    # Verify the file was created properly
    output_file = tmp_path / "document.md"
    assert output_file.exists()
    assert output_file.read_text() == markdown_content


@pytest.mark.asyncio
async def test_to_markdown_success(monkeypatch, tmp_path):
    """Test successful PDF to markdown conversion."""
    # Setup test data
    pdf_path = tmp_path / "test_document.pdf"
    # Create a minimal valid PDF file instead of empty file
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n%EOF\n")
    output_dir = tmp_path / "output"

    # Create image paths that would be returned by pdf_to_image conversion
    image_paths = [tmp_path / f"page_{i}.png" for i in range(3)]
    # No need to actually create the files

    # Mock results from text extraction
    extracted_texts = [
        "Content from page 1",
        "Content from page 2",
        "Content from page 3",
    ]
    expected_markdown = "\n\n".join(extracted_texts)

    # Setup mocks
    mock_pdf_to_image = AsyncMock(return_value=image_paths)
    mock_extract_texts = AsyncMock(return_value=extracted_texts)
    mock_save_markdown = AsyncMock()

    # Patch directly in the module where it's used - important!
    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.save_pdf_as_images", mock_pdf_to_image
    )
    monkeypatch.setattr(GeminiParserAsync, "extract_text_from_images", mock_extract_texts)
    monkeypatch.setattr(GeminiParserAsync, "_save_markdown", mock_save_markdown)

    # Execute the method
    result = await GeminiParserAsync.to_markdown(pdf_path, output_dir)

    # Verify all internal methods were called correctly
    mock_pdf_to_image.assert_called_once_with(pdf_path)
    mock_extract_texts.assert_called_once_with(image_paths)
    mock_save_markdown.assert_called_once_with(expected_markdown, pdf_path, output_dir)

    # Verify the result
    assert result == expected_markdown


@pytest.mark.asyncio
async def test_to_markdown_pdf_conversion_error(monkeypatch, tmp_path):
    """Test handling of PDF conversion errors."""
    # Setup
    pdf_path = tmp_path / "test_document.pdf"
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n%EOF\n")
    output_dir = tmp_path / "output"

    # Mock PDF conversion to fail
    mock_pdf_to_image = AsyncMock(side_effect=RuntimeError("PDF conversion failed"))

    # Patch at the right location
    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.save_pdf_as_images", mock_pdf_to_image
    )

    # Execute the method and verify it raises the exception
    with pytest.raises(RuntimeError, match="PDF conversion failed"):
        await GeminiParserAsync.to_markdown(pdf_path, output_dir)

    # Verify PDF conversion was attempted
    mock_pdf_to_image.assert_called_once_with(pdf_path)


@pytest.mark.asyncio
async def test_to_markdown_extraction_error(monkeypatch, tmp_path):
    """Test handling of text extraction errors."""
    # Setup
    pdf_path = tmp_path / "test_document.pdf"
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n%EOF\n")
    output_dir = tmp_path / "output"

    # Create image paths that would be returned by pdf_to_image conversion
    image_paths = [tmp_path / f"page_{i}.png" for i in range(3)]

    # Setup mocks
    mock_pdf_to_image = AsyncMock(return_value=image_paths)
    mock_extract_texts = AsyncMock(side_effect=Exception("Text extraction failed"))

    # Patch the dependencies at the correct locations
    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.save_pdf_as_images", mock_pdf_to_image
    )
    monkeypatch.setattr(GeminiParserAsync, "extract_text_from_images", mock_extract_texts)

    # Execute the method and verify it raises the exception
    with pytest.raises(Exception, match="Text extraction failed"):
        await GeminiParserAsync.to_markdown(pdf_path, output_dir)

    # Verify PDF conversion was successful before error occurred
    mock_pdf_to_image.assert_called_once_with(pdf_path)
    # Verify text extraction was attempted
    mock_extract_texts.assert_called_once_with(image_paths)


@pytest.mark.asyncio
async def test_to_markdown_empty_pdf(monkeypatch, tmp_path):
    """Test handling of PDF with no pages."""
    # Setup
    pdf_path = tmp_path / "empty_document.pdf"
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n%EOF\n")
    output_dir = tmp_path / "output"

    # Mock PDF conversion to return empty list (no pages)
    mock_pdf_to_image = AsyncMock(return_value=[])

    # Patch the dependencies
    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.save_pdf_as_images", mock_pdf_to_image
    )

    # Execute the method
    result = await GeminiParserAsync.to_markdown(pdf_path, output_dir)

    # Verify the result is empty or contains appropriate message
    assert result == "" or "empty" in result.lower() or "no pages" in result.lower()
    mock_pdf_to_image.assert_called_once_with(pdf_path)


@pytest.mark.asyncio
async def test_extract_text_from_images_api_key_usage(monkeypatch, tmp_path):
    """Test that extract_text_from_images uses GOOGLE_API_KEY when available."""
    # Create a test image file
    image_path = tmp_path / "test_image.png"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(image_path)

    # Mock the genai.Client constructor and _extract_text_from_image method
    mock_client = AsyncMock()
    mock_client_constructor = MagicMock(return_value=mock_client)

    async def mock_extract(client, file_path, **kwargs):
        return "Extracted text"

    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.genai.Client", mock_client_constructor
    )
    monkeypatch.setattr(GeminiParserAsync, "_extract_text_from_image", mock_extract)

    # Execute with mocked API key in environment
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-api-key"}):
        await GeminiParserAsync.extract_text_from_images([image_path])

    # Verify client was created with API key
    mock_client_constructor.assert_called_once()
    assert (
        "api_key" in mock_client_constructor.call_args[1]
        or "vertexai" in mock_client_constructor.call_args[1]
    )


@pytest.mark.asyncio
async def test_to_markdown_empty_image_list(monkeypatch, tmp_path):
    """Test handling of PDF that produces no images."""
    # Create a minimal PDF
    pdf_path = tmp_path / "empty.pdf"
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n%EOF\n")
    output_dir = tmp_path / "output"

    # Mock PDF to image conversion to return empty list
    mock_pdf_to_image = AsyncMock(return_value=[])
    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.save_pdf_as_images", mock_pdf_to_image
    )

    # Execute method
    result = await GeminiParserAsync.to_markdown(pdf_path, output_dir)

    # Verify result is an empty string since no content was extracted
    assert result == ""


@pytest.mark.asyncio
async def test_to_markdown_with_string_paths(monkeypatch, tmp_path):
    """Test to_markdown with string paths instead of Path objects."""
    # Setup with string paths
    pdf_path_str = str(tmp_path / "test.pdf")
    with open(pdf_path_str, "wb") as f:
        f.write(b"%PDF-1.4\n%EOF\n")
    output_dir_str = str(tmp_path / "output")

    # Mock dependencies
    image_paths = [tmp_path / "page_1.png"]
    mock_pdf_to_image = AsyncMock(return_value=image_paths)
    mock_extract_texts = AsyncMock(return_value=["Extracted content"])
    mock_save = AsyncMock()

    monkeypatch.setattr(
        "gemini_scribe.services.image_to_markdown.save_pdf_as_images", mock_pdf_to_image
    )
    monkeypatch.setattr(GeminiParserAsync, "extract_text_from_images", mock_extract_texts)
    monkeypatch.setattr(GeminiParserAsync, "_save_markdown", mock_save)

    # Execute with string paths
    result = await GeminiParserAsync.to_markdown(pdf_path_str, output_dir_str)

    # Verify Path conversion worked correctly
    mock_pdf_to_image.assert_called_once()
    assert isinstance(mock_pdf_to_image.call_args[0][0], Path)
    mock_save.assert_called_once()
    assert isinstance(mock_save.call_args[0][2], Path)

    # Verify the result matches the extracted content
    assert result == "Extracted content"


@pytest.mark.asyncio
async def test_save_markdown_permissions_error(tmp_path):
    """Test error handling when saving markdown with insufficient permissions."""
    # Setup
    markdown_content = "# Test Content"
    file_path = Path("test.pdf")

    # Create a directory with no write permissions
    restricted_dir = tmp_path / "restricted"
    restricted_dir.mkdir()

    # Mock permission error
    with patch.object(Path, "write_text", side_effect=PermissionError("Permission denied")):
        # Execute
        with pytest.raises(PermissionError):
            await GeminiParserAsync._save_markdown(
                markdown_content, file_path, restricted_dir
            )
