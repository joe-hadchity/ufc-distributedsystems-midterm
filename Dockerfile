FROM python:3.10-slim
WORKDIR /app
COPY scraper_consumer.py /app/
COPY healthcheck.py /app/
RUN pip install kafka-python requests beautifulsoup4
CMD ["python", "scraper_consumer.py"]
