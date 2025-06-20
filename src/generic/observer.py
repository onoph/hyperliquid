import traceback

from src.generic.cctx_mapper import safe_parse
from src.generic.hyperliquid_ws_model import WsMessage, WsOrder
from src.generic.algo import Algo

import logging
class HyperliquidObserver:
    logger = logging.getLogger(__name__)

    def __init__(self, address: str, observer_id: str, websocket_url: str, algo: Algo):
        self.address = address
        self.observer_id = observer_id
        self.algo = algo
        self.hyperliquid_ws = HyperliquidWebSocket(
            url=websocket_url,
            address=address,
            observer=self
        )

    def handle_order_updates(self, ws_orders: [WsOrder]):
        self.logger.debug(f"Observer {self.observer_id} received {len(ws_orders)} order updates")
        for ws_order in ws_orders:
            self.logger.debug(f"Observer {self.observer_id} processing order: {ws_order}")
            try:
                #if order.status == 'deleted':
                #    self.algo.on_deleted_order(order)
                if ws_order.status == 'filled':
                    self.algo.on_executed_order(ws_order)
                else:
                    pass
            except Exception as e:
                self.logger.error(f"Observer {self.observer_id} error processing order {ws_order.order.oid if hasattr(ws_order.order, 'oid') else 'unknown'}: {e}")
                self.logger.error(traceback.format_exc())


    def start(self):
        """Start the observer and keep it running."""
        self.logger.info(f"Starting HyperliquidObserver for {self.address}")
        self.hyperliquid_ws.start_watch()
        
        # Garder le thread principal vivant tant que le WebSocket tourne
        import time
        while self.hyperliquid_ws.running:
            time.sleep(1)
            
        self.logger.warning(f"HyperliquidObserver for {self.address} stopping (WebSocket stopped)")

    def stop(self):
        self.logger.info(f"Observer {self.observer_id} stopping HyperliquidObserver for address {self.address}")
        self.hyperliquid_ws.stop()
        self.logger.info(f"Observer {self.observer_id} HyperliquidObserver stopped successfully for address {self.address}")


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
                self.logger.info("Connecting to WebSocket...")
                self.ws.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": certifi.where()},)

                if not self.running:
                    self.logger.info("WebSocket run loop stopped (running=False)")
                    break
                else:
                    self.logger.warning("WebSocket run_forever ended but running=True, attempting reconnect...")
                    self._attempt_reconnect()
            except Exception as e:
                self.logger.error(f"WebSocket run_forever error: {e}")
                if self.running:
                    self._attempt_reconnect()
                else:
                    break

    def _attempt_reconnect(self):
        if not self.running:
            self.logger.info("Reconnection aborted: observer is stopping")
            return
            
        if self.reconnect_count >= self.max_reconnect_attempts:
            self.logger.error(f"Échec après {self.reconnect_count} tentatives de reconnexion. Abandon.")
            self.running = False
            return

        self.reconnect_count += 1
        delay = min(60, self.reconnect_delay * (2 ** (self.reconnect_count - 1)))  # Exponential backoff
        self.logger.info(f"Tentative de reconnexion #{self.reconnect_count} dans {delay:.2f} secondes...")
        
        for i in range(int(delay * 10)):  # Check every 0.1s if we should stop
            if not self.running:
                self.logger.info("Reconnection cancelled: observer is stopping")
                return
            time.sleep(0.1)
        
        if not self.running:
            return
            
        self.logger.info(f"Reconnecting to WebSocket (attempt #{self.reconnect_count})...")
        
        # Nettoyer l'ancienne connexion
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        
        # Recréer un nouveau WebSocketApp pour la reconnexion
        self._setup_websocket()

    def on_message(self, ws, message):
        if not self.running:
            return
            
        try:
            msg = json.loads(message)
            channel = msg.get("channel")
            self.logger.debug(f"Received message: {msg}")
            if channel == "orderUpdates":
                order_updates = safe_parse(WsMessage[WsOrder], msg)
                self.observer.handle_order_updates(order_updates.data)
            #else:
            #    ("Autre message :", msg)
        except Exception as e:
            if self.running:  # Ne logger que si on devrait encore tourner
                self.logger.error(f"Error processing message: {e}")

    def on_error(self, ws, error):
        if self.running:  # Ne logger que si on devrait encore tourner
            self.logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        if self.running:
            self.logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.running = False  # S'assurer que running est à False
        
    def stop(self):
        """Stop the WebSocket connection properly."""
        self.logger.info("Stopping WebSocket connection")
        self.running = False
        
        # Attendre un peu que les threads se terminent
        import time
        time.sleep(0.1)
        
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass  # Ignorer les erreurs de fermeture
            finally:
                self.ws = None  # Nettoyer la référence
        
        self.logger.info("WebSocket stopped")

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
        while self.running:
            time.sleep(10)
            if not self.running:
                break
            try:
                if self.ws:
                    self.ws.send(json.dumps({"method": "ping"}))
            except Exception as e:
                self.logger.error(f"Erreur ping : {e}")
                self.logger.error(traceback.format_exc())
                break

