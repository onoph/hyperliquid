"""Module de monitoring pour l'application Hyperliquid."""

import logging
from datetime import datetime
import threading
import time
from typing import Optional

class ApplicationMonitor:
    """Classe pour surveiller le cycle de vie de l'application."""
    
    def __init__(self):
        """Initialise le moniteur d'application."""
        self.start_time = datetime.now()
        self.is_running = True
        self.monitor_thread: Optional[threading.Thread] = None
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Configure le logging pour le monitoring."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ApplicationMonitor')
        
    def start_monitoring(self) -> None:
        """Démarre le monitoring de l'application."""
        self.logger.info(f"=== Démarrage de l'application à {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def _monitor_loop(self) -> None:
        """Boucle principale de monitoring."""
        while self.is_running:
            current_time = datetime.now()
            duration = (current_time - self.start_time).total_seconds()
            self.logger.info(f"Application en cours d'exécution depuis {duration:.2f} secondes")
            time.sleep(60)  # Log toutes les minutes
            
    def stop_monitoring(self) -> None:
        """Arrête le monitoring et log les informations de fin."""
        self.is_running = False
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        self.logger.info(f"=== Fin de l'application à {end_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        self.logger.info(f"Durée totale d'exécution: {duration:.2f} secondes")

# Instance globale du moniteur
monitor = ApplicationMonitor() 