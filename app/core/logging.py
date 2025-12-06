import logging
import sys
from app.core.config import settings

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    # Force external libraries to be verbose
    logging.getLogger("docling").setLevel(logging.DEBUG) 
    logging.getLogger("transformers").setLevel(logging.INFO)
    logging.getLogger("huggingface_hub").setLevel(logging.INFO)
