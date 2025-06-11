from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json


class OrderSide(Enum):
    """Side de l'ordre"""
    BUY = "B"
    SELL = "A"


class EventType(Enum):
    """Types d'objets observés"""
    ORDER = "order"
    POSITION = "position"


class PositionStatus(Enum):
    """Statuts possibles pour les positions"""
    FILLED = "filled"
    CREATED = "created"
    CANCELED = "canceled"
    PARTIAL_UPDATE = "partial_update"


@dataclass
class SimpleObservation:
    """Modèle simplifié pour les observations Hyperliquid"""
    
    # Identifiants essentiels
    event_type: EventType
    symbol: str
    user_address: str
    session_id: str
    
    # Timestamps
    timestamp: datetime
    
    # Données essentielles selon le type d'événement
    data: Dict[str, Any]
    
    # Champs optionnels spécifiques aux ordres
    oid: Optional[str] = None  # ID Hyperliquid pour les ordres
    price: Optional[str] = None  # Prix pour les ordres
    
    # Statut (uniquement pour les positions, None pour les ordres)
    status: Optional[PositionStatus] = None
    
    # Source et métadonnées minimales
    source: str = "hyperliquid_observer"
    
    def __post_init__(self):
        """Validation post-initialisation"""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.user_address:
            raise ValueError("User address cannot be empty")
        if not self.session_id:
            raise ValueError("Session ID cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversion en dictionnaire"""
        result = {
            'event_type': self.event_type.value,
            'symbol': self.symbol,
            'user_address': self.user_address,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'source': self.source
        }
        
        # Ajouter les champs optionnels s'ils sont présents
        if self.oid is not None:
            result['oid'] = self.oid
        if self.price is not None:
            result['price'] = self.price
        if self.status is not None:
            result['status'] = self.status.value
            
        return result
    
    def to_json(self) -> str:
        """Conversion en JSON"""
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimpleObservation':
        """Création depuis un dictionnaire"""
        return cls(
            event_type=EventType(data['event_type']),
            symbol=data['symbol'],
            user_address=data['user_address'],
            session_id=data['session_id'],
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data['timestamp'], str) else data['timestamp'],
            data=data['data'],
            oid=data.get('oid'),
            price=data.get('price'),
            status=PositionStatus(data['status']) if data.get('status') else None,
            source=data.get('source', 'hyperliquid_observer')
        )


# Fonctions utilitaires pour créer des observations spécifiques
def create_order_observation(
    symbol: str, 
    user_address: str, 
    session_id: str, 
    oid: str, 
    price: str, 
    order_data: Dict[str, Any]
) -> SimpleObservation:
    """Crée une observation d'ordre avec oid et prix"""
    return SimpleObservation(
        event_type=EventType.ORDER,
        symbol=symbol,
        user_address=user_address,
        session_id=session_id,
        timestamp=datetime.now(),
        data=order_data,
        oid=oid,
        price=price
    )


def create_position_observation(
    symbol: str, 
    user_address: str, 
    session_id: str, 
    status: PositionStatus, 
    position_data: Dict[str, Any]
) -> SimpleObservation:
    """Crée une observation de position avec statut"""
    return SimpleObservation(
        event_type=EventType.POSITION,
        symbol=symbol,
        user_address=user_address,
        session_id=session_id,
        timestamp=datetime.now(),
        data=position_data,
        status=status
    )


# Fonctions utilitaires pour créer des positions avec statuts spécifiques
def create_filled_position(symbol: str, user_address: str, session_id: str, position_data: Dict[str, Any]) -> SimpleObservation:
    """Crée une observation de position remplie"""
    return create_position_observation(symbol, user_address, session_id, PositionStatus.FILLED, position_data)


def create_created_position(symbol: str, user_address: str, session_id: str, position_data: Dict[str, Any]) -> SimpleObservation:
    """Crée une observation de position créée"""
    return create_position_observation(symbol, user_address, session_id, PositionStatus.CREATED, position_data)


def create_canceled_position(symbol: str, user_address: str, session_id: str, position_data: Dict[str, Any]) -> SimpleObservation:
    """Crée une observation de position annulée"""
    return create_position_observation(symbol, user_address, session_id, PositionStatus.CANCELED, position_data)


def create_partial_update_position(symbol: str, user_address: str, session_id: str, position_data: Dict[str, Any]) -> SimpleObservation:
    """Crée une observation de mise à jour partielle de position"""
    return create_position_observation(symbol, user_address, session_id, PositionStatus.PARTIAL_UPDATE, position_data)