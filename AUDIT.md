# AUDIT — dépôt `stage_rag` (E2 / C6-C7-C8)

Date de l'audit : 2026-09-05 — soutenance 2026-09-08 (J-3).
Périmètre : dépôt local `E2 - ragbot git`, commit `d33aee4`, branche `master`.
**Phase 1 : lecture seule. Aucun fichier du projet n'a été modifié.** Seul `AUDIT.md` a été créé.

---

## 0. Réponses directes aux questions posées

| Question | Réponse |
|---|---|
| 6 fichiers en conflit ? | **Confirmé** : `backend/app/api.py`, `backend/requirements.txt`, `backend/scripts/add_file.py`, `backend/services/qdrant.py`, `pyproject.toml`, `uv.lock`. |
| Le travail BGE-M3 / Ollama / Chainlit est-il commité ? | **Oui.** |
| Est-il poussé ? | **Oui.** `HEAD` = `origin/main` = `d33aee4`, `git status` propre, `git diff origin/main` vide. |
| `services/log.py` est-il vide ? | **Confirmé : 0 octet.** |
| Le remplacement du tiret est-il présent dans `sentence_chunk` ? | **Non.** Seul `;` est remplacé (`add_file.py:50`). |
| Le 4ᵉ modèle `paraphrase-multilingual-MiniLM-L12-v2` existe-t-il ? | **Non**, nulle part dans le dépôt. |

### Deux affirmations de votre brief que le dépôt contredit

1. **« Conflits Git non résolus »** — au sens Git, il n'y a **aucun conflit en cours** : pas de `.git/MERGE_HEAD`, index propre, une seule branche locale. Les marqueurs `<<<<<<< HEAD` / `>>>>>>> origin/main` ont été **commités tels quels** dans l'unique commit `d33aee4` (« first commit », 2026-07-15) puis poussés sur `origin`. Conséquence pratique : `git checkout --ours`, `git mergetool` et consorts sont inopérants ; la résolution devra être **textuelle**.
2. **« Conserve l'alerte de dépassement de seuil existante dans `sentence_chunk` »** — **cette alerte n'existe pas.** `sentence_chunk` (`backend/scripts/add_file.py:46-64`) ne contient ni `print`, ni `warning`, ni test de seuil autre que la coupe `length + count > max_words`. Il n'y a donc rien à conserver. Si vous comptez citer cette alerte comme preuve pour une autre épreuve, **dites-moi dans quel fichier vous pensiez qu'elle se trouvait** — en l'état c'est `NON DÉTERMINÉ`.

---

## 1.1 Détail des conflits

Dans les 5 fichiers texte, le côté **`HEAD` est systématiquement la version BGE-M3 / Ollama / Chainlit**. C'est le côté à conserver.

| Fichier | Côté `HEAD` | Côté `origin/main` | À garder |
|---|---|---|---|
| `backend/app/api.py:5-8` | `from FlagEmbedding import BGEM3FlagModel` | rien | **HEAD** |
| `backend/app/api.py:16-49` | `model_bge = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)` + `model_e5` + endpoints `/embed/bge` et `/embed/e5` ; ligne camembert mise en commentaire | `model = SentenceTransformer('dangvantuan/sentence-camembert-base')` + endpoint unique `/embed` | **HEAD** |
| `backend/requirements.txt:6-14` | `sentence-transformers`, `FlagEmbedding`, `docx`, `re`, `ollama` | `sentence-transformers` seul | **HEAD**, mais à corriger (voir 1.4) |
| `backend/scripts/add_file.py:9-20` | `import re`, `MODEL_URL_BGE = ...:8001/embed/bge`, `model_url_e5 = ...:8001/embed/e5` | `model_url = ...:8000/embed` | **HEAD** |
| `backend/scripts/add_file.py:30-34` | `plaquette_institutionnelle = "../data/plaquette_institutionnelle.txt"` | ligne vide | **HEAD** |
| `backend/scripts/add_file.py:68-72` | `MODEL_URL_BGE` | `model_url` | **HEAD** |
| `backend/scripts/add_file.py:110-128` | fonction `parse_plaquette()` | rien | **HEAD** |
| `backend/scripts/add_file.py:183-216` | `plaquette_to_qdrant()` + 3 appels sur collection `bge-m3` / 1024 | `conv_achat_to_qdrant("camembert3", 768, 100)` | **HEAD** |
| `backend/services/qdrant.py:40-44` | 2 lignes vides | rien | indifférent (conflit purement cosmétique) |
| `pyproject.toml:8-21` | + `chainlit`, `fitz`, `flagembedding`, `ollama`, `pymupdf` | sans ces 5 | **HEAD**, mais `fitz` est un faux paquet (voir 1.4) |
| `uv.lock` | 43 blocs de conflit, 241 paquets verrouillés | — | **à régénérer**, pas à résoudre |

