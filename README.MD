# DocEx API

DocEx is a robust document extraction backend built with [FastAPI](https://fastapi.tiangolo.com/) and [Docling](https://github.com/DS4SD/docling). It provides a simple yet powerful API to convert documents (PDFs, etc.) into structured Markdown and table data.

# DocEx-Serve

A powerful FastAPI-based document extraction service with multi-provider VLM support, batch processing, and multiple output formats.

## Features

- 📄 **PDF Extraction** - Convert PDFs to markdown with preserved structure
- 🔍 **OCR Support** - Extract text from scanned documents
- 📊 **Table Extraction** - Preserve table structure
- 🖼️ **Image Descriptions** - AI-powered image descriptions via VLM
- 🔄 **Multi-Provider VLM** - OpenAI, Groq, Anthropic, Google Gemini, Azure
- 📦 **Batch Processing** - Process multiple PDFs in one request
- 📋 **Multiple Output Formats** - Markdown, JSON, HTML, Plain Text
- 📄 **Page Numbers** - Automatic page numbering in multi-page PDFs

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
docker pull rehank25/docex-serve
docker run -p 8000:8000 docex-serve
```

## Quick Start

### Start the Server

**After pip install:**
```bash
docex-server
# Or with options
docex-server --host 0.0.0.0 --port 8080
```

**Using Python:**
```python
from docex_serve import start_server
start_server(port=8080)
```

**For development (from source):**
```bash
python3 main.py
```

Visit `http://localhost:8000/docs` for interactive API documentation.

### Extract Your First Document

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@document.pdf" \
  -F "ocr_enabled=true"
```

## Usage Examples

### Basic Extraction

-   **Swagger UI**: `http://localhost:8000/docs`
-   **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### `POST /api/v1/extract`

Upload a file to extract its content.

**Request:**
**Request:**
-   `file`: The document file to upload (multipart/form-data).
-   `ocr_enabled`: (Optional) Enable OCR for scanned documents. Default: `true`. Set to `false` for faster processing of digital PDFs.
-   `table_extraction_enabled`: (Optional) Enable advanced table structure recognition. Default: `true`.
-   `vlm_mode`: (Optional) Enable Image Description. Options: `none` (default), `local` (uses SmolVLM), `api` (uses OpenAI GPT-4o).

#### `POST /api/v1/extract-and-save`

Same as `/extract`, but saves the resulting Markdown file to the server's storage directory.

**Response:**
```json
{
  "message": "Extraction successful and file saved.",
  "saved_path": "/path/to/results/filename_timestamp.md",
  "extraction": { ... }
}
```

#### `POST /api/v1/warmup`

Triggers the download and loading of OCR and Table Extraction models. Call this once at startup to avoid delays on the first request.

**Response:**
```json
{
  "message": "Warmup completed successfully"
**Response:**
```json
{
  "markdown": "## Page 1\n\n# Document Title\n\nContent...\n\n---\n## Page 2\n\nMore content...",
  "tables": [
    {
      "data": [["Row 1 Col 1", "Row 1 Col 2"], ["Row 2 Col 1", "Row 2 Col 2"]],
      "headers": ["Header 1", "Header 2"]
    }
  ],
  "metadata": {
    "filename": "example.pdf",
    "page_count": 5
  }
}
```

#### `GET /health`

Health check endpoint to verify the service is running.

**Response:**
```json
{
  "status": "ok"
}
```

## Performance Optimization

Docling uses powerful AI models for OCR and Table Extraction. These models are downloaded on the first run, which can take time.

1.  **Warmup**: Call `POST /api/v1/warmup` immediately after deployment to download models.
2.  **Disable OCR**: If you are processing digital-native PDFs (not scanned images), set `ocr_enabled=false` in your request to significantly speed up extraction.

## Image Description (VLM)

You can enable image description to replace `<!-- image -->` tags with actual descriptions.

### Modes
1.  **Local (`vlm_mode="local"`)**:
    -   Uses `HuggingFaceTB/SmolVLM-256M-Instruct`.
    -   **Pros**: Free, private.
    -   **Cons**: Requires ~1-2GB RAM, slower warmup.
2.  **API (`vlm_mode="api"`)**:
    -   Uses OpenAI GPT-4o.
    -   **Pros**: Fast, high quality, no local model download.
    -   **Cons**: Costs money, requires `OPENAI_API_KEY`.

### Setup for API Mode
Set the `OPENAI_API_KEY` environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```

## Configuration

Configuration is managed via environment variables (or a `.env` file). Key settings include:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PROJECT_NAME` | Name of the project | "DocEx API" |
| `API_V1_STR` | API version prefix | "/api/v1" |
| `DEBUG` | Enable debug mode | `False` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `["*"]` |

## Project Structure

```
docEx/
├── app/
│   ├── api/            # API route definitions
│   ├── core/           # Core config and logging
│   ├── schemas/        # Pydantic models
│   ├── services/       # Business logic (Docling integration)
│   └── main.py         # FastAPI app factory
├── tests/              # Test suite
├── Dockerfile          # Docker build instructions
├── main.py             # Entry point for running the app
└── requirements.txt    # Project dependencies
```