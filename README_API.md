# Hyperliquid Observer API

API REST pour gérer les observateurs WebSocket Hyperliquid.

## Configuration

1. **Installez les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurez les variables d'environnement** :
   ```bash
   cp env.example .env
   # Éditez .env avec vos credentials
   ```

3. **Variables d'environnement requises** :
   - `API_USERNAME` : Nom d'utilisateur pour l'authentification
   - `API_PASSWORD` : Mot de passe pour l'authentification

## Démarrage

```bash
python start_api.py
```

L'API sera disponible sur `http://localhost:8000`

## Documentation

- **Documentation interactive** : http://localhost:8000/docs
- **Health check** : http://localhost:8000/health

## Endpoints

### Authentication
Tous les endpoints (sauf `/health`) nécessitent une authentification HTTP Basic avec les credentials configurés.

### Endpoints disponibles

#### `GET /health`
Vérification de l'état de l'API
- Pas d'authentification requise
- Retourne le statut et le nombre d'observateurs actifs

#### `POST /observers/start`
Démarre un nouvel observateur
```json
{
  "address": "0x1234...",
  "algo_type": "default"
}
```

#### `GET /observers`
Liste tous les observateurs

#### `GET /observers/{observer_id}/status`
Statut d'un observateur spécifique

#### `POST /observers/{observer_id}/stop`
Arrête un observateur spécifique

#### `POST /observers/stop-all`
Arrête tous les observateurs

## Exemples d'utilisation

### Curl

```bash
# Health check
curl http://localhost:8000/health

# Démarrer un observateur
curl -X POST http://localhost:8000/observers/start \
  -u admin:your_password \
  -H "Content-Type: application/json" \
  -d '{"address": "0x1234567890abcdef", "algo_type": "default"}'

# Lister les observateurs
curl -u admin:your_password http://localhost:8000/observers

# Arrêter un observateur
curl -X POST http://localhost:8000/observers/{observer_id}/stop \
  -u admin:your_password
```

### Python

```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('admin', 'your_password')
base_url = 'http://localhost:8000'

# Démarrer un observateur
response = requests.post(
    f'{base_url}/observers/start',
    json={'address': '0x1234567890abcdef', 'algo_type': 'default'},
    auth=auth
)

if response.status_code == 200:
    observer_id = response.json()['observer_id']
    print(f'Observer démarré: {observer_id}')

# Lister les observateurs
response = requests.get(f'{base_url}/observers', auth=auth)
observers = response.json()
print(f'Observateurs actifs: {len(observers)}')
```

## Sécurité

- Utilisez des mots de passe forts
- Considérez l'usage de HTTPS en production
- Les logs contiennent les adresses observées
- Limitez l'accès réseau si nécessaire

## Logs

Les logs sont affichés dans la console et incluent :
- Démarrage/arrêt des observateurs
- Erreurs de connexion WebSocket
- Actions des utilisateurs authentifiés

## Architecture

```
src/api/
├── __init__.py
├── main.py        # Application FastAPI principale
├── models.py      # Modèles Pydantic
├── auth.py        # Authentification HTTP Basic
└── service.py     # Service de gestion des observateurs
```

L'API utilise :
- **FastAPI** pour l'API REST
- **Pydantic** pour la validation des données
- **Threading** pour les observateurs WebSocket
- **HTTP Basic Auth** pour l'authentification 