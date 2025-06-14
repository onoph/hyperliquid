import pytest
from unittest.mock import MagicMock
from src.generic.algo import Algo
from src.generic.cctx_model import Order
from src.generic.hyperliquid_ws_model import WsOrder
from src.generic.algo import OrderSide
from tests.conftest import make_real_order, make_real_wsorder
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

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
def mock_dex() -> MagicMock:
    """Create a mock Dex instance for testing."""
    return MagicMock()

@pytest.fixture
def mock_data_service() -> MagicMock:
    """Create a mock DataService instance for testing."""
    return MagicMock()

@pytest.fixture
def algo(mock_dex: MagicMock, mock_data_service: MagicMock) -> Algo:
    """Create an Algo instance with mocked dependencies for testing."""
    algo = Algo(dex=mock_dex, data_service=mock_data_service)
    # Force le gap à 1000 pour le test
    algo.GAPS = [1000]
    # Patch create_open_long and create_close_long to return real orders
    def _create_open_long(qty, price):
        return make_real_order(price, 'buy', qty)
    def _create_close_long(qty, price):
        return make_real_order(price, 'sell', qty)
    mock_dex.create_open_long.side_effect = _create_open_long
    mock_dex.create_close_long.side_effect = _create_close_long
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

def test_remove_min_open_long_orders_empty_list(algo: Algo) -> None:
    """Test when there are no open long orders."""
    algo.previous_orders = []
    algo.remove_min_open_long_orders()
    assert len(algo.previous_orders) == 0

def test_remove_min_open_long_orders_single_order(algo: Algo) -> None:
    """Test when there is only one open long order."""
    single_order = make_real_order(100, 'buy')
    algo.previous_orders = [single_order]
    algo.remove_min_open_long_orders()
    assert len(algo.previous_orders) == 1
    assert algo.previous_orders[0] == single_order

def test_remove_min_open_long_orders_multiple_orders(algo: Algo) -> None:
    """Test when there are multiple open long orders."""
    # Create orders with different prices
    order1 = make_real_order(90, 'buy')  # lowest price
    order2 = make_real_order(100, 'buy')  # middle price
    order3 = make_real_order(110, 'buy')  # highest price
    algo.previous_orders = [order1, order2, order3]
    
    algo.remove_min_open_long_orders()
    
    # Should only keep the highest price order
    assert len(algo.previous_orders) == 1
    assert algo.previous_orders[0] == order3  # highest price order

def test_contains_open_long_at_price_empty(algo: Algo) -> None:
    """Retourne False si la liste est vide."""
    algo.previous_orders = []
    assert not algo.contains_open_long_at_price(100000)

def test_contains_open_long_at_price_found(algo: Algo) -> None:
    """Retourne True si un ordre d'achat existe au prix donné."""
    order = make_real_order(100000, 'buy')
    algo.previous_orders = [order]
    assert algo.contains_open_long_at_price(100000)

def test_contains_open_long_at_price_not_found(algo: Algo) -> None:
    """Retourne False si aucun ordre d'achat n'existe au prix donné."""
    order = make_real_order(100000, 'buy')
    algo.previous_orders = [order]
    assert not algo.contains_open_long_at_price(99000)

def test_contains_open_long_at_price_only_sell(algo: Algo) -> None:
    """Retourne False si seul un ordre de vente existe au prix donné."""
    sell_order = make_real_order(100000, 'sell')
    algo.previous_orders = [sell_order]
    assert not algo.contains_open_long_at_price(100000)

def test_contains_open_long_at_price_multiple(algo: Algo) -> None:
    """Retourne True si plusieurs ordres d'achat existent, dont un au prix donné."""
    algo.previous_orders = [
        make_real_order(99000, 'buy'),
        make_real_order(100000, 'buy'),
        make_real_order(101000, 'sell')
    ]
    assert algo.contains_open_long_at_price(99000)
    assert algo.contains_open_long_at_price(100000)
    assert not algo.contains_open_long_at_price(101000)

def test_contains_close_long_at_price_empty(algo: Algo) -> None:
    """Retourne False si la liste est vide."""
    algo.previous_orders = []
    assert not algo.contains_close_long_at_price(100000)

