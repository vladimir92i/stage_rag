# RAG Bot — Les Bricos du Cœur

Assistant documentaire conversationnel pour l'association **Les Bricos du Cœur**.
Il répond aux questions en s'appuyant uniquement sur les documents internes de
l'association, sans jamais inventer : recherche des passages pertinents dans une
base vectorielle, puis génération de la réponse à partir de ces seuls passages
(RAG — *Retrieval Augmented Generation*).

Projet réalisé dans le cadre de l'épreuve **E2** du titre professionnel
« Développeur en Intelligence Artificielle » (RNCP 37827).

## Chaîne technique

| Étape | Outil |
|---|---|
| Découpage des documents | NLTK — `backend/scripts/add_file.py` |
| Vectorisation | **BAAI/bge-m3** (1024 dimensions) servi par une API FastAPI, port 8001 |
| Stockage et recherche | **Qdrant**, collection `bge-m3`, distance cosinus, port 6333 |
| Génération de la réponse | **Ollama**, modèle `qwen3:1.7b`, port 11434 |
| Interface | **Chainlit**, port 8000 |

Tout s'exécute en local. Aucune donnée ne sort de la machine, aucune clé d'API
n'est nécessaire.

## Prérequis

- **Python 3.12** — voir `.python-version`. Le projet ne s'installe pas en 3.14.
- **Docker**, pour exécuter Qdrant.
- **Ollama**, avec le modèle `qwen3:1.7b`.

## Démarrage rapide

```bash
py -V:3.12 -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
python -c "import nltk; nltk.download('punkt_tab')"
```

Puis, un terminal par service :

```bash
# 1. base vectorielle
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# 2. génération
ollama serve

# 3. API d'embedding
cd backend/app && fastapi dev --port 8001 api.py

# 4. ingestion des documents — une seule fois, depuis la racine
python backend/scripts/add_file.py

# 5. interface
cd backend && chainlit run app.py -w
```

L'interface est alors disponible sur <http://localhost:8000>.

## Conteneurisation

`backend/Dockerfile` empaquette l'API d'embedding (port 8001). Qdrant utilise
son image officielle, Ollama s'installe comme service système, et Chainlit se
lance directement : il n'y a pas de `docker-compose.yml`, l'orchestration est
manuelle. Détails en section 9 de la documentation.

## Documentation

**[`backend/README.md`](backend/README.md)** contient la documentation complète :
interconnexions entre services, gestion des accès, procédure d'installation
détaillée, procédure de test, dépendances, données utilisées et choix techniques.

## Structure du projet

```
.
├── README.md              ce fichier
├── pyproject.toml         dépendances (uv)
├── uv.lock                verrou de dépendances
├── .python-version        3.12
├── main.py                point d'entrée généré par uv, non utilisé
├── chainlit.md            écran d'accueil de l'interface
└── backend/
    ├── README.md          documentation complète
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py             interface Chainlit
    ├── app/api.py         API d'embedding (FastAPI)
    ├── services/          orchestration RAG, Qdrant, journalisation, configuration
    ├── models/            bancs d'essai des modèles d'embedding
    ├── scripts/           ingestion des documents, extraction PDF
    └── data/              documents sources
```

## Support

Pour toute question sur l'association : `chantier@bricosducoeur.org`
