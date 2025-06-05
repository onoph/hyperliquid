from hyperliquidapi import HyperliquidAPI
from hyperliquidapi.hyperliquid_models import Order

GAPS = [500, 1000, 1500, 2000, 2500, 3000]
currentGapIdx = 0;
maxLeverage = 40
perpFundsPercentageForInitialLong = 10; # initial percentage to open Long position with PERP funds
maxShortPositions = 3
countPieces = 4

TRADED = "BTC"
MARGIN_COIN = "USDC"

def getGap():
    return GAPS[currentGapIdx]

def incrementGap():
    if currentGapIdx < len(GAPS) - 1:
        currentGapIdx += 1

def decrementGap():
    if currentGapIdx > 0:
        currentGapIdx -= 1

def getPerpAvailableFunds():
    return 1000; #TODO

def getCurrentBtcPrice():
    return 100000; #TODO

def getQuantityOrder():
    return getPerpAvailableFunds() / 6 / getCurrentBtcPrice()

def computeInitialPositionAmountToInvest():
    perpAvailableFunds = getPerpAvailableFunds()
    return perpAvailableFunds * perpFundsPercentageForInitialLong

def computeInitialPositionQty(asset_price: float):
    initialPerpAmount = computeInitialPositionAmountToInvest()
    initialPositionQty = initialPerpAmount / asset_price
    return initialPositionQty

def initPositions():
    assetPrice = hyperliquidapi.get_asset_price(TRADED)

    # initial position
    initialPositionQty = computeInitialPositionQty(assetPrice)
    hyperliquidapi.buyAtMarketPrice(symbol=TRADED, marginCoin=MARGIN_COIN, qty=initialPositionQty)

    # common 
    gap = getGap()
    qty = getQuantityOrder()

    # long position
    long_price = assetPrice + gap
    hyperliquidapi.createLongOrder(TRADED, MARGIN_COIN, qty, long_price)

    # short orders
    for i in range(1, maxShortPositions):
        short_price = assetPrice - (i * gap)
        hyperliquidapi.createShortOrder(TRADED, MARGIN_COIN, qty, short_price)

from enum import Enum
class PositionShiftType(Enum):
    UP,
    DOWN

def shift_positions(symbol: str, shiftType: PositionShiftType, incrementCount: int):
    #longOrders = [o for o in orders if o.order_type == 'long' and o.coin == symbol]
    #shortOrders = [o for o in orders if o.order_type == 'short' and o.coin == symbol]
    
    #increment gap
    for i in range(0, incrementCount):
        incrementGap()

    gap = getGap()
    fnPrice = incrementGap if shiftType == "UP" else decrementGap

    orders = hyperliquidapi.get_open_orders()
    for order in orders:
        newPrice = fnPrice(order, gap);
        # update or remove order

    
def getIncrementedOrderPrice(order: Order, gap: float) -> float:
    return order.price + gap;

def getDecrementedOrderPrice(order: Order, gap: float) -> float:
    return order.price - gap;

if __name__ == '__main__':
    hyperliquidapi = HyperliquidAPI()
    # print(hyperliquidapi.get_open_orders())
    print(hyperliquidapi.get_positions())