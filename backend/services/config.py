"""Configuration des services — source unique de vérité.

Les adresses et les noms étaient auparavant recopiés en dur dans llm.py,
qdrant.py, add_file.py et main.py, avec des valeurs divergentes (deux ports
d'embedding différents cohabitaient). Tout est désormais défini ici, et
surchargeable par variable d'environnement.
"""

import os

# --- API d'embedding (FastAPI, backend/app/api.py) ---
API_EMBEDDING_HOST = os.getenv("API_EMBEDDING_HOST", "127.0.0.1")
API_EMBEDDING_PORT = os.getenv("API_EMBEDDING_PORT", "8001")
API_EMBEDDING_URL = f"http://{API_EMBEDDING_HOST}:{API_EMBEDDING_PORT}"

EMBED_BGE_URL = f"{API_EMBEDDING_URL}/embed/bge"
EMBED_E5_URL = f"{API_EMBEDDING_URL}/embed/e5"
EMBEDDING_MODEL = "BAAI/bge-m3"

# --- Base vectorielle Qdrant ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "bge-m3-test")
VECTOR_SIZE = int(os.getenv("VECTOR_SIZE", "1024"))

# --- Génération (Ollama) ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
