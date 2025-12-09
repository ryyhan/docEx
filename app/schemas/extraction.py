from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ExtractionRequest(BaseModel):
    # Add options here if needed, e.g. ocr_enabled: bool = True
    pass

class TableData(BaseModel):
    data: List[List[str]]
    headers: Optional[List[str]] = None

class ExtractionResponse(BaseModel):
    markdown: str
    tables: List[TableData] = []
    metadata: Dict[str, Any] = {}

class BatchFileResult(BaseModel):
    """Result for a single file in batch processing."""
    filename: str
    status: str  # "success" or "error"
    markdown: Optional[str] = None
    tables: List[TableData] = []
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None

class BatchExtractionResponse(BaseModel):
    """Response for batch extraction containing multiple file results."""
    results: List[BatchFileResult]
    total_files: int
    successful: int
    failed: int

class JsonExtractionResponse(BaseModel):
    """Structured JSON response with full document tree."""
    content: Dict[str, Any]
    metadata: Dict[str, Any]

class HtmlExtractionResponse(BaseModel):
    """HTML formatted response."""
    html: str
    metadata: Dict[str, Any]

class TextExtractionResponse(BaseModel):
    """Plain text response."""
    text: str
    metadata: Dict[str, Any]
