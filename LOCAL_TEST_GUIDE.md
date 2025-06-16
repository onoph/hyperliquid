# Guide de Test Local (Simulation PythonAnywhere)

Ce guide vous permet de tester votre configuration PythonAnywhere en local avant le déploiement.

## 🧪 Tests Automatisés

### Test complet de l'environnement
```bash
python test_local_pythonanywhere.py
```

Ce script va tester :
- ✅ Variables d'environnement
- ✅ Dépendances Python
- ✅ Importation WSGI
- ✅ Simulation PythonAnywhere
- ✅ Endpoints API
- ✅ Serveur de test

## 🚀 Serveur de Test Simple

### Démarrage rapide
```bash
python local_test_server.py
```

### Ou via start_api.py (développement)
```bash
python start_api.py
```

## 📋 Pré-requis

### 1. Fichier .env
Créez `.env` à la racine :
```
API_USERNAME=admin
API_PASSWORD=your_secure_password
```

### 2. Dépendances
```bash
pip install -r requirements_prod.txt
```

## 🌐 URLs de Test

Une fois le serveur démarré :

- **API Base :** http://localhost:8000
- **Health Check :** http://localhost:8000/health
- **Documentation :** http://localhost:8000/docs
- **OpenAPI JSON :** http://localhost:8000/openapi.json

## 📋 Tests Manuels

### 1. Health Check (public)
```bash
curl http://localhost:8000/health
```

**Réponse attendue :**
```json
{
  "status": "healthy",
  "active_observers": 0
}
```

### 2. Liste des observateurs (authentifié)
```bash
curl -u admin:password http://localhost:8000/observers
```

**Réponse attendue :**
```json
[]
```

### 3. Niveau de log (authentifié)
```bash
curl -u admin:password http://localhost:8000/logs/level
```

**Réponse attendue :**
```json
{
  "success": true,
  "message": "Current log level is INFO",
  "current_level": "INFO"
}
```

### 4. Démarrer un observateur
```bash
curl -X POST http://localhost:8000/observers/start \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"address": "0x1234567890abcdef", "algo_type": "default"}'
```

### 5. Changer le niveau de log
```bash
curl -X POST http://localhost:8000/logs/level \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"level": "DEBUG"}'
```

## 🔧 Test de l'Importation WSGI

### Test manuel d'importation
```bash
python -c "
import sys, os
sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv()
from main_api import app
print('✅ Import WSGI réussi')
print(f'App type: {type(app)}')
"
```

### Test comme PythonAnywhere
```python
# Simulation du fichier WSGI PythonAnywhere
import os
import sys

# Ajouter le projet au path
path = '/path/to/your/project'
if path not in sys.path:
    sys.path.insert(0, path)

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Importer l'application
from main_api import app as application
```

## 🛠️ Dépannage

### Erreur de module non trouvé
```bash
# Vérifier le PYTHONPATH
python -c "import sys; print('\n'.join(sys.path))"

# Vérifier les dépendances
pip list | grep fastapi
```

### Erreur de variables d'environnement
```bash
# Vérifier le fichier .env
cat .env

# Tester le chargement
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('API_USERNAME:', os.getenv('API_USERNAME'))
print('API_PASSWORD:', os.getenv('API_PASSWORD'))
"
```

### Erreur de port occupé
```bash
# Changer le port dans local_test_server.py
# ou tuer le processus
lsof -ti:8000 | xargs kill -9
```

## ✅ Checklist de Validation

Avant le déploiement PythonAnywhere, vérifiez :

- [ ] `python test_local_pythonanywhere.py` passe tous les tests
- [ ] Health check répond correctement
- [ ] Authentification fonctionne
- [ ] Documentation accessible sur `/docs`
- [ ] Endpoints protégés refusent l'accès sans auth
- [ ] Logs s'affichent correctement
- [ ] Variables d'environnement chargées
- [ ] Aucune erreur d'importation

## 🚀 Après Validation Locale

Si tous les tests passent en local :

1. **Commitez** vos changements
2. **Pushez** sur votre repository
3. **Clonez** sur PythonAnywhere
4. **Exécutez** `python3.10 pythonanywhere_setup.py`
5. **Configurez** la Web App
6. **Testez** l'URL PythonAnywhere

Votre configuration locale réussie garantit un déploiement PythonAnywhere sans problème ! 🎉 