import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, 
    TableFormerMode,
    PictureDescriptionVlmOptions,
    PictureDescriptionApiOptions
)
from ..schemas.extraction import ExtractionResponse, TableData
from ..schemas.enums import VlmMode
from ..core.config import settings
import datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)

# VLM Provider Configuration
VLM_PROVIDER_URLS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "google": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "azure": None,  # Requires custom endpoint from user
    "custom": None,  # User must provide VLM_API_BASE_URL
}

def get_default_vlm_model(provider: str) -> str:
    """Get default model for a given VLM provider."""
    defaults = {
        "openai": "gpt-4o",
        "groq": "llama-3.2-11b-vision-preview",  # 90b version decommissioned
        "anthropic": "claude-3-5-sonnet-20241022",
        "google": "gemini-1.5-pro",
        "azure": "gpt-4o",
        "custom": "gpt-4o",  # Fallback
    }
    return defaults.get(provider.lower(), "gpt-4o")

DEFAULT_VLM_PROMPT = """
Analyze the provided image and extract all relevant information.
If the image contains text, transcribe it accurately.
If it's a diagram, chart, or any visual representation, describe its key elements, labels, and the relationships or trends it conveys.
Focus on factual details and avoid subjective interpretations.
Present the extracted information in a structured markdown format, prioritizing clarity and completeness.
"""

