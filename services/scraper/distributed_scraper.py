import ray
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from services.scraper.spiders.ufc_fighters import UfcFightersSpider

# Initialize Ray cluster
ray.init(ignore_reinit_error=True)

@ray.remote
def run_scraper_task(start_url: str):
    """Runs the Scrapy spider for a given URL in a distributed Ray worker."""
    print(f"🚀 Starting scraper for {start_url}")
    process = CrawlerProcess(get_project_settings())
    process.crawl(UfcFightersSpider, start_url=start_url)
    process.start()

# Define list of pages (distributed targets)
URLS = [
    "https://www.ufc.com/athletes/all?page=1",
    "https://www.ufc.com/athletes/all?page=2",
    "https://www.ufc.com/athletes/all?page=3"
]

# Launch scraping tasks in parallel
futures = [run_scraper_task.remote(url) for url in URLS]
ray.get(futures)

print("✅ All distributed scraping tasks completed successfully.")
