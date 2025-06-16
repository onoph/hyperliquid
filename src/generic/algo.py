from dataclasses import dataclass
import time
from pprint import pprint
from typing import Literal, Optional

from src.generic.cctx_balance_model import AccountData
from src.generic.hyperliquid_ws_model import WsOrder
from src.data.interface import IData
from src.data.position import Position
from src.data.null_data import NullData


@dataclass
class ExecutedOrder:
    type: Literal['buy', 'sell']
    price: float
    timestamp: time

@dataclass
class InitialSetupData:
    available_amount_to_trade: float
    current_price: float
    initial_qty_single_element: float


class ExecutedOrdersTracker:
    last_executed_orders: [ExecutedOrder] = []

    def add_order(self, wsOrder: WsOrder):
        if not wsOrder or not wsOrder.order:
            return
        order = ExecutedOrder(
            type='buy' if wsOrder.order.side == 'B' else 'sell',
            price=wsOrder.order.limitPx,
            timestamp=time.time())
        self.last_executed_orders.append(order)

    def add_buy(self, price: float):
        self.last_executed_orders.append(ExecutedOrder(type='buy', price=price, timestamp=time.time()))

    def add_sell(self, price: float):
        self.last_executed_orders.append(ExecutedOrder(type='sell', price=price, timestamp=time.time()))



#
#       principe pour les positions
#
# - Etat initial :
#  - ouverture de 3 long sous le prix BTC actuel à des intervalles définis par le gap
#  - ouverture de 1 short au dessus du prix BTC actuel au même intervalle défini par le gap
#
# - quand un long est executé :
#   - ouverture d'une position long (acheteuse) en dessous (prix BTC actuel - gap)
#   - ouverture d'une position short (vendeuse) au dessus (prix BTC actuel + gap)
#
# - quand un short est executé :
#   - Idem
#   principe pour la quantité achetée sur un long :
#
# objectif : éloigner la liquidation
# - quantité adaptative
#   - PERP funds / 6 / prix BTC

from typing import Optional, Literal

from src.generic.cctx_api import Dex
from src.generic.cctx_model import Order
import uuid
import logging

# Types pour les côtés d'ordre
OrderSide = Literal['buy', 'sell']
BUY: OrderSide = 'buy'
SELL: OrderSide = 'sell'

class CoinManager:
    count: int =0

    def setInitialCoinCount(self, count: int):
        self.count = count

    def getCoinCount(self) -> int:
        if self.count == 0:
            raise ValueError("Coin count has not been initialized.")
        return self.count

    def incrementCoinCount(self):
        self.count += 1

    def decrementCoinCount(self):
        if self.count <= 0:
            raise ValueError("Coin count cannot be decremented below zero.")
        self.count -= 1


