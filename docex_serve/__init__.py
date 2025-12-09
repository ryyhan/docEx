"""
DocEx-Serve: Document extraction with VLM support via FastAPI.

A powerful document extraction service with multi-provider VLM support,
batch processing, and multiple output formats.
"""

from docex_serve.app.services.extraction import ExtractionService
from docex_serve.app.schemas.enums import VlmMode
from docex_serve.server import start_server

__version__ = "1.0.0"
__all__ = ["ExtractionService", "VlmMode", "start_server"]
