import sys
from pathlib import Path

# le dossier backend/ doit etre importable quel que soit le repertoire courant
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from nltk.tokenize import sent_tokenize
import nltk
from services.qdrant import insert_vectors, create_collection
from services.log import log_vectorisation
from services.config import EMBED_BGE_URL, EMBED_E5_URL, QDRANT_URL, COLLECTION_NAME, VECTOR_SIZE
import httpx
import numpy as np
import uuid
import re
from qdrant_client import QdrantClient,models
import json
import time

MODEL_URL_BGE = EMBED_BGE_URL
model_url_e5 = EMBED_E5_URL
# how to req
# r = httpx.post(model, data={'key': 'value'})

client = QdrantClient(url=QDRANT_URL)

chunk_150 = "chunk_150"
chunk_100 = "chunk_100"
chunk_50 = "chunk_50"

# chemins relatifs au fichier, pas au repertoire courant
DATA = BACKEND / "data"
plaquette_institutionnelle = str(DATA / "plaquette_institutionnelle.txt")
page_de_base = str(DATA / "page_de_base.json")
conv_achat = str(DATA / "convention_achat.txt")


# sentences = "Tout achat au sein de La Quincaillerie Solidaire Les Bricos du cœur devra suivre un processus permettant de réaliser la transaction de manière satisfaisante pour les deux parties. - Dans un premier temps, le partenaire envoie un email à La Quincaillerie Solidaire - Les Bricos du Coeur Association loi 1901 135 rue Sadi Carnot - 59790 Ronchin ✉ contact@laquincaillerie.org - 3 - contact-haubourdin@laquincaillerie.org au moins 2 jours ouvrés avant toute visite. Cet email doit reprendre les produits recherchés et leurs quantités ainsi que le jour et l’heure du retrait souhaités; - Par retour d’email, La Quincaillerie Solidaire - Les Bricos du cœur confirme l’ensemble des informations (produits, quantités, jour et heure de passage) en fonction de la disponibilité produits et de l’activité. A noter que La Quincaillerie Solidaire Les Bricos du Cœur se réserve le droit de limiter les quantités de produits en fonction des stocks disponibles. De plus, sur demande, la Quincaillerie Solidaire les Bricos du coeur peut établir un devis correspondant aux produits demandés; - Le partenaire se rend à La Quincaillerie Solidaire Les Bricos du coeur selon les modalités convenues précédemment afin de récupérer, en un seul passage, l’ensemble des produits commandés disponibles; - La Quincaillerie Solidaire - Les Bricos du coeur émet une facture au nom du partenaire qui sera automatiquement envoyée par e-mail aux deux référents; - Le règlement des produits peut s’effectuer - au moment du retrait de la marchandise par Carte Bancaire, espèce ou chèque au nom de la structure partenaire; - à 30 jours par virement bancaire ou par chèque au nom de la structure partenaire. En cas d’article défectueux, La Quincaillerie Solidaire Les Bricos du cœur s’engage à reprendre ou remplacer ledit produit. Tout article non défectueux peut être retourné dans les 30 jours suivants l’achat sous condition de ne pas avoir été utilisé et d’être toujours dans son emballage d’origine. La Quincaillerie Solidaire Les Bricos du Coeur émet alors un avoir ou rembourse le partenaire sous 1 semaine par virement bancaire sur son compte bancaire."
#sent2 = "Tout achat au sein de La Quincaillerie Solidaire Les Bricos du cœur devra suivre un processus permettant de réaliser la transaction de manière satisfaisante pour les deux parties. - Dans un premier temps, le partenaire envoie un email à La Quincaillerie Solidaire - Les Bricos du Coeur Association loi 1901 135 rue Sadi Carnot - 59790 Ronchin ✉ contact@laquincaillerie.org - 3 - contact-haubourdin@laquincaillerie.org au moins 2 jours ouvrés avant toute visite. Cet email doit reprendre les produits recherchés et leurs quantités ainsi que le jour et l’heure du retrait souhaités; - Par retour d’email, La Quincaillerie Solidaire - Les Bricos du cœur confirme l’ensemble des informations (produits, quantités, jour et heure de passage) en fonction de la disponibilité produits et de l’activité. A noter que La Quincaillerie Solidaire Les Bricos du Cœur se réserve le droit de limiter les quantités de produits en fonction des stocks disponibles."
#sent3 = "Tout achat au sein de La Quincaillerie Solidaire Les Bricos du cœur devra suivre un processus permettant de réaliser la transaction de manière satisfaisante pour les deux parties. - Dans un premier temps, le partenaire envoie un email à La Quincaillerie Solidaire - Les Bricos du Coeur Association loi 1901 135 rue Sadi Carnot - 59790 Ronchin ✉ contact@laquincaillerie.org - 3 - contact-haubourdin@laquincaillerie.org au moins 2 jours ouvrés avant toute visite."
#sent4 = "En cas de manquement de l’une des Parties à l’une quelconque des obligations mises à sa charge par la présente convention ou faute grave par l’une ou l’autre des Parties, l’autre Partie notifiera ce manquement ou cette faute à la Partie défaillante par lettre recommandée avec accusé de réception. La Partie défaillante disposera alors d’un délai d’un (1) mois à compter de la date de réception de la lettre recommandée pour remédier à sa défaillance."
# phrases pour tester les retours de sentence_chunk (peut etre autant faire un fichier de test unitaire ? sinj)
#print(len(sent4.split()))