class Algo:
    logger = logging.getLogger(__name__)

    GAPS = [50, 100, 500, 1000, 1500, 2000, 2500, 3000] # gap price to 100 for testing
    current_gap_idx = 0

    max_leverage = 40
    max_long_orders = 3
    # perpFundsPercentageForInitialLong = 10 # initial percentage to open Long position with PERP funds

    previous_orders: [Order] = []
    executed_orders_tracker = ExecutedOrdersTracker()
    coin_manager = CoinManager()

    nbCoins = 4
    minNbCoins = 1
    initial_coins_buy = 5
    qtyDivider = 6 #TODO: set to 6

    event_id = 0
    
    # Interface de données et session ID
    data_service: IData
    session_id: str

    def __init__(self, dex: Dex, session_id: str, data_service: IData, max_leverage: int = 40):
        self.dex = dex
        self.max_leverage = max_leverage
        self.coin_manager.setInitialCoinCount(self.nbCoins)
        self.data_service = data_service
        self.session_id = session_id

    def get_gap(self):
        return self.GAPS[self.current_gap_idx]

    # Initialize the algorithm by setting up initial positions
    def setup_initial_positions(self):
        self.logger.info("Setting up initial positions...")

        self.logger.info(f"Setting leverage to {self.max_leverage} for cross margin trading")
        self.dex.set_cross_margin_leverage(self.max_leverage)

        #intial data: BOT should have no position
        initial_data = self.compute_initial_data()
        single_position_qty = initial_data.initial_qty_single_element
        current_price = initial_data.current_price

        # buy at market price
        initial_buy_qty = single_position_qty * self.initial_coins_buy
        print(f"Initial buy quantity: {initial_buy_qty} - unit : {initial_buy_qty}")
        self.dex.buy_at_market_price(qty=initial_buy_qty, price=current_price)

        # create initial OL and CL positions
        gap = self.get_gap()
        self.create_open_long_order(qty=single_position_qty, price=current_price - gap)
        self.create_close_long_order(qty=single_position_qty, price=current_price + gap)


    def compute_initial_data(self) -> InitialSetupData:
        available_amount_to_trade = self.dex.get_full_account_data().USDC.free
        current_price = self.dex.get_current_price()
        initial_position_qty = self.compute_coin_qty(perp_account_equity=available_amount_to_trade,
                                                     current_price=current_price)
        self.logger.info(f"Available amount to trade: {available_amount_to_trade} - Current price: {current_price} - Single position quantity : {initial_position_qty}")
        return InitialSetupData(available_amount_to_trade=available_amount_to_trade,
                                current_price=current_price,
                                initial_qty_single_element=initial_position_qty)


    def compute_coin_qty(self, perp_account_equity: float, current_price: float) -> float:
        return perp_account_equity / self.qtyDivider / current_price
    
    
    def retrieve_previous_orders(self):
        self.previous_orders = self.dex.get_open_orders()

    def on_canceled_order(self, wsOrder: WsOrder):
        self.remove_from_previous_orders(str(wsOrder.order.oid))
        # Note: Il faudrait ajouter une méthode on_canceled_order à l'interface IData


    def on_executed_order(self, wsOrder: WsOrder):
        self.event_id += 1
        self.logger.info(f"{self.event_id} on_executed_order: {wsOrder}")

        order = wsOrder.order
        self.logger.info(f"{self.event_id}Order executed: {order.oid} - {order.side} at price {order.limitPx}")

        # Enregistrer l'ordre exécuté
        self.data_service.on_new_order(wsOrder, self.session_id)

        # manage internal state
        self.executed_orders_tracker.add_order(wsOrder)
        self.remove_from_previous_orders(str(wsOrder.order.oid))

        full_account_data  = self.dex.get_full_account_data()
        perp_account_equity = full_account_data.USDC.total
        if self.isBuyOrder(wsOrder.order): # 'B' = Bid = buy
            self.handle_executed_open_long(perp_account_equity, wsOrder)
        elif self.isSellOrder(wsOrder.order): # 'A' = Ask = sell
            self.handle_executed_close_long(perp_account_equity, wsOrder)
        else:
            self.logger.error(f"{self.event_id} --> Unknown order side: {wsOrder.order.side}")

    def remove_from_previous_orders(self, order_id: str):
        # log size before and after
        self.logger.info(f"{self.event_id} - Removing order: {order_id} from previous orders. Size before: {len(self.previous_orders)}")
        self.logger.info(f"{self.event_id} - Size before: {len(self.previous_orders)}")
        self.logger.debug(f"{self.event_id} - Orders before removal: {[f'{o.id} (price: {o.price}, side: {o.side})' for o in self.previous_orders]}")
        self.previous_orders = [o for o in self.previous_orders if o.id != order_id]
        self.logger.info(f"{self.event_id} - Size after: {len(self.previous_orders)}")
        self.logger.debug(f"{self.event_id} - Orders after removal: {[f'{o.id} (price: {o.price}, side: {o.side})' for o in self.previous_orders]}")

    # close long executed -> means the price has gone up and we have sold a coin
    # we do the same as for open long executed, except we remove the previous open long order
    def handle_executed_close_long(self, perp_account_equity: float, wsOrder: WsOrder):
        self.logger.info(f"{self.event_id} --> Close long executed: {wsOrder.order.oid} at price {wsOrder.order.limitPx}")
        
        self.handle_common_close_open_long_executed(perp_account_equity, wsOrder)
        self.coin_manager.decrementCoinCount()

        if self.coin_manager.getCoinCount() <= self.minNbCoins:
            self.logger.info(f"Coin count is below minimum ({self.minNbCoins}). Buying {2} coins at market price")
            current_price = wsOrder.order.limitPx
            qty = 2 * self.compute_coin_qty(perp_account_equity, current_price)
            self.dex.buy_at_market_price(qty, current_price)

        # Enregistrer la position de vente remplie
        user_address = self.dex.get_user_address() if hasattr(self.dex, 'get_user_address') else "unknown"
        self.data_service.on_filled_sell_position(
            symbol=wsOrder.order.coin,
            user_address=user_address,
            side="SHORT",
            qty=wsOrder.order.sz,
            price=wsOrder.order.limitPx,
            session_id=self.session_id
        )


    # open long executed -> means the price has gone down and we have bought a coin
    # buying a coin means we must sell it later at a higher price
    def handle_executed_open_long(self, perp_account_equity: float, wsOrder: WsOrder):
        self.logger.info(f"{self.event_id} --> Open long executed: {wsOrder.order.oid} at price {wsOrder.order.limitPx}")
        
        self.handle_common_close_open_long_executed(perp_account_equity, wsOrder)
        self.coin_manager.incrementCoinCount()

        # Enregistrer la position d'achat remplie
        user_address = self.dex.get_user_address() if hasattr(self.dex, 'get_user_address') else "unknown"
        self.data_service.on_filled_buy_position(
            symbol=wsOrder.order.coin,
            user_address=user_address,
            side="LONG",
            qty=wsOrder.order.sz,
            price=wsOrder.order.limitPx,
            session_id=self.session_id
        )


    def handle_common_close_open_long_executed(self, perp_account_equity: float, wsOrder: WsOrder):
        # compute qty to buy
        qty = self.compute_coin_qty(perp_account_equity, wsOrder.order.limitPx)
        gap = self.get_gap()
        current_price = wsOrder.order.limitPx
        self.logger.info(f"{self.event_id} - new order qty: {qty} - current price: {current_price} - gap: {gap}")

        self.create_open_long_order(qty, current_price - gap)
        self.create_close_long_order(qty, current_price + gap)

        self.remove_min_open_long_orders()
        self.check_current_orders()


    def check_current_orders(self):
        bad_one_open_long = len([o for o in self.previous_orders if self.isBuyOrder(o)]) != 1
        bad_close_long = len([o for o in self.previous_orders if self.isSellOrder(o)]) == 0
        if bad_one_open_long or bad_close_long:
            self.logger.error(f"{self.event_id} - Bad orders state: one open long: {not bad_one_open_long}, close long: {not bad_close_long}")


    def create_open_long_order(self, qty: float, price: float) -> Order:
        if not self.contains_open_long_at_price(price):
            self.logger.info(f"{self.event_id} - Creating open long order: {qty} at {price}")
            new_open_long = self.dex.create_open_long(qty=qty, price=price)
            self.logger.debug(f"{self.event_id} --> Open long order created: {new_open_long}")
            self.previous_orders.append(new_open_long)
            
            # Enregistrer la nouvelle position d'achat
            symbol = getattr(new_open_long, 'symbol', "BTC-USD")
            user_address = self.dex.get_user_address() if hasattr(self.dex, 'get_user_address') else "unknown"
            self.data_service.on_new_buy_position(
                symbol=symbol,
                user_address=user_address,
                side="LONG",
                qty=qty,
                price=price,
                session_id=self.session_id
            )
            return new_open_long
        self.logger.info(f"{self.event_id} --> Open long order already exists at {price}")
        return None
    
    def create_close_long_order(self, qty: float, price: float) -> Order:
        if not self.contains_close_long_at_price(price):
            self.logger.info(f"{self.event_id} --> Creating close long order: {qty} at {price}")
            new_close_long = self.dex.create_close_long(qty=qty, price=price)
            self.logger.debug(f"{self.event_id} --> Close long order created: {new_close_long}")
            self.previous_orders.append(new_close_long)
    
            # Enregistrer la nouvelle position de vente
            symbol = getattr(new_close_long, 'symbol', "BTC-USD")
            user_address = self.dex.get_user_address() if hasattr(self.dex, 'get_user_address') else "unknown"
            self.data_service.on_new_sell_position(
                symbol=symbol,
                user_address=user_address,
                side="SHORT",
                qty=qty,
                price=price,
                session_id=self.session_id
            )
            return new_close_long
        self.logger.info(f"{self.event_id} --> Close long order already exists at {price}")
        return None

    def remove_min_open_long_orders(self):
        min_open_long_orders = self.get_min_open_long_orders()
        for order in min_open_long_orders:
            self.logger.info(f"{self.event_id} --> Removing min open long order: {order.id}")
            self.remove_order(order)

    def contains_open_long_at_price(self, price: float) -> bool:
        """Vérifie si un ordre d'achat existe au prix donné"""
        self.logger.info(f"{self.event_id} - previous orders : {self.previous_orders}")
        for order in self.previous_orders:
            if self.isBuyOrder(order) and float(order.price) == price:
                return True
        return False

    def contains_close_long_at_price(self, price: float) -> bool:
        """Vérifie si un ordre de vente existe au prix donné"""
        for order in self.previous_orders:
            if self.isSellOrder(order) and float(order.price) == price:
                return True
        return False

    def get_min_open_long_orders(self) -> [Order]:
        open_long_orders = [order for order in self.previous_orders if self.isBuyOrder(order)]
        open_long_orders.sort(key=lambda o: o.price)
        # Keep only the highest price open long order (most recent), remove all others
        if len(open_long_orders) > 1:
            return open_long_orders[:-1]  # Return all except the last (highest price)
        return []

    def get_min_open_long_order(self) -> Optional[Order]:
        """Retrieves the open long order with min price from previous orders."""
        open_long_orders = [order for order in self.previous_orders if self.isBuyOrder(order)]
        open_long_orders.sort(key=lambda o: o.price)
        self.logger.debug(f"{self.event_id} - Open long orders: {open_long_orders}")
        return open_long_orders[0] if open_long_orders else None


    ## adaptive quantity : because takes in account the margin account
    def compute_adaptive_order_qty(self, asset_price: float, full_account_data: AccountData) -> float:
        cross_margin_summary = full_account_data.info.crossMarginSummary
        # (total position value - total margin used)
        return (cross_margin_summary.totalNtlPos - cross_margin_summary.totalMarginUsed) / 6 / asset_price


    def compute_order_qty(self, asset_price: float) -> float:
        account_data = self.dex.get_account_data()
        return (account_data.totalPositionValue - account_data.positionMargin) / 6 / asset_price
    
    def remove_order(self, order: Order):
        self.dex.cancel_order(order.id)
        self.previous_orders = [o for o in self.previous_orders if o.id != order.id]

    def recover_previous_state(self):
        self.logger.info("Enter in recovering previous state")
        self.retrieve_previous_orders()

        if not self.requires_recover():
            self.logger.info("Nothing to recover")
            return

        if len(self.previous_orders) == 0:
            self.logger.info("requires to setup initial positions")
            self.setup_initial_positions()
            return
