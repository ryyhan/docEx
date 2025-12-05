# DocEx API

DocEx is a robust document extraction backend built with [FastAPI](https://fastapi.tiangolo.com/) and [Docling](https://github.com/DS4SD/docling). It provides a simple yet powerful API to convert documents (PDFs, etc.) into structured Markdown and table data.

## Features

-   **Document Conversion**: Converts documents to clean Markdown format.
-   **Table Extraction**: Identifies and extracts tables from documents into structured data (JSON/DataFrame-ready).
-   **FastAPI Powered**: High-performance, easy-to-use REST API.
-   **Docker Ready**: Includes a Dockerfile for easy containerization and deployment.
-   **Performance Optimized**: Configurable OCR and Table Extraction settings.
-   **Image Description**: Optional VLM support (Local or API) to describe images in documents.
-   **Warmup Endpoint**: Pre-load models for faster first-request performance.
-   **Swagger UI**: Automatic interactive API documentation.

## Requirements

-   Python 3.11+
-   Docker (optional, for containerized execution)

## Installation

### Local Development

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd docEx
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running Locally

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Running with Docker

1.  **Build the Docker image:**
    ```bash
    docker build -t docex .
    ```

2.  **Run the container:**
    ```bash
    docker run -p 8000:8000 docex
    ```

## API Documentation

Once the server is running, you can access the interactive API documentation at:

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
}
```

**Response:**
```json
{
  "markdown": "# Document Title\n\nContent...",
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