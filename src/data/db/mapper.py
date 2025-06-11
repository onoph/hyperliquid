from datetime import datetime
from typing import Dict, Any
from src.generic.hyperliquid_ws_model import WsOrder
from src.data.position import Position
from src.data.db.models import (
    SimpleObservation, 
    EventType, 
    PositionStatus,
    create_order_observation,
    create_position_observation
)


class DataMapper:
    """Mappeur pour convertir les objets métier en observations"""
    
    @staticmethod
    def ws_order_to_observation(ws_order: WsOrder, session_id: str) -> SimpleObservation:
        """Convertit un WsOrder en SimpleObservation"""
        order_data = {
            'side': ws_order.order.side,
            'size': ws_order.order.sz,
            'orig_size': ws_order.order.origSz,
            'coin': ws_order.order.coin,
            'status': ws_order.status,
            'status_timestamp': ws_order.statusTimestamp,
            'order_timestamp': ws_order.order.timestamp
        }
        
        return create_order_observation(
            symbol=ws_order.order.coin,
            user_address="",  # À renseigner selon le contexte
            session_id=session_id,
            oid=str(ws_order.order.oid),
            price=str(ws_order.order.limitPx),
            order_data=order_data
        )
    
    @staticmethod
    def position_to_observation(
        position: Position, 
        session_id: str, 
        status: PositionStatus
    ) -> SimpleObservation:
        """Convertit une Position en SimpleObservation avec statut"""
        position_data = {
            'side': position.side,
            'size': position.size,
            'entry_price': position.entry_price,
            'unrealized_pnl': position.unrealized_pnl,
            'realized_pnl': position.realized_pnl,
            'leverage': position.leverage,
            'margin_used': position.margin_used,
            'liquidation_price': position.liquidation_price
        }
        
        return create_position_observation(
            symbol=position.symbol,
            user_address=position.user_address,
            session_id=session_id,
            status=status,
            position_data=position_data
        )
    
    @staticmethod
    def new_buy_position_to_observation(position: Position, session_id: str) -> SimpleObservation:
        """Convertit une nouvelle position d'achat"""
        return DataMapper.position_to_observation(position, session_id, PositionStatus.CREATED)
    
    @staticmethod
    def new_sell_position_to_observation(position: Position, session_id: str) -> SimpleObservation:
        """Convertit une nouvelle position de vente"""
        return DataMapper.position_to_observation(position, session_id, PositionStatus.CREATED)
    
    @staticmethod
    def filled_buy_position_to_observation(position: Position, session_id: str) -> SimpleObservation:
        """Convertit une position d'achat remplie"""
        return DataMapper.position_to_observation(position, session_id, PositionStatus.FILLED)
    
    @staticmethod
    def filled_sell_position_to_observation(position: Position, session_id: str) -> SimpleObservation:
        """Convertit une position de vente remplie"""
        return DataMapper.position_to_observation(position, session_id, PositionStatus.FILLED) 