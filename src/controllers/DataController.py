from .BaseController import BaseController
from fastapi import UploadFile, HTTPException
from helpers import settings
import hashlib
import magic


class DataController(BaseController):
    """
    Controller responsible for validating and processing uploaded data files.

    This class provides utility methods for:
    - Checking file type (e.g., PDF only)
    - Validating project identifiers
    - Enforcing file size limits
    - Generating file content hashes for duplicate detection
    """

    def __init__(self):
        """
        Initialize the DataController with settings for file validation.

        Attributes:
            max_file_size_bytes (int): Maximum allowed file size in bytes.
            allowed_mime_types (list[str]): List of allowed MIME types for uploads.
        """
        super().__init__()
        self.max_file_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_mime_types = settings.ALLOWED_MIME_TYPES

    def file_hash(self, content: bytes) -> str:
        """
        Compute a SHA256 hash of the given file content.

        Args:
            content (bytes): The binary content of the file.

        Returns:
            str: Hexadecimal string representation of the SHA256 hash.
        """
        sha256 = hashlib.sha256()
        sha256.update(content)
        return sha256.hexdigest()

    def validate_content_type(self, file: UploadFile):
        """
        Validate the MIME type of the uploaded file.

        This function reads a small portion of the file to detect its MIME type
        using the `python-magic` library and compares it with allowed types.

        Args:
            file (UploadFile): The uploaded file object.

        Raises:
            HTTPException: If the file type is not allowed.
        """
        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(file.file.read(1024))
        file.file.seek(0)

        if content_type not in self.allowed_mime_types:
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    def validate_project_id(self, project_id: str):
        """
        Validate that the provided project_id is alphanumeric.

        Args:
            project_id (str): The unique identifier of the project.

        Raises:
            HTTPException: If project_id contains invalid characters.
        """
        if not project_id.isalnum():
            raise HTTPException(status_code=400, detail="Invalid project_id format.")
        if not (3 <= len(project_id) <= 50):
            raise HTTPException(status_code=400, detail="project_id must be between 3 and 50 characters.")

    def validate_file_size(self, file: UploadFile):
        """
        Validate that the uploaded file does not exceed the maximum allowed size.

        This method reads the file in small chunks to prevent memory overload
        and ensure the total size remains within the defined limit.

        Args:
            file (UploadFile): The uploaded file object.

        Raises:
            HTTPException: If the file size exceeds the configured maximum.
        """
        file_size = 0
        while chunk := file.file.read(1024):
            file_size += len(chunk)
            if file_size > self.max_file_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds the {settings.MAX_FILE_SIZE_MB} MB limit."
                )
        file.file.seek(0)
