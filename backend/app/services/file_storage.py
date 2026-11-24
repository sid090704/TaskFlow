
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".docx",
    ".xlsx",
}


async def save_upload(file: UploadFile) -> tuple[str, int]:
    original_name = (file.filename or "").replace("\\", "/")
    extension = Path(original_name).suffix.lower()

    if not original_name or extension not in ALLOWED_EXTENSIONS:
        raise ValueError("This file type is not allowed.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / stored_filename
    file_size = 0

    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise ValueError("File size cannot exceed 10 MB.")

                output.write(chunk)

        if file_size == 0:
            raise ValueError("Empty files cannot be uploaded.")

        return stored_filename, file_size

    except Exception:
        destination.unlink(missing_ok=True)
        raise

    finally:
        await file.close()


def get_stored_file_path(stored_filename: str) -> Path:
    # Only allow a filename, never a user-supplied directory path.
    if Path(stored_filename).name != stored_filename:
        raise ValueError("Invalid stored filename.")

    return UPLOAD_DIR / stored_filename


def delete_stored_file(stored_filename: str) -> None:
    path = get_stored_file_path(stored_filename)
    path.unlink(missing_ok=True)
