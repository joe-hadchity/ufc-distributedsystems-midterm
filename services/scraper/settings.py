import os

BOT_NAME = "ufc_scraper"
SPIDER_MODULES = ["services.scraper.spiders"]
NEWSPIDER_MODULE = "services.scraper.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = int(os.getenv("SCRAPY_CONCURRENCY", "8"))
DOWNLOAD_DELAY = float(os.getenv("SCRAPY_DELAY", "0.8"))
RETRY_ENABLED = True
RETRY_TIMES = 3
DEPTH_LIMIT = int(os.getenv("SCRAPY_DEPTH", "2"))
LOG_LEVEL = os.getenv("SCRAPY_LOG_LEVEL", "INFO")
USER_AGENT = f"UFC-Scraper/1.0 (+contact: {os.getenv('CRAWL_CONTACT_EMAIL', 'contact@example.com')})"

FEEDS = {
    os.getenv("SCRAPY_FEED_URI", "outputs/ufc_fighters_%(time)s.jsonl"): {
        "format": "jsonlines",
        "encoding": "utf8",
        "overwrite": False,
    }
}

ITEM_PIPELINES = {
    "services.scraper.pipelines.MongoAndKafkaPipeline": 300,
}

# Disable cookies and Telnet console
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
