# UFC Distributed RAG Web Scraper Framework

Docker-based distributed pipeline:
- Scraping → Kafka → Processing → Embeddings → Qdrant → RAG API
- Orchestrated with Ray; storage in MongoDB & Qdrant; monitoring via Prometheus/Grafana

## Quick start
1. Copy `.env.example` to `.env` and fill values.
2. Start stack:
   - `cd infra`
   - `docker compose up -d`
3. Verify:
   - Kafka UI: http://localhost:8080
   - Qdrant: http://localhost:6333/dashboard
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)
   - Ray Dashboard: http://localhost:8265

## Services (to be added)
- `services/scraper`: Scrapy spider for UFC fighters directory
- `services/processor`: HTML cleaning, schema normalization
- `services/embedder`: Chunk + embedding + Qdrant upsert
- `services/rag_api`: FastAPI endpoints `/search`, `/qa`, `/fighters/{id}`
- `services/orchestrator`: Ray tasks consuming/producing Kafka


