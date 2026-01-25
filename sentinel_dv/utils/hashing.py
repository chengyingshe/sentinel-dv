"""Hashing utilities for Sentinel DV."""

import hashlib
from typing import Union


def sha256_hex(data: Union[str, bytes]) -> str:
    """Compute SHA-256 hash and return as hexadecimal string.

    Args:
        data: Input data (string or bytes).

    Returns:
        Lowercase hexadecimal SHA-256 hash (64 characters).
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def stable_signature(components: list[str]) -> str:
    """Create a stable signature hash from multiple components.

    Args:
        components: List of string components to hash.

    Returns:
        Stable signature hash (shortened to 16 chars for readability).
    """
    # Sort components for determinism
    sorted_components = sorted(components)
    # Join with null byte separator
    combined = "\x00".join(sorted_components)
    # Return first 16 chars of SHA-256
    return sha256_hex(combined)[:16]


def hash_file_chunk(file_path: str, start_line: int, end_line: int) -> str:
    """Compute SHA-256 hash of a line range in a file.

    Args:
        file_path: Path to file.
        start_line: Starting line number (1-indexed).
        end_line: Ending line number (1-indexed, inclusive).

    Returns:
        SHA-256 hash of the line range.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If line range is invalid.
    """
    if start_line < 1 or end_line < start_line:
        raise ValueError(f"Invalid line range: {start_line}-{end_line}")

    with open(file_path, "rb") as f:
        lines = f.readlines()

    if start_line > len(lines) or end_line > len(lines):
        raise ValueError(f"Line range {start_line}-{end_line} exceeds file length {len(lines)}")

    # Extract lines (convert to 0-indexed)
    chunk_lines = lines[start_line - 1 : end_line]
    chunk_bytes = b"".join(chunk_lines)

    return sha256_hex(chunk_bytes)
