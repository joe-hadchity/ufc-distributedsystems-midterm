import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from pymongo import MongoClient
from services.embedder.embed_qdrant import upsert_clean_docs_to_qdrant


def main():
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "ufc")
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI is required")

    client = MongoClient(mongo_uri)
    clean = client[db_name]["clean_docs"]
    docs: List[Dict[str, Any]] = list(clean.find({}, projection={"url": 1, "text": 1}))
    upsert_clean_docs_to_qdrant(docs)
    client.close()
    print(f"Embedded and upserted {len(docs)} clean docs.")


if __name__ == "__main__":
    main()

