import os
from urllib.parse import urljoin
import scrapy

DEFAULT_START_URL = "https://www.ufc.com/athletes/all"


class UfcFightersSpider(scrapy.Spider):
    name = "ufc_fighters"
    allowed_domains = ["ufc.com", "www.ufc.com"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.8,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "USER_AGENT": f"UFC-Scraper/1.0 (+contact: {os.getenv('CRAWL_CONTACT_EMAIL', 'contact@example.com')})",
        "LOG_LEVEL": "INFO",
        "DEPTH_LIMIT": 2,
    }

    def __init__(self, start_url: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url or DEFAULT_START_URL]

    def parse(self, response: scrapy.http.Response):
        # Parse listing page: extract fighter profile links and pagination
        for href in response.css("a[href*='/athlete/']::attr(href)").getall():
            url = urljoin(response.url, href)
            yield scrapy.Request(url, callback=self.parse_fighter)

        # Follow pagination if present
        next_href = response.css("a.pager__item--next::attr(href), a[rel='next']::attr(href)").get()
        if next_href:
            yield scrapy.Request(urljoin(response.url, next_href), callback=self.parse)

    def parse_fighter(self, response: scrapy.http.Response):
        # Yield raw HTML and basic metadata; further parsing occurs downstream
        yield {
            "url": response.url,
            "title": response.css("title::text").get() or "",
            "fetched_at": response.headers.get("Date", b"").decode("utf-8", errors="ignore"),
            "status": response.status,
            "html": response.text,
        }

