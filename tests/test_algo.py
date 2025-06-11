import pytest
from unittest.mock import MagicMock
from src.generic.algo import Algo
from src.generic.cctx_model import Order
from src.generic.hyperliquid_ws_model import WsOrder
from src.generic.algo import OrderSide
from tests.conftest import make_real_order, make_real_wsorder

def check_order(algo: Algo, price: float, side: OrderSide) -> None:
    if side == 'buy':
        assert any(o for o in algo.previous_orders if o.price == price and o.side == 'buy' or o.side == 'B')
    elif side == 'sell':
        assert any(o for o in algo.previous_orders if o.price == price and o.side == 'sell' or o.side == 'A')

@pytest.fixture
def ws_order_open_long() -> MagicMock:
    wsOrder = MagicMock(spec=WsOrder)
    wsOrder.order = make_real_order(90, 'B')
    return wsOrder

@pytest.fixture
def close_long() -> Order:
    return make_real_order(110, 'sell')

@pytest.fixture
def open_long() -> Order:
    return make_real_order(80, 'buy')

@pytest.fixture
def algo(mock_dex) -> Algo:
    algo = Algo(dex=mock_dex)
    # Force le gap à 1000 pour le test
    algo.GAPS = [1000]
    algo.current_gap_idx = 0
    return algo

def make_ws_order(price: float, side: OrderSide) -> MagicMock:
    order = make_real_order(price, side)
    wsOrder = MagicMock(spec=WsOrder)
    wsOrder.order = order
    return wsOrder

def test_only_one_open_long_order(
    algo: Algo,
    mock_dex,
) -> None:
    """Il ne doit rester qu'un seul open long après exécution d'un open long."""
    initial_price = 100000
    gap = algo.get_gap()

    initial_open_long = make_real_order(initial_price - gap, 'buy')
    initial_close_long = make_real_order(initial_price + gap, 'sell')
    algo.previous_orders = [initial_open_long, initial_close_long]

    ws_order_open_long = make_real_wsorder(initial_price - gap, 'buy')
    algo.on_executed_order(wsOrder=ws_order_open_long)
    open_longs = [o for o in algo.previous_orders if o.side == 'buy' or o.side == 'B']
    assert len(open_longs) == 1

def test_close_long_order_persists_until_executed(
    algo: Algo,
    mock_dex,
    close_long: Order
) -> None:
    """Le close long doit rester tant qu'il n'est pas exécuté."""
    algo.previous_orders = [close_long]
    ws_order_open_long = make_real_wsorder(110, 'buy')
    algo.on_executed_order(wsOrder=ws_order_open_long)
    assert close_long in algo.previous_orders

def test_price_moves_up_and_down_scenario(algo: Algo, mock_dex) -> None:
    """
    Simule :
    - prix initial 100000
    - monte 3x du gap
    - descend 2x du gap
    Vérifie l'état des ordres à chaque étape.
    """
    gap = algo.get_gap()
    initial_price = 100000
    
    # État initial : quelques ordres représentatifs
    initial_open_long = make_real_order(initial_price - gap, 'buy')
    initial_close_long = make_real_order(initial_price + gap, 'sell')
    algo.previous_orders = [initial_open_long, initial_close_long]

    # 1. Monte du gap (close long exécuté)
    ws1 = make_real_wsorder(initial_price + gap, 'sell')
    algo.on_executed_order(wsOrder=ws1)
    assert len(algo.previous_orders) == 2
    check_order(algo, initial_price + 2 * gap, 'sell')
    check_order(algo, initial_price, 'buy')

    # 2. Monte encore du gap (close long execute)
    ws2 = make_real_wsorder(initial_price + 2 * gap, 'sell')
    algo.on_executed_order(wsOrder=ws2)
    assert len(algo.previous_orders) == 2
    check_order(algo, initial_price + 3 * gap, 'sell')
    check_order(algo, initial_price - gap, 'buy')

    # 3. Monte encore du gap (close long execute)
    ws3 = make_real_wsorder(initial_price + 3 * gap, 'sell')
    algo.on_executed_order(wsOrder=ws3)
    assert len(algo.previous_orders) == 2
    check_order(algo, initial_price + 4 * gap, 'sell')
    check_order(algo, initial_price + 2 * gap, 'buy')

    # 4. Descend du gap (open long exécuté)
    ws4 = make_real_wsorder(initial_price + 2 * gap, 'buy')
    algo.on_executed_order(wsOrder=ws4)
    assert len(algo.previous_orders) == 3
    check_order(algo, initial_price + 4 * gap, 'sell')
    check_order(algo, initial_price + 3 * gap, 'sell')
    check_order(algo, initial_price + gap, 'buy')

    # 5. Descend encore du gap (open long exécuté)
    ws5 = make_real_wsorder(initial_price + gap, 'buy')
    algo.on_executed_order(wsOrder=ws5)
    assert len(algo.previous_orders) == 4
    check_order(algo, initial_price + 4 * gap, 'sell')
    check_order(algo, initial_price + 3 * gap, 'sell')
    check_order(algo, initial_price + 2 * gap, 'sell')
    check_order(algo, initial_price, 'buy')

def test_remove_from_previous_orders(algo: Algo):
    """Test that remove_from_previous_orders correctly removes an order."""
    order1 = make_real_order(100, 'buy')
    order2 = make_real_order(101, 'sell')
    order3 = make_real_order(102, 'buy')

    algo.previous_orders = [order1, order2, order3]

    # Remove an existing order
    algo.remove_from_previous_orders(order2.id)
    assert len(algo.previous_orders) == 2
    assert order1 in algo.previous_orders
    assert order3 in algo.previous_orders
    assert order2 not in algo.previous_orders

    # Try to remove a non-existent order
    algo.remove_from_previous_orders("order_non_existent_id")
    assert len(algo.previous_orders) == 2
    assert order1 in algo.previous_orders
    assert order3 in algo.previous_orders