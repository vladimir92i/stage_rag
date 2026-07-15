# RAG Bot

## Description
RAG Bot est un assistant basé sur la Récupération Augmentée par Génération (RAG) pour répondre aux questions en utilisant des documents sources.

## Prérequis
- Python 3.8+
- pip (gestionnaire de paquets Python)

## Installation

1. Cloner le projet :
```bash
git clone <repository-url>
cd RAG_Bot
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
```

3. Activer l'environnement virtuel :
- **Windows** :
```bash
venv\Scripts\activate
```
- **Linux/Mac** :
```bash
source venv/bin/activate
```

4. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

Lancer l'application :
avoir qdrant de lancer avec la bdd sinon lancer les fichier dans script
```bash
à la racine : 
ollama serve

dans backend :
pour lancer chainlit :
chainlit run app.py -w

dans app
pour lancer l'api d'embedding :
fastapi dev --port 8001 api.py

```

## Configuration
Modifier les fichiers de configuration dans le dossier `config/` si nécessaire.

## Structure du projet
```
RAG_Bot/
├── main.py
├── requirements.txt
├── config/
├── src/
└── README.md
```

## Support
Pour toute question ou problème, veuillez contacter l'équipe de développement.
