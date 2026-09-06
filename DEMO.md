# Démonstration devant le jury — séquence exacte

Assistant documentaire RAG — Les Bricos du Cœur.
Durée de la séquence si tout est préchargé : **3 à 4 minutes**.

> ⚠️ **Les étapes 0 sont à faire la veille, pas devant le jury.** Le
> téléchargement des modèles et l'installation des dépendances prennent
> plusieurs dizaines de minutes et nécessitent le réseau.

---

## 0. La veille — préparation (ne pas faire devant le jury)

```bash
# 0.1 Environnement Python 3.12
py -V:3.12 -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt

# 0.2 Corpus de segmentation NLTK
python -c "import nltk; nltk.download('punkt_tab')"

# 0.3 Modèle de génération
ollama pull qwen3:1.7b

# 0.4 Préchargement du modèle d'embedding (~2 min, évite l'attente en séance)
#     Lancer l'API une fois, attendre "Application startup complete", puis Ctrl+C
cd backend/app && fastapi dev --port 8001 api.py
```

**Vérification la veille** : dérouler toute la séquence ci-dessous une fois en
entier. Si l'ingestion a déjà été faite, Qdrant conserve les données : l'étape 3
du jour peut alors être présentée sans être rejouée.

---

## 1. Base vectorielle — Qdrant

**Terminal 1**

```bash
docker run -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

**Attendu** — le logo Qdrant en ASCII, puis :

```
Access web UI at http://localhost:6333/dashboard
```

*À dire :* « Qdrant est la base vectorielle. Elle stocke les documents de
l'association sous forme de vecteurs de 1024 dimensions et permet la recherche
par similarité cosinus. »

---

## 2. Moteur de génération — Ollama

**Terminal 2**

```bash
ollama serve
```

**Attendu** : des lignes de journal se terminant par
`Listening on 127.0.0.1:11434`.

> Si Ollama tourne déjà comme service Windows, la commande répond
> `address already in use` : **c'est normal, le service est actif**. Le
> démontrer avec `ollama list`, qui doit afficher `qwen3:1.7b`.

*À dire :* « La génération est locale, avec `qwen3:1.7b`. Aucune donnée de
l'association ne sort de la machine, et aucun service payant n'est appelé. »

---

## 3. API d'embedding — FastAPI + BGE-M3

**Terminal 3**

```bash
cd backend/app
fastapi dev --port 8001 api.py
```

**Attendu** — après le chargement du modèle (quelques secondes si préchargé) :

```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Application startup complete.
```

**Preuve immédiate, dans un terminal libre :**

```bash
curl -X POST http://127.0.0.1:8001/embed/bge -H "Content-Type: application/json" -d "{\"text\":\"test\"}"
```

**Attendu** : un JSON `{"vector":[...]}`. Pour montrer la dimension plutôt que
de faire défiler 1024 nombres :

```bash
python -c "import httpx; r=httpx.post('http://127.0.0.1:8001/embed/bge', json={'text':'test'}, timeout=60); print('dimension =', len(r.json()['vector']))"
```

**Attendu : `dimension = 1024`**

*À dire :* « L'API expose deux modèles : `/embed/bge` en production, et
`/embed/e5` conservé pour rejouer la comparaison entre modèles. »

---

## 4. Ingestion des documents

**Terminal 4, depuis la racine du dépôt**

```bash
python backend/scripts/add_file.py
```

**Attendu, dans cet ordre exact :**

```
12 points ajoutés dans Qdrant
30 points ajoutés dans Qdrant
13 points ajoutés dans Qdrant
```

Soit **55 points** : 12 pour la page de présentation du site, 30 pour la
convention d'achat, 13 pour la plaquette institutionnelle.

**Preuve dans Qdrant :**

```bash
curl http://localhost:6333/collections/bge-m3
```

**Attendu** : `"status":"green"`, `"points_count":55`, `"size":1024`,
`"distance":"Cosine"`.

Ou visuellement, sur <http://localhost:6333/dashboard> → collection `bge-m3`.

*À dire :* « Le découpage est adapté à la structure de chaque document :
50 mots par chunk pour la page web, 100 pour la convention, et une section
par chunk pour la plaquette dont les sections sont déjà thématiquement
homogènes. Le benchmark avait montré que la taille de chunk était une variable
secondaire — les scores stagnaient entre 150 et 50 mots. Le vrai levier était
le modèle d'embedding. »

---

## 5. Recherche seule — sans génération

Utile pour montrer l'étage de récupération isolément, avant d'ajouter le LLM.

```bash
python backend/main.py
```

**Attendu** : trois blocs, chacun avec `Titre :`, `Texte :` et `Score :`,
séparés par une ligne de tirets. Les scores sont des similarités cosinus,
d'autant plus élevées que le passage est proche de la question.

*À dire :* « Voici ce que remonte la base avant toute génération. Le LLM ne
reçoit que ces passages : c'est ce qui l'empêche d'inventer. »

---

## 6. Interface — Chainlit

**Terminal 5**

```bash
cd backend
chainlit run app.py -w
```

**Attendu** : le navigateur s'ouvre sur <http://localhost:8000>, avec les trois
questions de démarrage affichées :

- Quels types de produits sont collectés auprès des entreprises ?
- Qu'est-ce que la Quincaillerie Solidaire ?
- Quelle sont les valeurs de votre association

---

## 7. La question de démonstration

**Cliquer sur « Quelle sont les valeurs de votre association ».**

**Attendu** : une réponse qui cite **l'entraide, le partage, la proximité et
l'authenticité**. Ces quatre valeurs viennent de la section `## NOS VALEURS` de
la plaquette institutionnelle — c'est le chunk le plus court de la base
(12 mots), ce qui rend la traçabilité facile à montrer.

