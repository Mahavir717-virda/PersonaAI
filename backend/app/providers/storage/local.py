"""Local File Storage Provider implementation."""

import os
from pathlib import Path
from app.providers.storage.base import StorageProvider


class LocalFileStorageProvider(StorageProvider):
    """Saves file attachments directly to the local host filesystem."""

    def __init__(self, base_dir: str = "f:/PersonaAI/storage_data") -> None:
        self.base_dir = Path(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, filename: str, content: bytes) -> str:
        """Save file to the base directory and return absolute URI path."""
        file_path = self.base_dir / filename
        # Ensure parent directories exist (in case of nested names)
        os.makedirs(file_path.parent, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return f"file:///{file_path.as_posix()}"

    async def get_file(self, filename: str) -> bytes:
        """Read file from base directory."""
        file_path = self.base_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        with open(file_path, "rb") as f:
            return f.read()

    async def delete_file(self, filename: str) -> bool:
        """Remove file from base directory."""
        file_path = self.base_dir / filename
        if file_path.exists():
            os.remove(file_path)
            return True
        return False
