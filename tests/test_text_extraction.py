import re

import pytest

from gemini_scribe.services.text_extraction import extract_and_concatenate_code_blocks
from gemini_scribe.services.text_extraction import extract_code_block
from gemini_scribe.services.text_extraction import extract_code_blocks_from_text


@pytest.mark.asyncio
async def test_extract_code_block():
    """Test extract_code_block with a simple pattern."""
    # Arrange
    text = "This is some text [code]print('hello')[/code] and more text."
    pattern = re.compile(r"\[code\](.*?)\[\/code\]")

    # Act
    result = await extract_code_block(text, pattern)

    # Assert
    assert result == ["print('hello')"]


@pytest.mark.asyncio
async def test_extract_code_block_multiple():
    """Test extract_code_block with multiple matches."""
    # Arrange
    text = "[code]def func():[/code] text [code]return 42[/code]"
    pattern = re.compile(r"\[code\](.*?)\[\/code\]")

    # Act
    result = await extract_code_block(text, pattern)

    # Assert
    assert result == ["def func():", "return 42"]


@pytest.mark.asyncio
async def test_extract_code_block_no_matches():
    """Test extract_code_block with no matches."""
    # Arrange
    text = "This text has no code blocks"
    pattern = re.compile(r"\[code\](.*?)\[\/code\]")

    # Act
    result = await extract_code_block(text, pattern)

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_extract_code_blocks_from_text():
    """Test extracting code blocks with language markers."""
    # Arrange
    text = """
    Here is some python code:
    ```python
    def hello():
        print("Hello, world!")
    ```
    
    And some JavaScript:
    ```javascript
    function greet() {
        console.log("Hi!");
    }
    ```
    """

    # Act
    result = await extract_code_blocks_from_text(text)

    # Assert
    assert len(result) == 2
    assert "def hello():" in result[0]
    assert 'print("Hello, world!")' in result[0]
    assert "function greet()" in result[1]
    assert 'console.log("Hi!");' in result[1]


@pytest.mark.asyncio
async def test_extract_code_blocks_from_text_empty():
    """Test extracting code blocks from empty text."""
    # Act
    result = await extract_code_blocks_from_text("")

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_extract_code_blocks_from_text_no_code():
    """Test extracting code blocks when none exist."""
    # Arrange
    text = "This is just regular text without any code blocks."

    # Act
    result = await extract_code_blocks_from_text(text)

    # Assert
    assert result == []


@pytest.mark.asyncio
async def test_extract_and_concatenate_code_blocks():
    """Test extracting and concatenating code blocks."""
    # Arrange
    text = """
    ```python
    def func1():
        return 1
    ```
    
    Some text in between.
    
    ```python
    def func2():
        return 2
    ```
    """

    # Act
    result = await extract_and_concatenate_code_blocks(text)

    # Assert
    assert "def func1():" in result
    assert "def func2():" in result
    assert "return 1" in result
    assert "return 2" in result
    # Check for separator
    assert "\n\n" in result


@pytest.mark.asyncio
async def test_extract_and_concatenate_code_blocks_custom_separator():
    """Test concatenating code blocks with custom separator."""
    # Arrange
    text = """
    ```python
    x = 1
    ```
    
    ```python
    y = 2
    ```
    """

    # Act
    result = await extract_and_concatenate_code_blocks(text, sep="###")

    # Assert
    assert result.startswith("x = 1")
    assert result.endswith("y = 2")
    assert "y = 2" in result
    assert "###" in result


@pytest.mark.asyncio
async def test_extract_and_concatenate_code_blocks_empty():
    """Test concatenating when no code blocks exist."""
    # Act
    result = await extract_and_concatenate_code_blocks("No code blocks here")

    # Assert
    assert result == ""
