# RAG Bot — assistant documentaire des Bricos du Cœur

Assistant conversationnel qui répond aux questions sur l'association
**Les Bricos du Cœur** en s'appuyant uniquement sur ses documents internes
(RAG — _Retrieval Augmented Generation_).

Tout tourne en local : aucune donnée ne sort de la machine, aucun service
externe payant n'est appelé.

---

## 1. Interconnexions entre services

Quatre services indépendants, chacun sur son port :

```
   Navigateur
       │
       ▼
┌──────────────────┐
│    Chainlit      │  interface de conversation
│  backend/app.py  │  port 8000
└────────┬─────────┘
         │  appel Python direct (services/llm.py)
         ▼
┌────────────────────────────────────────────────────────┐
│              services/llm.py — orchestration           │
└───┬──────────────────┬──────────────────┬──────────────┘
    │ HTTP             │ HTTP             │ HTTP
    ▼                  ▼                  ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
│ API embed.  │  │    Qdrant    │  │      Ollama      │
│  FastAPI    │  │ base vect.   │  │   qwen3:1.7b     │
│  port 8001  │  │  port 6333   │  │   port 11434     │
│  BGE-M3     │  │ coll. bge-m3 │  │                  │
└─────────────┘  └──────────────┘  └──────────────────┘
```

Le parcours d'une question :

1. **Chainlit** (`backend/app.py`) reçoit le message et appelle `generate_response()`.
2. **`services/llm.py`** envoie la question à l'**API d'embedding** (`POST /embed/bge`),
   qui la transforme en vecteur de 1024 dimensions avec BGE-M3.
3. Ce vecteur sert à interroger **Qdrant**, qui renvoie les 3 chunks les plus
   proches par distance cosinus.
4. Ces chunks sont injectés dans un prompt contraint, envoyé à **Ollama**
   (`qwen3:1.7b`), dont la réponse remonte jusqu'à Chainlit.
5. Chaque vectorisation et chaque recherche sont journalisées
   (`services/log.py` → `backend/logs/vectorisation_AAAA-MM-JJ.log`).

L'ingestion (`scripts/add_file.py`) est un processus séparé, lancé une fois :
elle découpe les documents, appelle la même API d'embedding, et écrit les points
dans Qdrant.

---

## 2. Gestion des accès

**Le projet ne comporte aucun mécanisme d'authentification, et c'est un choix
assumé lié à son contexte de déploiement.**

| Service         | Écoute sur        | Authentification | Justification                    |
| --------------- | ----------------- | ---------------- | -------------------------------- |
| Chainlit        | `localhost:8000`  | aucune           | usage interne, poste unique      |
| API d'embedding | `127.0.0.1:8001`  | aucune           | appelée uniquement en local      |
| Qdrant          | `localhost:6333`  | aucune clé d'API | conteneur local, port non exposé |
| Ollama          | `localhost:11434` | aucune           | service local                    |

- **Aucun secret dans le dépôt** : pas de clé d'API, pas de jeton, pas de mot de
  passe, pas de fichier `.env`. Il n'y a rien à protéger parce qu'aucun service
  distant n'est appelé.
- **Tous les services écoutent sur la boucle locale.** Ils ne sont pas joignables
  depuis le réseau. C'est ce qui rend l'absence d'authentification acceptable.
- **Si le service devait être exposé**, il faudrait au minimum : une clé d'API
  Qdrant (`QDRANT__SERVICE__API_KEY`), une authentification Chainlit
  (`@cl.password_auth_callback`), et un reverse proxy en HTTPS devant l'API
  d'embedding. Rien de tout cela n'est en place aujourd'hui.
- **Les données traitées ne sont pas personnelles** : documents institutionnels
  publics de l'association (plaquette, convention type, page de présentation).
  Aucune donnée d'adhérent ou de bénéficiaire n'est indexée.

---

## 3. Dépendances

