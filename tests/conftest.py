import pytest
from unittest.mock import MagicMock
from src.generic.algo import Algo
from src.generic.cctx_model import Order, Info
from src.generic.cctx_api import Dex as CctxDex
# Import local OrderSide type
from src.generic.algo import OrderSide
from src.generic.hyperliquid_ws_model import WsOrder

# Helper to create mock Order objects
def make_mock_order(price: float, side: OrderSide, qty: float = 0.1) -> Order:
    hyperliquid_side = 'B' if side == 'buy' else 'A'
    return Order(
        id=f"mock_order_{price}_{side}",
        oid=f"mock_order_{price}_{side}",
        price=price,
        limitPx=price,
        side=hyperliquid_side,
        qty=qty
    )

def make_real_order(price: float, side: OrderSide, qty: float = 0.1) -> Order:
    hyperliquid_side = 'B' if side == 'buy' else 'A'
    order = Order(
        info=Info(
            coin="BTC",
            side=hyperliquid_side,
            limitPx=str(price),
            sz=str(qty),
            oid=f"mock_order_{price}_{side}",
            timestamp="0",
            triggerCondition="",
            isTrigger=False,
            triggerPx="",
            children=[],
            isPositionTpsl=False,
            reduceOnly=False,
            orderType="limit",
            origSz=str(qty),
            tif="",
            cloid=None
        ),
        id=f"mock_order_{price}_{side}",
        clientOrderId=None,
        timestamp=0,
        datetime="",
        lastTradeTimestamp=None,
        lastUpdateTimestamp=None,
        symbol="BTC/USDC",
        type="limit",
        timeInForce="",
        postOnly=False,
        reduceOnly=False,
        side=hyperliquid_side,
        price=price,
        triggerPrice=None,
        amount=qty,
        cost=0.0,
        average=None,
        filled=0.0,
        remaining=qty,
        status="open",
        fee=None,
        trades=[],
        fees=[],
        stopPrice=None,
        takeProfitPrice=None,
        stopLossPrice=None
    )
    # Ajout des attributs dynamiques attendus par l'algo
    order.oid = order.id
    order.limitPx = order.price
    return order

def make_real_wsorder(price: float, side: OrderSide, qty: float = 0.1) -> WsOrder:
    return WsOrder(
        order=make_real_order(price, side, qty),
        status="open",
        statusTimestamp=0
    )

@pytest.fixture
def mock_dex():
    dex = MagicMock(spec=CctxDex)
    dex.get_full_account_data.return_value.USDC.free = 1000
    dex.get_full_account_data.return_value.USDC.total = 1000  # Ensure total is also mocked
    dex.get_current_price.return_value = 100
    dex.set_cross_margin_leverage.return_value = None
    dex.buy_at_market_price.return_value = None

    # Mock order creation methods to use the helper
    dex.create_open_long.side_effect = lambda qty, price: make_real_order(price, 'buy', qty)
    dex.create_close_long.side_effect = lambda qty, price: make_real_order(price, 'sell', qty)
    dex.cancel_order.return_value = None
    dex.get_open_orders.return_value = []
    return dex

@pytest.fixture
def algo(mock_dex) -> Algo:
    algo_instance = Algo(symbol="BTC", marginCoin="USDC", dex_instance=mock_dex)
    assert algo_instance.dex is mock_dex
    return algo_instance

def test_algo(algo):
    order = make_real_order(100, 'buy')
    algo.previous_orders = [order]
    ws_order = make_real_wsorder(100, 'buy')
    algo.on_executed_order(wsOrder=ws_order) 