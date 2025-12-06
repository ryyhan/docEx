# DocEx Project Documentation

DocEx is a high-performance, FastAPI-based microservice for document extraction. It leverages [Docling](https://github.com/DS4SD/docling) to convert PDF documents into structured Markdown, with optional support for OCR, Table Extraction, and Vision Language Models (VLM) for image description.

## Table of Contents
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)

---

## Configuration

The application is configured via environment variables. You can set these in a `.env` file in the root directory.

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `STORAGE_DIR` | Directory where extracted files are saved (for `/extract-and-save`). | `./results` | No |
| `OPENAI_API_KEY` | API Key for OpenAI. Required if using `vlm_mode="api"`. | `None` | Conditional |
| `VLM_PROMPT` | Custom prompt for image description. Set to `"default"` to use the built-in optimized prompt. | `"default"` | No |
| `DEBUG` | Enable debug logging. | `False` | No |

---

## Supported Formats
The API is optimized for **PDF** documents, where it provides granular control over OCR and table extraction.

- **PDF** (`.pdf`): Full support with configurable OCR, Table Extraction, and VLM.
- **Other Formats**: The underlying Docling engine also supports `DOCX`, `PPTX`, `HTML`, and Images. These will be processed using Docling's default settings for those formats. The `ocr_enabled` and `table_extraction_enabled` flags primarily affect the PDF pipeline.

---

## API Reference

### `POST /api/v1/extract`

Extracts content from a uploaded document and returns the structured data.

**Parameters (Form Data):**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | Required | The document file to upload (PDF, etc.). |
| `ocr_enabled` | Boolean | `true` | Enable OCR for scanned documents. Set to `false` for digital PDFs to improve speed. |
| `table_extraction_enabled` | Boolean | `true` | Enable advanced table structure recognition. |
| `vlm_mode` | Enum | `none` | Image Description mode. Options: `none`, `local`, `api`. |
| `vlm_model_id` | String | `None` | Specific model ID to use. <br>For `local`: Hugging Face Repo ID (e.g., `HuggingFaceTB/SmolVLM-256M-Instruct`).<br>For `api`: Model name (e.g., `gpt-4o`). |

**Response:** JSON object containing `markdown`, `tables`, and `metadata`.

### `POST /api/v1/extract-and-save`

Same as `/extract`, but also saves the resulting Markdown file to the server's `STORAGE_DIR`.

**Response:** JSON object containing `message`, `saved_path`, and the extraction result.

### Response Structure
The API returns a JSON object with the following fields:

- **`markdown`** (string): The full document content converted to Markdown format. Multi-page PDFs will include page separators (e.g., `## Page 2`) between pages. Tables are represented as Markdown tables, and images are described (if VLM is enabled).
- **`tables`** (list): A list of extracted tables. Each item contains:
    - `data`: 2D array of cell values.
    - `headers`: List of column headers.
- **`metadata`** (object):
    - `filename`: Original filename.
    - `page_count`: Number of pages in the document.

### `POST /api/v1/warmup`

Triggers the download and loading of necessary models to ensure subsequent requests are fast.

**Parameters (Form Data):**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vlm_mode` | Enum | `none` | If set to `local` or `api`, will also preload VLM models/clients. |
| `vlm_model_id` | String | `None` | Specific model ID to preload. |

### Error Codes
The API uses standard HTTP status codes to indicate success or failure.

| Code | Description |
|------|-------------|
| `200` | **Success**: The extraction was successful. |
| `400` | **Bad Request**: Missing filename or invalid parameters. |
| `422` | **Validation Error**: Invalid input data (e.g., wrong type for a parameter). |
| `500` | **Internal Server Error**: An error occurred during processing (e.g., model failure, disk error). Check server logs for details.

### Warmup Strategy
The `/warmup` endpoint is designed to initialize the heavy machine learning models (OCR, Table Former, VLM) into memory *before* you serve user traffic.

- **Recommended**: Call this endpoint immediately after your application starts (e.g., in your Kubernetes readiness probe or startup script).
- **Optional**: If you **only** process digital-native PDFs (no scans) and set `ocr_enabled=false`, the startup overhead is minimal, and you might skip warmup.
- **Impact**: Skipping warmup means the first user request will take significantly longer (10-30s) as models load on demand.

### ⚠️ Critical: Model Consistency
**You must warmup with the same model you intend to use for extraction.**

If you warmup with the default model (e.g., `SmolVLM-256M`) but then send an extraction request with a *different* model (e.g., `idefics2-8b`):
1.  The system will have to **unload** the warmed-up model.
2.  It will then **download/load** the new model on the fly.
3.  This results in a **double penalty** and a very slow request.

**Best Practice**: Define your target model in your deployment configuration and ensure both the `/warmup` call and your client applications use that exact same `vlm_model_id`.

---

## Usage Guide

### 1. Basic Extraction
Extract a document with default settings (OCR and Tables enabled).

```bash
curl -X POST -F "file=@/path/to/document.pdf" http://localhost:8000/api/v1/extract
```

### 2. Performance Mode (Fast Extraction)
If your PDF is digital-native (not scanned), disable OCR for significantly faster processing.

```bash
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "ocr_enabled=false" \
  http://localhost:8000/api/v1/extract
```

### 3. Image Description (VLM)

Replace `<!-- image -->` placeholders with actual descriptions using AI.

#### Local Mode (Free, Private)
Uses a local model (default: `HuggingFaceTB/SmolVLM-256M-Instruct`). Requires ~1-2GB RAM.

```bash
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "vlm_mode=local" \
  http://localhost:8000/api/v1/extract
