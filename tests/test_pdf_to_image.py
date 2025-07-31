from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from PIL import Image

from gemini_scribe.services.pdf_to_image import _save_image
from gemini_scribe.services.pdf_to_image import save_images
from gemini_scribe.services.pdf_to_image import save_pdf_as_images


@pytest.mark.asyncio
async def test_save_image_success(sample_images, tmp_path):
    """Test successful image saving."""
    # Arrange
    img = sample_images[0]
    filepath = tmp_path / "subdir" / "test_image.png"

    # Act
    result = await _save_image(img, filepath)

    # Assert
    assert result == filepath
    assert filepath.exists()
    assert filepath.is_file()

    # Verify parent directory was created
    assert filepath.parent.exists()

    # Verify the saved image can be opened
    saved_img = Image.open(filepath)
    assert saved_img.size == img.size


@pytest.mark.asyncio
async def test_save_image_failure(sample_images, tmp_path):
    """Test image saving failure."""
    # Arrange
    img = sample_images[0]
    filepath = tmp_path / "subdir" / "test_image.png"

    # Act/Assert
    with patch.object(Image.Image, "save", side_effect=OSError("Mocked save error")):
        with pytest.raises(OSError, match="Mocked save error"):
            await _save_image(img, filepath)

        # Verify file wasn't created despite the parent directory being created
        assert filepath.parent.exists()
        assert not filepath.exists()


@pytest.mark.asyncio
async def test_save_images_success(sample_images, tmp_path):
    """Test saving multiple images successfully."""
    # Arrange
    destination = tmp_path / "multiple"

    # Act
    result = await save_images(sample_images, destination)

    # Assert
    assert len(result) == len(sample_images)
    for i, path in enumerate(result):
        expected_path = destination / f"page_{i}.png"
        assert path == expected_path
        assert path.exists()
        assert path.is_file()

        # Verify the saved image can be opened
        saved_img = Image.open(path)
        assert saved_img.size == sample_images[i].size


@pytest.mark.asyncio
async def test_save_images_with_failure(sample_images, tmp_path):
    """Test handling of errors when saving multiple images."""
    # Arrange
    destination = tmp_path / "failure_test"

    # Create a side effect that fails on the second image
    def mock_save_image(img, filepath):
        if filepath.name == "page_1.png":
            raise OSError("Failed to save second image")
        return filepath

    # Act/Assert
    with patch(
        "gemini_scribe.services.pdf_to_image._save_image", side_effect=mock_save_image
    ):
        with pytest.raises(OSError, match="Failed to save second image"):
            await save_images(sample_images, destination)


@pytest.mark.asyncio
async def test_save_pdf_as_images_success(sample_images, tmp_path, monkeypatch):
    """Test successful PDF to image conversion."""
    # Arrange
    pdf_path = Path("fake.pdf")
    destination = tmp_path / "output"

    # Mock convert_from_path to return sample images instead of requiring real PDF
    with patch(
        "gemini_scribe.services.pdf_to_image.convert_from_path",
        return_value=sample_images,
    ) as mock_convert:
        # Mock save_images to verify it's called correctly
        with patch(
            "gemini_scribe.services.pdf_to_image.save_images",
            return_value=["path1", "path2", "path3"],
        ) as mock_save:
            # Act
            result = await save_pdf_as_images(pdf_path, destination)

            # Assert
            mock_convert.assert_called_once_with(pdf_path)
            mock_save.assert_called_once_with(sample_images, destination)
            assert result == ["path1", "path2", "path3"]


@pytest.mark.asyncio
async def test_save_pdf_as_images_with_default_destination(sample_images, monkeypatch):
    """Test PDF conversion with default destination path generation."""
    # Arrange
    pdf_path = Path("document.pdf")

    # Mock datetime to get consistent timestamp
    fixed_timestamp = 1622548800000  # Example timestamp
    mock_dt = MagicMock()
    mock_dt.now.return_value.timestamp.return_value = fixed_timestamp / 1000
    monkeypatch.setattr("gemini_scribe.services.pdf_to_image.datetime", mock_dt)

    expected_destination = Path(f".cache/data/document/{fixed_timestamp}")

    # Act/Assert
    with patch(
        "gemini_scribe.services.pdf_to_image.convert_from_path",
        return_value=sample_images,
    ):
        with patch("gemini_scribe.services.pdf_to_image.save_images") as mock_save:
            await save_pdf_as_images(pdf_path)
            mock_save.assert_called_once()

            # Get the destination path from the save_images call
            actual_destination = mock_save.call_args[0][1]
            assert actual_destination == expected_destination
