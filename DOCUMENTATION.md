# DocEx-Serve Documentation

**DocEx-Serve** is a FastAPI-based service that extracts structured content from PDFs and other documents using [Docling](https://github.com/DS4SD/docling). It provides OCR, table extraction, and multi-provider VLM (Vision Language Model) support for image descriptions.

---

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install docex-serve
```

### Option 2: Install from Source

```bash
git clone https://github.com/ryyhan/docEx.git
cd docEx
pip install -r requirements.txt
```

### Option 3: Docker

```bash
docker pull rehank25/docex-serve  # Once published
# Or build locally
docker build -t docex-serve .
docker run -p 8000:8000 docex-serve
```

---

---

## Quick Start

### Start the Server

**Using CLI (after pip install):**
```bash
docex-server
# Or with options
docex-server --host 0.0.0.0 --port 8080 --reload
```

**Using Python:**
```python
from docex_serve import start_server
start_server(port=8080)
```

**Using local development:**
```bash
python3 main.py
```

### Extract Your First Document

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@document.pdf" \
  -F "ocr_enabled=true"
```

Or visit http://localhost:8000/docs for the interactive API documentation.

---

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
| `VLM_API_PROVIDER` | VLM API provider. Options: `openai`, `groq`, `anthropic`, `google`, `azure`, `custom`. | `openai` | No |
| `VLM_API_KEY` | API key for the selected VLM provider. | `None` | Conditional (required for `vlm_mode=api`) |
| `VLM_API_BASE_URL` | Custom API endpoint URL (for Azure or custom providers). | `None` | Conditional (required for Azure/custom) |
| `OPENAI_API_KEY` | **Deprecated.** Use `VLM_API_KEY` instead. Legacy support maintained. | `None` | No |
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

### `POST /api/v1/batch-extract`

Process multiple PDF files in a single request.

**Parameters (Form Data):**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `files` | List[File] | Required | Multiple document files to upload. |
| `ocr_enabled` | Boolean | `true` | Enable OCR for scanned documents. |
| `table_extraction_enabled` | Boolean | `true` | Enable table structure recognition. |
| `vlm_mode` | Enum | `none` | Image Description mode. Options: `none`, `local`, `api`. |
| `vlm_model_id` | String | `None` | Specific model ID to use. |

**Response:** JSON object containing:
- `results`: Array of individual file results (each with `filename`, `status`, `markdown`, `tables`, `metadata`, or `error`)
- `total_files`: Total number of files processed
- `successful`: Count of successfully processed files
- `failed`: Count of failed files

**Note:** Individual file failures won't stop processing of other files.

### `POST /api/v1/extract-json`

Extract content and return as structured JSON.

**Parameters:** Same as `/extract`

**Response:** JSON object containing:
- `content`: Structured document with `markdown` and `tables`
- `metadata`: Document metadata

### `POST /api/v1/extract-html`

Extract content and return as formatted HTML.

**Parameters:** Same as `/extract`

**Response:** HTML document with CSS styling (Content-Type: `text/html`)

### `POST /api/v1/extract-text`

Extract content and return as plain text.

**Parameters:** Same as `/extract`

**Response:** Plain text without markdown formatting (Content-Type: `text/plain`)

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

#### API Mode - Multi-Provider Support

DocEx supports multiple VLM API providers. Configure the provider in your `.env` file:

```bash
# .env file
VLM_API_PROVIDER=groq  # Options: openai, groq, anthropic, google, azure, custom
VLM_API_KEY=your-api-key-here
```

**Supported Providers:**

| Provider | Default Model | Notes |
|----------|---------------|-------|
| `openai` | gpt-4o | OpenAI GPT-4 with vision |
| `groq` | llama-3.2-11b-vision-preview | Fast, free tier available |
| `anthropic` | claude-3-5-sonnet-20241022 | High quality vision understanding |
| `google` | gemini-1.5-pro | Google's multimodal model |
| `azure` | gpt-4o | Requires custom endpoint URL |
| `custom` | gpt-4o | Any OpenAI-compatible API |

**Example: Groq (Fast & Free)**
```bash
# .env
VLM_API_PROVIDER=groq
VLM_API_KEY=gsk_your_groq_key

# API Request
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "vlm_mode=api" \
  http://localhost:8000/api/v1/extract
```

**Example: Google Gemini**
```bash
# .env
VLM_API_PROVIDER=google
VLM_API_KEY=your_google_api_key

# API Request (uses gemini-1.5-pro by default)
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "vlm_mode=api" \
  http://localhost:8000/api/v1/extract
```

**Example: Anthropic Claude**
```bash
# .env
VLM_API_PROVIDER=anthropic
VLM_API_KEY=sk-ant-your_key

# API Request
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "vlm_mode=api" \
  http://localhost:8000/api/v1/extract
```

**Example: Azure OpenAI**
```bash
# .env
VLM_API_PROVIDER=azure
VLM_API_KEY=your_azure_key
VLM_API_BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2024-02-15-preview

# API Request
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

**Example: Using a specific API model**
```bash
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  -F "vlm_mode=api" \
  -F "vlm_model_id=gpt-4-turbo" \
  http://localhost:8000/api/v1/extract
```

### 4. Batch Processing

Process **multiple PDF files** in a single API request.

**Endpoint:** `POST /api/v1/batch-extract`

**Features:**
- Upload multiple files at once
- Individual success/error status per file
- One file failing won't stop others
- Returns summary statistics

**Basic Example:**
```bash
curl -X POST http://localhost:8000/api/v1/batch-extract \
  -F "files=@invoice1.pdf" \
  -F "files=@invoice2.pdf" \
  -F "files=@invoice3.pdf" \
  -F "ocr_enabled=true"
```

**With VLM:**
```bash
curl -X POST http://localhost:8000/api/v1/batch-extract \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "vlm_mode=api" \
  -F "table_extraction_enabled=true"
```

**Response Format:**
```json
{
  "results": [
    {
      "filename": "invoice1.pdf",
      "status": "success",
      "markdown": "## Page 1\n\n...",
      "tables": [],
      "metadata": {"page_count": 2}
    },
    {
      "filename": "invoice2.pdf",
      "status": "error",
      "error": "File corrupted"
    }
  ],
  "total_files": 2,
  "successful": 1,
  "failed": 1
}
```

**Use Cases:**
- Process 50 invoices for accounting
- Batch convert contracts for analysis
- Screen multiple resumes
- Migrate document archives

### 5. Performance Considerations & Best Practices

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
```

## Programmatic Usage (Library Mode)

You can use DocEx as a Python library in your own scripts without running the API server.

### Single File Extraction
```python
import asyncio
from docex_serve import ExtractionService, VlmMode

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

### Batch Processing Multiple Files
```python
import asyncio
from pathlib import Path
from docex_serve import ExtractionService, VlmMode

async def batch_process():
    service = ExtractionService()
    files = ["invoice1.pdf", "invoice2.pdf", "invoice3.pdf"]
    results = []
    
    for file_path in files:
        try:
            result = await service.extract_from_path(
                file_path=file_path,
                ocr_enabled=True,
                vlm_mode=VlmMode.API
            )
            results.append({
                "filename": file_path,
                "status": "success",
                "markdown": result.markdown,
                "page_count": result.metadata["page_count"]
            })
            print(f"✓ Processed {file_path}")
        except Exception as e:
            results.append({
                "filename": file_path,
                "status": "error",
                "error": str(e)
            })
            print(f"✗ Failed {file_path}: {e}")
    
    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    print(f"\nProcessed {len(files)} files: {successful} successful, {len(files)-successful} failed")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(batch_process())
```

### Using Different Output Formats

```python
import asyncio
from docex_serve import ExtractionService, VlmMode

async def export_formats():
    service = ExtractionService()
    
    # Extract once
    result = await service.extract_from_path(
        file_path="document.pdf",
        ocr_enabled=True
    )
    
    # JSON format (already structured)
    json_output = {
        "content": {
            "markdown": result.markdown,
            "tables": [{"data": t.data, "headers": t.headers} for t in result.tables]
        },
        "metadata": result.metadata
    }
    
    # HTML format
    import markdown
    html_content = markdown.markdown(result.markdown, extensions=['tables'])
    full_html = f"""<!DOCTYPE html>
<html>
<head><title>Document</title></head>
<body>{html_content}</body>
</html>"""
    
    # Plain text format (strip markdown)
    import re
    text = result.markdown
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)  # Remove headers
    text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)   # Remove bold/italic
    
    # Save to files
    import json
    with open("output.json", "w") as f:
        json.dump(json_output, f, indent=2)
    
    with open("output.html", "w") as f:
        f.write(full_html)
    
    with open("output.txt", "w") as f:
        f.write(text)
    
    print("Exported to JSON, HTML, and TXT")

if __name__ == "__main__":
    asyncio.run(export_formats())
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
