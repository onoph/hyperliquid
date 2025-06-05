from dataclasses import dataclass

@dataclass
class Position:
    coin: str
    entry_price: float
    size: float
    leverage: float
    unrealized_pnl: float

@dataclass
class Order:
    coin: str
    is_buy: bool
    price: float
    size: float
    order_type: str
    tif: str
