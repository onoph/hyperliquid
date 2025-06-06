# Guide de déploiement sur PythonAnywhere

Ce guide vous explique comment déployer votre API Hyperliquid Observer sur PythonAnywhere.

## 📋 Prérequis

- Un compte PythonAnywhere (gratuit ou payant)
- Accès à la console bash sur PythonAnywhere

## 🚀 Étapes de déploiement

### 1. Upload du projet

#### Option A: Via Git (recommandé)
```bash
# Dans la console PythonAnywhere
cd ~
git clone https://github.com/votre-username/hyperliquid.git
cd hyperliquid
```

#### Option B: Upload manuel
- Utilisez l'interface web "Files" de PythonAnywhere
- Uploadez tous les fichiers du projet dans `/home/yourusername/hyperliquid/`

### 2. Installation des dépendances

```bash
# Dans la console PythonAnywhere
cd ~/hyperliquid

# Installer les dépendances de production
pip3.10 install --user -r requirements_prod.txt
```

### 3. Configuration des variables d'environnement

Créez le fichier `.env` :
```bash
cd ~/hyperliquid
nano .env
```

Contenu du fichier `.env` :
```
API_USERNAME=votre_username
API_PASSWORD=votre_mot_de_passe_securise
```

### 4. Configuration de l'application web

1. **Accédez à l'onglet "Web" de votre dashboard PythonAnywhere**

2. **Cliquez sur "Add a new web app"**

3. **Choisissez "Manual configuration"**

4. **Sélectionnez Python 3.10**

5. **Configuration WSGI :**
   - Source code: `/home/yourusername/hyperliquid`
   - WSGI configuration file: `/var/www/yourusername_pythonanywhere_com_wsgi.py`

6. **Éditez le fichier WSGI :**
```python
import os
import sys

# Ajouter le projet au path
path = '/home/yourusername/hyperliquid'
if path not in sys.path:
    sys.path.insert(0, path)

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv('/home/yourusername/hyperliquid/.env')

# Configuration du logging pour production
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importer l'application
from src.api.main import app as application
```

### 5. Configuration finale

```bash
# Exécuter le script de configuration
cd ~/hyperliquid
python3.10 deploy_config.py yourusername
```

### 6. Test et lancement

1. **Rechargez votre application web** depuis l'onglet "Web"

2. **Testez l'API :**
```bash
# Health check
curl https://yourusername.pythonanywhere.com/health

# Test avec authentification
curl -u votre_username:votre_password https://yourusername.pythonanywhere.com/observers
```

## 📂 Structure finale sur PythonAnywhere

```
/home/yourusername/hyperliquid/
├── src/
│   ├── api/
│   │   ├── main.py          # Application FastAPI
│   │   ├── models.py
│   │   ├── auth.py
│   │   └── service.py
│   └── generic/
│       ├── observer.py
│       ├── algo.py
│       └── ...
├── logs/                    # Logs de production
├── .env                     # Variables d'environnement
├── wsgi.py                  # Adapter WSGI
├── requirements_prod.txt    # Dépendances production
└── deploy_config.py         # Script de configuration
```

## 🔧 URLs disponibles

Une fois déployé, votre API sera accessible sur :

- **API Base :** `https://yourusername.pythonanywhere.com`
- **Health Check :** `https://yourusername.pythonanywhere.com/health`
- **Documentation :** `https://yourusername.pythonanywhere.com/docs`
- **Observers :** `https://yourusername.pythonanywhere.com/observers`

## 📋 Endpoints disponibles

### Publics (sans authentification)
- `GET /health` - Vérification de l'état

### Authentifiés (HTTP Basic Auth)
- `GET /observers` - Liste des observateurs
- `POST /observers/start` - Démarrer un observateur
- `POST /observers/{id}/stop` - Arrêter un observateur
- `GET /observers/{id}/status` - Statut d'un observateur
- `POST /observers/stop-all` - Arrêter tous les observateurs
- `GET /logs/level` - Niveau de log actuel
- `POST /logs/level` - Changer le niveau de log

## 🛠️ Dépannage

### Problème de modules non trouvés
```bash
# Vérifier l'installation des dépendances
pip3.10 show fastapi
pip3.10 list | grep fastapi
```

### Problème de permissions
```bash
# Donner les permissions sur les fichiers
chmod +x ~/hyperliquid/deploy_config.py
```

### Consulter les logs
- **Logs de l'application :** `/home/yourusername/hyperliquid/logs/app.log`
- **Logs d'erreur web :** Onglet "Web" → "Error log"
- **Logs d'accès :** Onglet "Web" → "Access log"

### Recharger l'application
Après toute modification :
1. Aller dans l'onglet "Web"
2. Cliquer sur "Reload yourusername.pythonanywhere.com"

## 🔒 Sécurité

1. **Variables d'environnement** : Ne jamais commiter le fichier `.env`
2. **Mots de passe forts** : Utilisez des mots de passe complexes
3. **HTTPS** : PythonAnywhere fournit HTTPS automatiquement
4. **Logs** : Surveillez les logs d'accès régulièrement

## 📊 Monitoring

### Health Check automatique
```bash
# Script pour vérifier la santé de l'API
curl -f https://yourusername.pythonanywhere.com/health || echo "API DOWN"
```

### Vérifier les observateurs actifs
```bash
curl -u username:password https://yourusername.pythonanywhere.com/observers | jq '.[] | .status'
```

## 🔄 Mise à jour

Pour mettre à jour l'application :

```bash
cd ~/hyperliquid
git pull  # Si vous utilisez Git
# Ou re-upload les fichiers modifiés

# Recharger l'application depuis l'onglet Web
```

## 💡 Conseils d'optimisation

1. **Compte payant** : Pour des performances optimales et plus de CPU
2. **Scheduled tasks** : Utilisez les tâches programmées pour la maintenance
3. **Always-on tasks** : Pour maintenir les WebSocket connections (compte payant requis)

Votre API Hyperliquid Observer est maintenant déployée et accessible sur Internet ! 🎉 