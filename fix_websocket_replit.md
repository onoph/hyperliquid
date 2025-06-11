# Fix WebSocket Issue on Replit

## Problème
```
"detail": "Failed to start observer: module 'websocket' has no attribute 'WebSocketApp'"
```

## Cause
Conflit entre les packages `websocket` et `websocket-client`. Replit a probablement installé le mauvais package.

## Solutions

### Solution 1: Désinstaller et réinstaller le bon package
```bash
pip uninstall websocket
pip uninstall websocket-client
pip install websocket-client==1.8.0
```

### Solution 2: Forcer l'installation (sur Replit)
```bash
pip install --force-reinstall --no-deps websocket-client==1.8.0
```

### Solution 3: Dans le shell Replit
```bash
# Vérifier les packages installés
pip list | grep websocket

# Désinstaller tous les packages websocket
pip uninstall websocket websocket-client -y

# Réinstaller le bon package
pip install websocket-client==1.8.0
```

### Solution 4: Modification du code (si les solutions précédentes ne marchent pas)

Dans `src/generic/observer.py`, remplacer :

```python
import websocket
```

Par :

```python
try:
    import websocket_client as websocket
except ImportError:
    import websocket
```

Ou plus explicitement :

```python
from websocket import WebSocketApp
# puis utiliser WebSocketApp directement au lieu de websocket.WebSocketApp
```

## Vérification
Après le fix, tester avec :

```python
import websocket
print(hasattr(websocket, 'WebSocketApp'))  # Doit retourner True
```

## Note importante
Le package correct est `websocket-client`, pas `websocket`. Le package `websocket` simple n'a pas la classe `WebSocketApp`. 