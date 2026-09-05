from ollama import chat
from ollama import ChatResponse
import httpx
import time
from qdrant_client import QdrantClient
from services.qdrant import search_nearest_neighbors
from services.log import log_vectorisation, log_voisins

EMBED_URL = "http://127.0.0.1:8001/embed/bge"
client = QdrantClient(url="http://localhost:6333")
MODEL_NAME = "qwen3:1.7b"  # change si besoin
COLLECTION_NAME = "bge-m3"

def transform_text_to_embedding(model_url:str, texte:str)->list[float]:
        
    response = httpx.post(
        model_url,
        json={"text": texte},
        timeout=30.0
    )
    return response.json()["vector"]

def generate_response(question: str, top_k: int = 3, embed_timeout: int = 120):
    try:
        debut = time.perf_counter()
        vector = transform_text_to_embedding(EMBED_URL, question)
        log_vectorisation("question", 1, time.perf_counter() - debut)
    except Exception as e:
        print("Embedding error:", e)
        return "Désolé, problème d'embeddings — réessaye plus tard."

    try:
        debut = time.perf_counter()
        resp = search_nearest_neighbors(vector, COLLECTION_NAME)
        chunks = resp.points if resp and hasattr(resp, "points") else []
        log_voisins(question, chunks, time.perf_counter() - debut)
    except Exception as e:
        print("Qdrant search error:", e)
        chunks = []

    if not chunks:
        return "Désolé, je n'ai pas trouvé d'information pertinente."

    # build context from top_k chunks
    contexte = "\n".join(
        f"- {getattr(p.payload, 'texte', p.payload['texte']) if p.payload is not None else ''}"
        if hasattr(p, "payload") else f"- {p['payload']['texte']}" #type: ignore
        for p in chunks[:top_k]
    )

    prompt = f"""
    L’association s’appelle STRICTEMENT "Les Bricos du Cœur".
    Ne jamais renommer, reformuler ou substituer ce nom.
    Ne jamais inventer un autre nom d’organisation.
    Si un autre nom apparaît dans le contexte, il doit être ignoré sauf s’il est explicitement demandé.
    Ne fusionne jamais plusieurs organisations ou sources.
    Chaque réponse doit concerner uniquement "Les Bricos du Cœur".
    Tu es un assistant pour l'association Les Bricos du Cœur, sois aimable, chaleureux et accueillant.
    Tu réponds toujours avec politesse et bienveillance.
    Tu peux ajouter une courte phrase d’introduction conviviale avant de répondre.
    Le ton doit rester naturel, pas exagéré
    Réponds à la question en utilisant uniquement le contexte fourni. n'inventes rien
    Si tu ne trouves pas la réponse, ou que tu sens que tu as repondu à toutes les questions
    propose toujours d'envoyer un mail à chantier@bricosducoeur.org.

    Contexte :{contexte}
    Question : {question}
    """

    try:
        response = chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}])
        content = response.message.content
        if not content:
            print("LLM returned empty content:", response)
            return "Désolé, le modèle n'a pas retourné de réponse."
        return content
    except Exception as e:
        print("LLM call error:", e)
        return "Désolé, le modèle est indisponible pour l'instant."
    
