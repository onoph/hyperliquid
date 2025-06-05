import os
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL, TESTNET_API_URL
from .hyperliquid_mappers import HyperliquidApiMapper
from .hyperliquid_models import Position, Order
from typing import List, Dict

class HyperliquidAPI:
    def __init__(self):
        load_dotenv()
        self.wallet_address = os.getenv("WALLET_ADDRESS")
        if not self.wallet_address:
            raise ValueError("WALLET_ADDRESS environment variable is not set")
            
        self.is_prod = os.getenv("IS_PROD", "false").strip().lower() == 'true'
        self.api_url = MAINNET_API_URL if self.is_prod else TESTNET_API_URL
        print(f"Using API URL: {self.api_url}")
        print(f"Wallet address: {self.wallet_address}")
        print(f"Environment: {'Mainnet' if self.is_prod else 'Testnet'}")
        print(f"Mainnet URL: {MAINNET_API_URL}")
        print(f"Testnet URL: {TESTNET_API_URL}")
        self.info = Info(base_url=self.api_url, skip_ws=True)

    def get_balance(self) -> Dict:
        user_state = self.info.user_state(self.wallet_address)
        return user_state.get("marginSummary", {})
    
    def get_asset_price(self, traded: str) -> float:
        return 100000;

    def get_positions(self) -> List[Position]:
        user_state = self.info.user_state(self.wallet_address)
        asset_positions = user_state.get("assetPositions", [])
        print("asset_positions", asset_positions)
        return HyperliquidApiMapper.map_positions(asset_positions)

    def get_open_orders(self) -> List[Order]:
        open_orders = self.info.open_orders(self.wallet_address)
        return HyperliquidApiMapper.map_orders(open_orders)

    def buyAtMarketPrice(self, symbol: str, marginCoin: str, qty: float):
        print("")

    def openLongPosition(self, symbol: str, marginCoin: str, qty: float):
        print("")

    def createLongOrder(self, symbol: str, marginCoin: str, qty: float, price: float):
        self.info.exchange_order(self.wallet_address, symbol, marginCoin, qty, price)
        print("")

    def createShortOrder(self, symbol: str, marginCoin: str, qty: float, price: float):
        print("")