# scripts/export_clean_sample.py
from pymongo import MongoClient
import json, os
from datetime import datetime

def convert_datetime(obj):
    """Convert datetime objects to ISO 8601 strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# connect to local MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["ufc"]

# fetch a few cleaned docs
sample = list(db["clean_docs"].find({}, {"_id": 0}).limit(3))

# make sure the outputs directory exists
os.makedirs("outputs", exist_ok=True)

# write to JSON file (with datetime serialization)
out_path = os.path.join("outputs", "clean_sample.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(sample, f, ensure_ascii=False, indent=2, default=convert_datetime)

print(f"✅ Wrote sample to {out_path} with {len(sample)} records.")
