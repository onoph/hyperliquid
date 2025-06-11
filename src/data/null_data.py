from src.data.interface import IData
from src.generic.hyperliquid_ws_model import WsOrder
from src.data.position import Position


class NullData(IData):
    """Implémentation null de IData qui ne fait rien (pattern Null Object)"""
    
    def on_new_order(self, ws_order: WsOrder, session_id: str) -> None:
        """Ne fait rien"""
        pass
    
    def on_new_buy_position(self, position: Position, session_id: str) -> None:
        """Ne fait rien"""
        pass
    
    def on_new_sell_position(self, position: Position, session_id: str) -> None:
        """Ne fait rien"""
        pass
    
    def on_filled_buy_position(self, position: Position, session_id: str) -> None:
        """Ne fait rien"""
        pass
    
    def on_filled_sell_position(self, position: Position, session_id: str) -> None:
        """Ne fait rien"""
        pass 