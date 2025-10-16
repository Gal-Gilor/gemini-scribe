import re
from typing import List

# Common UTF-8 encoding issues and their fixes
# Pattern: Double-encoded UTF-8 (UTF-8 bytes interpreted as Latin-1 then re-encoded)
ENCODING_FIXES = {
    # Double-encoded em dash variants
    "\u00e2\u20ac\u201d": "\u2014",  # em dash (most common)
    "\u00e2\u20ac\u201c": "\u2013",  # en dash
    "\u00e2\u20ac\u02dc": "\u2018",  # left single quote
    "\u00e2\u20ac\u2122": "\u2019",  # right single quote
    "\u00e2\u20ac\u0153": "\u201c",  # left double quote
    "\u00e2\u20ac\u009d": "\u201d",  # right double quote
    "\u00e2\u20ac\u00a6": "\u2026",  # ellipsis
    "\u00e2\u20ac\u00a2": "\u2022",  # bullet
    "\u00e2\u20ac ": "*",  # dagger/asterisk (used for footnotes)
    "\u00e2\u20ac": "*",  # dagger/asterisk without trailing space
    # Mathematical symbols
    "\u00c3\u0097": "\u00d7",  # multiplication sign (×)
    "\u00c3\u2014": "\u00d7",  # another variant of multiplication sign
    "\u00c3\u00b7": "\u00f7",  # division sign (÷)
    "\u00e2\u02c6\u2019": "\u2212",  # minus sign (U+2212) - triple-encoded
    # Fractions
    "Â½": "½",  # one-half
    "Â¼": "¼",  # one-quarter
    "Â¾": "¾",  # three-quarters
    # Accented characters
    "\u00c3\u00a9": "\u00e9",  # e with acute
    "\u00c3\u00a8": "\u00e8",  # e with grave
    "\u00c3\u00a0": "\u00e0",  # a with grave
    "\u00c3\u00a7": "\u00e7",  # c with cedilla
}


async def fix_encoding_issues(text: str) -> str:
    """Fix common UTF-8 encoding issues in text.

    Args:
        text: The text to fix.

    Returns:
        Text with encoding issues corrected.
    """
    for broken, fixed in ENCODING_FIXES.items():
        text = text.replace(broken, fixed)
    return text


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


async def extract_and_fix_code_blocks(text: str) -> List[str]:
    """Extract code blocks and fix encoding issues in each block.

    Args:
        text: The source text containing code blocks.

    Returns:
        A list of strings with encoding issues fixed.
    """
    blocks = await extract_code_blocks_from_text(text)
    # Fix encoding issues in each block
    return [await fix_encoding_issues(block) for block in blocks]


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


async def extract_fix_and_concatenate(text: str, sep: str = "\n\n") -> str:
    """Extract code blocks, fix encoding issues, and concatenate them.

    Args:
        text: The source text containing code blocks.
        sep: The string to use between concatenated blocks.

    Returns:
        A single string with all code blocks (encoding fixed) joined by the separator.
    """
    blocks = await extract_and_fix_code_blocks(text)

    return sep.join(blocks) if blocks else ""
