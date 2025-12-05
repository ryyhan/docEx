from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from app.services.extraction import ExtractionService
from app.schemas.extraction import ExtractionResponse

router = APIRouter()

# Dependency injection for the service
def get_extraction_service():
    return ExtractionService()

@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: UploadFile = File(...),
    ocr_enabled: bool = Form(True),
    table_extraction_enabled: bool = Form(True),
    service: ExtractionService = Depends(get_extraction_service)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    try:
        return await service.extract(file, ocr_enabled, table_extraction_enabled)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-and-save")
async def extract_and_save_document(
    file: UploadFile = File(...),
    ocr_enabled: bool = Form(True),
    table_extraction_enabled: bool = Form(True),
    service: ExtractionService = Depends(get_extraction_service)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    try:
        extraction_response = await service.extract(file, ocr_enabled, table_extraction_enabled)
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
    service: ExtractionService = Depends(get_extraction_service)
):
    try:
        service.warmup()
        return {"message": "Warmup completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
