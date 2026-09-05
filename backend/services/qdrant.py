from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import httpx
import numpy as np
import uuid

model_url = "http://127.0.0.1:8000/embed"
# how to req
#r = httpx.post(model, data={'key': 'value'})

client = QdrantClient(url="http://localhost:6333")

def create_collection(name: str,vector_size:int):
    if not client.collection_exists(name):
        response = client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        print(response)

# mettre en param list[dict] + coll name
# ex : points = [{vector = [],"payload": {"text": "texte 1", "source": "convention"} }]
def insert_vectors(points:list[dict], collection_name: str):
    client.upsert(
        collection_name=collection_name,
            points=[
                PointStruct(
                    id= uuid.uuid4(),
                    vector=point["vector"],
                    payload=point["payload"],
                )
                for point in points
            ],
    )

def search_nearest_neighbors(vector: list[float], collection_name: str):

    return client.query_points(collection_name=collection_name, query=vector,limit=3)


# sentences = ["Je suis une structure et souhaite être soutenue par les Bricos"]

# response = httpx.post(model, json={'text': sentences[0]},timeout=30.0)
# # response.json() par defaut quand on veut acceder aux données


# embeddings = response.json()["vector"]



# print(search_nearest_neighbors(embeddings, "all-MiniLM-L6-v2"))
#print(embeddings.tolist())  


# #create_collection("all-MiniLM-L6-v2")