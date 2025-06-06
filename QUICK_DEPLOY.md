# Déploiement Rapide sur PythonAnywhere

## 🚀 Déploiement en 5 minutes

### 1. Upload du projet
```bash
# Dans la console PythonAnywhere
cd ~
git clone https://votre-repo/hyperliquid.git
cd hyperliquid
```

### 2. Configuration automatique
```bash
python3.10 pythonanywhere_setup.py
```
Ce script va :
- ✅ Installer les dépendances
- ✅ Créer les répertoires nécessaires
- ✅ Configurer les variables d'environnement
- ✅ Générer le fichier WSGI
- ✅ Tester l'importation de l'API

### 3. Configuration Web App

1. **Onglet "Web"** → **"Add a new web app"**
2. **Manual configuration** → **Python 3.10**
3. **Source code:** `/home/yourusername/hyperliquid`
4. **WSGI file:** Copier le contenu de `wsgi_template.py`

### 4. Test
```bash
curl https://yourusername.pythonanywhere.com/health
```

## 🔧 URLs de votre API

- **API:** `https://yourusername.pythonanywhere.com`
- **Documentation:** `https://yourusername.pythonanywhere.com/docs`
- **Health Check:** `https://yourusername.pythonanywhere.com/health`

## 📋 Endpoints principaux

### Authentifiés (username:password)
```bash
# Lister les observateurs
curl -u admin:password https://yourusername.pythonanywhere.com/observers

# Démarrer un observateur
curl -X POST https://yourusername.pythonanywhere.com/observers/start \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"address": "0x1234567890abcdef"}'

# Changer le niveau de log
curl -X POST https://yourusername.pythonanywhere.com/logs/level \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"level": "DEBUG"}'
```

## 🛠️ Dépannage Express

### Problème d'importation
```bash
cd ~/hyperliquid
python3.10 -c "from src.api.main import app; print('✅ OK')"
```

### Vérifier les dépendances
```bash
pip3.10 list | grep fastapi
```

### Consulter les logs
- **Application:** `/home/yourusername/hyperliquid/logs/app.log`
- **Web errors:** Onglet "Web" → "Error log"

### Recharger après modification
1. Onglet "Web" → "Reload yourusername.pythonanywhere.com"

## 🔄 Mise à jour rapide

```bash
cd ~/hyperliquid
git pull
# Recharger depuis l'onglet Web
```

Votre API est maintenant déployée et accessible ! 🎉 