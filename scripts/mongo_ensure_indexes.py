import os
from dotenv import load_dotenv
from pymongo import MongoClient


def main():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "ufc")
    if not uri:
        raise RuntimeError("MONGODB_URI is required")
    client = MongoClient(uri)
    db = client[db_name]
    # Create text index on text field
    db["clean_docs"].create_index([("text", "text")], name="clean_text_idx")
    print("Created/ensured text index clean_text_idx on clean_docs.text")
    client.close()


if __name__ == "__main__":
    main()
