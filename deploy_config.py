"""Configuration script for PythonAnywhere deployment."""

import os
import logging
from pathlib import Path

def setup_logging(username: str = "yourusername") -> None:
    """Configure logging for production.
    
    Args:
        username: PythonAnywhere username.
    """
    log_dir = Path(f"/home/{username}/hyperliquid/logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configuration plus conservatrice pour la production
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / 'app.log')
        ]
    )


def check_environment() -> None:
    """Vérifier que toutes les variables d'environnement sont présentes."""
    required_vars = ['API_USERNAME', 'API_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        raise EnvironmentError(f"Variables d'environnement manquantes: {missing}")
    
    print("✅ Variables d'environnement OK")


def create_directories(username: str = "yourusername") -> None:
    """Créer les répertoires nécessaires.
    
    Args:
        username: PythonAnywhere username.
    """
    directories = [
        f"/home/{username}/hyperliquid/logs",
        f"/home/{username}/hyperliquid/tmp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Répertoire créé: {directory}")


if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else "yourusername"
    
    print(f"🚀 Configuration du déploiement pour l'utilisateur: {username}")
    
    create_directories(username)
    setup_logging(username)
    check_environment()
    
    print("✅ Configuration terminée !") 