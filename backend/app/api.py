from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
# from qdrant_client import QdrantClient
from pydantic import BaseModel
from FlagEmbedding import BGEM3FlagModel

app = FastAPI()

class EmbedRequest(BaseModel):
    text: str

# Chargé une seule fois au démarrage
# model = SentenceTransformer('dangvantuan/sentence-camembert-base')
model_bge = BGEM3FlagModel('BAAI/bge-m3',  
                       use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation

model_e5 = SentenceTransformer("intfloat/multilingual-e5-large-instruct")
#client = QdrantClient(url="http://localhost:6333")

# @app.post("/embed")
# async def embed(req: EmbedRequest):
#     vector = model.encode(req.text).tolist()
#     return {"vector": vector }

@app.post("/embed/bge")
async def embed_bge(req: EmbedRequest):
    result = model_bge.encode(req.text,return_dense=True)
    vector = result['dense_vecs'].tolist() # type: ignore
    return {"vector": vector}

@app.post("/embed/e5")
async def embed_e5(req: EmbedRequest):
    result = model_e5.encode(req.text,normalize_embeddings=True)
    vector = result.tolist() # type: ignore
    return {"vector": vector}

