import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from app.schemas.extraction import ExtractionResponse, TableData
from app.core.config import settings
import datetime

logger = logging.getLogger(__name__)

class ExtractionService:
    def __init__(self):
        self.converter = DocumentConverter()

    def _get_pipeline_options(self, ocr_enabled: bool, table_extraction_enabled: bool) -> PdfPipelineOptions:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = ocr_enabled
        pipeline_options.do_table_structure = table_extraction_enabled
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        return pipeline_options

    async def extract(self, file: UploadFile, ocr_enabled: bool = True, table_extraction_enabled: bool = True) -> ExtractionResponse:
        logger.info(f"Starting extraction for file: {file.filename}")
        
        # Configure pipeline based on options
        pipeline_options = self._get_pipeline_options(ocr_enabled, table_extraction_enabled)
        
        # Create a new converter instance with specific options for this request
        # Note: In a production scenario, we might want to cache converters with different configs
        # or use a single converter and pass options per conversion if supported.
        # For now, creating a new one ensures thread safety and config isolation.
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Docling currently works best with file paths, so we save the upload to a temp file
        suffix = Path(file.filename).suffix
        with NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.flush()
            
            logger.debug(f"File saved to temporary path: {tmp.name}")
            
            # Convert
            result = converter.convert(tmp.name)
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

    def warmup(self):
        """
        Triggers the download of necessary models (OCR, Table Extraction) by running a dummy conversion.
        """
        logger.info("Starting warmup...")
        
        # Enable everything to force download
        pipeline_options = self._get_pipeline_options(ocr_enabled=True, table_extraction_enabled=True)
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # We don't actually need to convert a file to trigger downloads if we initialize the pipeline,
        # but running a small dummy conversion is the surest way to load everything into memory.
        
        # Minimal valid PDF binary string (1 page, empty)
        dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n>>\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000117 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n223\n%%EOF"
        
        with NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            tmp.write(dummy_pdf)
            tmp.flush()
            logger.info("Converting dummy PDF for warmup...")
            converter.convert(tmp.name)
        
        logger.info("Warmup completed (Models downloaded and loaded).")
        return True
