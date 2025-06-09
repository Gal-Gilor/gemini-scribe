from pydantic import BaseModel
from pydantic import Field


class ExtractTextResponse(BaseModel):
    """Response model for text extraction."""

    uri: str = Field(description="Original URI that was processed")
    markdown: str = Field(description="Extracted text content in Markdown format")
