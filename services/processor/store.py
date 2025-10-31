import os
from typing import Dict, Any
from datetime import datetime
from pymongo import MongoClient, UpdateOne


class MongoStore:
    def __init__(self):
        uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB", "ufc")
        if not uri:
            raise RuntimeError("MONGODB_URI is required")
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.clean = self.db["clean_docs"]
        self.fighters = self.db["fighters"]

    def upsert_clean_doc(self, doc: Dict[str, Any]):
        doc = {**doc, "updated_at": datetime.utcnow()}
        self.clean.update_one({"url": doc["url"]}, {"$set": doc}, upsert=True)

    def upsert_fighter(self, fighter: Dict[str, Any]):
        key = {"url": fighter.get("url")}
        fighter = {**fighter, "updated_at": datetime.utcnow()}
        self.fighters.update_one(key, {"$set": fighter}, upsert=True)

    def bulk_upsert_fighters(self, fighters: list[Dict[str, Any]]):
        ops = []
        now = datetime.utcnow()
        for f in fighters:
            f = {**f, "updated_at": now}
            ops.append(UpdateOne({"url": f.get("url")}, {"$set": f}, upsert=True))
        if ops:
            self.fighters.bulk_write(ops)

    def close(self):
        self.client.close()