```

#### API Mode (High Quality)
Uses OpenAI (default: `gpt-4o`). Requires `OPENAI_API_KEY` to be set.

```bash
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "vlm_mode=api" \
  http://localhost:8000/api/v1/extract
```

#### Custom Model
You can specify a different model for either mode.

**Example: Using a specific local model**
```bash
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "vlm_mode=local" \
  -F "vlm_model_id=HuggingFaceM4/idefics2-8b" \
  http://localhost:8000/api/v1/extract
```

**Example: Using a specific OpenAI model**
```bash
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "vlm_mode=api" \
  -F "vlm_model_id=gpt-4-turbo" \
  http://localhost:8000/api/v1/extract
```

### 4. Performance Considerations & Best Practices

#### OCR vs. Digital PDFs
- **Digital PDFs**: Documents created directly from text editors (Word, Google Docs, LaTeX). These contain embedded text.
    - **Action**: Set `ocr_enabled=false`.
    - **Benefit**: Extraction is extremely fast (< 1s/page) and accurate.
    - **Tip**: Try selecting text in your PDF viewer. If you can select individual words easily, it's likely a digital PDF.
- **Scanned Documents**: Images of documents.
    - **Action**: Keep `ocr_enabled=true` (default).
    - **Cost**: Slower processing (seconds per page) as the OCR engine must analyze the image.

#### VLM Model Switching
The system supports dynamic model selection via `vlm_model_id`. However, be aware of the performance implications:
- **Model Loading**: When you request a *new* local model that isn't currently loaded, the system must unload the old one and load the new one into RAM. This takes time (seconds to minutes depending on model size).
- **Production Tip**: In a production environment, try to standardize on a single VLM model to avoid constant reloading penalties. If you need multiple models, consider deploying separate instances of the service.

#### Local vs. API VLM
- **Local**:
    - **Pros**: Data privacy (no data leaves your server), no per-token cost.
    - **Cons**: High RAM usage, slower inference (depending on GPU/CPU), initial download time.
- **API (OpenAI)**:
    - **Pros**: State-of-the-art quality, zero local RAM usage, fast inference.
    - **Cons**: Per-request cost, data privacy considerations.

#### Recommended Models
Here are some tested models you can use with `vlm_model_id`:

| Model ID | Type | Size | Notes |
|----------|------|------|-------|
| `HuggingFaceTB/SmolVLM-256M-Instruct` | Local | ~1GB | **Default**. Very fast, low memory. Good for simple descriptions. |
| `HuggingFaceTB/SmolVLM-Instruct` | Local | ~5GB | Better quality than 256M, but requires more RAM/VRAM. |
| `HuggingFaceM4/idefics2-8b` | Local | ~16GB | High quality, requires powerful GPU (A10/A100). |
| `gpt-4o` | API | N/A | **Default API**. Best overall quality. |
| `gpt-4-turbo` | API | N/A | Alternative high-quality API model. |

### 5. Deployment Recommendations
- **CPU vs GPU**: For local VLM, a GPU is highly recommended. On CPU, models like `SmolVLM` might take 5-10 seconds per image.
- **Memory**: Allocate at least 4GB RAM for the container if using Local VLM. If using only API mode or no VLM, 1-2GB is sufficient.
- **Concurrency**: The `DocumentConverter` is thread-safe, but heavy models (VLM/OCR) are compute-bound. For high throughput, run multiple workers (e.g., `uvicorn ... --workers 4`) or multiple replicas behind a load balancer.

### 6. Custom Prompts
To use a custom prompt for image description, set the `VLM_PROMPT` environment variable in your `.env` file.

```bash
VLM_PROMPT="Describe this image briefly for a blind user."
```

---

## Docker Deployment

The project includes a `Dockerfile` for easy containerization.

### Build the Image
```bash
docker build -t docex-api .
```

### Run the Container
```bash
docker run -d -p 8000:8000 \
  -e OPENAI_API_KEY="sk-..." \
  -e VLM_PROMPT="default" \
  -v $(pwd)/results:/app/results \
  docex-api
```

### Docker Compose (Recommended)
Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  docex:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./results:/app/results
```

---

## Development Setup

### Prerequisites
- Python 3.10+
- `pip`

### Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/ryyhan/docEx.git
   cd docEx
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**:
   ```bash
   python3 main.py
   ```

---

## Programmatic Usage (Library Mode)

You can use DocEx as a Python library in your own scripts without running the API server.

### Example
```python
import asyncio
from app.services.extraction import ExtractionService
from app.schemas.enums import VlmMode

async def main():
    service = ExtractionService()
    
    # Extract from a local file
    result = await service.extract_from_path(
        file_path="my_document.pdf",
        ocr_enabled=False,
        vlm_mode=VlmMode.LOCAL
    )
    
    print(f"Extracted {result.metadata.page_count} pages.")
    print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Troubleshooting

### "Not enough free disk space"
If you see this error when using `vlm_mode=local`, the default model might be too large for your disk.
**Solution**: Use a smaller model by setting `vlm_model_id` (e.g., `HuggingFaceTB/SmolVLM-256M-Instruct`) or free up disk space.

### "VLM API mode requested but OPENAI_API_KEY is not set"
You are trying to use `vlm_mode=api` but haven't configured the API key.
**Solution**: Set `OPENAI_API_KEY` in your `.env` file or environment variables.

### Slow First Request
The first request often takes longer because models are being loaded into memory.
**Solution**: Call the `/warmup` endpoint immediately after starting the server.
```bash
curl -X POST http://localhost:8000/api/v1/warmup
```
