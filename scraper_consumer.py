import time
import random

print("✅ Scraper worker started...")

while True:
    print(f"Scraping task batch {random.randint(1,100)}")
    time.sleep(5)
