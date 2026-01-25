"""Bounded text utilities for Sentinel DV.

Ensures text fields don't exceed size limits and are properly truncated.
"""



def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "...",
    preserve_newlines: bool = False,
) -> str:
    """Truncate text to maximum length with suffix.

    Args:
        text: Input text to truncate.
        max_length: Maximum length (including suffix).
        suffix: Suffix to add if truncated (default: "...").
        preserve_newlines: If True, preserve newline count in truncation.

    Returns:
        Truncated text (or original if shorter than max_length).
    """
    if len(text) <= max_length:
        return text

    if preserve_newlines:
        # Try to preserve number of lines
        lines = text.split("\n")
        truncated_lines = []
        current_length = 0

        for line in lines:
            line_with_newline = line + "\n"
            if current_length + len(line_with_newline) + len(suffix) <= max_length:
                truncated_lines.append(line)
                current_length += len(line_with_newline)
            else:
                # Add partial line if space
                remaining = max_length - current_length - len(suffix)
                if remaining > 0:
                    truncated_lines.append(line[:remaining])
                break

        return "\n".join(truncated_lines) + suffix

    else:
        # Simple truncation
        cutoff = max_length - len(suffix)
        return text[:cutoff] + suffix


def extract_excerpt(
    text: str,
    start_line: int | None = None,
    end_line: int | None = None,
    max_length: int = 1024,
    context_lines: int = 0,
) -> str:
    """Extract bounded excerpt from text.

    Args:
        text: Full text to extract from.
        start_line: Starting line number (1-indexed).
        end_line: Ending line number (1-indexed, inclusive).
        max_length: Maximum excerpt length in characters.
        context_lines: Number of context lines to include before/after.

    Returns:
        Extracted excerpt (bounded to max_length).
    """
    lines = text.split("\n")

    if start_line is None and end_line is None:
        # Extract from beginning
        excerpt = "\n".join(lines[: min(len(lines), 10)])  # Default to first 10 lines
    else:
        # Convert to 0-indexed
        start_idx = max(0, (start_line or 1) - 1 - context_lines)
        end_idx = min(len(lines), (end_line or len(lines)) + context_lines)

        excerpt = "\n".join(lines[start_idx:end_idx])

    return truncate_text(excerpt, max_length, preserve_newlines=True)


def normalize_whitespace(text: str, single_line: bool = False) -> str:
    """Normalize whitespace in text.

    Args:
        text: Input text.
        single_line: If True, convert to single line (replace newlines with spaces).

    Returns:
        Normalized text.
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    if single_line:
        # Convert to single line
        text = " ".join(text.split())
    else:
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)

    return text.strip()


def count_lines(text: str) -> int:
    """Count number of lines in text.

    Args:
        text: Input text.

    Returns:
        Number of lines (minimum 1 for non-empty text).
    """
    if not text:
        return 0
    return len(text.split("\n"))
