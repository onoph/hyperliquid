#!/usr/bin/env python3
"""
Script de diagnostic WebSocket pour Replit
Teste la connectivité et les limitations WebSocket
"""

import json
import time
import threading
import websocket
import ssl
import certifi
import os
from datetime import datetime
from dotenv import load_dotenv

class WebSocketDiagnostic:
    def __init__(self, test_address: str = None):
        # Charger les variables d'environnement
        load_dotenv()
        
        # Utiliser l'adresse depuis .env si pas d'adresse fournie
        if test_address is None:
            test_address = os.getenv("WALLET_ADDRESS")
            if test_address:
                print(f"📋 Adresse chargée depuis .env: {test_address}")
            else:
                test_address = "0x0000000000000000000000000000000000000000"
                print("⚠️  Aucune WALLET_ADDRESS dans .env, utilisation d'une adresse test")
        
        self.url = "wss://api.hyperliquid-testnet.xyz/ws"
        self.test_address = test_address
        self.ws = None
        self.connected = False
        self.messages_received = 0
        self.last_message_time = None
        self.start_time = None
        
    def log(self, message: str):
        """Log avec timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")

    def test_connection(self, duration_seconds: int = 30):
        """Test la connexion WebSocket pendant X secondes"""
        self.log("🔍 DIAGNOSTIC WEBSOCKET HYPERLIQUID SUR REPLIT")
        self.log("=" * 60)
        self.log(f"URL: {self.url}")
        self.log(f"Adresse test: {self.test_address}")
        self.log(f"Durée du test: {duration_seconds}s")
        self.log("")
        
        # Configurer WebSocket
        websocket.enableTrace(True)  # Debug détaillé
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        # Lancer en thread
        self.start_time = time.time()
        wst = threading.Thread(target=self._run_websocket)
        wst.daemon = True
        wst.start()
        
        # Attendre et monitorer
        try:
            for i in range(duration_seconds):
                time.sleep(1)
                if i % 5 == 0:  # Status toutes les 5s
                    uptime = time.time() - self.start_time if self.start_time else 0
                    self.log(f"⏱️  Uptime: {uptime:.1f}s | Connecté: {self.connected} | Messages: {self.messages_received}")
                    
                    if self.last_message_time:
                        since_last = time.time() - self.last_message_time
                        self.log(f"   Dernier message il y a: {since_last:.1f}s")
                        
        except KeyboardInterrupt:
            self.log("⚠️  Test interrompu par l'utilisateur")
        
        # Fermer connexion
        if self.ws:
            self.ws.close()
            
        # Résultats
        total_time = time.time() - self.start_time if self.start_time else 0
        self.log("")
        self.log("📊 RÉSULTATS DU TEST")
        self.log("=" * 30)
        self.log(f"Durée totale: {total_time:.1f}s")
        self.log(f"Connexion réussie: {'✅' if self.connected else '❌'}")
        self.log(f"Messages reçus: {self.messages_received}")
        
        if self.connected and self.messages_received > 0:
            rate = self.messages_received / total_time * 60
            self.log(f"Taux de messages: {rate:.1f} msg/min")
            self.log("🎉 WebSocket fonctionne sur Replit !")
        elif self.connected:
            self.log("⚠️  Connexion OK mais pas de messages (normal si pas d'activité)")
        else:
            self.log("❌ Problème de connexion WebSocket sur Replit")
            
        return self.connected, self.messages_received

    def _run_websocket(self):
        """Lance la connexion WebSocket"""
        try:
            self.ws.run_forever(
                sslopt={"cert_reqs": ssl.CERT_REQUIRED, "ca_certs": certifi.where()},
                ping_interval=10,  # Ping toutes les 10s
                ping_timeout=5     # Timeout ping 5s
            )
        except Exception as e:
            self.log(f"❌ Erreur WebSocket: {e}")

    def on_open(self, ws):
        """Connexion établie"""
        self.log("✅ WebSocket connecté !")
        self.connected = True
        
        # S'abonner aux mises à jour
        subscription = {
            "method": "subscribe",
            "subscription": {
                "type": "orderUpdates",
                "user": self.test_address
            }
        }
        ws.send(json.dumps(subscription))
        self.log(f"📡 Abonnement envoyé pour: {self.test_address}")

    def on_message(self, ws, message):
        """Message reçu"""
        self.messages_received += 1
        self.last_message_time = time.time()
        
        try:
            data = json.loads(message)
            channel = data.get("channel", "unknown")
            self.log(f"📨 Message #{self.messages_received}: channel='{channel}'")
            
            # Log détaillé pour orderUpdates
            if channel == "orderUpdates":
                orders = data.get("data", [])
                self.log(f"   → {len(orders)} ordre(s) dans la mise à jour")
                for i, order in enumerate(orders):
                    status = order.get("status", "unknown")
                    oid = order.get("order", {}).get("oid", "unknown")
                    self.log(f"   → Ordre {i+1}: ID={oid}, Status={status}")
            
        except json.JSONDecodeError:
            self.log(f"📨 Message #{self.messages_received}: [Non-JSON] {message[:100]}...")

    def on_error(self, ws, error):
        """Erreur WebSocket"""
        self.log(f"❌ Erreur WebSocket: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Connexion fermée"""
        self.log(f"🔌 WebSocket fermé: code={close_status_code}, msg='{close_msg}'")
        self.connected = False

def main():
    """Point d'entrée principal"""
    print("🔧 Diagnostic WebSocket Hyperliquid sur Replit")
    print("")
    
    # Durée du test
    duration = input("Durée du test en secondes (ENTER=30s): ").strip()
    try:
        duration = int(duration) if duration else 30
    except:
        duration = 30
    
    # Lancer le diagnostic (l'adresse est chargée automatiquement dans __init__)
    diagnostic = WebSocketDiagnostic()
    connected, messages = diagnostic.test_connection(duration)
    
    # Conclusion
    print("\n" + "=" * 60)
    if connected:
        print("🎉 RÉSULTAT: WebSocket fonctionne sur Replit !")
        if messages == 0:
            print("💡 Aucun message reçu - normal si aucune activité trading")
        print("✅ Votre observer devrait fonctionner correctement")
    else:
        print("❌ RÉSULTAT: Problème de connexion WebSocket")
        print("🔧 Solutions possibles:")
        print("   - Vérifier la connexion internet de Replit")
        print("   - Essayer plus tard (serveurs Hyperliquid occupés)")
        print("   - Utiliser un VPS au lieu de Replit")

if __name__ == "__main__":
    main() 