def sentence_chunk(text, max_words=50):
    """
    renvoie une liste de phrase qui font le max word
    """
    text = text.replace(";", ".")
    text = text.replace("-", ".")
    sentences = sent_tokenize(text)
    chunks, buffer, length = [], [], 0

    for sent in sentences:
        count = len(sent.split())
        if length + count > max_words and buffer:
            chunks.append(" ".join(buffer))
            buffer, length = [], 0
        buffer.append(sent)
        length += count

    if buffer:
        chunks.append(" ".join(buffer))
    return chunks

def transform_text_to_embedding(texte:str)->list[float]:
    response = httpx.post(
        MODEL_URL_BGE,
        json={"text": texte },
        timeout=30.0
    )
    return response.json()["vector"]
        

def parse_convention(text: str)->list[dict]:
    chunks = []
    current_titre = ""
    current_texte = []
    
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        if line.isupper():  # ligne entièrement en majuscules = titre
            # sauvegarde le chunk précédent
            if current_texte:
                chunks.append({
                    "titre": current_titre,
                    "texte": " ".join(current_texte)
                })
            current_titre = line
            current_texte = []
        else:
            current_texte.append(line)
    
    # dernier chunk
    if current_texte:
        chunks.append({
            "titre": current_titre,
            "texte": " ".join(current_texte)
        })
    
    return chunks

def parse_plaquette(file_url: str)->list[dict]:
    with open(file_url, "r", encoding="utf-8") as file:
        data = file.read()

    sections = re.split(r'^## ', data, flags=re.MULTILINE)
    paragraphes = []
    for section in sections:
        if section.strip():
            lines = section.strip().split('\n', 1)
            titre = lines[0].strip()
            texte = lines[1].strip() if len(lines) > 1 else ""
            texte = texte.replace("\n", " ").replace("•", "").strip()
            paragraphes.append({"titre": titre, "texte": texte.lower()})
    
    return paragraphes
    

