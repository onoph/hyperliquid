from typing import List, Dict
from .hyperliquid_models import Position, Order

class HyperliquidApiMapper:
    @staticmethod
    def map_position(pos: Dict) -> Position:
        position_info = pos.get("position", {})
        return Position(
            coin=position_info.get("coin", ""),
            entry_price=float(position_info.get("entryPx", 0)),
            size=float(position_info.get("s", 0)),
            leverage=float(position_info.get("leverage", 0)),
            unrealized_pnl=float(position_info.get("unrealizedPnl", 0))
        )

    @staticmethod
    def map_positions(asset_positions: List[Dict]) -> List[Position]:
        return [HyperliquidApiMapper.map_position(pos) for pos in asset_positions]

    @staticmethod
    def map_order(order: Dict) -> Order:
        order_type_info = order.get("orderType", {})
        return Order(
            coin=order.get("coin", ""),
            is_buy=order.get("isBuy", False),
            price=float(order.get("px", 0)),
            size=float(order.get("sz", 0)),
            order_type=order_type_info.get("type", ""),
            tif=order_type_info.get("tif", "")
        )

    @staticmethod
    def map_orders(open_orders: List[Dict]) -> List[Order]:
        return [HyperliquidApiMapper.map_order(order) for order in open_orders]
