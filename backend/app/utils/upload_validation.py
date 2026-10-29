import os

ALLOWED_UPLOAD_EXTENSIONS = frozenset({
    ".pdf", ".doc", ".docx", ".txt", ".md",
    ".png", ".jpg", ".jpeg", ".gif", ".json", ".csv",
})


def validate_upload(filename: str | None, size: int, max_size: int) -> tuple[str, str]:
    """Return a sanitized display filename and normalized extension.

    Raises ValueError when the extension is unsupported or the size is invalid.
    This checks the filename suffix only; parsers must still validate file contents.
    """
    safe_name = os.path.basename((filename or "").replace("\\", "/"))
    extension = os.path.splitext(safe_name)[1].lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError("Unsupported file type")
    if size < 0 or size > max_size:
        raise ValueError("File size is outside the allowed range")
    return safe_name, extension
