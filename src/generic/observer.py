import traceback

from src.generic.cctx_mapper import safe_parse
from src.generic.hyperliquid_ws_model import WsMessage, WsOrder
from src.generic.algo import Algo

import logging
class HyperliquidObserver:
    logger = logging.getLogger(__name__)

    def __init__(self, address: str, algo: Algo):
        self.address = address
        self.algo = algo
        self.hyperliquid_ws = HyperliquidWebSocket(
            url="wss://api.hyperliquid-testnet.xyz/ws",
            address=address,
            observer=self
        )

    def handle_order_updates(self, ws_orders: [WsOrder]):
        self.logger.debug(f"Received {len(ws_orders)} order updates")
        for ws_order in ws_orders:
            self.logger.debug(f"Processing order: {ws_order}")
            try:
                #if order.status == 'deleted':
                #    self.algo.on_deleted_order(order)
                if ws_order.status == 'filled':
                    self.algo.on_executed_order(ws_order)
                else:
                    pass
            except Exception as e:
                self.logger.error(f"Error processing order {ws_order.order.oid if hasattr(ws_order.order, 'oid') else 'unknown'}: {e}")
                self.logger.error(traceback.format_exc())


    def start(self):
        self.hyperliquid_ws.start_watch()

    def stop(self):
        print("Stopping HyperliquidObserver...")
        self.running = False
        if self.hyperliquid_ws.ws:
            self.hyperliquid_ws.ws.close()


import json
import ssl
import threading
import time

import certifi
try:
    import websocket
    # Vérifier que WebSocketApp existe
    if not hasattr(websocket, 'WebSocketApp'):
        raise ImportError("websocket module doesn't have WebSocketApp")
except ImportError:
    # Fallback sur websocket-client si websocket n'a pas WebSocketApp
    try:
        import websocket_client as websocket
    except ImportError:
        raise ImportError("Neither 'websocket' with WebSocketApp nor 'websocket-client' is available")
from dacite import from_dict

from src.generic.hyperliquid_ws_model import WsMessage, WsOrder
import logging

class HyperliquidWebSocket:
    logger = logging.getLogger(__name__)

    def __init__(self, url, address: str, observer: HyperliquidObserver):
        self.url = url
        self.address = address
        self.observer = observer
        self.ws = None
        self.running = False
        self.reconnect_count = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 1  # délai initial en secondes
        self._setup_websocket()

    def _setup_websocket(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )


    def start_watch(self):
        self.running = True
        threading.Thread(target=self._run_websocket, daemon=True).start()

    def _run_websocket(self):
        websocket.enableTrace(False)
        while self.running:
            try:
                self.ws.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": certifi.where()},)

                if not self.running:
                    break
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                self._attempt_reconnect()

    def _attempt_reconnect(self):
        if self.reconnect_count >= self.max_reconnect_attempts:
            self.logger.error(f"Échec après {self.reconnect_count} tentatives de reconnexion. Abandon.")
            self.running = False
            return

        delay = min(60, self.reconnect_delay * (2 ** self.reconnect_count))  # Exponential backoff
        self.logger.info(f"Tentative de reconnexion dans {delay:.2f} secondes...")
        time.sleep(delay)
        self.reconnect_count += 1
        self.logger.info(f"Tentative de reconnexion #{self.reconnect_count}...")

        # Recréer un nouveau WebSocketApp pour la reconnexion
        self._setup_websocket()

    def on_message(self, ws, message):
        msg = json.loads(message)
        channel = msg.get("channel")
        self.logger.debug(f"Received message: {msg}")
        if channel == "orderUpdates":
            order_updates = safe_parse(WsMessage[WsOrder], msg)
            self.observer.handle_order_updates(order_updates.data)
        #else:
        #    ("Autre message :", msg)

    def on_error(self, ws, error):
        print("Erreur :", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket fermé :", close_status_code, close_msg)

    def on_open(self, ws):
        print("WebSocket connecté avec succès")
        self.reconnect_count = 0

        # subscribe to updates
        user_address = self.address
        subscription_message = {
            "method": "subscribe",
            "subscription": {
                "type": "orderUpdates",
                "user": user_address
            }
        }
        ws.send(json.dumps(subscription_message))

        # keep connection alive with ping
        threading.Thread(target=self.run_ping, daemon=True).start()

    def run_ping(self):
        while True:
            time.sleep(10)
            try:
                self.ws.send(json.dumps({"method": "ping"}))
            except Exception as e:
                self.logger.error(f"Erreur ping : {e}")
                self.logger.error(traceback.format_exc())
                break

