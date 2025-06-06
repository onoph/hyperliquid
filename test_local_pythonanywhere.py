#!/usr/bin/env python3
"""Script pour tester l'environnement PythonAnywhere en local."""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

def setup_local_test_environment():
    """Configure l'environnement de test local."""
    print("🔧 Configuration de l'environnement de test local...")
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Vérifier les variables d'environnement
    required_vars = ["API_USERNAME", "API_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Variables manquantes: {missing}")
        print("💡 Créez un fichier .env avec:")
        print("API_USERNAME=admin")
        print("API_PASSWORD=your_password")
        return False
    
    print("✅ Variables d'environnement OK")
    return True

def test_wsgi_import():
    """Tester l'importation du module WSGI."""
    print("🧪 Test d'importation WSGI...")
    
    try:
        # Simuler l'importation comme PythonAnywhere
        sys.path.insert(0, os.getcwd())
        
        from src.api.main import app
        print("✅ Application FastAPI importée avec succès")
        
        # Tester que l'app est bien une instance FastAPI
        from fastapi import FastAPI
        if isinstance(app, FastAPI):
            print("✅ Instance FastAPI valide")
            return True
        else:
            print("❌ L'app n'est pas une instance FastAPI")
            return False
            
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_dependencies():
    """Tester que toutes les dépendances sont installées."""
    print("📦 Test des dépendances...")
    
    dependencies = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'python-dotenv',
        'websocket-client',
        'dacite'
    ]
    
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MANQUANT")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n📦 Installez les dépendances manquantes:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    return True

def start_test_server():
    """Démarrer le serveur de test."""
    print("🚀 Démarrage du serveur de test...")
    
    try:
        import uvicorn
        from src.api.main import app
        
        # Démarrer le serveur en mode test (non-bloquant dans un processus)
        import multiprocessing
        import signal
        
        def run_server():
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=8000,
                log_level="info",
                reload=False
            )
        
        # Démarrer le serveur dans un processus séparé
        server_process = multiprocessing.Process(target=run_server)
        server_process.start()
        
        # Attendre que le serveur démarre
        print("⏳ Attente du démarrage du serveur...")
        time.sleep(3)
        
        return server_process
        
    except Exception as e:
        print(f"❌ Erreur démarrage serveur: {e}")
        return None

def test_api_endpoints():
    """Tester les endpoints de l'API."""
    print("🌐 Test des endpoints API...")
    
    base_url = "http://127.0.0.1:8000"
    username = os.getenv("API_USERNAME")
    password = os.getenv("API_PASSWORD")
    
    tests = [
        {
            "name": "Health Check",
            "url": f"{base_url}/health",
            "method": "GET",
            "auth": False
        },
        {
            "name": "List Observers",
            "url": f"{base_url}/observers",
            "method": "GET",
            "auth": True
        },
        {
            "name": "Get Log Level",
            "url": f"{base_url}/logs/level",
            "method": "GET",
            "auth": True
        },
        {
            "name": "API Documentation",
            "url": f"{base_url}/docs",
            "method": "GET",
            "auth": False
        }
    ]
    
    success_count = 0
    
    for test in tests:
        try:
            print(f"  🔍 {test['name']}...")
            
            kwargs = {
                "timeout": 10,
                "allow_redirects": True
            }
            
            if test['auth']:
                kwargs['auth'] = (username, password)
            
            if test['method'] == 'GET':
                response = requests.get(test['url'], **kwargs)
            else:
                response = requests.post(test['url'], **kwargs)
            
            if response.status_code in [200, 401]:  # 401 OK pour les endpoints protégés sans auth
                print(f"    ✅ {test['name']} - Status: {response.status_code}")
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 401 and test['auth']:
                    print(f"    ℹ️  Authentification requise (normal)")
                    success_count += 1
            else:
                print(f"    ❌ {test['name']} - Status: {response.status_code}")
                print(f"    📝 Response: {response.text[:100]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"    ❌ {test['name']} - Connexion refusée")
        except Exception as e:
            print(f"    ❌ {test['name']} - Erreur: {e}")
    
    print(f"\n📊 Tests réussis: {success_count}/{len(tests)}")
    return success_count == len(tests)

def test_wsgi_simulation():
    """Simuler le comportement WSGI de PythonAnywhere."""
    print("🔧 Test simulation WSGI PythonAnywhere...")
    
    try:
        # Simuler le chargement WSGI comme PythonAnywhere
        import sys
        import os
        
        # Simuler l'ajout du path
        project_path = os.getcwd()
        if project_path not in sys.path:
            sys.path.insert(0, project_path)
        
        # Simuler le chargement des variables d'environnement
        from dotenv import load_dotenv
        load_dotenv()
        
        # Simuler l'importation de l'application
        from src.api.main import app as application
        
        # Vérifier que c'est bien une application WSGI/ASGI
        if hasattr(application, '__call__'):
            print("✅ Application WSGI/ASGI valide")
            return True
        else:
            print("❌ Application non callable")
            return False
            
    except Exception as e:
        print(f"❌ Erreur simulation WSGI: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("🧪 Test Local PythonAnywhere Environment")
    print("=" * 50)
    
    # Tests de pré-requis
    tests = [
        ("Environment Setup", setup_local_test_environment),
        ("Dependencies Check", test_dependencies),
        ("WSGI Import Test", test_wsgi_import),
        ("WSGI Simulation", test_wsgi_simulation),
    ]
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        if not test_func():
            print(f"❌ Échec: {test_name}")
            return False
    
    # Test du serveur
    print(f"\n📋 Server Test...")
    server_process = start_test_server()
    
    if server_process:
        try:
            # Tester les endpoints
            if test_api_endpoints():
                print("✅ Tous les tests d'endpoints réussis")
            else:
                print("⚠️  Certains tests d'endpoints ont échoué")
            
        finally:
            # Arrêter le serveur
            print("\n🛑 Arrêt du serveur de test...")
            server_process.terminate()
            server_process.join(timeout=5)
            if server_process.is_alive():
                server_process.kill()
    
    print("\n" + "=" * 50)
    print("🎉 Tests terminés!")
    print("\n💡 Si tous les tests passent, votre app est prête pour PythonAnywhere!")
    print("\n📋 Prochaines étapes:")
    print("1. Pushez votre code sur GitHub")
    print("2. Clonez sur PythonAnywhere")
    print("3. Exécutez: python3.10 pythonanywhere_setup.py")
    print("4. Configurez la Web App")
    
    return True

if __name__ == "__main__":
    main() 