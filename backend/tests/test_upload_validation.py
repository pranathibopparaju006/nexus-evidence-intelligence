import pytest

from app.utils.upload_validation import validate_upload


@pytest.mark.parametrize(
    ("filename", "expected_extension"),
    [
        ("notes.PDF", ".pdf"),
        ("report.docx", ".docx"),
        ("data.csv", ".csv"),
        (r"C:\\temp\\notes.txt", ".txt"),
    ],
)
def test_supported_uploads_return_sanitized_filename_and_extension(filename, expected_extension):
    safe_name, extension = validate_upload(filename, 10, 1024)
    assert extension == expected_extension
    assert "\\" not in safe_name
    assert "/" not in safe_name


@pytest.mark.parametrize("filename", ["payload.exe", "file.html", "no-extension", "", None])
def test_unsupported_extensions_are_rejected(filename):
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_upload(filename, 10, 1024)


def test_oversized_upload_is_rejected():
    with pytest.raises(ValueError, match="outside the allowed range"):
        validate_upload("notes.txt", 1025, 1024)


def test_negative_size_is_rejected():
    with pytest.raises(ValueError, match="outside the allowed range"):
        validate_upload("notes.txt", -1, 1024)


def test_size_at_limit_is_allowed():
    assert validate_upload("notes.txt", 1024, 1024) == ("notes.txt", ".txt")
