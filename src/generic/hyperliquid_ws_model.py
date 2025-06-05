from dataclasses import dataclass
from typing import TypeVar, Generic, List

T = TypeVar("T")

@dataclass
class WsMessage(Generic[T]):
    channel: str
    data: List[T]


@dataclass
class WsBasicOrder:
    coin: str
    side: str
    limitPx: float
    sz: str
    oid: int
    timestamp: int
    origSz: str

@dataclass
class WsOrder:
    order: WsBasicOrder
    status: str
    statusTimestamp: int

