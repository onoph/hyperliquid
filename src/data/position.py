from dataclasses import dataclass
from typing import Optional, Literal
from datetime import datetime


@dataclass
class Position:
    """Modèle représentant une position de trading"""
    
    # Identifiants
    symbol: str
    user_address: str
    
    # Position details
    side: Literal['OPEN_LONG', 'CLOSE_LONG']  # Type de position
    size: str  # Taille de la position
    entry_price: Optional[str] = None  # Prix d'entrée moyen
    
    # PnL et valeurs
    unrealized_pnl: Optional[str] = None  # PnL non réalisé
    realized_pnl: Optional[str] = None   # PnL réalisé
    
    # Timestamps
    timestamp: datetime = None
    
    # Métadonnées optionnelles
    leverage: Optional[str] = None
    margin_used: Optional[str] = None
    liquidation_price: Optional[str] = None
    
    def __post_init__(self):
        """Validation et initialisation post-création"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
        if not self.user_address:
            raise ValueError("User address cannot be empty")
        if self.side not in ["LONG", "SHORT"]:
            raise ValueError("Side must be 'LONG' or 'SHORT'")
    
    def to_dict(self) -> dict:
        """Conversion en dictionnaire"""
        return {
            'symbol': self.symbol,
            'user_address': self.user_address,
            'side': self.side,
            'size': self.size,
            'entry_price': self.entry_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'leverage': self.leverage,
            'margin_used': self.margin_used,
            'liquidation_price': self.liquidation_price
        } 