#
        #initial_data = self.compute_initial_data()
        #if not self.contains_open_long():
        #    self.create_open_long_order(initial_data.initial_qty_single_element, initial_data.current_price)
        #if not self.contains_close_long():
        #    self.create_close_long_order(initial_data.initial_qty_single_element, initial_data.current_price)

    ## BAD idea: should think about what represents a real try to compute pricing (market evolution)
    # recover price from previous longs :
    ## min long price +

    def requires_recover(self):
        return not self.contains_close_long() and not self.contains_open_long()

    def contains_open_long(self):
        return any(order for order in self.previous_orders if self.isBuyOrder(order))

    def contains_close_long(self):
        return any(order for order in self.previous_orders if self.isSellOrder(order))

    def isBuyOrder(self, order) -> bool:
        """Vérifie si un ordre est un ordre d'achat."""
        return order.side in ['B', 'buy', BUY]

    def isSellOrder(self, order) -> bool:
        """Vérifie si un ordre est un ordre de vente."""
        return order.side in ['A', 'sell', SELL]

    class LazyCurrentPrice:
        current_price: float = None

        def __init__(self, dex: Dex):
            self.dex = dex

        def get(self) -> float:
            """Fetch the current price from the dex."""
            if self.current_price is None:
                self.current_price = self.dex.get_current_price()
            return self.current_price