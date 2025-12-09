from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from ..services.extraction import ExtractionService
from ..schemas.extraction import (
    ExtractionResponse, BatchExtractionResponse, BatchFileResult,
    JsonExtractionResponse, HtmlExtractionResponse, TextExtractionResponse
)
from ..schemas.enums import VlmMode
from typing import Optional, List
import logging

router = APIRouter()

# Dependency injection for the service
def get_extraction_service():
    return ExtractionService()

@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    ocr_enabled: bool = Form(True),
    table_extraction_enabled: bool = Form(True),
    vlm_mode: VlmMode = Form(VlmMode.NONE),
    vlm_model_id: Optional[str] = Form(None),
    service: ExtractionService = Depends(get_extraction_service)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received extract request - vlm_mode: {vlm_mode}, vlm_model_id: {vlm_model_id}, ocr: {ocr_enabled}, tables: {table_extraction_enabled}")
    
    try:
        return await service.extract(file, ocr_enabled, table_extraction_enabled, vlm_mode, vlm_model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-and-save")
async def extract_and_save_document(
    file: UploadFile = File(...),
    ocr_enabled: bool = Form(True),
    table_extraction_enabled: bool = Form(True),
    vlm_mode: VlmMode = Form(VlmMode.NONE),
    vlm_model_id: Optional[str] = Form(None),
    service: ExtractionService = Depends(get_extraction_service)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Received extract-and-save request - vlm_mode: {vlm_mode}, vlm_model_id: {vlm_model_id}, ocr: {ocr_enabled}, tables: {table_extraction_enabled}")
    
    try:
        extraction_response = await service.extract(file, ocr_enabled, table_extraction_enabled, vlm_mode, vlm_model_id)
        saved_path = await service.save_markdown(extraction_response.markdown, file.filename)
        return {
            "message": "Extraction successful and file saved.",
            "saved_path": saved_path,
            "extraction": extraction_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warmup")
async def warmup_service(
    vlm_mode: VlmMode = Form(VlmMode.NONE),
    vlm_model_id: Optional[str] = Form(None),
    service: ExtractionService = Depends(get_extraction_service)
):
    try:
        service.warmup(vlm_mode, vlm_model_id)
        return {"message": "Warmup completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-extract", response_model=BatchExtractionResponse)
async def batch_extract_documents(
    files: List[UploadFile] = File(...),
    ocr_enabled: bool = Form(True),
    table_extraction_enabled: bool = Form(True),
    vlm_mode: VlmMode = Form(VlmMode.NONE),
    vlm_model_id: Optional[str] = Form(None),
    service: ExtractionService = Depends(get_extraction_service)
):
    """
    Extract content from multiple PDF files in a single request.
    
    Returns results for each file with individual success/error status.
    One file failing won't prevent others from processing.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Received batch extract request for {len(files)} files - vlm_mode: {vlm_mode}, ocr: {ocr_enabled}, tables: {table_extraction_enabled}")
    
    results = []
    
    for file in files:
        try:
            if not file.filename:
                results.append(BatchFileResult(
                    filename="unknown",
                    status="error",
                    error="No filename provided"
                ))
                continue
                
            logger.info(f"Processing file: {file.filename}")
            result = await service.extract(file, ocr_enabled, table_extraction_enabled, vlm_mode, vlm_model_id)
            
            results.append(BatchFileResult(
                filename=file.filename,
                status="success",
                markdown=result.markdown,
                tables=result.tables,
                metadata=result.metadata
            ))
            logger.info(f"Successfully processed: {file.filename}")
            
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            results.append(BatchFileResult(
                filename=file.filename if hasattr(file, 'filename') else "unknown",
                status="error",
                error=str(e)
            ))
    
    successful = sum(1 for r in results if r.status == "success")
    failed = len(results) - successful
    
    logger.info(f"Batch processing complete - Total: {len(results)}, Successful: {successful}, Failed: {failed}")
    
    return BatchExtractionResponse(
        results=results,
        total_files=len(files),
        successful=successful,
        failed=failed
    )

@router.post("/extract-json", response_model=JsonExtractionResponse)
async def extract_document_json(
    file: UploadFile = File(...),
    ocr_enabled: bool = Form(True),
    table_extraction_enabled: bool = Form(True),
    vlm_mode: VlmMode = Form(VlmMode.NONE),
    vlm_model_id: Optional[str] = Form(None),
    service: ExtractionService = Depends(get_extraction_service)
):
    """
    Extract content and return as structured JSON.
    
    Returns the full document structure in JSON format with all metadata.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    logger = logging.getLogger(__name__)
    logger.info(f"Received extract-json request for {file.filename}")
    
    try:
        result = await service.extract(file, ocr_enabled, table_extraction_enabled, vlm_mode, vlm_model_id)
        # Convert document to dict/JSON - using markdown for now, can enhance later
        return JsonExtractionResponse(
            content={
                "markdown": result.markdown,
                "tables": [{"data": t.data, "headers": t.headers} for t in result.tables]
            },
            metadata=result.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-html")
async def extract_document_html(
    file: UploadFile = File(...),
    ocr_enabled: bool = Form(True),
    table_extraction_enabled: bool = Form(True),
    vlm_mode: VlmMode = Form(VlmMode.NONE),
    vlm_model_id: Optional[str] = Form(None),
    service: ExtractionService = Depends(get_extraction_service)
):
    """
    Extract content and return as HTML.
    
    Returns the document formatted as HTML.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    logger = logging.getLogger(__name__)
    logger.info(f"Received extract-html request for {file.filename}")
    
    try:
        result = await service.extract(file, ocr_enabled, table_extraction_enabled, vlm_mode, vlm_model_id)
        # Convert markdown to basic HTML
        import markdown
        html_content = markdown.markdown(result.markdown, extensions=['tables'])
        
        # Wrap in basic HTML structure
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{result.metadata.get('filename', 'Document')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        return HTMLResponse(content=full_html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-text")
async def extract_document_text(
    file: UploadFile = File(...),
    ocr_enabled: bool = Form(True),
    table_extraction_enabled: bool = Form(True),
    vlm_mode: VlmMode = Form(VlmMode.NONE),
    vlm_model_id: Optional[str] = Form(None),
    service: ExtractionService = Depends(get_extraction_service)
):
    """
    Extract content and return as plain text.
    
    Returns the document as plain text without formatting.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    logger = logging.getLogger(__name__)
    logger.info(f"Received extract-text request for {file.filename}")
    
    try:
        result = await service.extract(file, ocr_enabled, table_extraction_enabled, vlm_mode, vlm_model_id)
        # Strip markdown formatting to get plain text
        import re
        text = result.markdown
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove markdown bold/italic
        text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        return PlainTextResponse(content=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
