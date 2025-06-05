from dataclasses import dataclass
import time
from pprint import pprint
from typing import Literal

from src.generic.cctx_balance_model import AccountData
from src.generic.hyperliquid_ws_model import WsOrder


@dataclass
class ExecutedOrder:
    type: Literal['buy', 'sell']
    price: float
    timestamp: time

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
from IPython.core.events import available_events
#   principe pour la quantité achetée sur un long :
#
# objectif : éloigner la liquidation
# - quantité adaptative
#   - PERP funds / 6 / prix BTC

from hyperliquid.ccxt.base.types import OrderSide
from typing import Optional

from src.generic.cctx_api import Dex
from src.generic.cctx_model import Order

import logging

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

    GAPS = [100, 500, 1000, 1500, 2000, 2500, 3000] # gap price to 100 for testing
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

    def get_gap(self):
        return self.GAPS[self.current_gap_idx]

    def __init__(self, dex: Dex, max_leverage: int = 40):
        self.dex = dex
        self.max_leverage = max_leverage
        self.coin_manager.setInitialCoinCount(self.nbCoins)

    # Initialize the algorithm by setting up initial positions
    def setup_initial_positions(self):
        self.logger.info("Setting up initial positions...")

        self.logger.info(f"Setting leverage to {self.max_leverage} for cross margin trading")
        self.dex.set_cross_margin_leverage(self.max_leverage)

        #intial data: BOT should have no position
        available_amount_to_trade = self.dex.get_full_account_data().USDC.free
        current_price = self.dex.get_current_price()
        self.logger.info(f"Available amount to trade: {available_amount_to_trade} - Current price: {current_price}")

        # buy at market price
        initial_position_qty = self.compute_coin_qty(perp_account_equity=available_amount_to_trade,
                                                     current_price=current_price)
        initial_buy_qty = initial_position_qty * self.initial_coins_buy
        print(f"Initial buy quantity: {initial_buy_qty} - unit : {initial_buy_qty}")
        self.dex.buy_at_market_price(qty=initial_buy_qty, price=current_price)

        # create initial OL and CL positions
        gap = self.get_gap()
        self.create_open_long_order(qty=initial_buy_qty, price=current_price - gap)
        self.create_close_long_order(qty=initial_buy_qty, price=current_price + gap)


    def compute_coin_qty(self, perp_account_equity: float, current_price: float) -> float:
        return perp_account_equity / self.qtyDivider / current_price


    #def create_initial_positions_from_start(self, current_price: float):
    #    order_qty = self.compute_order_qty(current_price)
    #    self.create_initial_positions(qty=order_qty, current_price=current_price, gap = self.get_gap())


    # create initial long and short positions
