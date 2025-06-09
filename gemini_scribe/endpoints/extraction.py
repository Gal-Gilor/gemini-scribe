from pathlib import Path
from typing import Annotated
from uuid import uuid4

import aiohttp
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status
from pydantic import BeforeValidator
from pydantic import Field

from gemini_scribe.models import ExtractTextResponse
from gemini_scribe.services.cloud_storage import extract_file_path_from_gsutil_url
from gemini_scribe.services.cloud_storage import get_storage_bucket
from gemini_scribe.services.image_to_markdown import GeminiParserAsync
from gemini_scribe.settings import config
from gemini_scribe.settings import logger

extract_router = APIRouter()


def validate_gsutil_url(url: str) -> str:
    """Validate that URL starts with 'gs://'.

    Args:
        url: The URL to validate.

    Returns:
        str: The original URL if valid.
    """
    if not url.startswith("gs://"):
        raise ValueError("URL must start with 'gs://'")

    return url


GsutilUrl = Annotated[
    str,
    BeforeValidator(validate_gsutil_url),
    Field(description="A URI starting with 'gs://'"),
]


@extract_router.post("/extract_text", tags=["Parser"])
async def extract_text_from_uri(uri: GsutilUrl) -> ExtractTextResponse:
    """Extract text from a file located at the given URI and convert it to Markdown.

    Args:
        uri: The GS URI of the file to process.

    Returns:
        ExtractTextResponse: Object with the original URI and extracted Markdown.
    """
    # Create temporary file path
    temp_file_path = Path(f".cache/downloads/temp_{uuid4()}.pdf")
    temp_file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        async with aiohttp.ClientSession() as session:
            # Create bucket instance
            bucket = await get_storage_bucket(config.GOOGLE_CLOUD_BUCKET, session)

            # Check if bucket exists and is accessible
            if not await bucket.exists():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Storage bucket '{config.GOOGLE_CLOUD_BUCKET}' not accessible",
                )

            source_file_path = await extract_file_path_from_gsutil_url(uri)
            if not await bucket.blob_exists(source_file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File '{source_file_path}' not found",
                )

            # Download and process the file
            logger.info(f"Processing file: {source_file_path}")
            await bucket.download_blob(source_file_path, str(temp_file_path))
            markdown_text = await GeminiParserAsync().to_markdown(temp_file_path)

            return ExtractTextResponse(uri=uri, markdown=markdown_text)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error processing '{uri}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Text extraction failed",
        )

    finally:
        temp_file_path.unlink(missing_ok=True)
