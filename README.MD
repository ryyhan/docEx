# DocEx API

DocEx is a robust document extraction backend built with [FastAPI](https://fastapi.tiangolo.com/) and [Docling](https://github.com/DS4SD/docling). It provides a simple yet powerful API to convert documents (PDFs, etc.) into structured Markdown and table data.

## Features

-   **Document Conversion**: Converts documents to clean Markdown format.
-   **Table Extraction**: Identifies and extracts tables from documents into structured data (JSON/DataFrame-ready).
-   **FastAPI Powered**: High-performance, easy-to-use REST API.
-   **Docker Ready**: Includes a Dockerfile for easy containerization and deployment.
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
-   `file`: The document file to upload (multipart/form-data).

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