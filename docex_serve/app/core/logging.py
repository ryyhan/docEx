import logging
import sys
from .config import settings

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    # Set external libraries to INFO level (less verbose)
    logging.getLogger("docling").setLevel(logging.INFO) 
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
