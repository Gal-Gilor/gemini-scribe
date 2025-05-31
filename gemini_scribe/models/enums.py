from enum import StrEnum


class Status(StrEnum):
    """Status Enum"""

    OK = "ok"
    ERROR = "error"


class GeminiModels(StrEnum):
    """Gemini Models Enum"""

    GEMINI_2_0_PRO = "gemini-2.0-pro"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
