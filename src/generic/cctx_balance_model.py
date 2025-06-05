from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CumFunding:
    allTime: str
    sinceOpen: str
    sinceChange: str

@dataclass
class Leverage:
    type: str
    value: str

@dataclass
class Position:
    coin: str
    szi: str
    leverage: Leverage
    entryPx: str
    positionValue: str
    unrealizedPnl: str
    returnOnEquity: str
    liquidationPx: str
    marginUsed: str
    maxLeverage: str
    cumFunding: CumFunding

@dataclass
class AssetPosition:
    type: str
    position: Position

@dataclass
class MarginSummary:
    accountValue: float
    totalNtlPos: float
    totalRawUsd: float
    totalMarginUsed: float

@dataclass
class Info:
    marginSummary: MarginSummary
    crossMarginSummary: MarginSummary
    crossMaintenanceMarginUsed: str
    withdrawable: str
    assetPositions: List[AssetPosition]
    time: str

@dataclass
class BalanceDetails:
    total: float
    used: float
    free: float

@dataclass
class AccountData:
    info: Info
    USDC: BalanceDetails
    timestamp: int
    datetime: str
    free: dict
    used: dict
    total: dict
