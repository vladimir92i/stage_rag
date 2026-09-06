"""Journalisation des appels de vectorisation.

Chaque appel de vectorisation est tracé dans un fichier de log daté, avec
l'horodatage, le nombre de chunks traités, le temps de calcul et, pour une
recherche, les voisins les plus proches retournés.

N'utilise que la bibliothèque standard.
Fichier produit : backend/logs/vectorisation_AAAA-MM-JJ.log
"""

import logging
from datetime import date
from pathlib import Path

DOSSIER_LOGS = Path(__file__).resolve().parent.parent / "logs"
DOSSIER_LOGS.mkdir(parents=True, exist_ok=True)
FICHIER_LOG = DOSSIER_LOGS / f"vectorisation_{date.today().isoformat()}.log"

logger = logging.getLogger("rag_bot.vectorisation")

if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(FICHIER_LOG, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def log_vectorisation(source: str, nb_chunks: int, duree: float):
    """Trace un appel de vectorisation : d'où viennent les chunks,
    combien il y en avait, et combien de temps le calcul a pris."""
    logger.info(
        "vectorisation | source=%s | chunk=%d | duree=%.3fs",
        source, nb_chunks, duree,
    )


def log_voisins(question: str, points, duree: float):
    """Trace une recherche de voisins : la question posée, le temps de
    recherche, puis chaque voisin retourné avec son score et son titre."""
    logger.info(
        "recherche | question=%s | voisins=%d | duree=%.3fs",
        question, len(points), duree,
    )
    for rang, point in enumerate(points, start=1):
        payload = getattr(point, "payload", None) or {}
        logger.info(
            "  voisin %d | score=%.4f | source=%s | titre=%s",
            rang,
            getattr(point, "score", 0.0),
            payload.get("source", "?"),
            payload.get("titre", "?"),
        )
