"""Point d'entrée principal de l'application Hyperliquid."""

import logging
import traceback
import sys
from datetime import datetime
import time
import signal
import os

from src.generic.observer import HyperliquidObserver
from src.generic.algo import Algo
from src.data.db.sqlite_data_service import SQLiteDataService
from src.generic.cctx_api import Dex
from src.generic.monitoring import monitor
from src.generic.logging_config import setup_logging

# Variable globale pour contrôler l'exécution
running = True

def signal_handler(signum, frame):
    """Gestionnaire de signal pour l'arrêt propre."""
    global running
    logger = logging.getLogger('HyperliquidTrading')
    logger.info(f"Signal reçu: {signum}")
    running = False

def exception_handler(exc_type, exc_value, exc_traceback):
    """Gestionnaire d'exceptions global."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger = logging.getLogger('HyperliquidTrading')
    logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

def save_pid():
    """Sauvegarde le PID du processus dans un fichier."""
    pid = str(os.getpid())
    with open('trading.pid', 'w') as f:
        f.write(pid)
    return pid

def remove_pid_file():
    """Supprime le fichier PID."""
    try:
        os.remove('trading.pid')
    except OSError:
        pass

def main():
    """Fonction principale de l'application."""
    global running
    
    # Configuration du logging
    logger = setup_logging()
    
    # Sauvegarde du PID
    pid = save_pid()
    logger.info(f"Process ID: {pid}")
    
    # Définir le hook d'exception
    sys.excepthook = exception_handler
    
    # Configurer les gestionnaires de signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Démarrer le monitoring
    monitor.start_monitoring()
    
    from dotenv import load_dotenv
    load_dotenv()
    address = os.getenv('ADDRESS')

    try:
        # Initialisation des composants
        logger.info("Initialisation des composants...")
        dex = Dex(symbol='BTC', marginCoin='USDC')
        data_service = SQLiteDataService()
        algo = Algo(dex=dex, data_service=data_service, max_leverage=30)
        
        # Configuration initiale
        logger.info("Configuration des positions initiales...")
        algo.setup_initial_positions()
        
        # Création et démarrage de l'observateur
        logger.info("Création de l'observateur...")
        hyperliquid_observer = HyperliquidObserver(
            address=address,
            algo=algo
        )
        
        logger.info("=== Application démarrée avec succès ===")
        logger.info(f"Session ID: {algo.session_id}")
        logger.info(f"Adresse: {hyperliquid_observer.address}")
        logger.info(f"Leverage: {algo.max_leverage}")
        
        # Démarrer l'observateur
        logger.info("Démarrage de l'observateur...")
        hyperliquid_observer.start()
        
        # Boucle principale
        logger.info("En attente des événements WebSocket...")
        while running:
            time.sleep(1)  # Évite de surcharger le CPU
            
    except Exception as e:
        logger.error(f"=== Erreur lors de l'exécution de l'application ===")
        logger.error(f"Type d'erreur: {type(e).__name__}")
        logger.error(f"Message d'erreur: {str(e)}")
        logger.error("Trace complète:", exc_info=True)
        raise
    finally:
        # Arrêter proprement
        logger.info("Arrêt de l'application...")
        if 'hyperliquid_observer' in locals():
            hyperliquid_observer.stop()
        monitor.stop_monitoring()
        remove_pid_file()
        logger.info("=== Application arrêtée ===")

if __name__ == "__main__":
    main() 