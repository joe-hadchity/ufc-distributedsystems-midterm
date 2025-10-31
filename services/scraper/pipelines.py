import os
import json
from typing import Any, Dict
from datetime import datetime
from pymongo import MongoClient

try:
    from kafka import KafkaProducer  # type: ignore
except Exception:  # pragma: no cover
    KafkaProducer = None  # type: ignore


class MongoAndKafkaPipeline:
    def __init__(self):
        self.mongo_client = None
        self.mongo_collection = None
        self.kafka_producer = None
        self.kafka_topic = os.getenv("KAFKA_TOPIC_HTML", "html")
        self.enable_kafka = os.getenv("ENABLE_KAFKA", "false").lower() == "true"

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        mongo_uri = os.getenv("MONGODB_URI")
        mongo_db = os.getenv("MONGODB_DB", "ufc")
        if not mongo_uri:
            raise RuntimeError("MONGODB_URI is required in environment to store raw pages")
        pipeline.mongo_client = MongoClient(mongo_uri)
        pipeline.mongo_collection = pipeline.mongo_client[mongo_db]["raw_pages"]

        if pipeline.enable_kafka and KafkaProducer is not None:
            try:
                bootstrap = os.getenv("KAFKA_BROKERS", "localhost:9092")
                pipeline.kafka_producer = KafkaProducer(
                    bootstrap_servers=bootstrap.split(","),
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    linger_ms=50,
                    retries=3,
                )
            except Exception:
                pipeline.kafka_producer = None
        return pipeline

    def process_item(self, item: Dict[str, Any], spider):
        doc = {
            "url": item.get("url"),
            "title": item.get("title", ""),
            "status": item.get("status"),
            "fetched_at": datetime.utcnow(),
            "html": item.get("html", ""),
            "source": "scrapy",
        }
        self.mongo_collection.insert_one(doc)

        if self.kafka_producer is not None:
            payload = {k: doc[k] for k in ("url", "title", "status", "html")}
            try:
                self.kafka_producer.send(self.kafka_topic, payload)
            except Exception:
                pass
        return item

    def close_spider(self, spider):
        if self.kafka_producer is not None:
            try:
                self.kafka_producer.flush(5)
                self.kafka_producer.close()
            except Exception:
                pass
        if self.mongo_client is not None:
            self.mongo_client.close()

