from abc import ABC, abstractmethod
from src.generic.hyperliquid_ws_model import WsOrder
from src.data.position import Position


class IData(ABC):
    """Interface pour la gestion des données d'observations"""
    
    @abstractmethod
    def on_new_order(self, ws_order: WsOrder, session_id: str) -> None:
        """Traite un nouvel ordre"""
        pass
    
    @abstractmethod
    def on_new_buy_position(self, position: Position, session_id: str) -> None:
        """Traite une nouvelle position d'achat"""
        pass
    
    @abstractmethod
    def on_new_sell_position(self, position: Position, session_id: str) -> None:
        """Traite une nouvelle position de vente"""
        pass
    
    @abstractmethod
    def on_filled_buy_position(self, position: Position, session_id: str) -> None:
        """Traite une position d'achat remplie"""
        pass
    
    @abstractmethod
    def on_filled_sell_position(self, position: Position, session_id: str) -> None:
        """Traite une position de vente remplie"""
        pass 