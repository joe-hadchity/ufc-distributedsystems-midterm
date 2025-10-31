import os
from typing import Any, Dict
from dotenv import load_dotenv
from pymongo import MongoClient
from services.processor.cleaner import clean_html_to_text, parse_fighter_schema
from services.processor.store import MongoStore


def main():
    load_dotenv()
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "ufc")
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI is required")

    client = MongoClient(mongo_uri)
    raw = client[db_name]["raw_pages"]
    store = MongoStore()

    cursor = raw.find({}, projection={"url": 1, "html": 1})
    count = 0
    for doc in cursor:
        url = doc.get("url")
        html = doc.get("html", "")
        text = clean_html_to_text(html)
        normalized: Dict[str, Any] = {
            "url": url,
            "text": text,
        }
        store.upsert_clean_doc(normalized)
        fighter = parse_fighter_schema(html, url)
        store.upsert_fighter(fighter)
        count += 1

    store.close()
    client.close()
    print(f"Processed {count} documents.")


if __name__ == "__main__":
    main()

