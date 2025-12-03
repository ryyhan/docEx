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