---

## 1.2 État Git

```
2026-07-15 d33aee4 (HEAD -> master, origin/main, origin/HEAD) first commit
git status --short           → (vide)
git diff --stat origin/main  → (vide)
git stash list               → (vide)
git reflog                   → d33aee4 HEAD@{0}: initial pull
origin  https://github.com/vladimir92i/stage_rag.git
```

- **Un seul commit** dans tout le dépôt. Aucune trajectoire de projet lisible : ni passage CamemBERT → BGE-M3, ni ajout d'Ollama, ni ajout de Chainlit.
- Auteur du commit : `vladimir92i <vladimir.boussekeyt@gmail.com>`. **Contribution personnelle : INDÉTERMINÉ par Git** — un unique commit d'import ne prouve la paternité d'aucune ligne.
- **Aucun `.gitignore`.** Sont commités : `backend/__pycache__/`, `backend/app/__pycache__/`, `backend/services/__pycache__/`, et **trois copies** du dossier `.chainlit/` (racine, `backend/`, `backend/app/`).
- **Aucun secret détecté** : pas de clé API, pas de token, pas de `.env`, pas de mot de passe. L'architecture est entièrement locale.

> **Remarque sur la Phase 3, point 3.** « Préparer plusieurs commits lisibles décrivant la trajectoire réelle » à partir d'un dépôt qui n'a qu'un commit d'import revient à **fabriquer un historique**, ce que votre brief interdit par ailleurs. Ce qui est faisable honnêtement : découper les **corrections d'aujourd'hui** en commits datés d'aujourd'hui. Reconstituer les étapes de juillet, non. À arbitrer par vous.

---

## 1.3 Le code fait-il ce que le rapport annonce ?