**Python 3.12 **

Onze dépendances directes, listées à l'identique dans `backend/requirements.txt`
et `pyproject.toml` :

| Paquet                  | Rôle                             | Utilisé par                             |
| ----------------------- | -------------------------------- | --------------------------------------- |
| `fastapi[standard]`     | API d'embedding                  | `app/api.py`                            |
| `pydantic`              | validation du corps des requêtes | `app/api.py`                            |
| `FlagEmbedding`         | modèle BGE-M3                    | `app/api.py`, `models/bge.py`           |
| `sentence-transformers` | modèle multilingual-e5           | `app/api.py`, `models/e5.py`            |
| `qdrant-client`         | base vectorielle                 | `services/qdrant.py`, `services/llm.py` |
| `httpx`                 | appels HTTP entre services       | `services/`, `scripts/`                 |
| `numpy`                 | manipulation de vecteurs         | `services/qdrant.py`                    |
| `nltk`                  | découpage en phrases             | `scripts/add_file.py`                   |
| `ollama`                | génération de la réponse         | `services/llm.py`                       |
| `chainlit`              | interface conversationnelle      | `app.py`                                |
| `pymupdf`               | extraction du texte des PDF      | `scripts/ocr.py`                        |

`uv.lock` verrouille les 213 paquets de l'arbre complet (dont `torch`, tiré par
`sentence-transformers`).

Services externes non-Python : **Docker** (pour Qdrant) et **Ollama**.

---

## 4. Procédure d'installation

### 4.1 Environnement Python

```bash
py -V:3.12 -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

pip install -r backend/requirements.txt
```

Environ 190 paquets, dont `torch` — comptez plusieurs Go et quelques minutes.

Avec `uv`, l'équivalent est `uv sync` à la racine.

### 4.2 Corpus NLTK

`sentence_chunk` utilise le segmenteur de phrases de NLTK, dont les données ne
sont pas incluses dans le paquet :

```bash
python -c "import nltk; nltk.download('punkt_tab')"
```

Sans cette étape, l'ingestion échoue sur `LookupError`.

### 4.3 Qdrant

```bash
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

Tableau de bord : <http://localhost:6333/dashboard>

### 4.4 Ollama

```bash
ollama serve
ollama pull qwen3:1.7b
```

`ollama list` indique la taille réellement téléchargée.

---

## 5. Lancement

Trois terminaux, dans cet ordre.

**1 — API d'embedding**

```bash
cd backend/app
fastapi dev --port 8001 api.py
```

Le premier démarrage télécharge BGE-M3 depuis Hugging Face (plusieurs Go) et
prend plusieurs minutes. Les suivants lisent le cache local.

**2 — Ingestion des documents** (une seule fois, ou après modification des données)

Depuis la racine du dépôt, sans variable d'environnement particulière :

```bash
python backend/scripts/add_file.py
```

Le script fonctionne depuis n'importe quel répertoire courant : il calcule
lui-même l'emplacement de `backend/` et de `data/` à partir de `__file__`.

Sortie attendue :

```
12 points ajoutés dans Qdrant
30 points ajoutés dans Qdrant
13 points ajoutés dans Qdrant
```

**3 — Interface**

```bash
cd backend
chainlit run app.py -w
```

Puis <http://localhost:8000>.

---

## 5 bis. Configuration

Adresses, noms et dimensions sont définis en un seul endroit,
`services/config.py`, et surchargeables par variable d'environnement :

| Variable | Défaut | Rôle |
|---|---|---|
| `API_EMBEDDING_HOST` | `127.0.0.1` | hôte de l'API d'embedding |
| `API_EMBEDDING_PORT` | `8001` | port de l'API d'embedding |
| `QDRANT_URL` | `http://localhost:6333` | adresse de Qdrant |
| `QDRANT_COLLECTION` | `bge-m3` | collection interrogée |
| `VECTOR_SIZE` | `1024` | dimension des vecteurs |
| `OLLAMA_MODEL` | `qwen3:1.7b` | modèle de génération |

