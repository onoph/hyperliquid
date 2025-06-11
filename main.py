#!/usr/bin/env python3
"""
Point d'entrée principal pour Replit
Lance l'API FastAPI Hyperliquid Observer
"""

import uvicorn
import os

if __name__ == "__main__":
    # Variables d'environnement pour Replit
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Démarrage de l'API Hyperliquid Observer sur {host}:{port}")
    
    # Lancer l'application FastAPI
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=False,  # Pas de reload en production
        log_level="info"
    ) 