import sqlite3
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.data.interface import IData
from src.generic.hyperliquid_ws_model import WsOrder
from src.data.position import Position
from src.data.db.mapper import DataMapper
from src.data.db.models import SimpleObservation


class SQLiteDataService(IData):
    """Implémentation SQLite pour la gestion des données d'observations"""
    
    def __init__(self, db_path: str = "data/observations.db"):
        """
        Initialise la connexion à la base SQLite
        
        Args:
            db_path: Chemin vers le fichier de base de données
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Créer le répertoire si nécessaire
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialiser la base de données
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialise les tables de la base de données"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table principale pour toutes les observations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    user_address TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    oid TEXT,
                    price TEXT,
                    status TEXT,
                    source TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index pour optimiser les requêtes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON observations(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON observations(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON observations(symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON observations(timestamp)")
            
            conn.commit()
    
    def _save_observation(self, observation: SimpleObservation) -> None:
        """Sauvegarde une observation en base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO observations 
                    (event_type, symbol, user_address, session_id, timestamp, data, oid, price, status, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    observation.event_type.value,
                    observation.symbol,
                    observation.user_address,
                    observation.session_id,
                    observation.timestamp.isoformat(),
                    observation.to_json(),
                    observation.oid,
                    observation.price,
                    observation.status.value if observation.status else None,
                    observation.source
                ))
                
                conn.commit()
                self.logger.debug(f"Observation saved: {observation.event_type.value} for {observation.symbol}")
                
        except Exception as e:
            self.logger.error(f"Error saving observation: {e}")
            raise
    
    def on_new_order(self, ws_order: WsOrder, session_id: str) -> None:
        """Traite un nouvel ordre"""
        try:
            self.logger.info(f"Processing new order: {ws_order.order.oid} for {ws_order.order.coin}")
            observation = DataMapper.ws_order_to_observation(ws_order, session_id)
            self._save_observation(observation)
        except Exception as e:
            self.logger.error(f"Failed to record new order {ws_order.order.oid}: {e}")
    
    def on_new_buy_position(self, position: Position, session_id: str) -> None:
        """Traite une nouvelle position d'achat"""
        try:
            self.logger.info(f"Processing new buy position: {position.symbol} - {position.side}")
            observation = DataMapper.new_buy_position_to_observation(position, session_id)
            self._save_observation(observation)
        except Exception as e:
            self.logger.error(f"Failed to record new buy position {position.symbol}: {e}")
    
    def on_new_sell_position(self, position: Position, session_id: str) -> None:
        """Traite une nouvelle position de vente"""
        try:
            self.logger.info(f"Processing new sell position: {position.symbol} - {position.side}")
            observation = DataMapper.new_sell_position_to_observation(position, session_id)
            self._save_observation(observation)
        except Exception as e:
            self.logger.error(f"Failed to record new sell position {position.symbol}: {e}")
    
    def on_filled_buy_position(self, position: Position, session_id: str) -> None:
        """Traite une position d'achat remplie"""
        try:
            self.logger.info(f"Processing filled buy position: {position.symbol} - {position.side}")
            observation = DataMapper.filled_buy_position_to_observation(position, session_id)
            self._save_observation(observation)
        except Exception as e:
            self.logger.error(f"Failed to record filled buy position {position.symbol}: {e}")
    
    def on_filled_sell_position(self, position: Position, session_id: str) -> None:
        """Traite une position de vente remplie"""
        try:
            self.logger.info(f"Processing filled sell position: {position.symbol} - {position.side}")
            observation = DataMapper.filled_sell_position_to_observation(position, session_id)
            self._save_observation(observation)
        except Exception as e:
            self.logger.error(f"Failed to record filled sell position {position.symbol}: {e}")
    
    def get_observations_by_session(self, session_id: str) -> list[dict]:
        """Récupère toutes les observations d'une session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Pour avoir des résultats sous forme de dict
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM observations 
                WHERE session_id = ? 
                ORDER BY timestamp ASC
            """, (session_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_observations_by_symbol(self, symbol: str) -> list[dict]:
        """Récupère toutes les observations d'un symbole"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM observations 
                WHERE symbol = ? 
                ORDER BY timestamp ASC
            """, (symbol,))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_all_sessions(self) -> list[str]:
        """Récupère tous les IDs de session uniques"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT session_id FROM observations")
            return [row[0] for row in cursor.fetchall()]
    
    def get_sessions_with_stats(self) -> list[dict]:
        """Récupère tous les IDs de session avec des statistiques détaillées"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    session_id,
                    MIN(timestamp) as start_time,
                    MAX(timestamp) as last_activity,
                    COUNT(*) as total_events,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    COUNT(DISTINCT event_type) as event_types_count
                FROM observations 
                GROUP BY session_id
                ORDER BY start_time DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def close(self) -> None:
        """Ferme la connexion (si nécessaire pour le nettoyage)"""
        # SQLite avec context manager gère automatiquement les connexions
        pass 