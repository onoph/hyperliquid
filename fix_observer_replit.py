#!/usr/bin/env python3
"""
Fix pour l'observer WebSocket sur Replit
Améliore le debugging et corrige les problèmes courants
"""

import traceback
import json
import ssl
import threading
import time
import logging
import certifi
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import WebSocket avec fallback
try:
    import websocket
    if not hasattr(websocket, 'WebSocketApp'):
        raise ImportError("websocket module doesn't have WebSocketApp")
    logger.info("✅ websocket-client importé avec succès")
except ImportError:
    try:
        import websocket_client as websocket
        logger.info("✅ websocket_client importé comme fallback")
    except ImportError:
        logger.error("❌ Aucun module WebSocket disponible")
        raise ImportError("Neither 'websocket' with WebSocketApp nor 'websocket-client' is available")

from dacite import from_dict
from src.generic.hyperliquid_ws_model import WsMessage, WsOrder
from src.generic.cctx_mapper import safe_parse
from src.generic.algo import Algo


class ImprovedHyperliquidObserver:
    """Version améliorée de l'observer avec meilleur debugging pour Replit"""
    
    def __init__(self, address: str, algo: Algo, debug: bool = True):
        self.address = address
        self.algo = algo
        self.debug = debug
        self.hyperliquid_ws = ImprovedHyperliquidWebSocket(
            url="wss://api.hyperliquid-testnet.xyz/ws",
            address=address,
            observer=self,
            debug=debug
        )
        
        if self.debug:
            logger.info(f"🔍 Observer créé pour adresse: {address[:10]}...")

    def handle_order_updates(self, ws_orders: [WsOrder]):
        """Gestion améliorée des mises à jour d'ordres"""
        logger.info(f"📋 Traitement de {len(ws_orders)} mise(s) à jour d'ordre")
        
        for i, ws_order in enumerate(ws_orders):
            try:
                if self.debug:
                    logger.info(f"📦 Ordre {i+1}: Status={ws_order.status}")
                    
                if ws_order.status == 'filled':
                    logger.info(f"✅ Ordre exécuté: {ws_order.order.oid}")
                    self.algo.on_executed_order(ws_order)
                elif ws_order.status == 'open':
                    logger.info(f"📝 Ordre ouvert: {ws_order.order.oid}")
                elif ws_order.status == 'canceled':
                    logger.info(f"❌ Ordre annulé: {ws_order.order.oid}")
                else:
                    logger.info(f"ℹ️  Autre status '{ws_order.status}': {ws_order.order.oid}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur traitement ordre {i+1}: {e}")
                if self.debug:
                    traceback.print_exc()

    def start(self):
        """Démarrer l'observer"""
        logger.info("🚀 Démarrage de l'observer...")
        self.hyperliquid_ws.start_watch()

    def stop(self):
        """Arrêter l'observer"""
        logger.info("🛑 Arrêt de l'observer...")
        self.hyperliquid_ws.running = False
        if self.hyperliquid_ws.ws:
            self.hyperliquid_ws.ws.close()


