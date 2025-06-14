"""Configuration du logging pour l'application Hyperliquid."""

import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """Configure le système de logging avec un fichier unique par exécution."""
    # Créer le dossier logs s'il n'existe pas
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Nom du fichier de log avec timestamp détaillé
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = os.path.join(log_dir, f"trading_{timestamp}.log")

    # Configuration du format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler pour le fichier
    file_handler = logging.FileHandler(
        log_file,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Supprimer tous les handlers existants
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Ajouter les nouveaux handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Logger spécifique pour l'application
    app_logger = logging.getLogger('HyperliquidTrading')
    app_logger.propagate = False  # Évite la propagation vers le logger racine
    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)
    app_logger.setLevel(logging.INFO)
    
    app_logger.info(f"=== Démarrage de l'application - Log file: {log_file} ===")

    return app_logger 