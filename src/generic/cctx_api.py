import logging
from pprint import pprint

import ccxt
import dataclasses
from ccxt.base.types import Balances

from src.generic.cctx_balance_model import AccountData
from src.generic.cctx_mapper import parse_order, parse_balance
from src.generic.cctx_model import Order


def to_float(value) -> float:
    return float(value)

@dataclasses.dataclass
class AccountDataOld:
    totalPositionValue: float
    positionMargin: float

@dataclasses.dataclass
class DexConfig:
    symbol: str
    marginCoin: str
    isTest: bool
    walletAddress: str
    apiKey: str

class Dex:
    buy = 'buy'
    sell = 'sell'

    logger = logging.getLogger(__name__)

    def __init__(self, dex_config: DexConfig):
        self.symbol = dex_config.symbol
        self.marginCoin = dex_config.marginCoin
        self.dex = ccxt.hyperliquid({
            'walletAddress': dex_config.walletAddress,
            "privateKey": dex_config.apiKey,
            'options': {'sandbox': dex_config.isTest},
        })
        self.previous_orders = []

    def get_open_orders(self) -> [Order]:
        open_orders = self.dex.fetch_open_orders()
        return [parse_order(order) for order in open_orders]

    # immediate market buy
    def buy_at_market_price(self, qty: float, price: float):
        self.logger.info(f"Buying {qty} at market price : {price}")
        return self._create_and_fetch_order('market', 'buy', qty, price)

    def _create_and_fetch_order(self, order_type: str, side: str, qty: float, price: float, params: dict = None) -> Order:
        """
        Méthode générique pour créer un ordre et récupérer ses détails complets.
        
        Args:
            order_type: Type d'ordre ('limit', 'market', etc.)
            side: 'buy' ou 'sell'
            qty: Quantité
            price: Prix
            params: Paramètres additionnels pour l'ordre
            
        Returns:
            Order: Objet ordre parsé avec tous les détails
            
        Raises:
            Exception: Si la création de l'ordre échoue
        """
        if params is None:
            params = {}
            
        self.logger.info(f"api - Creating {side} {order_type} order: {qty} at {price}")
        
        try:
            # Créer l'ordre
            order_creation_response = self.dex.create_order(
                symbol=self.get_symbol(), 
                type=order_type, 
                side=side, 
                amount=qty, 
                price=price, 
                params=params
            )
            
            if not order_creation_response:
                raise Exception("Order creation returned empty response")
                
            self.logger.info(f"Order creation response: {order_creation_response}")
            
            # Vérifier que l'ordre a bien été créé
            if 'id' not in order_creation_response or not order_creation_response['id']:
                raise Exception(f"Order creation failed: {order_creation_response}")
                
            order_id = order_creation_response['id']
            
            # Récupérer les détails complets de l'ordre
            try:
                full_order = self.dex.fetch_order(order_id, self.get_symbol())
                if not full_order:
                    raise Exception(f"Could not fetch order details for {order_id}")
                self.logger.info(f"Successfully fetched order details: {full_order}")
                return parse_order(full_order)
            except Exception as e:
                self.logger.warning(f"Could not fetch full order details for {order_id}: {e}")
                # Fallback vers la réponse de création si fetch_order échoue
                parsed_order = parse_order(order_creation_response)
                self.logger.info(f"Using creation response as fallback: {parsed_order}")
                return parsed_order
                
        except Exception as e:
            self.logger.error(f"Failed to create order: {e}")
            raise

    def create_open_long(self, qty, price) -> Order:
        return self._create_and_fetch_order('limit', 'buy', qty, price)

    def create_close_long(self, qty, price) -> Order:
        return self._create_and_fetch_order('limit', 'sell', qty, price)

    def cancel_order(self, order_id: str):
        self.logger.info(f"api - Cancelling order {order_id}")
        self.dex.cancel_order(order_id, symbol=self.get_symbol())

    def get_perp_available_balance(self) -> float:
        amount = self.dex.fetch_balance()[self.marginCoin]['free']
        return to_float(amount)

    def get_perp_balance_infos(self) -> Balances:
        return self.dex.fetch_balance()

    def get_current_price(self) -> float:
        price = self.dex.fetch_ticker(self.get_symbol())['last']
        return to_float(price)

    def set_cross_margin_leverage(self, leverage: int):
        self.dex.set_margin_mode('cross', symbol=self.get_symbol(), params={"leverage": leverage})

    def get_symbol(self) -> str:
        return self.symbol + '/' + self.marginCoin + ':' + self.marginCoin

    def get_full_account_data(self) -> AccountData:
        data = self.dex.fetch_balance()
        return parse_balance(data)


    ## TODO: remove
    def get_account_data(self) -> AccountDataOld :
        full_data = self.dex.fetch_balance()
        # nb: there is also a 'MarginSummary' key. Since we are in CrossMargin they contain the same data
        return AccountDataOld(
            totalPositionValue=float(full_data['info']['crossMarginSummary']['totalNtlPos']),
            positionMargin=float(full_data['info']['crossMarginSummary']['totalMarginUsed']))

    ## TODO: test this method
    def transfer_from_perp_to_spot(self, amount: float):
        amount = 10  # Amount in USDC
        currency = 'USDC'
        from_account = 'perp'
        to_account = 'spot'

#        await exchange.transfer(currency, amount, from_account, to_account)

        self.dex.transfer(code=currency,
                          amount=amount,
                          fromAccount='perp',
                          toAccount='spot')

    def get_account_value(self) -> float:
        self.logger.info('API - Fetching account value')
        account_value = self.dex.fetch_balance()
        return to_float(account_value)
