import asyncio
import os
import time
from pathlib import Path
from typing import List
from typing import Union

from google import genai
from google.genai import types
from PIL import Image

from gemini_scribe.services.pdf_to_image import save_pdf_as_images
from gemini_scribe.services.text_extraction import extract_and_concatenate_code_blocks
from gemini_scribe.settings import GENERATION_CONFIG
from gemini_scribe.settings import jinja2_env_async
from gemini_scribe.settings import logger


class GeminiParserAsync:
    """An asynchronous client for converting PDF documents to Markdown using Google Gemini"""

    @staticmethod
    async def _extract_text_from_image(
        client: genai.Client,
        file_path: Path,
        generation_config: types.GenerationConfig = GENERATION_CONFIG,
    ) -> str:
        """Extract text from an image using OCR.

        Args:
            client: Google Gemini client instance.
            file_path: Path to the image file.
            generation_config: Configuration for text generation.

        Returns:
            Extracted text from the image.
        """
        instructions = await jinja2_env_async.get_template(
            "extract_text_from_image.txt"
        ).render_async()

        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            with open(file_path, "rb") as image:
                img = Image.open(image)

                response = await client.aio.models.generate_content(
                    model=os.getenv("GOOGLE_GEMINI_MODEL", "gemini-2.0-flash"),
                    contents=[instructions, img],
                    config=generation_config,
                )
                return await extract_and_concatenate_code_blocks(response.text)

        except Exception as e:
            logger.error(f"Failed to extract text from image: {e}")
            return ""

    @staticmethod
    async def extract_text_from_images(file_paths: List[Path]) -> List[str]:
        """Extract text from multiple images using OCR.

        Args:
            file_paths: List of paths to image files.

        Returns:
            List of extracted text strings from each image.
        """
        # Initialize the client
        client = genai.Client(
            vertexai=os.getenv("GOOGLE_GENAI_USE_VERTEXAI", True),
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "agent-dnd"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )

        # Create actual coroutines by calling extract_text_from_image
        coroutines = [
            GeminiParserAsync._extract_text_from_image(client, file_path)
            for file_path in file_paths
        ]
        return await asyncio.gather(*coroutines)

    @staticmethod
    async def _save_markdown(markdown: str, file_path: Path, destination_path: Path) -> None:
        """Save markdown content to a file.

        Args:
            markdown: The markdown content to save.
            file_path: Original file path (for naming).
            destination_path: Directory to save the markdown file.
        """
        destination_path = Path(destination_path)
        destination_path.mkdir(parents=True, exist_ok=True)

        output_path = destination_path / f"{file_path.stem}.md"
        output_path.write_text(markdown, encoding="utf-8")

        logger.info(f"Saved markdown to: {output_path}")

    @classmethod
    async def to_markdown(
        cls,
        file_path: Union[str, Path],
        destination_path: Union[str, Path, None] = None,
        **kwargs,
    ) -> str:
        """Convert a PDF file to Markdown format.

        Args:
            file_path: Path to the PDF file.
            destination_path: Directory to save the markdown file (optional).
            **kwargs: Additional keyword arguments (for future extensibility).

        Returns:
            A Markdown representation of the PDF file.

        Raises:
            FileNotFoundError: If the PDF file doesn't exist.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Converting PDF to Markdown: {file_path.name}")
        start_time = time.time()

        try:
            # Convert PDF pages to images
            image_paths = await save_pdf_as_images(file_path)
            logger.debug(f"Generated {len(image_paths)} images from PDF")

            # Extract text from all images
            extracted_text = await cls.extract_text_from_images(image_paths)
            markdown = "\n\n".join(extracted_text)

            # Save to file if destination specified
            if destination_path:
                await cls._save_markdown(markdown, file_path, Path(destination_path))

            elapsed = time.time() - start_time
            logger.info(f"Conversion completed in {elapsed:.2f}s")

            return markdown

        except Exception as e:
            logger.error(f"Failed to convert {file_path.name}: {e}", exc_info=True)
            raise

        finally:
            # Clean up temporary image files
            delete_temp_folder = True
            if "image_paths" in locals() and isinstance(image_paths, list):
                for img_path in image_paths:
                    try:
                        img_path.unlink(missing_ok=True)

                    except Exception as e:
                        logger.warning(f"Failed to delete {img_path}: {e}")
                        delete_temp_folder = False

                # Remove the temporary parent directory if empty
                if delete_temp_folder:
                    try:

                        # Remvove the temporary parent directory if empty
                        internal_data_directory = image_paths[-1].parent
                        internal_data_directory.rmdir()

                        # Remove the temporary grandparent directory if empty
                        temp_dir = internal_data_directory.parent
                        temp_dir.rmdir()

                    except Exception as e:
                        logger.warning(f"Failed to delete temp directory {temp_dir}: {e}")
