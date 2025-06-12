#!/usr/bin/env python3
"""
Test WebSocket pour Replit - Diagnostic Hyperliquid Testnet
"""

import json
import time
import threading
import ssl
import certifi
import os
from datetime import datetime
from dotenv import load_dotenv

# Test des imports WebSocket
print("🔍 Test des imports WebSocket...")
try:
    import websocket
    print(f"✅ websocket importé: {websocket.__version__ if hasattr(websocket, '__version__') else 'version inconnue'}")
    
    if hasattr(websocket, 'WebSocketApp'):
        print("✅ WebSocketApp disponible")
    else:
        print("❌ WebSocketApp non disponible")
        
except ImportError as e:
    print(f"❌ Erreur import websocket: {e}")

print("\n" + "="*50)

class ReplitWebSocketTest:
    def __init__(self, wallet_address: str):
        self.url = "wss://api.hyperliquid-testnet.xyz/ws"
        self.wallet_address = wallet_address
        self.ws = None
        self.connected = False
        self.messages_received = 0
        self.subscription_sent = False
        self.start_time = None
        
    def log(self, message: str):
        """Log avec timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def test_connection(self, duration: int = 30):
        """Test la connexion WebSocket"""
        self.log(f"🚀 Test WebSocket Replit - Testnet Hyperliquid")
        self.log(f"URL: {self.url}")
        self.log(f"Wallet: {self.wallet_address}")
        self.log(f"Durée: {duration}s")
        self.log("")
        
        # Créer WebSocket
        try:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            self.log("✅ WebSocketApp créé")
        except Exception as e:
            self.log(f"❌ Erreur création WebSocket: {e}")
            return False
        
        # Lancer en thread
        self.start_time = time.time()
        wst = threading.Thread(target=self._run_websocket)
        wst.daemon = True
        wst.start()
        self.log("🔄 Thread WebSocket démarré")
        
        # Monitorer
        for i in range(duration):
            time.sleep(1)
            if i % 10 == 0:  # Status toutes les 10s
                self.log(f"⏱️  {i}s - Connecté: {self.connected} | Messages: {self.messages_received}")
                
        # Fermer
        if self.ws:
            self.ws.close()
            
        # Résultats
        self.log("")
        self.log("📊 RÉSULTATS:")
        self.log(f"   Connexion réussie: {'✅' if self.connected else '❌'}")
        self.log(f"   Souscription envoyée: {'✅' if self.subscription_sent else '❌'}")
        self.log(f"   Messages reçus: {self.messages_received}")
        
        if self.connected and self.subscription_sent:
            self.log("🎉 WebSocket fonctionne sur Replit !")
            if self.messages_received == 0:
                self.log("💡 Pas de messages = pas d'activité trading (normal)")
        else:
            self.log("❌ Problème de connexion WebSocket")
            
        return self.connected

    def _run_websocket(self):
        """Lance WebSocket"""
        try:
            self.log("🔌 Connexion WebSocket...")
            self.ws.run_forever(
                sslopt={
                    "cert_reqs": ssl.CERT_REQUIRED, 
                    "ca_certs": certifi.where()
                },
                ping_interval=20,
                ping_timeout=10
            )
        except Exception as e:
            self.log(f"❌ Erreur run_forever: {e}")

    def on_open(self, ws):
        """Connexion ouverte"""
        self.log("✅ WebSocket connecté !")
        self.connected = True
        
        # Envoyer souscription
        try:
            subscription = {
                "method": "subscribe",
                "subscription": {
                    "type": "orderUpdates",
                    "user": self.wallet_address
                }
            }
            ws.send(json.dumps(subscription))
            self.subscription_sent = True
            self.log(f"📡 Souscription envoyée pour: {self.wallet_address[:10]}...")
        except Exception as e:
            self.log(f"❌ Erreur souscription: {e}")

    def on_message(self, ws, message):
        """Message reçu"""
        self.messages_received += 1
        try:
            data = json.loads(message)
            channel = data.get("channel", "unknown")
            self.log(f"📨 Message #{self.messages_received}: {channel}")
            
            if channel == "orderUpdates":
                orders = data.get("data", [])
                self.log(f"   📋 {len(orders)} ordre(s) mis à jour")
                for order in orders:
                    status = order.get("status", "?")
                    self.log(f"   → Status: {status}")
                    
        except Exception as e:
            self.log(f"📨 Message #{self.messages_received}: {str(message)[:100]}...")

    def on_error(self, ws, error):
        """Erreur"""
        self.log(f"❌ Erreur: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Fermé"""
        self.log(f"🔌 Fermé: {close_status_code} - {close_msg}")
        self.connected = False


def main():
    """Test principal"""
    print("🧪 DIAGNOSTIC WEBSOCKET REPLIT + HYPERLIQUID TESTNET")
    print("="*60)
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Vérifier si .env existe
    if not os.path.exists('.env'):
        print("⚠️  Fichier .env non trouvé. Créez un fichier .env avec:")
        print("   WALLET_ADDRESS=votre_adresse_wallet_testnet")
        print("")
    
    # Récupérer l'adresse wallet depuis .env
    wallet = os.getenv("WALLET_ADDRESS")
    if wallet:
        print(f"📋 Adresse chargée depuis .env: {wallet[:10]}...")
        # Validation basique de l'adresse Ethereum
        if not wallet.startswith('0x') or len(wallet) != 42:
            print(f"⚠️  Format d'adresse suspect: {wallet}")
            print("   Une adresse Ethereum devrait commencer par 0x et faire 42 caractères")
    else:
        # Fallback: demander l'adresse si pas dans .env
        print("❓ WALLET_ADDRESS non trouvée dans .env")
        wallet = input("Entrez votre adresse wallet testnet (ou ENTER pour test): ").strip()
        if not wallet:
            wallet = "0x0000000000000000000000000000000000000000"
            print(f"💡 Utilisation adresse test: {wallet}")
        else:
            print(f"💡 Suggestion: Ajoutez 'WALLET_ADDRESS={wallet}' dans votre .env")
    
    # Durée du test
    duration_str = input("Durée du test en secondes (ENTER=30): ").strip()
    duration = int(duration_str) if duration_str.isdigit() else 30
    
    print("\n" + "="*60)
    
    # Lancer le test
    tester = ReplitWebSocketTest(wallet)
    success = tester.test_connection(duration)
    
    print("\n" + "="*60)
    if success:
        print("✅ DIAGNOSTIC: WebSocket fonctionne sur Replit !")
        print("💡 Si pas de messages d'ordres, c'est normal sans activité trading")
    else:
        print("❌ DIAGNOSTIC: Problème WebSocket sur Replit")
        print("\n🔧 SOLUTIONS À ESSAYER:")
        print("1. Vérifier le package websocket:")
        print("   pip uninstall websocket websocket-client -y")
        print("   pip install websocket-client==1.8.0")
        print("")
        print("2. Redémarrer le Repl")
        print("")
        print("3. Vérifier les logs de l'observer pour plus de détails")


if __name__ == "__main__":
    main() 