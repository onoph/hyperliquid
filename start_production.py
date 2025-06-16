#!/usr/bin/env python3
"""Production startup script for PythonAnywhere."""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

def setup_production_environment():
    """Configure the production environment."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging for production
    log_dir = Path.home() / "hyperliquid" / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / 'app.log')
        ]
    )
    
    # Check required environment variables
    required_vars = ["API_USERNAME", "API_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logging.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    logging.info("✅ Production environment configured")

def main():
    """Main entry point for production."""
    setup_production_environment()
    
    # Import and run the FastAPI app
    from main_api import app
    import uvicorn
    
    # For PythonAnywhere, we typically don't run uvicorn directly
    # This is mainly for testing the app works
    logging.info("🚀 FastAPI app is ready for production deployment")
    
    # If you want to test locally on PythonAnywhere console:
    if "--test" in sys.argv:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )

if __name__ == "__main__":
    main() 