from fastapi import APIRouter
from fastapi.responses import JSONResponse

from gemini_scribe.models import Status

health_router = APIRouter()


@health_router.get("/", tags=["Health"])
async def root() -> JSONResponse:
    """Root endpoint providing basic API information.

    Returns:
        A dictionary containing basic information about the API.
    """
    return JSONResponse(
        status_code=200,
        content={
            "message": "Welcome to the Gemini Scribe API",
            "version": "0.1.0",
            "description": (
                "API for converting PDF documents into Markdown using Google's Gemini"
            ),
        },
    )


@health_router.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """Health check endpoint to verify API is operational.

    Returns:
        A dictionary with status information.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": Status.OK,
            "message": "Gemini Scribe API is running smoothly",
        },
    )
