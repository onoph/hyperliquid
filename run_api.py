#!/usr/bin/env python3
"""
Script pour démarrer l'API FastAPI en local
"""

import uvicorn
import os
from pathlib import Path

def main():
    # Configuration de l'environnement
    os.environ.setdefault("API_USERNAME", "admin")
    os.environ.setdefault("API_PASSWORD", "secret123")
    
    # Créer le répertoire data si nécessaire
    Path("data").mkdir(exist_ok=True)
    
    print("🚀 Démarrage de l'API Hyperliquid Observer...")
    print("📍 URL: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔐 Auth: admin / secret123")
    print("\n" + "="*50)
    
    # Démarrer le serveur
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 