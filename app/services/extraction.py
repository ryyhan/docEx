import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
from docling.document_converter import DocumentConverter
from app.schemas.extraction import ExtractionResponse, TableData

logger = logging.getLogger(__name__)

class ExtractionService:
    def __init__(self):
        self.converter = DocumentConverter()

    async def extract(self, file: UploadFile) -> ExtractionResponse:
        logger.info(f"Starting extraction for file: {file.filename}")
        
        # Docling currently works best with file paths, so we save the upload to a temp file
        suffix = Path(file.filename).suffix
        with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.flush()
            
            logger.debug(f"File saved to temporary path: {tmp.name}")
            
            # Convert
            result = self.converter.convert(tmp.name)
            doc = result.document
            
            # Extract tables
            tables = []
            for table in doc.tables:
                # Basic table extraction - can be enhanced
                grid = table.export_to_dataframe()
                # Convert dataframe to list of lists
                data = grid.values.tolist()
                headers = grid.columns.tolist()
                tables.append(TableData(data=data, headers=headers))

            markdown_content = doc.export_to_markdown()
            
            logger.info("Extraction completed successfully")
            
            return ExtractionResponse(
                markdown=markdown_content,
                tables=tables,
                metadata={
                    "filename": file.filename,
                    "page_count": doc.num_pages
                }
            )