Exemple, pour pointer vers un Qdrant conteneurisé :

```bash
QDRANT_URL=http://qdrant:6333 python backend/scripts/add_file.py
```

---

## 6. Procédure de test

Le projet ne comporte pas de suite de tests automatisés. La vérification est
manuelle, service par service.

**Test 1 — l'API d'embedding répond et produit la bonne dimension**

```bash
curl -X POST http://127.0.0.1:8001/embed/bge \
     -H "Content-Type: application/json" \
     -d "{\"text\": \"test\"}"
```

Attendu : un JSON `{"vector": [...]}` de **1024** valeurs.
Le second endpoint `POST /embed/e5` répond sur le même principe (1024 également),
il sert au banc d'essai des modèles.

**Test 2 — la collection Qdrant existe et est peuplée**

```bash
curl http://localhost:6333/collections/bge-m3
```

Attendu : `"status": "green"`, `"points_count": 55`, `"size": 1024`,
`"distance": "Cosine"`.

**Test 3 — la recherche de voisins remonte des chunks pertinents**

```bash
python backend/main.py
```

Affiche les 3 voisins les plus proches avec leur titre, leur texte et leur
score. L'option `-c` permet de viser une autre collection.

**Test 4 — chaîne complète**

Dans Chainlit, poser une des trois questions de démarrage, par exemple
_« Quelle sont les valeurs de votre association »_. La réponse doit citer
l'entraide, le partage, la proximité et l'authenticité — contenu de la section
`## NOS VALEURS` de la plaquette.

**Test 5 — la journalisation fonctionne**

Après une question, `backend/logs/vectorisation_AAAA-MM-JJ.log` doit contenir
une ligne `vectorisation` et une ligne `recherche` suivie de ses 3 voisins.

---

## 7. Données utilisées

Trois documents sont indexés dans la collection `bge-m3`, pour un total de
**55 chunks** :

| Fichier                               | Nature                                                            | Découpage                         | chunks |
| ------------------------------------- | ----------------------------------------------------------------- | --------------------------------- | ------ |
| `data/page_de_base.json`              | contenu du site `bricosducoeur.org`, 7 paragraphes titrés         | `sentence_chunk`, `max_words=50`  | 12     |
| `data/convention_achat.txt`           | convention d'achat partenaire, 13 sections (titres en majuscules) | `sentence_chunk`, `max_words=100` | 30     |
| `data/plaquette_institutionnelle.txt` | plaquette de présentation, 13 sections (titres `##`)              | aucun — une section = un chunk    | 13     |

Chaque point Qdrant porte un payload : `texte`, `titre`, `source`, `chunk_size`.

**Découpage.** `sentence_chunk` remplace les points-virgules et les tirets par des
points, segmente en phrases avec NLTK, puis regroupe les phrases tant que le
cumul reste sous `max_words`. Elle ne coupe jamais à l'intérieur d'une phrase :
une phrase plus longue que `max_words` donne donc un chunk hors seuil.

Le remplacement du tiret vise les énumérations `; -` de la convention. Effet
mesuré sur `convention_achat.txt` à `max_words=50` : les chunks dépassant le
seuil passent de 6 à 2. Effet de bord accepté : les mots composés sont coupés
dans le texte stocké (`ci-dessus` devient `ci.dessus`).

**Fichiers de travail** conservés dans `data/` — ils ne sont pas indexés et
documentent la démarche : `24-04.txt`, `idée.txt`, `question type.txt`, ainsi que
les versions `.pdf` et `.docx` de la plaquette dont le `.txt` a été extrait.

---

## 8. Arborescence réelle

