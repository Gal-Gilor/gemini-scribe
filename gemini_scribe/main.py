"""Main FastAPI application entry point for Gemini Scribe.

This module defines the FastAPI application and its routes for converting
PDF documents into Markdown using Google's Gemini.
"""

from contextlib import asynccontextmanager

import uvicorn
from endpoints.health import health_router
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from settings import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events.

    Args:
        app: The FastAPI application instance.
    """

    logger.info("Starting Gemini Scribe application")
    yield

    # Shutdown
    logger.info("Shutting down Gemini Scribe application")


app = FastAPI(
    title="Gemini Scribe",
    description="API for converting PDF documents into Markdown using Google's Gemini.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router, tags=["Health"])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific origins when deployed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTP exceptions.

    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.

    Returns:
        JSONResponse: A formatted JSON response with error details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "message": exc.detail,
            }
        },
    )


if __name__ == "__main__":
    uvicorn.run("gemini_scribe.main:app", host="0.0.0.0", port=8080, reload=True)
