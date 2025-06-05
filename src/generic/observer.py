import traceback

from src.generic.cctx_mapper import safe_parse
from src.generic.hyperliquid_ws_model import WsMessage, WsOrder
from src.generic.algo import Algo


class HyperliquidObserver:
    def __init__(self, address: str, algo: Algo):
        self.address = address
        self.algo = algo
        self.hyperliquid_ws = HyperliquidWebSocket(
            url="wss://api.hyperliquid-testnet.xyz/ws",
            address=address,
            observer=self
        )

    def handle_order_updates(self, ws_orders: [WsOrder]):
        for ws_order in ws_orders:
            print(ws_order)
            try:
                #if order.status == 'deleted':
                #    self.algo.on_deleted_order(order)
                if ws_order.status == 'filled':
                    self.algo.on_executed_order(ws_order)
                else:
                    pass
            except Exception as e:
                print(f"Error processing order {ws_order.order.oid if hasattr(ws_order.order, 'oid') else 'unknown'}: {e}")
                # Afficher la stacktrace complète
                traceback.print_exc()


    def start(self):
        self.hyperliquid_ws.start_watch()

    def stop(self):
        if self.hyperliquid_ws.ws:
            self.hyperliquid_ws.ws.close()


import json
import ssl
import threading
import time

import certifi
import websocket
from dacite import from_dict

from src.generic.hyperliquid_ws_model import WsMessage, WsOrder

class HyperliquidWebSocket:

    def __init__(self, url, address: str, observer: HyperliquidObserver):
        self.url = url
        self.address = address
        self.observer = observer
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )

    def start_watch(self):
        websocket.enableTrace(False)
        #self.ws.run_forever(sslopt={"context": ssl.create_default_context(cafile=certifi.where())})
        self.ws.run_forever(
            sslopt={"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": certifi.where()},
            #ping_interval=10,
            #ping_timeout=5
        )

    def on_message(self, ws, message):
        msg = json.loads(message)
        channel = msg.get("channel")
        if channel == "orderUpdates":
            # retrieves a list of order updates
            order_updates = safe_parse(WsMessage[WsOrder], msg)
            self.observer.handle_order_updates(order_updates.data)
        else:
            print("Autre message :", msg)


    def on_error(self, ws, error):
        print("Erreur :", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket fermé :", close_status_code, close_msg)

    def on_open(self, ws):
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
                print("Erreur ping :", e)
                break