#    def create_initial_positions(self, qty: float, current_price: float, gap: float):
#        # init short position
#        short_price = current_price + gap
#        order = self.dex.create_close_long(qty, short_price)
#        self.previous_orders.append(order)
#
#        # init long positions
#        for i in range(1, self.max_long_orders):
#            long_price = current_price - (i * gap)
#            order = self.dex.create_open_long(qty, long_price)
#            self.previous_orders.append(order)


    def retrieve_previous_orders(self):
        self.previous_orders = self.dex.get_open_orders()

    # retrieves current orders from dex and checks if they have been executed
    # if some have been executed creates new ones
    # def check_orders(self):
    #     current_open_orders = self.dex.get_open_orders()
    #     previous_order_ids = [o.id for o in self.previous_orders]
    #     executed_orders = [order for order in current_open_orders if order.id not in previous_order_ids]
    #
    #     lazy_current_price = self.LazyCurrentPrice(self.dex)
    #
    #     if len(current_open_orders) == 0:
    #         # all have been executed
    #         self.create_initial_positions_from_start(current_price=lazy_current_price.get())
    #
    #     ## DEMO
    #     # if len(executed_orders) == 0:
    #     #     executed_orders = [current_open_orders[0]]
    #     #     executed_orders[0].price = 111000
    #
    #     # TODO : check if many orders were executed. If true it could be more interesting to do something else
    #     if executed_orders:
    #         print(f"Executed order: {executed_orders[0].id} : {executed_orders[0].side} at price {executed_orders[0].price}")
    #         asset_price = lazy_current_price.get()
    #         position_qty = self.compute_order_qty(asset_price)
    #
    #         if self.should_place_short(asset_price, current_open_orders):
    #             short_price = asset_price + self.get_gap()
    #             print(f"Creating short limit order: {position_qty} at {short_price}")
    #             #self.dex.createShortLimit(position_qty, short_price)
    #
    #         if self.should_place_long(asset_price, current_open_orders):
    #             long_price = asset_price - self.get_gap()
    #             print(f"Creating long limit order: {position_qty} at {long_price}")
    #             #self.dex.createLongLimit(position_qty, long_price)


    def on_canceled_order(self, wsOrder: WsOrder):
        self.remove_from_previous_orders(str(wsOrder.order.oid))


    def on_executed_order(self, wsOrder: WsOrder):
        pprint(f"on_executed_order: {wsOrder}")
        order = wsOrder.order
        self.logger.info(f"Order executed: {order.oid} - {order.side} at price {order.limitPx}")

        # manage internal state
        self.executed_orders_tracker.add_order(wsOrder)
        self.remove_from_previous_orders(str(wsOrder.order.oid))

        full_account_data  = self.dex.get_full_account_data()
        perp_account_equity = full_account_data.USDC.total
        print(' --> in on_executed_order')
        print(f" --> wsOrder.order.side: {wsOrder.order.side}")
        if wsOrder.order.side == 'B': # 'B' = Bid = buy
            self.handle_executed_open_long(perp_account_equity, wsOrder)
        elif wsOrder.order.side == 'A': # 'A' = Ask = sell
            self.handle_executed_close_long(perp_account_equity, wsOrder)

        #if order.side == 'B':
        #    min_long_price = self.get_min_long_order() - self.get_gap()
        #    qty = self.compute_adaptive_order_qty(asset_price, full_account_data)
        #    self.executed_orders_tracker.add_buy(order.limitPx)
        #    self.dex.create_open_long(qty=qty, price=min_long_price)
        #elif order.side == 'S':
        #    new_short_price = order.limitPx + self.get_gap()
        #    qty = self.compute_adaptive_order_qty(asset_price, full_account_data)
        #    self.executed_orders_tracker.add_sell(order.limitPx)
        #    self.dex.create_close_long(qty=qty, price=new_short_price)

    def remove_from_previous_orders(self, order_id: str):
        # log size before and after
        print(f"Removing order: {order_id} from previous orders. Size before: {len(self.previous_orders)}")
        print(f"Orders before removal: {[f'{o.id} (price: {o.price}, side: {o.side})' for o in self.previous_orders]}")
        self.previous_orders = [o for o in self.previous_orders if o.id != order_id]
        print(f"Size after: {len(self.previous_orders)}")
        print(f"Orders after removal: {[f'{o.id} (price: {o.price}, side: {o.side})' for o in self.previous_orders]}")
        print(" -------- ")


    # close long executed -> means the price has gone up and we have sold a coin
    # we do the same as for open long executed, except we remove the previous open long order
    def handle_executed_close_long(self, perp_account_equity: float, wsOrder: WsOrder):
        print(f" --> in function handle_executed_close_long")
        self.logger.info(f" --> Close long executed: {wsOrder.order.oid} at price {wsOrder.order.limitPx}")
        self.handle_common_close_open_long_executed(perp_account_equity, wsOrder)
        self.coin_manager.decrementCoinCount()

        if self.coin_manager.getCoinCount() < self.minNbCoins:
            self.logger.info(f"Coin count is below minimum ({self.minNbCoins}). Buying {2} coins at market price")
            current_price = wsOrder.order.limitPx
            qty = 2 * self.compute_coin_qty(perp_account_equity, current_price)
            self.dex.buy_at_market_price(qty, current_price)


    # open long executed -> means the price has gone down and we have bought a coin
    # buying a coin means we must sell it later at a higher price
    def handle_executed_open_long(self, perp_account_equity: float, wsOrder: WsOrder):
        print(f" --> in function handle_executed_open_long")
        self.logger.info(f" --> Open long executed: {wsOrder.order.oid} at price {wsOrder.order.limitPx}")
        self.handle_common_close_open_long_executed(perp_account_equity, wsOrder)
        self.coin_manager.incrementCoinCount()


    def handle_common_close_open_long_executed(self, perp_account_equity: float, wsOrder: WsOrder):
        # compute qty to buy
        qty = self.compute_coin_qty(perp_account_equity, wsOrder.order.limitPx)
        gap = self.get_gap()
        current_price = wsOrder.order.limitPx
        self.logger.info(f"new order qty: {qty} - current price: {current_price} - gap: {gap}")

        self.create_open_long_order(qty, current_price - gap)
        self.create_close_long_order(qty, current_price + gap)

        self.remove_min_open_long_orders()


    def create_open_long_order(self, qty: float, price: float) -> Order:
        print(f" --> in function create_open_long_order")
        if not self.contains_open_long_at_price(price):
            print(f"Creating open long order: {qty} at {price}")
            new_open_long = self.dex.create_open_long(qty=qty, price=price)
            print(f" --> Open long order created: {new_open_long}")
            self.previous_orders.append(new_open_long)
            return new_open_long
        print(f" --> Open long order already exists at {price}")
        return None
    
    def create_close_long_order(self, qty: float, price: float) -> Order:
        print(f" --> in function create_close_long_order")
        if not self.contains_close_long_at_price(price):
            print(f" --> Creating close long order: {qty} at {price}")
            new_close_long = self.dex.create_close_long(qty=qty, price=price)
            print(f" --> Close long order created: {new_close_long}")
            self.previous_orders.append(new_close_long)
            return new_close_long
        print(f" --> Close long order already exists at {price}")
        return None

    def remove_min_open_long_orders(self):
        min_open_long_orders = self.get_min_open_long_orders()
        for order in min_open_long_orders:
            self.logger.info(f" --> Removing min open long order: {order.id}")
            self.remove_order(order)

    def contains_open_long_at_price(self, price: float) -> bool:
        return any(order for order in self.previous_orders if order.price == price and order.side == BUY)
    
    def contains_close_long_at_price(self, price: float) -> bool:
        return any(order for order in self.previous_orders if order.price == price and order.side == SELL)

    def get_min_open_long_orders(self) -> [Order]:
        open_long_orders = [order for order in self.previous_orders if order.side == BUY or order.side == 'B']
        open_long_orders.sort(key=lambda o: o.price)
        # Keep only the highest price open long order (most recent), remove all others
        if len(open_long_orders) > 1:
            return open_long_orders[:-1]  # Return all except the last (highest price)
        return []

    def get_min_open_long_order(self) -> Optional[Order]:
        """Retrieves the open long order with min price from previous orders."""
        open_long_orders = [order for order in self.previous_orders if order.side == BUY]
        open_long_orders.sort(key=lambda o: o.price)
        self.logger.info(f"Open long orders: {open_long_orders}")
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

    #def get_min_long_order(self) -> float:
    #    # retrieves prder with min price from previous orders
    #    if not self.previous_orders:
    #        return 0.0
    #    min_long_order = min(
    #        (order for order in self.previous_orders if order.side == BUY),
    #        key=lambda o: o.price,
    #        default=None
    #    )
    #    return min_long_order.price if min_long_order else 0.0

    #def should_place_short(self, asset_price, orders: [Order]) -> bool:
    #    order = self.find_order_in_range(asset_price, orders, SELL, self.get_gap())
    #    if order:
    #        print(f"Order already exists in range: {order.get('id') - order.get('price')}")
    #        return False
    #    return True


    #def should_place_long(self, asset_price: float, orders: [Order]) -> bool:
    #    order = self.find_order_in_range(asset_price, orders, BUY, self.get_gap())
    #    if order:
    #        print(f"Order already exists in range: {order.get('id') - order.get('price')}")
    #        return False
    #    return True

    #def find_order_in_range(self, asset_price, orders: [Order], order_type: OrderSide, gap: float) -> Optional[any]:
    #    target_price = asset_price + gap
    #    price_range_start = target_price - (gap)
    #    price_range_end = target_price - (gap)
    #
    #    order_in_range = list(filter(lambda o:
    #                                order_type == o.side and
    #                                price_range_start <= o.price <= price_range_end, orders))
    #    if len(order_in_range) > 0:
    #        return order_in_range[0]
    #    return None

    class LazyCurrentPrice:
        current_price: float = None

        def __init__(self, dex: Dex):
            self.dex = dex

        def get(self) -> float:
            """Fetch the current price from the dex."""
            if self.current_price is None:
                self.current_price = self.dex.get_current_price()
            return self.current_price