class ExtractionService:
    def __init__(self):
        self.converter = DocumentConverter()

    def _get_pipeline_options(self, ocr_enabled: bool, table_extraction_enabled: bool, vlm_mode: VlmMode = VlmMode.NONE, vlm_model_id: Optional[str] = None) -> PdfPipelineOptions:
        logger.info(f"_get_pipeline_options called - vlm_mode: {vlm_mode} (type: {type(vlm_mode)}), vlm_model_id: {vlm_model_id}")
        
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = ocr_enabled
        pipeline_options.do_table_structure = table_extraction_enabled
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        
        # Determine prompt
        prompt = settings.VLM_PROMPT if settings.VLM_PROMPT != "default" else DEFAULT_VLM_PROMPT
        
        if vlm_mode == VlmMode.LOCAL:
            logger.info(f"LOCAL VLM mode detected - initializing VLM")
            pipeline_options.do_picture_description = True
            # Handle case where Swagger UI sends "string" as value
            model_to_use = vlm_model_id if vlm_model_id and vlm_model_id != "string" else "HuggingFaceTB/SmolVLM-256M-Instruct"
            pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
                repo_id=model_to_use,
                prompt=prompt,
                picture_area_threshold=0  # Process all images regardless of size
            )
        elif vlm_mode == VlmMode.API:
            logger.info(f"API VLM mode detected")
            
            # Get provider and API key (with backward compatibility)
            provider = settings.VLM_API_PROVIDER.lower()
            api_key = settings.VLM_API_KEY or settings.OPENAI_API_KEY
            
            if not api_key:
                logger.warning(f"VLM API mode requested but VLM_API_KEY/OPENAI_API_KEY is not set. Skipping image description.")
            else:
                # Determine API URL
                if settings.VLM_API_BASE_URL:
                    # User provided custom URL
                    api_url = settings.VLM_API_BASE_URL
                    logger.info(f"Using custom VLM API URL: {api_url}")
                elif provider in VLM_PROVIDER_URLS and VLM_PROVIDER_URLS[provider]:
                    # Use predefined provider URL
                    api_url = VLM_PROVIDER_URLS[provider]
                    logger.info(f"Using {provider} VLM provider at: {api_url}")
                else:
                    logger.error(f"Unknown VLM provider '{provider}' and no VLM_API_BASE_URL provided. Supported providers: {list(VLM_PROVIDER_URLS.keys())}")
                    return pipeline_options
                
                # Determine model to use
                if vlm_model_id and vlm_model_id != "string":
                    model_to_use = vlm_model_id
                else:
                    model_to_use = get_default_vlm_model(provider)
                    logger.info(f"Using default model for {provider}: {model_to_use}")
                
                # Enable remote services for API calls
                pipeline_options.enable_remote_services = True
                pipeline_options.do_picture_description = True
                
                # Format API key as Bearer token in header
                headers = {"Authorization": f"Bearer {api_key}"}
                
                # Add model to request params
                params = {"model": model_to_use}
                
                pipeline_options.picture_description_options = PictureDescriptionApiOptions(
                    url=api_url,
                    headers=headers,
                    params=params,
                    prompt=prompt,
                    picture_area_threshold=0  # Process all images regardless of size
                )
        else:
            logger.info(f"VLM mode is NONE - skipping picture description")
        
        return pipeline_options

    async def extract(self, file: UploadFile, ocr_enabled: bool = True, table_extraction_enabled: bool = True, vlm_mode: VlmMode = VlmMode.NONE, vlm_model_id: Optional[str] = None) -> ExtractionResponse:
        logger.info(f"Starting extraction for file: {file.filename}")
        
        # Configure pipeline based on options
        pipeline_options = self._get_pipeline_options(ocr_enabled, table_extraction_enabled, vlm_mode, vlm_model_id)
        
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

            # Export to markdown with page break markers
            markdown_content = doc.export_to_markdown(page_break_placeholder="\n\n---\n## PAGE_BREAK_MARKER\n\n")
            
            # Post-process to add actual page numbers
            page_counter = 1
            markdown_lines = []
            for line in markdown_content.split('\n'):
                if line.strip() == "## PAGE_BREAK_MARKER":
                    page_counter += 1
                    markdown_lines.append(f"## Page {page_counter}")
                else:
                    markdown_lines.append(line)
            
            # Add page 1 marker at the beginning if there are multiple pages
            if page_counter > 1:
                markdown_content = f"## Page 1\n\n" + '\n'.join(markdown_lines)
            else:
                markdown_content = '\n'.join(markdown_lines)
            
            logger.info("Extraction completed successfully")
            
            logger.info(f"Markdown content type: {type(markdown_content)}")
            logger.info(f"Tables type: {type(tables)}")
            if tables:
                logger.info(f"Table 0 type: {type(tables[0])}")
            logger.info(f"Filename type: {type(file.filename)}")
            logger.info(f"Page count type: {type(doc.num_pages)}")
            
            return ExtractionResponse(
                markdown=markdown_content,
                tables=tables,
                metadata={
                    "filename": file.filename,
                    "page_count": doc.num_pages() if callable(doc.num_pages) else doc.num_pages
                }
            )

    async def extract_from_path(self, file_path: Union[str, Path], ocr_enabled: bool = True, table_extraction_enabled: bool = True, vlm_mode: VlmMode = VlmMode.NONE, vlm_model_id: Optional[str] = None) -> ExtractionResponse:
        """
        Extracts content from a local file path. Useful for programmatic usage.
        """
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Starting extraction for local file: {path_obj.name}")
        
        # Configure pipeline based on options
        pipeline_options = self._get_pipeline_options(ocr_enabled, table_extraction_enabled, vlm_mode, vlm_model_id)
        
        # Create a new converter instance with specific options
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        # Convert the document
        result = converter.convert(path_obj)
        doc = result.document
        
        # Extract markdown
        # Export to markdown with page break markers
        markdown_content = doc.export_to_markdown(page_break_placeholder="\n\n---\n## PAGE_BREAK_MARKER\n\n")
        
        # Post-process to add actual page numbers
        page_counter = 1
        markdown_lines = []
        for line in markdown_content.split('\n'):
            if line.strip() == "## PAGE_BREAK_MARKER":
                page_counter += 1
                markdown_lines.append(f"## Page {page_counter}")
            else:
                markdown_lines.append(line)
        
        # Add page 1 marker at the beginning if there are multiple pages
        if page_counter > 1:
            markdown_content = f"## Page 1\n\n" + '\n'.join(markdown_lines)
        else:
            markdown_content = '\n'.join(markdown_lines)
        
        # Extract tables
        tables = []
        if table_extraction_enabled:
            for table in doc.tables:
                grid = table.export_to_dataframe()
                if not grid.empty:
                    tables.append(TableData(
                        data=grid.values.tolist(),
                        headers=grid.columns.tolist()
                    ))
        
        return ExtractionResponse(
            markdown=markdown_content,
            tables=tables,
            metadata={
                "filename": path_obj.name,
                "page_count": doc.num_pages() if callable(doc.num_pages) else doc.num_pages
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

    def warmup(self, vlm_mode: VlmMode = VlmMode.NONE, vlm_model_id: Optional[str] = None):
        """
        Triggers the download of necessary models (OCR, Table Extraction) by running a dummy conversion.
        """
        logger.info(f"Starting warmup with vlm_mode={vlm_mode}...")
        
        # Enable everything to force download
        pipeline_options = self._get_pipeline_options(ocr_enabled=True, table_extraction_enabled=True, vlm_mode=vlm_mode, vlm_model_id=vlm_model_id)
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
