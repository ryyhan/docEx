"""
Programmatic server launcher for DocEx-Serve.
Allows users to start the server from Python code.
"""

import uvicorn


def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: int = 1
):
    """
    Start the DocEx-Serve FastAPI server programmatically.
    
    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 8000)
        reload: Enable auto-reload (default: False)
        workers: Number of worker processes (default: 1)
    
    Example:
        >>> from docex_serve import start_server
        >>> start_server(port=8080)
    """
    print(f"Starting DocEx-Serve on {host}:{port}")
    print(f"API documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "docex_serve.app.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1
    )
