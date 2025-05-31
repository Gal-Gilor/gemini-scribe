import asyncio
from datetime import datetime
from pathlib import Path
from typing import List
from typing import Optional

from pdf2image import convert_from_path
from PIL import Image


async def _save_image(img: Image.Image, filepath: Path) -> Path:
    """Save a single image to the specified filepath."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    img.save(filepath)

    return filepath


async def save_images(images: List[Image.Image], destination: Path) -> List[Path]:
    """Save multiple images to the destination directory with sequential naming."""

    coroutines = [
        _save_image(img, destination / f"page_{i}.png") for i, img in enumerate(images)
    ]
    return await asyncio.gather(*coroutines)


async def save_pdf_as_images(filepath: Path, destination: Optional[Path] = None) -> None:
    """Convert a PDF file to images and save them to the specified destination.

    Args:
        filepath: Path to the PDF file
        destination: Directory to save images (default: './images')
    """
    current_datetime = datetime.now()
    timestamp_ms = int(current_datetime.timestamp() * 1000)
    file_name = filepath.stem
    destination = destination or f".cache/data/{file_name}/{timestamp_ms}"

    try:
        images = convert_from_path(filepath)
        return await save_images(images, Path(destination))

    except Exception as e:
        raise RuntimeError(f"Failed to convert PDF {filepath}: {e}")