def page_de_base_to_qdrant(my_coll:str,vector_size:int, max_word:int):
    debut = time.perf_counter()
    points = []
    create_collection(my_coll,vector_size)
    with open(page_de_base, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for paragraphe in data["paragraphes"]:  # ← boucle sur chaque paragraphe
        for chunk in sentence_chunk(paragraphe["texte"],max_word):
            embed = transform_text_to_embedding(chunk)
            chunk_size = len(chunk.split())
    
            points.append({
                "vector": embed,
                "payload": {
                    "source": data["source"],
                    "titre": paragraphe["titre"],
                    "texte": chunk,
                    "chunk_size": chunk_size
                }
            })

    insert_vectors(points,my_coll)
    log_vectorisation("page_de_base", len(points), time.perf_counter() - debut)
    print(f"{len(points)} points ajoutés dans Qdrant")



def conv_achat_to_qdrant(my_coll:str,vector_size:int, max_word:int):
    debut = time.perf_counter()
    create_collection(my_coll,vector_size)
    points = []
    with open(conv_achat, "r", encoding="utf-8") as file:
        data = file.read()
    
    sections = parse_convention(data)
    
    for section in sections:
        titre = section["titre"]
        texte = section["texte"]
        for chunk in sentence_chunk(texte,max_word):
            chunk_size = len(chunk.split())
            embedding = transform_text_to_embedding(chunk)
            points.append({
                "vector":embedding,
                "payload":{
                    "texte": chunk,
                    "titre": titre,
                    "source": "convention_achat",
                    "chunk_size": chunk_size
                }
            })
    
    insert_vectors(points, my_coll)
    log_vectorisation("convention_achat", len(points), time.perf_counter() - debut)
    print(f"{len(points)} points ajoutés dans Qdrant")

def plaquette_to_qdrant(my_coll:str,vector_size:int):
    debut = time.perf_counter()
    create_collection(my_coll,vector_size)
    points = []
    
    sections = parse_plaquette(plaquette_institutionnelle)
    
    for section in sections:
        titre = section["titre"]
        texte = section["texte"]
        chunk_size = len(texte.split())
        embedding = transform_text_to_embedding(texte)
        points.append({
            "vector":embedding,
            "payload":{
                "texte": texte,
                "titre": titre,
                "source": "convention_achat",
                "chunk_size": chunk_size
            }
        })
    
    insert_vectors(points, my_coll)
    log_vectorisation("plaquette_institutionnelle", len(points), time.perf_counter() - debut)
    print(f"{len(points)} points ajoutés dans Qdrant")
    

if __name__ == "__main__":
    page_de_base_to_qdrant(COLLECTION_NAME, VECTOR_SIZE, 50)
    conv_achat_to_qdrant(COLLECTION_NAME, VECTOR_SIZE, 100)
    plaquette_to_qdrant(COLLECTION_NAME, VECTOR_SIZE)

  
# txt = "9.1 Chaque partie conservera la propriété totale et exclusive de ses connaissances antérieures et des éléments (données, informations, dénomination sociale, logo…) communiqués dans le cadre de la mise en œuvre de la présente convention. 9.2 Chaque partie détient des droits de propriété exclusifs sur ses marques, sa dénomination sociale et son logo (cf.annexe). Chaque partie bénéficie d'un droit d'usage non exclusif de la marque et du logo de l'autre Partie aux seules fins mentionnées par la présente Convention. Dans ce cadre, chacune des Parties s'engage à respecter les règles techniques définies par l'autre Partie pour l'utilisation de sa marque et de son logo, et de solliciter en amont de toute utilisation l’autre partie pour accord. 9.3 La présente Convention n'a pas pour effet d'entraîner un transfert de propriété des éléments fournis (données, informations, dénomination sociale, logo…) par l'une des Parties à l'autre Partie. Chacune des Parties s’interdit toute utilisation de ceux-ci sans le consentement préalable écrit de l'autre Partie. 9.4 Les Parties s’accordent sur les moyens à mettre en œuvre pour améliorer la communication relative à la présente convention. Sauf décision contraire des deux Parties, elles s’engagent à mentionner dans toute publication ou action de communication le soutien financier ou la contribution de chacune des Parties aux actions menées dans le cadre de la présente Convention, y compris lors d’une conférence ou d’un séminaire. 9.5 Les Parties s’engagent mutuellement à faire figurer leur logo respectif sur tout support de diffusion relatif au partenariat objet de la présente. En cas d’utilisation des données (logo, dénomination, support de communication etc.), hors champ de la convention, d’une des parties par l’autre partie, cette dernière se réserve le droit d’exercer son opposition à cette utilisation par tous moyens écrits. Ce droit d’opposition entraîne la suppression immédiate et au plus tard, dans les 48 heures, La Quincaillerie Solidaire - Les Bricos du Coeur Association loi 1901 135 rue Sadi Carnot - 59790 Ronchin ✉ contact@laquincaillerie.org - 5 - du support litigieux."