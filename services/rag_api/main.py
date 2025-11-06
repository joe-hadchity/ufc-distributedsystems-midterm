import os
from typing import List
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from qdrant_client import QdrantClient
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv

# ================================================
# Rate limiting
# ================================================
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# ================================================
# Load environment
# ================================================
load_dotenv()

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{os.getenv('API_RATE_LIMIT', '60')}/minute"]
)

# ================================================
# Initialize FastAPI app
# ================================================
app = FastAPI(title="UFC RAG API", version="1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ================================================
# Azure OpenAI (optional)
# ================================================
try:
    from openai import AzureOpenAI
except Exception:
    AzureOpenAI = None  # type: ignore


class QARequest(BaseModel):
    q: str
    k: int = 5


@app.on_event("startup")
def startup_event():
    """Initialize external connections on startup."""
    # ---------------- Qdrant ----------------
    try:
        app.state.qdrant = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    except Exception:
        app.state.qdrant = None

    # ---------------- Azure OpenAI ----------------
    if AzureOpenAI is not None:
        try:
            app.state.azure = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            )
        except Exception:
            app.state.azure = None
    else:
        app.state.azure = None

    # ---------------- MongoDB ----------------
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI is required")
    app.state.mongo = MongoClient(mongo_uri)
    db_name = os.getenv("MONGODB_DB", "ufc")
    app.state.db = app.state.mongo[db_name]


@app.on_event("shutdown")
def shutdown_event():
    """Close connections cleanly."""
    try:
        app.state.mongo.close()
    except Exception:
        pass


# ================================================
# Health Endpoint
# ================================================
@app.get("/health")
def health():
    """Quick check for service health and dependencies."""
    return {
        "status": "ok",
        "qdrant": app.state.qdrant is not None,
        "azure": app.state.azure is not None
    }


# ================================================
# Fighters Endpoints
# ================================================
@app.get("/fighters")
@limiter.limit("60/minute")
def list_fighters(request: Request, limit: int = 20, skip: int = 0):
    """Return list of fighters (raw scraped data)."""
    try:
        cur = app.state.db["fighters"].find({}, {"_id": 0}).skip(skip).limit(limit)
        return list(cur)
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fighters/by_url")
@limiter.limit("60/minute")
def get_fighter_by_url(request: Request, url: str):
    """Fetch a fighter document by its UFC URL."""
    try:
        doc = app.state.db["fighters"].find_one({"url": url}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Not found")
        return doc
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================
# Search Endpoint
# ================================================
@app.get("/search")
@limiter.limit("60/minute")
def search(request: Request, q: str = Query(...), k: int = Query(5)):
    """Search indexed fighter content (vector + text fallback)."""
    # Prefer vector search
    if app.state.azure and app.state.qdrant:
        collection = os.getenv("QDRANT_COLLECTION", "fighter_chunks")
        emb_model = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-large")
        emb = app.state.azure.embeddings.create(input=[q], model=emb_model).data[0].embedding
        results = app.state.qdrant.search(
            collection_name=collection,
            query_vector=emb,
            limit=k,
            with_payload=True,
        )
        return [
            {"score": r.score, "url": r.payload.get("url"), "text": r.payload.get("text")}
            for r in results
        ]

    # Mongo text index fallback
    try:
        cur = app.state.db["clean_docs"].find(
            {"$text": {"$search": q}},
            {"_id": 0, "url": 1, "text": 1, "score": {"$meta": "textScore"}},
        ).sort([("score", {"$meta": "textScore"})]).limit(k)
        out = list(cur)
        if out:
            return [
                {"score": d.get("score"), "url": d.get("url"), "text": d.get("text", "")[:500]}
                for d in out
            ]
    except PyMongoError:
        pass

    # Regex fallback
    try:
        cur = app.state.db["clean_docs"].find(
            {"text": {"$regex": q, "$options": "i"}},
            {"_id": 0, "url": 1, "text": 1}
        ).limit(k)
        return [{"score": None, "url": d.get("url"), "text": d.get("text", "")[:500]} for d in cur]
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================
# QA Endpoint (RAG)
# ================================================
@app.post("/qa")
@limiter.limit("60/minute")
def qa(request: Request, body: QARequest):
    """Answer questions using RAG (retrieval-augmented generation)."""
    # Prefer vector + LLM if available
    if app.state.azure and app.state.qdrant:
        collection = os.getenv("QDRANT_COLLECTION", "fighter_chunks")
        emb_model = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-large")
        chat_model = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "o4-mini")
        emb = app.state.azure.embeddings.create(input=[body.q], model=emb_model).data[0].embedding
        results = app.state.qdrant.search(
            collection_name=collection,
            query_vector=emb,
            limit=body.k,
            with_payload=True,
        )
        contexts = [r.payload.get("text", "") for r in results]
        context_block = "\n\n".join(contexts)
        prompt = (
            "You are a helpful assistant. Answer the question using the context.\n"
            "If unsure, say you don't know.\n\n"
            f"Context:\n{context_block}\n\nQuestion: {body.q}\nAnswer:"
        )
        chat = app.state.azure.chat.completions.create(
            model=chat_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        answer = chat.choices[0].message.content
        return {
            "answer": answer,
            "citations": [{"url": r.payload.get("url"), "score": r.score} for r in results],
        }

    # Mongo-only fallback
    try:
        cur = app.state.db["clean_docs"].find(
            {"$text": {"$search": body.q}},
            {"_id": 0, "url": 1, "text": 1, "score": {"$meta": "textScore"}},
        ).sort([("score", {"$meta": "textScore"})]).limit(body.k)
        docs = list(cur)
    except PyMongoError:
        docs = []

    if not docs:
        return {"answer": "I don't know.", "citations": []}

    snippets = [d["text"][:300] for d in docs]
    return {
        "answer": "\n\n".join(snippets),
        "citations": [{"url": d.get("url"), "score": d.get("score")} for d in docs],
    }
