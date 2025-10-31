import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

os.makedirs("outputs", exist_ok=True)

# Ensure settings module path
if not os.getenv("SCRAPY_SETTINGS_MODULE"):
    os.environ["SCRAPY_SETTINGS_MODULE"] = "services.scraper.settings"

from services.scraper.spiders.ufc_fighters import UfcFightersSpider  # noqa: E402


def main():
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(UfcFightersSpider)
    process.start()


if __name__ == "__main__":
    main()
