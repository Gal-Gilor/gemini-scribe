import asyncio
import functools
import os
import random
import time
from pathlib import Path
from typing import Any
from typing import Callable
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union

from google import genai
from google.genai import types
from google.genai.errors import APIError
from PIL import Image

from gemini_scribe.services.pdf_to_image import save_pdf_as_images
from gemini_scribe.services.text_extraction import extract_and_concatenate_code_blocks
from gemini_scribe.settings import GENERATION_CONFIG
from gemini_scribe.settings import jinja2_env_async
from gemini_scribe.settings import logger

F = TypeVar("F", bound=Callable[..., Any])


def retry_transient_errors(
    max_retries: int = 10,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    use_jitter: bool = True,
) -> Callable[[F], F]:
    """Decorator to retry functions on transient API errors with exponential backoff.

    Implements exponential backoff with optional jitter for API calls that may fail
    with transient errors. Only retries on specific HTTP status codes (500, 503, 429).
    All other errors are raised immediately.

    Args:
        max_retries: Maximum number of retry attempts. Defaults to 3.
        initial_delay: Initial delay in seconds before first retry. Defaults to 1.0.
        backoff_factor: Multiplicative factor for exponential delay growth. Defaults to 2.0.
        use_jitter: Whether to add random jitter (±50%) to delays. Defaults to True.

    Returns:
        Callable[[F], F]: Decorator that preserves the original function signature.

    Raises:
        APIError: Re-raised if max retries exceeded or if status code is not retryable.

    Examples:
        >>> @retry_transient_errors(max_retries=5, initial_delay=2.0)
        ... def call_gemini():
        ...     return client.generate_content("Hello")
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception: Optional[APIError] = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except APIError as e:
                    last_exception = e
                    is_retryable = e.status_code in (500, 503, 429)
                    has_retries_left = attempt < max_retries

                    if is_retryable and has_retries_left:
                        wait_time = (
                            delay * (0.5 + random.random() / 2) if use_jitter else delay
                        )
                        logger.warning(
                            f"Transient error (status {e.status_code}) on attempt "
                            f"{attempt}/{max_retries}. Retrying in {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        delay *= backoff_factor
                    else:
                        raise

            # This line is reached only if all retries exhausted without success
            if last_exception:
                raise last_exception

        return wrapper  # type: ignore[return-value]

    return decorator


class GeminiParserAsync:
    """An asynchronous client for converting PDF documents to Markdown using Google Gemini"""

    @staticmethod
    @retry_transient_errors()
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
            if "image_paths" in locals() and isinstance(image_paths, list) and image_paths:
                for img_path in image_paths:
                    try:
                        img_path.unlink(missing_ok=True)

                    except Exception as e:
                        logger.warning(f"Failed to delete {img_path}: {e}")
                        delete_temp_folder = False

                # Remove the temporary parent directory if empty
                if delete_temp_folder:
                    try:
                        # Remove the temporary parent directory if empty
                        internal_data_directory = image_paths[-1].parent
                        internal_data_directory.rmdir()

                        # Remove the temporary grandparent directory if empty
                        temp_dir = internal_data_directory.parent
                        temp_dir.rmdir()

                    except Exception as e:
                        logger.warning(
                            f"Failed to delete temp directory "
                            f"{internal_data_directory.parent}: {e}"
                        )
