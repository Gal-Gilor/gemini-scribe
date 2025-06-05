import re
from typing import List


async def extract_code_block(text: str, pattern: re.Pattern) -> List[str]:
    """
    Extract code blocks from a single text string asynchronously.

    Args:
        text: The text to extract code blocks from.
        pattern: Compiled regex pattern for code blocks.

    Returns:
        List of extracted code blocks.
    """
    return [match.group(1) for match in pattern.finditer(text)]


async def extract_code_blocks_from_text(text: str) -> List[str]:
    """Asynchronously extract all code blocks from a single text.

    This is a standalone function rather than a wrapper that relies on
    implementation details of another function.

    Args:
        text: The source text containing code blocks.

    Returns:
        A list of strings, each containing the content of a code block.
    """
    pattern = re.compile(r"```(?:[^\n]*)\n(.*?)```", re.DOTALL)
    blocks = await extract_code_block(text, pattern)

    # Strip each block of leading/trailing whitespace
    return [block.strip() for block in blocks]


async def extract_and_concatenate_code_blocks(text: str, sep: str = "\n\n") -> str:
    """Extract all code blocks and concatenate them into a single string.

    Args:
        text: The source text containing code blocks.
        sep: The string to use between concatenated blocks.

    Returns:
        A single string containing all code blocks joined by the separator.
    """
    blocks = await extract_code_blocks_from_text(text)

    return sep.join(blocks) if blocks else ""
