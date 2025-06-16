#!/usr/bin/env python3
"""Serveur de test local pour simuler PythonAnywhere."""

import os
import sys
import logging
from dotenv import load_dotenv

def setup_local_environment():
    """Configure l'environnement local comme PythonAnywhere."""
    print("🔧 Configuration environnement local...")
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Configurer le logging comme en production
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Vérifier les variables d'environnement
    required_vars = ["API_USERNAME", "API_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Variables manquantes: {missing}")
        print("Créez un fichier .env avec:")
        print("API_USERNAME=admin")
        print("API_PASSWORD=your_password")
        return False
    
    print("✅ Environnement configuré")
    return True

def main():
    """Démarrer le serveur de test local."""
    print("🚀 Démarrage serveur test local (simulation PythonAnywhere)")
    print("=" * 60)
    
    if not setup_local_environment():
        return False
    
    try:
        # Importer l'application comme le ferait PythonAnywhere
        from main_api import app
        import uvicorn
        
        print("✅ Application importée avec succès")
        print("\n🌐 Serveur disponible sur:")
        print("- URL: http://localhost:8000")
        print("- Health: http://localhost:8000/health")
        print("- Docs: http://localhost:8000/docs")
        print("\n🔐 Authentification:")
        print(f"- Username: {os.getenv('API_USERNAME')}")
        print("- Password: ***")
        print("\n🛑 Arrêt: Ctrl+C")
        print("=" * 60)
        
        # Démarrer le serveur
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True
        )
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        print("💡 Vérifiez que toutes les dépendances sont installées:")
        print("pip install -r requirements_prod.txt")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    main() 