| # | Affirmation | Verdict | Preuve |
|---|---|---|---|
| 1 | `BAAI/bge-m3` via `FlagEmbedding`, `use_fp16=True` | **PROUVÉ** (sous réserve : fichier non exécutable en l'état) | `backend/app/api.py:6,18-19` ; `backend/models/bge.py:1,3-4` |
| 2 | Endpoints `POST /embed/bge` et `POST /embed/e5` | **PROUVÉ** (même réserve) | `backend/app/api.py:29-33` et `35-39` |
| 3 | Trois modèles réellement implémentés (bge, e5, camembert) | **PARTIEL** | bge et e5 sont servis par l'API (`api.py:18,21,29,35`) et ont chacun un script de benchmark (`backend/models/bge.py`, `backend/models/e5.py`). **CamemBERT n'existe plus que dans le côté `origin/main` du conflit (`api.py:41`) et en commentaire (`api.py:17`)** ; aucun `models/camembert.py`. Trace d'ingestion CamemBERT subsistante : `add_file.py:214-215` (`"camembert"`, `"camembert3"`, dim 768). |
| 4 | 4ᵉ modèle `paraphrase-multilingual-MiniLM-L12-v2` | **NON DÉMONTRÉ — CONTRADICTION** | Zéro occurrence dans le dépôt. Ce qu'on trouve est **un autre modèle** : `all-MiniLM-L6-v2`, en commentaire dans `backend/services/qdrant.py:55,59` et dans le bytecode commité `backend/__pycache__/api.cpython-312.pyc` (chaîne `all-MiniLM-L6-v2`, chemin source `C:\Users\vlad\...\RAG_Bot\backend\api.py`). Le rapport nomme `paraphrase-multilingual-MiniLM-L12-v2` ; le code n'a jamais contenu que `all-MiniLM-L6-v2`. À assumer à l'oral. |
| 5 | Collection `bge-m3`, dimension **1024**, distance **cosinus** | **PROUVÉ** | `backend/services/qdrant.py:17` (`Distance.COSINE`) ; `backend/scripts/add_file.py:209-211` (`"bge-m3"`, `1024`) ; `backend/services/llm.py:10` (`COLLECTION_NAME = "bge-m3"`) |
| 6 | Trois documents ingérés | **PROUVÉ** | `add_file.py:209-211` : `page_de_base_to_qdrant` (`data/page_de_base.json`), `conv_achat_to_qdrant` (`data/convention_achat.txt`), `plaquette_to_qdrant` (`data/plaquette_institutionnelle.txt`). Les trois fichiers existent dans `backend/data/`. |
| 7 | Ollama, `qwen3:1.7b`, prompt contraint, repli e-mail | **PROUVÉ** | `backend/services/llm.py:1,9,65` (`chat`, `MODEL_NAME = "qwen3:1.7b"`) ; prompt contraint `llm.py:45-62` ; `chantier@bricosducoeur.org` en `llm.py:58`. **Nuance à connaître** : le repli est une *instruction de prompt*, pas une garantie de code ; aucun test ne vérifie que le modèle l'applique. |
| 8 | Chainlit, gestion explicite des erreurs, 3 questions de démarrage | **PROUVÉ** | `backend/app.py:16-22` (`try/except`, message d'erreur, fallback réponse vide) ; `backend/app.py:24-39` (exactement 3 `cl.Starter`) |
| 9 | Journalisation de chaque vectorisation | **CONTREDIT** | `backend/services/log.py` = **0 octet**. Aucun `import logging` dans le dépôt. Aucun appel de journalisation dans `llm.py` ni `add_file.py`. Le seul « journal » est `backend/nearest_neighbors.txt`, **lui aussi vide (0 octet)**, et son écriture est commentée (`backend/main.py:33,44-45`). Le rapport annonce horodatage + nombre de fragments + temps de calcul + voisins retournés : **rien de tout cela n'existe.** |
| 10 | Découpage remplaçant `;` **et** `-` | **CONTREDIT (partiellement)** | `backend/scripts/add_file.py:50` : `text = text.replace(";", ".")`. **Le remplacement du tiret est absent.** Le rapport E5 documente une résolution d'incident qui n'est pas dans le code livré. |

---

## 1.4 Le projet démarre-t-il ? Non.

### `pip install -r backend/requirements.txt` → **échoue**

| Ligne | Contenu | Problème |
|---|---|---|
| 6, 12, 14 | marqueurs de conflit | **pip refuse le fichier** dès la première ligne invalide. Bloquant absolu. |
| 10 | `re` | `re` est un **module de la bibliothèque standard** ; aucun paquet PyPI de ce nom n'existe. Échec garanti. |
| 9 | `docx` | Paquet PyPI existant mais **obsolète (Python 2) — ce n'est pas `python-docx`**. Et **aucun fichier du projet n'importe `docx`** : dépendance à retirer, pas à renommer. |
| — | `chainlit` | **Manquant**, alors que `backend/app.py:1` l'importe. |
| — | `pymupdf` | **Manquant** ; `backend/scripts/ocr.py:1-4` importe `fitz` (en commentaire). |
| — | `numpy` | **Manquant** ; importé par `qdrant.py:4` et `add_file.py:7` (imports par ailleurs inutilisés). |
| 1 | `fastapi[standard]>=0.113.0,<0.114.0` | **CONTRADICTION** avec `pyproject.toml:10` qui exige `fastapi[standard]>=0.135.3`. Les deux contraintes sont incompatibles. |

`pyproject.toml:11` : `fitz>=0.0.1.dev2` — **`fitz` sur PyPI n'est pas PyMuPDF**, c'est un paquet sans rapport. Le bon nom est `pymupdf`, déjà présent ligne 16. À retirer.

### `fastapi dev --port 8001 backend/app/api.py` → **échoue**
`SyntaxError` sur `backend/app/api.py:5` (marqueur `<<<<<<< HEAD`). Le fichier n'est pas du Python valide.

### `chainlit run backend/app.py` → **échoue**
- `chainlit` n'est pas installé (absent de `requirements.txt`).
- `backend/app.py:2` fait `from services.llm import ...` : ne résout que si le **répertoire courant est `backend/`**. Depuis la racine du dépôt → `ModuleNotFoundError`. Le `README.md:46-48` le dit (« dans backend »), mais la commande de votre brief l'ignore.
- Aucun `__init__.py` nulle part : `services`, `scripts`, `models` sont des namespace packages implicites. Ça fonctionne, mais rend chaque import dépendant du répertoire courant.

### `python -m scripts.add_file` → **échoue, et de façon insoluble en l'état**
1. `SyntaxError` (5 blocs de conflit).
2. **Contradiction de répertoire courant, qui subsistera même après résolution des conflits** :
   - `from services.qdrant import ...` (`add_file.py:5`) exige cwd = `backend/` ;
   - `page_de_base = '../data/page_de_base.json'` (`add_file.py:31,35,36`) exige cwd = `backend/scripts/`.
   Aucun répertoire ne satisfait les deux. Le script ne « marchait » que grâce au `sys.path.append("C:/Users/vlad/Documents/Cours B3/Notes stage/RAG_Bot/backend")` (`add_file.py:2`) — **chemin absolu de la machine d'origine, dont l'utilisateur est `vlad` et non `vladi`** : il ne résout sur aucune autre machine, y compris celle-ci.
3. `nltk` : `sent_tokenize` est appelé (`add_file.py:51`) sans qu'aucun `nltk.download('punkt_tab')` n'existe dans le dépôt. Sur une machine vierge → `LookupError`. (`nltk` est importé en `add_file.py:4` mais jamais utilisé autrement.)
4. Les trois ingestions sont **au niveau module** (`add_file.py:209-211`), sans garde `if __name__ == "__main__"` : le simple import du module déclenche l'ingestion complète.
5. `sent_tokenize(text)` est appelé **sans `language="french"`** sur du texte français.

### `docker build` puis `docker compose up` → **échouent**
- `backend/Dockerfile:7` : `pip install -r requirements.txt` → même échec que ci-dessus (`re`, marqueurs). **Build impossible.**
- `backend/Dockerfile:1` : `FROM python:3.14` alors que `.python-version` dit `3.12` et `pyproject.toml:6` `>=3.12`. La disponibilité des roues `torch` / `FlagEmbedding` pour 3.14 est un risque majeur — **NON DÉTERMINÉ** sans tentative d'installation réelle.
- `backend/Dockerfile:9,12` : `COPY . /backend/app` puis `CMD ["fastapi","run","app/main.py",...]`. Le fichier `/backend/app/main.py` existe bien, **mais c'est `backend/main.py`, un script de test à `argparse` qui n'expose aucun objet `app` FastAPI** (`backend/main.py:1-55`). L'API réelle se retrouve en `/backend/app/app/api.py`. Le `CMD` est faux.
- Pas de `EXPOSE` ; `WORKDIR` = `/backend` alors que le code atterrit dans `/backend/app` → les chemins relatifs `../data/` sont cassés.
- `docker-compose.yml` = **0 octet** → `docker compose up` échoue (« top-level object must be a mapping »). Aucun service Qdrant, aucun volume, aucun réseau.

### État de l'environnement local (constaté)
`python` = **3.14.2**, aucun venv (`pyvenv.cfg` absent), **aucune** dépendance installée (`nltk`, `fastapi`, `qdrant_client`, `httpx`, `chainlit`, `ollama`, `FlagEmbedding`, `sentence_transformers`, `fitz`, `docx` : toutes manquantes). `docker` est présent. **`ollama` n'est pas installé** (aucun binaire dans le `PATH`). **`uv` n'est pas installé**, alors que `uv.lock` est le format de verrouillage du projet.

---

## 1.5 Cohérence interne

- **Ports — trois valeurs concurrentes pour le même service d'embedding :**
  - `8001/embed/bge` : `services/llm.py:7`, `scripts/add_file.py:14`, `backend/main.py:12`, `README.md:52`
  - `8001/embed/e5` : `scripts/add_file.py:15`
  - `8000/embed` : `services/qdrant.py:7` (variable `model_url` **jamais utilisée**), `scripts/add_file.py:19` (côté origin/main), `backend/main.py:13`
  - Qdrant `6333` : cohérent partout (`qdrant.py:11`, `llm.py:8`, `add_file.py:24`). Ollama utilise son défaut implicite `11434`, jamais écrit nulle part.
  - Aucune variable d'environnement, aucun fichier de configuration : **cinq littéraux en dur**.
- **Double affectation écrasante** — `backend/main.py:12-13` : `model = ".../8001/embed/bge"` puis immédiatement `model = ".../8000/embed"`. La valeur réellement utilisée par `send_sentence_and_print_nearest_neighbors` (`main.py:30`) est **la seconde**, donc l'ancien endpoint CamemBERT. Or ce script interroge la collection `bge-m3` (`main.py:52`) : vecteurs 768 contre collection 1024 → incohérence de dimension à l'exécution.
- **Paramètre ignoré** — `send_sentence_and_print_nearest_neighbors` déclare `model_url` (`main.py:20`) mais `main.py:30` utilise la globale `model` ; le paramètre n'est jamais transmis.
- **Chemin absolu en dur** — `backend/scripts/add_file.py:2`, machine et utilisateur d'origine (`C:/Users/vlad/...`).
- **Fichiers vides (0 octet)** : `docker-compose.yml`, `backend/services/log.py`, `backend/nearest_neighbors.txt`.
- **`backend/README.md` : absent.** Le référentiel exige gestion des accès / installation / test / dépendances / interconnexions / données. Rien de tout cela n'existe.
- **`README.md` racine — arborescence fausse** : annonce `config/` (lignes 57 et 64) et `src/` (ligne 65), **qui n'existent pas**, et un `requirements.txt` à la racine (lignes 35 et 63) alors qu'il est dans `backend/`. Ne mentionne ni `backend/`, ni `data/`, ni `services/`, ni `models/`, ni `scripts/`, ni Qdrant, ni BGE-M3, ni Docker. Annonce « Python 3.8+ » (ligne 7) alors que `pyproject.toml:6` exige `>=3.12`.
- **Trois copies de `.chainlit/`** (racine, `backend/`, `backend/app/`) et trois `chainlit.md` **identiques au modèle par défaut de Chainlit** : le jury verra l'écran d'accueil « Welcome to Chainlit! 🚀🤖 ».
- **Bug de payload** — `backend/scripts/add_file.py:200` : la plaquette institutionnelle est indexée avec `"source": "convention_achat"`. Toute citation de source sur ces fragments sera fausse. *(Signalé, non corrigé.)*
- **`top_k` inopérant** — `services/llm.py:21` accepte `top_k: int = 3`, mais `search_nearest_neighbors` (`qdrant.py:38`) code `limit=3` en dur ; un `top_k > 3` serait silencieusement ignoré.
- **`backend/test.py`** porte le nom d'un test sans en être un (aucun `assert`, aucun framework) et embarque une **copie divergente** de `sentence_chunk` (`test.py:4-21`) **sans** le `replace(";", ".")`. Il ouvre `./data/...` → exige cwd = `backend/`.
- **Imports morts** : `numpy` (`qdrant.py:4`, `add_file.py:7`), `uuid` (`add_file.py:8`), `models` (`add_file.py:11`), `nltk` (`add_file.py:4`), `QdrantClient` et la variable `client` (`llm.py:4,8`), `ChatResponse` (`llm.py:2`).

---

## 1.6 Tableau de synthèse

| # | Constat | Fichier:ligne | Gravité | Action proposée |
|---|---|---|---|---|
| 1 | Marqueurs de conflit commités → `SyntaxError` | `backend/app/api.py:5,8,16,40,49` | **bloquant** | Étape 1 — garder HEAD |
| 2 | Marqueurs de conflit commités → `SyntaxError` | `backend/scripts/add_file.py:9,16,20,30,32,34,68,70,72,110,127,128,183,213,216` | **bloquant** | Étape 1 — garder HEAD |
| 3 | Marqueurs de conflit → `pip` refuse le fichier | `backend/requirements.txt:6,12,14` | **bloquant** | Étapes 1 et 2 |
| 4 | `re` listé comme dépendance (module standard, pas de paquet PyPI) | `backend/requirements.txt:10` | **bloquant** | Étape 2 — retirer |
| 5 | Marqueurs de conflit | `pyproject.toml:8,17,21` | **bloquant** | Étape 1 |
| 6 | 43 blocs de conflit dans le verrou | `uv.lock:5,158,162,…` | **bloquant** | Étape 1 — régénérer (`uv lock`), ne pas éditer à la main |
| 7 | `docker-compose.yml` vide (0 o) | `docker-compose.yml` | **bloquant** (démo Docker) | Étape 7 — Qdrant + API |
| 8 | `CMD` du Dockerfile pointe un script sans objet `app` | `backend/Dockerfile:12` | **bloquant** | Étape 7 |
| 9 | `sys.path.append` absolu vers `C:/Users/vlad/...` | `backend/scripts/add_file.py:2` | **bloquant** hors machine d'origine | Étape 6 |
| 10 | Chemins `../data/` incompatibles avec l'import `services.*` : aucun cwd ne fonctionne | `backend/scripts/add_file.py:5,31,35,36` | **bloquant** | Étape 6 — chemins relatifs au fichier |
| 11 | `services/log.py` vide alors que le rapport annonce une journalisation détaillée | `backend/services/log.py` | **majeur** (critère « monitorage opérationnel ») | Étape 3 |
| 12 | `sentence_chunk` ne remplace pas le tiret, contrairement au rapport E5 | `backend/scripts/add_file.py:50` | **majeur** | Étape 5 + mesures chiffrées |
| 13 | `backend/README.md` absent (accès, installation, test, dépendances, interconnexions, données) | — | **majeur** (critère référentiel) | Étape 4 |
| 14 | README racine décrit `config/` et `src/` inexistants, et Python 3.8+ | `README.md:7,35,57,63-66` | **majeur** | Étape 4 |
| 15 | `chainlit`, `pymupdf`, `numpy` absents de `requirements.txt` | `backend/requirements.txt` | **majeur** | Étape 2 |
| 16 | `docx` déclaré, jamais importé, et mauvais paquet | `backend/requirements.txt:9` | **majeur** | Étape 2 — retirer |
| 17 | `fitz` déclaré : ce n'est pas PyMuPDF | `pyproject.toml:11` | **majeur** | Étape 2 — retirer |
| 18 | Contrainte `fastapi` contradictoire entre les deux fichiers | `backend/requirements.txt:1` vs `pyproject.toml:10` | **majeur** | Étape 2 — aligner |
| 19 | Aucun `nltk.download('punkt_tab')` → `LookupError` sur machine vierge | `backend/scripts/add_file.py:4,51` | **majeur** | Étape 2 ou 6 — **à arbitrer** |
| 20 | `model` réassigné puis écrasé → l'ancien endpoint CamemBERT est celui utilisé | `backend/main.py:12-13,30` | **majeur** | Étape 6 |
| 21 | Trois littéraux de port concurrents, aucune source unique de vérité | `llm.py:7`, `qdrant.py:7`, `add_file.py:14,15,19`, `main.py:12,13`, `README.md:52` | **majeur** | Étape 6 |
| 22 | Plaquette indexée avec `"source": "convention_achat"` | `backend/scripts/add_file.py:200` | **majeur** (fausse citation devant le jury) | **hors plan — me demander** |
| 23 | `paraphrase-multilingual-MiniLM-L12-v2` du rapport absent du code (seul `all-MiniLM-L6-v2` a existé) | `backend/services/qdrant.py:55,59` ; `backend/__pycache__/api.cpython-312.pyc` | **majeur** — CONTRADICTION rapport/code | **ne pas coder** : à assumer à l'oral |
| 24 | CamemBERT n'existe que dans le côté à supprimer du conflit | `backend/app/api.py:17,41` | **mineur** | conserver `api.py:17` en commentaire comme trace C7 |
| 25 | `FROM python:3.14` vs `.python-version` = 3.12 | `backend/Dockerfile:1` | **majeur** (roues torch) | Étape 7 |
| 26 | Ingestion exécutée à l'import (pas de `if __name__`) | `backend/scripts/add_file.py:209-211` | **mineur** | Étape 6 |
| 27 | `sent_tokenize` sans `language="french"` | `backend/scripts/add_file.py:51` | **mineur** | à arbitrer (change les mesures de l'étape 5) |
| 28 | `top_k` de `generate_response` sans effet (`limit=3` en dur) | `llm.py:21` vs `qdrant.py:38` | **mineur** | signalé |
| 29 | Aucun `.gitignore` ; `__pycache__` et 3 copies de `.chainlit/` commités | racine | **mineur** | à arbitrer |
| 30 | `chainlit.md` = modèle par défaut non personnalisé (visible par le jury) | `chainlit.md`, `backend/chainlit.md`, `backend/app/chainlit.md` | **mineur** | à arbitrer |
| 31 | `backend/test.py` n'est pas un test et duplique `sentence_chunk` sans le `replace` | `backend/test.py:4-21` | **mineur** | ne pas supprimer (trace) ; signalé |
| 32 | `nearest_neighbors.txt` vide, écriture commentée | `backend/nearest_neighbors.txt` ; `backend/main.py:33,44-45` | **mineur** | conserver (trace) |
| 33 | Imports morts (`numpy`, `uuid`, `nltk`, `ChatResponse`, `QdrantClient`/`client`) | divers | **mineur** | ne pas toucher (J-3) |
| 34 | Historique Git : un seul commit d'import, contribution non traçable | `d33aee4` | **majeur** pour la soutenance | voir 1.2 — à arbitrer |
| 35 | Environnement local : Python 3.14, aucun venv, zéro dépendance installée, `ollama` absent, `uv` absent | machine | **bloquant** pour la Phase 3 | à préparer avant la démo |

---

## Points qui exigent votre arbitrage avant la Phase 2

1. **L'« alerte de dépassement de seuil » de `sentence_chunk` n'existe pas.** Où pensiez-vous qu'elle se trouvait ?
2. **Constat 22** : corriger `"source": "convention_achat"` sur la plaquette n'est prévu par aucune étape de votre plan. Je corrige, ou je laisse ?
3. **Constat 19** : `nltk.download('punkt_tab')` ajouté au code, ou documenté comme étape manuelle dans le README ?
4. **Constat 27** : passer `sent_tokenize(..., language="french")` changerait les chiffres demandés à l'étape 5. Par défaut je mesure avec le comportement actuel (tokenizer anglais). Confirmez.
5. **Constat 35** : la Phase 3 (chaîne complète de bout en bout) n'est **pas réalisable sur cette machine** sans installation préalable d'Ollama + `qwen3:1.7b` (~1,4 Go), d'un Python 3.12 et d'un conteneur Qdrant. Dites-moi comment procéder.
6. **Phase 3, point 3** : reconstituer un historique de juillet serait de la fabrication. Je propose des commits datés d'aujourd'hui décrivant les corrections. Confirmez.

**Fin de la Phase 1. Aucun fichier du projet n'a été modifié. J'attends votre validation.**