```
.
├── README.md                  documentation racine
├── pyproject.toml             dépendances (uv)
├── uv.lock                    verrou, 190 paquets
├── .python-version            3.12
├── main.py                    point d'entrée généré par uv, non utilisé
├── chainlit.md                écran d'accueil Chainlit
└── backend/
    ├── README.md              ce fichier
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py                 interface Chainlit
    ├── main.py                script de test des voisins (ligne de commande)
    ├── test.py                script d'essai du découpage (pas un test unitaire)
    ├── app/
    │   └── api.py             API FastAPI : /embed/bge et /embed/e5
    ├── services/
    │   ├── llm.py             orchestration RAG + appel Ollama
    │   ├── qdrant.py          création de collection, insertion, recherche
    │   ├── log.py             journalisation des vectorisations
    │   └── config.py          adresses et noms, source unique de vérité
    ├── models/
    │   ├── bge.py             banc d'essai BGE-M3
    │   └── e5.py              banc d'essai multilingual-e5
    ├── scripts/
    │   ├── add_file.py        ingestion des trois documents
    │   └── ocr.py             extraction du texte de la plaquette PDF
    ├── data/                  documents sources et fichiers de travail
    └── logs/                  journaux de vectorisation (créé au 1er lancement)
```

---

## 9. Conteneurisation

`backend/Dockerfile` empaquette **l'API d'embedding uniquement** : image
`python:3.12`, dépendances installées depuis `requirements.txt`, port 8001
exposé.

```bash
cd backend
docker build -t ragbot-api .
docker run -p 8001:8001 ragbot-api
```

**Ce qui n'est pas conteneurisé, et pourquoi :**

- **Qdrant** dispose de son image officielle, utilisée telle quelle
  (`docker run -p 6333:6333 qdrant/qdrant`). La réempaqueter n'apporterait rien.
- **Ollama** s'installe comme service système et gère son propre cache de
  modèles. Le conteneuriser imposerait de retélécharger `qwen3:1.7b` dans un
  volume, sans bénéfice pour un usage local.
- **Chainlit** est l'interface de développement et de démonstration ; elle est
  lancée directement, sans conteneur.

Il n'y a donc **pas de `docker-compose.yml`** : l'orchestration des quatre
services se fait manuellement, comme décrit en section 5. Le conteneur de l'API
doit alors joindre les autres services de l'hôte — voir les variables
d'environnement de la section 5 bis.

**Limite à connaître** : le modèle BGE-M3 n'est pas inclus dans l'image. Il est
téléchargé depuis Hugging Face au premier démarrage du conteneur, ce qui
suppose un accès réseau et allonge ce premier lancement. Monter un volume sur
le cache Hugging Face évite de le retélécharger à chaque `docker run`.

---

## 10. Choix techniques

**Modèles d'embedding comparés.** Trois modèles ont été essayés avant de
trancher : `dangvantuan/sentence-camembert-base` (768 dimensions),
`intfloat/multilingual-e5-large-instruct` et `BAAI/bge-m3` (1024 dimensions).
C'est BGE-M3 qui est en production. Les scripts de comparaison sont conservés
dans `models/bge.py` et `models/e5.py`, et l'endpoint `/embed/e5` reste exposé
par l'API pour permettre de rejouer la comparaison.

**Pourquoi `qwen3:1.7b`.** Modèle assez petit pour tourner sur un poste sans GPU
dédié, tout en restant correct en français. Le prompt est fortement contraint
(`services/llm.py`) : interdiction d'inventer, obligation de s'en tenir au
contexte fourni, et repli sur `chantier@bricosducoeur.org` quand la réponse est
absente des documents.

**Distance cosinus.** La collection est créée avec `Distance.COSINE`
(`services/qdrant.py`), mesure usuelle pour les vecteurs denses de ce type.

**Non retenu** : reranking, recherche hybride dense/lexicale, HyDE,
authentification, historique de conversation en base. Ces pistes ont été
identifiées mais écartées, faute de gain démontré à ce volume de données
(55 chunks).
