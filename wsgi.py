"""WSGI adapter for PythonAnywhere deployment."""

import os
import sys
from pathlib import Path

# Ajouter le répertoire du projet au PYTHONPATH
project_home = '/home/yourusername/hyperliquid'  # Remplacez par votre nom d'utilisateur
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Importer l'application FastAPI
from src.api.main import app

# Pour PythonAnywhere, nous devons utiliser une application WSGI
application = app 