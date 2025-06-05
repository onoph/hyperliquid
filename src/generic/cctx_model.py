from dataclasses import dataclass
from typing import Optional, List, Any

@dataclass
class Info:
    coin: str
    side: str
    limitPx: str
    sz: str
    oid: str
    timestamp: str
    triggerCondition: str
    isTrigger: bool
    triggerPx: str
    children: List[Any]
    isPositionTpsl: bool
    reduceOnly: bool
    orderType: str
    origSz: str
    tif: str
    cloid: Optional[str]

@dataclass
class Order:
    info: Info
    id: str
    clientOrderId: Optional[str]
    timestamp: int
    datetime: str
    lastTradeTimestamp: Optional[int]
    lastUpdateTimestamp: Optional[int]
    symbol: str
    type: str
    timeInForce: str
    postOnly: bool
    reduceOnly: bool
    side: str
    price: float
    triggerPrice: Optional[float]
    amount: float
    cost: float
    average: Optional[float]
    filled: float
    remaining: float
    status: str
    fee: Optional[Any]
    trades: List[Any]
    fees: List[Any]
    stopPrice: Optional[float]
    takeProfitPrice: Optional[float]
    stopLossPrice: Optional[float]


    @dataclass
    class Balance:
        total: float
        used: float
        free: float