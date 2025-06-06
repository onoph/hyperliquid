#!/usr/bin/env python3
"""Startup script for the Hyperliquid Observer API."""

import os
import sys
import uvicorn
from dotenv import load_dotenv


def main() -> None:
    """Start the API server."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["API_USERNAME", "API_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file or environment")
        sys.exit(1)
    
    print("🚀 Starting Hyperliquid Observer API...")
    print(f"📋 Authentication: {os.getenv('API_USERNAME')}")
    print("🔐 Password: ***")
    print("🌐 URL: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("💚 Health: http://localhost:8000/health")
    
    # Start the server
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main() 