def test_contains_close_long_at_price_found(algo: Algo) -> None:
    """Retourne True si un ordre de vente existe au prix donné."""
    order = make_real_order(100000, 'sell')
    algo.previous_orders = [order]
    assert algo.contains_close_long_at_price(100000)

def test_contains_close_long_at_price_not_found(algo: Algo) -> None:
    """Retourne False si aucun ordre de vente n'existe au prix donné."""
    order = make_real_order(100000, 'sell')
    algo.previous_orders = [order]
    assert not algo.contains_close_long_at_price(99000)

def test_contains_close_long_at_price_only_buy(algo: Algo) -> None:
    """Retourne False si seul un ordre d'achat existe au prix donné."""
    buy_order = make_real_order(100000, 'buy')
    algo.previous_orders = [buy_order]
    assert not algo.contains_close_long_at_price(100000)

def test_contains_close_long_at_price_multiple(algo: Algo) -> None:
    """Retourne True si plusieurs ordres de vente existent, dont un au prix donné."""
    algo.previous_orders = [
        make_real_order(99000, 'sell'),
        make_real_order(100000, 'sell'),
        make_real_order(101000, 'buy')
    ]
    assert algo.contains_close_long_at_price(99000)
    assert algo.contains_close_long_at_price(100000)
    assert not algo.contains_close_long_at_price(101000)

def test_is_same_price() -> None:
    """Test la comparaison de prix flottants avec tolérance."""
    from src.generic.algo import Algo
    # Strictement égal
    assert Algo.is_same_price(100.0, 100.0)
    # Différence dans la tolérance
    assert Algo.is_same_price(100.0000001, 100.0)
    assert Algo.is_same_price(99.9999999, 100.0)
    # Différence hors tolérance
    assert not Algo.is_same_price(100.0001, 100.0)
    assert not Algo.is_same_price(99.9998, 100.0)

def test_scenario_open_close_long_sequence(algo: Algo, mock_dex) -> None:
    """
    Scénario :
    - Prix initial 100000
    - OL à 99k, CL à 101k
    - Descend à 99k : CL exécuté, OL à 98k et CL à 100k créés
    - Remonte à 100k : OL exécuté, il doit rester OL à 99k et CL à 101k
    """
    gap = 1000
    initial_price = 100000
    algo.GAPS = [gap]
    algo.current_gap_idx = 0

    # 1. État initial
    ol_99k = make_real_order(99000, 'buy')
    cl_101k = make_real_order(101000, 'sell')
    algo.previous_orders = [ol_99k, cl_101k]

    # 2. Descend à 99k (exécution du CL à 99k)
    ws_cl_99k = make_real_wsorder(99000, 'sell')
    algo.on_executed_order(wsOrder=ws_cl_99k)
    # On doit avoir OL à 98k et CL à 100k en plus
    assert any(o for o in algo.previous_orders if Algo.is_same_price(o.price, 98000) and algo.isBuyOrder(o))
    assert any(o for o in algo.previous_orders if Algo.is_same_price(o.price, 100000) and algo.isSellOrder(o))

    # 3. Remonte à 100k (exécution de l'OL à 100k)
    ws_ol_100k = make_real_wsorder(100000, 'buy')
    algo.on_executed_order(wsOrder=ws_ol_100k)
    # Il doit rester OL à 99k et CL à 101k
    ol_99k_exists = any(o for o in algo.previous_orders if Algo.is_same_price(o.price, 99000) and algo.isBuyOrder(o))
    cl_101k_exists = any(o for o in algo.previous_orders if Algo.is_same_price(o.price, 101000) and algo.isSellOrder(o))
    assert ol_99k_exists, "Il doit rester un OL à 99k"
    assert cl_101k_exists, "Il doit rester un CL à 101k"
    # Il ne doit pas y avoir de doublons
    assert sum(1 for o in algo.previous_orders if Algo.is_same_price(o.price, 99000) and algo.isBuyOrder(o)) == 1
    assert sum(1 for o in algo.previous_orders if Algo.is_same_price(o.price, 101000) and algo.isSellOrder(o)) == 1