#!/usr/bin/env python3
"""
CLI entry point for DocEx-Serve.
Allows users to start the server via `docex-server` command.
"""

import argparse
import uvicorn


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DocEx-Serve: Document extraction API with VLM support"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting DocEx-Serve on {args.host}:{args.port}")
    print(f"API documentation: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "docex_serve.app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1
    )


if __name__ == "__main__":
    main()