**Puis poser une question hors périmètre**, par exemple :
*« Quels sont vos horaires d'ouverture le dimanche ? »*

**Attendu** : le modèle ne doit pas inventer d'horaires. Le prompt lui impose de
s'en tenir au contexte et de proposer d'écrire à `chantier@bricosducoeur.org`.

*À dire :* « C'est le comportement recherché : le système préfère renvoyer vers
un humain plutôt que produire une réponse plausible mais fausse. »

---

## 8. Le monitorage — la preuve écrite

```bash
type backend\logs\vectorisation_2026-09-08.log
```

*(sous Linux/macOS : `cat backend/logs/vectorisation_$(date +%F).log`)*

**Attendu** — pour chaque question posée :

```
<horodatage> | vectorisation | source=question | chunk=1 | duree=<x>s
<horodatage> | recherche | question=Quelle sont les valeurs... | voisins=3 | duree=<x>s
<horodatage> |   voisin 1 | score=<x> | source=plaquette_institutionnelle | titre=NOS VALEURS
<horodatage> |   voisin 2 | score=<x> | source=<...> | titre=<...>
<horodatage> |   voisin 3 | score=<x> | source=<...> | titre=<...>
```

Le format est fixe ; les valeurs dépendent de l'exécution. Sur la question des
valeurs, le voisin 1 doit être `NOS VALEURS`, issu de la plaquette.

*À dire :* « Chaque appel de vectorisation est journalisé : horodatage, nombre
de chunks traités, temps de calcul, et les voisins retournés avec leur score et
leur source. C'est ce qui permet de diagnostiquer une réponse insatisfaisante :
on voit immédiatement si le problème vient de la récupération ou de la
génération. »

---

## 9. Si quelque chose casse

| Symptôme | Cause probable | Réponse |
|---|---|---|
| `Désolé, problème d'embeddings` | l'API du terminal 3 n'est pas démarrée | la relancer ; le message d'erreur est volontaire, il ne plante pas l'interface |
| `Désolé, je n'ai pas trouvé d'information pertinente` | collection vide ou Qdrant arrêté | vérifier `curl http://localhost:6333/collections/bge-m3` |
| `Désolé, le modèle est indisponible` | Ollama arrêté ou modèle absent | `ollama list` |
| Réponse très lente | premier appel, le modèle se charge en mémoire | l'annoncer avant de cliquer |
| `ModuleNotFoundError: chainlit` | environnement en Python 3.14 | activer le venv 3.12 |

**Le point à faire remarquer** : les trois premiers cas affichent un message
clair dans l'interface au lieu d'une trace d'erreur. La gestion des pannes est
explicite dans `services/llm.py` et `backend/app.py`.

---

## 10. Ordre de lancement — mémo

```
1. docker run ... qdrant/qdrant          (terminal 1)
2. ollama serve                          (terminal 2)
3. cd backend/app && fastapi dev --port 8001 api.py   (terminal 3)
4. python backend/scripts/add_file.py    (terminal 4, une seule fois)
5. cd backend && chainlit run app.py -w  (terminal 5)
```

L'ordre compte : l'ingestion (4) a besoin de l'API (3) et de Qdrant (1) ;
l'interface (5) a besoin des trois.
