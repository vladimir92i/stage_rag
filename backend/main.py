import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from services.qdrant import search_nearest_neighbors
from services.config import EMBED_BGE_URL, COLLECTION_NAME
import httpx
import argparse
sent1 = "retour remboursement article Bricos du cœur politique"
sent2 = "association Franco-Togolaise accès soins médicaux scolaire Togo matériel informatique mobilier produits médicaux don"
sent3= "retour remboursement article politique"
sent4= "Quelle est la politique de retour et de remboursement des articles ?"
sent5= "Le centre social de l'Hommelet, association partenaire, organise un chantier de peinture participatif impliquant ses bénéficiaires et des bénévoles. L'objectif est de réaménager l'espace jeune, laissé vacant suite au déménagement de la crèche."
sent6= "Puis je devenir partenaire ?"
sent7 = "Qui peut devenir partenaire ?"

model = EMBED_BGE_URL
chunk_150 = "chunk_150"
chunk_100 = "chunk_100"
chunk_50 = "chunk_50"



def transform_text_to_embedding(model_url:str, texte:str)->list[float]:
        
    response = httpx.post(
        model_url,
        json={"text": texte},
        timeout=30.0
    )
    return response.json()["vector"]

def send_sentence_and_print_nearest_neighbors(sentence:str,coll_name:str):
    vector = transform_text_to_embedding(model,sentence)
    r = search_nearest_neighbors(vector,coll_name)

    #with open("nearest_neighbors.txt","w",encoding="utf-8") as f:
    for point in r.points:
        payload = point.payload
        if payload is None:
            continue
        print("Titre :", payload["titre"])
        print("Texte :", payload["texte"])
        print("Score :", point.score)
        print("-" * 40)
    return r.points
        
#     for i in r:
#         f.write(str(i) + "\n")
sent = "quest ce que la quincaillerie solidare et quelles sont les valeurs de l'asso?"
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c","--collection", type=str, default=COLLECTION_NAME)
    args = parser.parse_args()
    # args.collection
    send_sentence_and_print_nearest_neighbors(sent, COLLECTION_NAME)
    
    
    send_sentence_and_print_nearest_neighbors(sent7, args.collection)
