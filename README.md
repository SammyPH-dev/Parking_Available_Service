# Parking Available Service

API Flask permettant d’évaluer les règles de stationnement associées aux panneaux et poteaux de Montréal.

L’API utilise la position géographique de l’utilisateur et l’heure locale de Montréal pour trouver les poteaux à proximité et déterminer si leurs règles de stationnement sont actives.

## Limite importante

L’API évalue la légalité du stationnement selon les panneaux disponibles.

Elle ne détermine pas si une place physique est actuellement occupée.

## Architecture

```text
API Flask
    ↓
Services
    ↓
DAO
    ↓
SQLAlchemy
    ↓
SQLite
```

La logique géographique et temporelle se trouve dans le domaine et ne dépend pas de Flask ou de la base de données.

## Installation

Créer et activer un environnement virtuel :

```bash
python -m venv .venv
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Données

Placer le fichier GeoJSON des panneaux dans :

```text
data/raw/parking_signs.geojson
```

Importer un petit échantillon :

```bash
python scripts/import_parking_signs.py --limite 500
```

Importer le fichier complet :

```bash
python scripts/import_parking_signs.py --tout
```

La base SQLite est créée dans :

```text
data/parking.db
```

## Démarrage

```bash
python main.py
```

URL locale de base :

```text
http://127.0.0.1:5000/api/v1
```

## Endpoint principal pour Android

```http
GET /api/v1/poteaux/proches
```

### Paramètres

| Paramètre | Obligatoire | Valeur par défaut | Description |
|---|---:|---:|---|
| `latitude` | Oui | — | Latitude de l’utilisateur, entre -90 et 90 |
| `longitude` | Oui | — | Longitude de l’utilisateur, entre -180 et 180 |
| `date_heure` | Non | Heure actuelle de Montréal | Date ISO 8601 à évaluer |
| `rayon` | Non | `300` | Rayon de recherche en mètres, maximum 5 000 |
| `limite` | Non | `20` | Nombre maximal de poteaux, entre 1 et 100 |

### Exemple

```http
GET /api/v1/poteaux/proches?latitude=45.589862&longitude=-73.541538&rayon=100&limite=10
```

Une date peut être fournie explicitement :

```http
GET /api/v1/poteaux/proches?latitude=45.589862&longitude=-73.541538&date_heure=2026-10-07T14:00:00
```

Une date UTC se terminant par `Z` est convertie vers le fuseau `America/Toronto`.

### Réponse simplifiée

```json
{
  "centre": {
    "latitude": 45.589862,
    "longitude": -73.541538
  },
  "date_heure": "2026-10-07T14:00:00-04:00",
  "rayon_metres": 100,
  "nombre": 1,
  "poteaux": [
    {
      "poteau_id": 1679,
      "latitude": 45.589862,
      "longitude": -73.541538,
      "distance_metres": 0.0,
      "nombre_panneaux": 3,
      "statut_global": {
        "code": "STATIONNEMENT_INTERDIT",
        "stationnement_autorise_selon_ce_poteau": false,
        "message": "Au moins un panneau actif interdit le stationnement."
      },
      "evaluations": []
    }
  ]
}
```

Le tableau `evaluations` contient les interprétations détaillées des panneaux appartenant au poteau.

## Codes de statut

### Statuts d’un poteau

| Code | Signification |
|---|---|
| `ARRET_INTERDIT` | Au moins un panneau actif interdit l’arrêt |
| `STATIONNEMENT_INTERDIT` | Au moins un panneau actif interdit le stationnement |
| `AUTORISE_AVEC_CONDITIONS` | Le stationnement semble autorisé avec certaines conditions |
| `AUCUNE_REGLE_ACTIVE` | Aucune règle active n’a été détectée |
| `INDETERMINE` | Au moins une règle importante ne peut pas être interprétée |

### Statuts d’un panneau

| Code | Signification |
|---|---|
| `ARRET_INTERDIT` | L’arrêt et le stationnement sont interdits |
| `STATIONNEMENT_INTERDIT` | Le stationnement est interdit |
| `STATIONNEMENT_PAYANT` | Le stationnement est autorisé avec paiement |
| `STATIONNEMENT_LIMITE` | Le stationnement est autorisé avec une limite |
| `REGLE_INACTIVE` | La règle n’est pas active à l’heure demandée |
| `INDETERMINE` | Le service ne peut pas conclure |

L’application cliente ne doit jamais interpréter `INDETERMINE` ou une autorisation `null` comme une permission de stationner.

## Autres endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/sante` | Vérifie que l’API fonctionne |
| GET | `/api/v1/panneaux` | Liste les panneaux |
| GET | `/api/v1/panneaux/{id}` | Obtient un panneau |
| GET | `/api/v1/panneaux/proches` | Trouve les panneaux proches |
| GET | `/api/v1/panneaux/{id}/interpretation` | Interprète un panneau |
| GET | `/api/v1/panneaux/{id}/evaluation` | Évalue un panneau à une date donnée |
| GET | `/api/v1/poteaux/{id}/evaluation` | Évalue tous les panneaux d’un poteau |
| GET | `/api/v1/poteaux/proches` | Trouve et évalue les poteaux proches |

## Format des erreurs

```json
{
  "erreur": {
    "code": "COORDONNEES_MANQUANTES",
    "message": "Les paramètres latitude et longitude sont obligatoires."
  }
}
```

Codes HTTP courants :

| Code HTTP | Signification |
|---:|---|
| `200` | Requête réussie |
| `400` | Paramètre obligatoire manquant |
| `404` | Panneau ou poteau introuvable |
| `422` | Paramètre présent, mais invalide |

## Tests

Exécuter tous les tests :

```bash
pytest
```

Exécuter uniquement les tests unitaires :

```bash
pytest tests/unit
```

## Connexion Android en développement

Depuis l’émulateur Android, utiliser :

```text
http://10.0.2.2:5000/api/v1/
```

`10.0.2.2` redirige vers l’ordinateur qui exécute l’émulateur.

Depuis un téléphone physique sur le même réseau, utiliser l’adresse IP locale de l’ordinateur et démarrer Flask afin qu’il accepte les connexions réseau.

L’utilisation de HTTP non chiffré doit être limitée à la configuration Android de développement. Une API déployée doit utiliser HTTPS.

## Limitations actuelles

- Certaines expressions de panneaux ne sont pas encore interprétées.
- Les exceptions telles que `EXCEPTE`, `AUX AUTOBUS` et `JOURS D’ECOLE` peuvent produire `INDETERMINE`.
- Les flèches et directions d’application des panneaux ne sont pas encore évaluées.
- Plusieurs panneaux peuvent s’appliquer à une même zone.
- L’API ne fournit aucune donnée d’occupation physique en temps réel.