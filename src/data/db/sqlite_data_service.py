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
from src.data.db.position_repository import PositionRepository


class SQLiteDataService(IData):
    """Implémentation SQLite pour la gestion des données d'observations"""
    
    def __init__(self, db_path: str = "data/observations.db"):
        """
        Initialise la connexion à la base SQLite
        
        Args:
            db_path: Chemin vers le fichier de base de données
        """
        self.logger = logging.getLogger(__name__)
        self.position_repository = PositionRepository(db_path)
    
    def on_new_order(self, ws_order: WsOrder, session_id: str) -> None:
        """Traite un nouvel ordre"""
        try:
            self.logger.info(f"Processing new order: {ws_order.order.oid} for {ws_order.order.coin}")
            observation = DataMapper.ws_order_to_observation(ws_order, session_id)
            self.position_repository._save_observation(observation)
        except Exception as e:
            self.logger.error(f"Failed to record new order {ws_order.order.oid}: {e}")
    
    def on_new_buy_position(self, symbol: str, user_address: str, side: str, qty: float, price: float, session_id: str) -> None:
        position = Position(
            symbol=symbol,
            user_address=user_address,
            side=side,
            size=str(qty),
            entry_price=str(price)
        )
        self.position_repository.save_new_buy_position(position, session_id)
    
    def on_new_sell_position(self, symbol: str, user_address: str, side: str, qty: float, price: float, session_id: str) -> None:
        position = Position(
            symbol=symbol,
            user_address=user_address,
            side=side,
            size=str(qty),
            entry_price=str(price)
        )
        self.position_repository.save_new_sell_position(position, session_id)
    
    def on_filled_buy_position(self, symbol: str, user_address: str, side: str, qty: float, price: float, session_id: str) -> None:
        position = Position(
            symbol=symbol,
            user_address=user_address,
            side=side,
            size=str(qty),
            entry_price=str(price)
        )
        self.position_repository.save_filled_buy_position(position, session_id)
    
    def on_filled_sell_position(self, symbol: str, user_address: str, side: str, qty: float, price: float, session_id: str) -> None:
        position = Position(
            symbol=symbol,
            user_address=user_address,
            side=side,
            size=str(qty),
            entry_price=str(price)
        )
        self.position_repository.save_filled_sell_position(position, session_id)
    
    def get_observations_by_session(self, session_id: str) -> list[dict]:
        """Récupère toutes les observations d'une session"""
        return self.position_repository.get_observations_by_session(session_id)
    
    def get_observations_by_symbol(self, symbol: str) -> list[dict]:
        """Récupère toutes les observations d'un symbole"""
        return self.position_repository.get_observations_by_symbol(symbol)
    
    def get_all_sessions(self) -> list[str]:
        """Récupère tous les IDs de session uniques"""
        return self.position_repository.get_all_sessions()
    
    def get_sessions_with_stats(self) -> list[dict]:
        """Récupère tous les IDs de session avec des statistiques détaillées"""
        return self.position_repository.get_sessions_with_stats()
    
    def close(self) -> None:
        """Ferme la connexion (si nécessaire pour le nettoyage)"""
        # SQLite avec context manager gère automatiquement les connexions
        pass 