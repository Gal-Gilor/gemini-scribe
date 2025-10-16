import itertools
import json
from pathlib import Path
from typing import Any
from typing import AsyncIterator
from typing import Iterable
from typing import Iterator
from typing import TypeVar

import aiofiles

from gemini_scribe.settings import logger

T = TypeVar("T")


def create_batches(iterable: Iterable[T], batch_size: int = 20) -> Iterator[tuple[T, ...]]:
    """Break an iterable into fixed-size chunks.

    Args:
        iterable: The iterable to batch.
        batch_size: Size of each batch. Must be >= 1. Defaults to 20.

    Returns:
        Iterator yielding tuples of items from the iterable.

    Raises:
        ValueError: If batch_size is less than 1.
        TypeError: If batch_size is not an integer.

    Examples:
        >>> list(create_batches([1, 2, 3, 4, 5], 2))
        [(1, 2), (3, 4), (5,)]
        >>> list(create_batches([], 3))
        []
        >>> list(create_batches(range(10), 3))
        [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)]
    """
    if not isinstance(batch_size, int):
        raise TypeError(f"batch_size must be an integer, got {type(batch_size).__name__}")

    if batch_size < 1:
        raise ValueError(f"batch_size must be at least 1, got {batch_size}")

    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))
    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))


async def read_chunks_in_batches(
    file_path: str | Path, batch_size: int = 10, strict: bool = False
) -> AsyncIterator[list[dict[str, Any]]]:
    """Read JSONL file and yield batches of chunk objects in a streaming manner.

    This function processes the file line-by-line without loading the entire
    file into memory, making it suitable for large files.

    Args:
        file_path: Path to the JSONL file containing chunk data.
        batch_size: Number of chunks per batch. Must be >= 1. Defaults to 10.
        strict: If True, raise exception on JSON parse errors. If False, log
            and skip invalid lines. Defaults to False.

    Yields:
        Lists of chunk dictionaries with keys: section_header, section_text,
        header_level, metadata.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If batch_size is less than 1.
        json.JSONDecodeError: If strict=True and a line contains invalid JSON.

    Examples:
        >>> async for batch in read_chunks_in_batches("data/chunks.jsonl"):
        ...     process_batch(batch)
        >>> async for batch in read_chunks_in_batches("data/chunks.jsonl", strict=True):
        ...     # Will raise on invalid JSON
        ...     process_batch(batch)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if batch_size < 1:
        raise ValueError(f"batch_size must be at least 1, got {batch_size}")

    current_batch: list[dict[str, Any]] = []
    line_number = 0

    async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
        async for line in f:
            line_number += 1
            line = line.strip()

            if not line:
                continue

            try:
                chunk = json.loads(line)
                current_batch.append(chunk)

                # Yield batch when it reaches the desired size
                if len(current_batch) >= batch_size:
                    yield current_batch
                    current_batch = []

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON at line {line_number} in {file_path}: {e}"

                if strict:
                    raise json.JSONDecodeError(error_msg, e.doc, e.pos) from e

                logger.error(error_msg)
                continue

    # Yield any remaining chunks in the final partial batch
    if current_batch:
        yield current_batch
