import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from tenacity import retry, wait_exponential, stop_after_attempt

try:
    from openai import AzureOpenAI
except Exception as exc:  # pragma: no cover
    AzureOpenAI = None  # type: ignore


def get_azure_client():
    if AzureOpenAI is None:
        raise RuntimeError("openai package not available")
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )


def ensure_collection(client: QdrantClient, name: str, dim: int = 3072):
    exists = False
    try:
        client.get_collection(name)
        exists = True
    except Exception:
        exists = False
    if not exists:
        client.recreate_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
        )


@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
def embed_texts(client: AzureOpenAI, texts: List[str]) -> List[List[float]]:
    deployment = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-large")
    resp = client.embeddings.create(input=texts, model=deployment)
    return [d.embedding for d in resp.data]


def chunk_text(text: str, max_tokens: int = 800) -> List[str]:
    # naive chunk by characters ~ good enough starter
    chunk_size = max_tokens * 4
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def upsert_clean_docs_to_qdrant(docs: List[Dict[str, Any]]):
    load_dotenv()
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("QDRANT_COLLECTION", "fighter_chunks")
    client = QdrantClient(url=qdrant_url)
    ensure_collection(client, collection)

    azure = get_azure_client()

    points = []
    for idx, doc in enumerate(docs):
        url = doc["url"]
        text = doc.get("text", "")
        chunks = chunk_text(text)
        if not chunks:
            continue
        vectors = embed_texts(azure, chunks)
        for j, (chunk, vec) in enumerate(zip(chunks, vectors)):
            points.append(qmodels.PointStruct(
                id=f"{idx}-{j}",
                vector=vec,
                payload={"url": url, "chunk_id": j, "text": chunk},
            ))

    if points:
        client.upsert(collection_name=collection, points=points)