class ImprovedHyperliquidWebSocket:
    """Version améliorée du WebSocket avec meilleur debugging"""
    
    def __init__(self, url: str, address: str, observer: ImprovedHyperliquidObserver, debug: bool = True):
        self.url = url
        self.address = address
        self.observer = observer
        self.debug = debug
        self.ws = None
        self.running = False
        self.connected = False
        self.subscription_sent = False
        self.reconnect_count = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2
        self.last_ping = None
        self.message_count = 0
        
        logger.info(f"🔧 WebSocket configuré pour: {url}")
        self._setup_websocket()

    def _setup_websocket(self):
        """Configurer le WebSocket"""
        try:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            logger.info("✅ WebSocketApp configuré")
        except Exception as e:
            logger.error(f"❌ Erreur configuration WebSocket: {e}")
            raise

    def start_watch(self):
        """Démarrer la surveillance"""
        self.running = True
        logger.info("🔄 Démarrage du thread WebSocket...")
        threading.Thread(target=self._run_websocket, daemon=True).start()

    def _run_websocket(self):
        """Boucle principale WebSocket"""
        if self.debug:
            websocket.enableTrace(True)
            
        while self.running:
            try:
                logger.info("🔌 Tentative de connexion WebSocket...")
                self.ws.run_forever(
                    sslopt={
                        "cert_reqs": ssl.CERT_REQUIRED, 
                        "ca_certs": certifi.where()
                    },
                    ping_interval=20,
                    ping_timeout=10
                )
                
                if not self.running:
                    break
                    
            except Exception as e:
                logger.error(f"❌ Erreur WebSocket: {e}")
                if self.debug:
                    traceback.print_exc()
                self._attempt_reconnect()

    def _attempt_reconnect(self):
        """Tentative de reconnexion avec backoff exponentiel"""
        if self.reconnect_count >= self.max_reconnect_attempts:
            logger.error(f"🚫 Abandon après {self.reconnect_count} tentatives")
            self.running = False
            return

        delay = min(30, self.reconnect_delay * (2 ** self.reconnect_count))
        logger.warning(f"⏳ Reconnexion dans {delay}s (tentative {self.reconnect_count + 1})")
        time.sleep(delay)
        self.reconnect_count += 1
        
        # Recréer WebSocket
        self._setup_websocket()

    def on_open(self, ws):
        """Connexion ouverte"""
        logger.info("✅ WebSocket connecté avec succès !")
        self.connected = True
        self.reconnect_count = 0
        
        # Envoyer souscription
        try:
            subscription_message = {
                "method": "subscribe",
                "subscription": {
                    "type": "orderUpdates",
                    "user": self.address
                }
            }
            ws.send(json.dumps(subscription_message))
            self.subscription_sent = True
            logger.info(f"📡 Souscription envoyée pour: {self.address[:10]}...")
            
            # Démarrer ping
            threading.Thread(target=self.run_ping, daemon=True).start()
            
        except Exception as e:
            logger.error(f"❌ Erreur souscription: {e}")

    def on_message(self, ws, message):
        """Message reçu"""
        self.message_count += 1
        
        try:
            msg = json.loads(message)
            channel = msg.get("channel", "unknown")
            
            if self.debug:
                logger.info(f"📨 Message #{self.message_count}: channel='{channel}'")
            
            if channel == "orderUpdates":
                logger.info("📋 Mise à jour d'ordres reçue")
                try:
                    order_updates = safe_parse(WsMessage[WsOrder], msg)
                    self.observer.handle_order_updates(order_updates.data)
                except Exception as e:
                    logger.error(f"❌ Erreur parsing ordre: {e}")
                    if self.debug:
                        logger.debug(f"Message brut: {message}")
            elif channel == "pong":
                self.last_ping = time.time()
                if self.debug:
                    logger.debug("🏓 Pong reçu")
            else:
                if self.debug:
                    logger.debug(f"📨 Autre message: {channel}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur JSON: {e}")
            if self.debug:
                logger.debug(f"Message invalide: {message[:200]}...")
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")

    def on_error(self, ws, error):
        """Erreur WebSocket"""
        logger.error(f"❌ Erreur WebSocket: {error}")
        if self.debug:
            traceback.print_exc()

    def on_close(self, ws, close_status_code, close_msg):
        """Connexion fermée"""
        logger.warning(f"🔌 WebSocket fermé: {close_status_code} - {close_msg}")
        self.connected = False
        self.subscription_sent = False

    def run_ping(self):
        """Maintenir la connexion avec ping"""
        logger.info("🏓 Démarrage du ping keeper")
        while self.connected and self.running:
            try:
                time.sleep(20)
                if self.ws and self.connected:
                    self.ws.send(json.dumps({"method": "ping"}))
                    if self.debug:
                        logger.debug("🏓 Ping envoyé")
            except Exception as e:
                logger.error(f"❌ Erreur ping: {e}")
                break
        logger.info("🏓 Ping keeper arrêté")


# Test de l'observer amélioré
def test_improved_observer():
    """Test de l'observer amélioré"""
    print("🧪 Test de l'observer amélioré")
    
    # Adresse de test
    test_address = input("Adresse wallet testnet (ENTER pour test): ").strip()
    if not test_address:
        test_address = "0x0000000000000000000000000000000000000000"
    
    # Mock algo simple
    class TestAlgo(Algo):
        def on_executed_order(self, ws_order: WsOrder):
            logger.info(f"🎯 ALGO: Ordre exécuté reçu ! {ws_order.order.oid}")
    
    # Créer observer
    algo = TestAlgo()
    observer = ImprovedHyperliquidObserver(test_address, algo, debug=True)
    
    # Démarrer
    observer.start()
    
    # Attendre
    try:
        print("⏳ Observer en cours... (Ctrl+C pour arrêter)")
        while True:
            time.sleep(10)
            logger.info(f"📊 Status: Connecté={observer.hyperliquid_ws.connected}, Messages={observer.hyperliquid_ws.message_count}")
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé")
        observer.stop()
        time.sleep(2)


if __name__ == "__main__":
    test_improved_observer() 