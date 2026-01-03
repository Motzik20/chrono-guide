import os
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile


class FileStorage:
    def __init__(self, base_dir: str = "/tmp/chrono_uploads"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, file: UploadFile) -> str:
        # Generate a unique filename to prevent collisions
        ext = os.path.splitext(file.filename or "")[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = self.base_dir / filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return str(file_path)

    def delete(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists() and self.base_dir in path.parents:  # Security check
            path.unlink()


# Global instance or dependency
storage = FileStorage()
