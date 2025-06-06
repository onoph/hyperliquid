#!/usr/bin/env python3
"""Setup script spécifique pour PythonAnywhere."""

import os
import sys
import subprocess
from pathlib import Path

def get_username():
    """Obtenir le nom d'utilisateur PythonAnywhere."""
    return os.environ.get('USER', 'yourusername')

def install_dependencies():
    """Installer les dépendances Python."""
    print("📦 Installation des dépendances...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--user", "-r", "requirements_prod.txt"
        ], check=True)
        print("✅ Dépendances installées avec succès")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation des dépendances: {e}")
        return False
    return True

def create_directories(username):
    """Créer les répertoires nécessaires."""
    print("📁 Création des répertoires...")
    
    directories = [
        f"/home/{username}/hyperliquid/logs",
        f"/home/{username}/hyperliquid/tmp"
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"✅ Répertoire créé: {directory}")
        except Exception as e:
            print(f"❌ Erreur création {directory}: {e}")
            return False
    return True

def setup_env_file(username):
    """Configurer le fichier .env."""
    env_file = Path(f"/home/{username}/hyperliquid/.env")
    
    if env_file.exists():
        print("✅ Fichier .env existe déjà")
        return True
    
    print("📝 Création du fichier .env...")
    
    api_username = input("Entrez l'API_USERNAME: ")
    api_password = input("Entrez l'API_PASSWORD: ")
    
    env_content = f"""# Configuration API Hyperliquid Observer
API_USERNAME={api_username}
API_PASSWORD={api_password}

# Optionnel: Niveau de log par défaut
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Fichier .env créé")
        return True
    except Exception as e:
        print(f"❌ Erreur création .env: {e}")
        return False

def update_wsgi_config(username):
    """Mettre à jour le fichier wsgi.py avec le bon nom d'utilisateur."""
    wsgi_file = Path(f"/home/{username}/hyperliquid/wsgi.py")
    
    if not wsgi_file.exists():
        print("❌ Fichier wsgi.py non trouvé")
        return False
    
    try:
        with open(wsgi_file, 'r') as f:
            content = f.read()
        
        # Remplacer yourusername par le vrai nom d'utilisateur
        content = content.replace('yourusername', username)
        
        with open(wsgi_file, 'w') as f:
            f.write(content)
        
        print("✅ Fichier wsgi.py mis à jour")
        return True
    except Exception as e:
        print(f"❌ Erreur mise à jour wsgi.py: {e}")
        return False

def generate_wsgi_template(username):
    """Générer un template WSGI pour PythonAnywhere."""
    print("📄 Génération du template WSGI...")
    
    wsgi_template = f"""# WSGI configuration file for PythonAnywhere
# Copiez ce contenu dans: /var/www/{username}_pythonanywhere_com_wsgi.py

import os
import sys

# Ajouter le projet au path
path = '/home/{username}/hyperliquid'
if path not in sys.path:
    sys.path.insert(0, path)

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv('/home/{username}/hyperliquid/.env')

# Configuration du logging pour production
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importer l'application
from src.api.main import app as application
"""
    
    template_file = Path(f"/home/{username}/hyperliquid/wsgi_template.py")
    
    try:
        with open(template_file, 'w') as f:
            f.write(wsgi_template)
        print(f"✅ Template WSGI créé: {template_file}")
        print(f"📋 Copiez le contenu dans: /var/www/{username}_pythonanywhere_com_wsgi.py")
        return True
    except Exception as e:
        print(f"❌ Erreur création template WSGI: {e}")
        return False

def test_api_import():
    """Tester que l'API peut être importée."""
    print("🧪 Test d'importation de l'API...")
    
    try:
        from src.api.main import app
        print("✅ API importée avec succès")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Script principal de setup."""
    print("🚀 Configuration PythonAnywhere pour Hyperliquid Observer API")
    print("=" * 60)
    
    username = get_username()
    print(f"👤 Utilisateur détecté: {username}")
    
    # Étapes de configuration
    steps = [
        ("Installation des dépendances", install_dependencies),
        ("Création des répertoires", lambda: create_directories(username)),
        ("Configuration .env", lambda: setup_env_file(username)),
        ("Mise à jour wsgi.py", lambda: update_wsgi_config(username)),
        ("Génération template WSGI", lambda: generate_wsgi_template(username)),
        ("Test importation API", test_api_import),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        if not step_func():
            print(f"❌ Échec: {step_name}")
            print("⚠️  Configuration incomplète")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 Configuration PythonAnywhere terminée avec succès!")
    print("\n📋 Prochaines étapes:")
    print("1. Aller dans l'onglet 'Web' de PythonAnywhere")
    print("2. Créer une nouvelle web app (Manual configuration, Python 3.10)")
    print(f"3. Source code: /home/{username}/hyperliquid")
    print(f"4. Copier le contenu de wsgi_template.py dans le fichier WSGI")
    print("5. Recharger l'application")
    print(f"6. Tester: https://{username}.pythonanywhere.com/health")
    
    return True

if __name__ == "__main__":
    main() 