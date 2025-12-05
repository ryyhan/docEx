import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
from docling.document_converter import DocumentConverter
from app.schemas.extraction import ExtractionResponse, TableData
from app.core.config import settings
import datetime

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
            
            logger.info(f"Markdown content type: {type(markdown_content)}")
            logger.info(f"Tables type: {type(tables)}")
            if tables:
                logger.info(f"Table 0 type: {type(tables[0])}")
            logger.info(f"Filename type: {type(file.filename)}")
            logger.info(f"Page count type: {type(doc.num_pages)}")
            
            # Defensive coding to avoid serialization errors
            page_count = doc.num_pages
            if callable(page_count):
                page_count = page_count()
            
            return ExtractionResponse(
                markdown=str(markdown_content),
                tables=tables,
                metadata={
                    "filename": str(file.filename),
                    "page_count": int(page_count) if isinstance(page_count, (int, float, str)) else 0
                }
            )

    async def save_markdown(self, content: str, original_filename: str) -> str:
        """
        Saves the markdown content to a file in the storage directory.
        Returns the absolute path of the saved file.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(original_filename).stem
        filename = f"{base_name}_{timestamp}.md"
        
        storage_path = Path(settings.STORAGE_DIR)
        storage_path.mkdir(parents=True, exist_ok=True)
        
        file_path = storage_path / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info(f"Saved markdown to: {file_path}")
        return str(file_path.absolute())
