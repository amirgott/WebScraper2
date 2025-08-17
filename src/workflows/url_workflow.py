from src.scrapers.url_scraper import URLScraper
from src.utils.llm_client import LLMClient

class URLWorkflow:
    def __init__(self, event_schema):
        """Initialize the URL workflow"""
        self.event_schema = event_schema
        self.url_scraper = URLScraper()
        self.llm_client = LLMClient()

    def process(self, url):
        """Process a URL"""
        # Skip empty URL
        if not url:
            return {}, []

        # Scrape the URL
        scrape_result = self.url_scraper.scrape(url)

        # Extract text, URLs, and images
        scraped_text = scrape_result.get('scraped_text', '')
        scraped_urls = [url[1] for url in scrape_result.get('scraped_urls', [])]
        scraped_imgs = scrape_result.get('scraped_imgs', [])

        # Extract event information from text
        event_record = self.llm_client.extract_event_info(scraped_text, self.event_schema)

        # Find event-related URLs
        event_urls = self.llm_client.find_event_related_urls(scraped_urls)

        # Find event-related images
        # event_images = self.llm_client.find_event_related_images(scraped_imgs)
        event_images = []

        # Prepare new sources to process
        new_sources = []

        # Add event-related URLs (depth 1)
        for event_url in event_urls:
            new_sources.append(('url', event_url))

        # Add event-related images
        for image_url in event_images:
            new_sources.append(('image', image_url))

        # Add current URL to event record if any information was found
        if event_record and any(event_record.values()):
            if 'לינקים נוספים' in event_record:
                if url not in event_record['לינקים נוספים']:
                    if event_record['לינקים נוספים']:
                        event_record['לינקים נוספים'] += f", {url}"
                    else:
                        event_record['לינקים נוספים'] = url
            else:
                event_record['לינקים נוספים'] = url

        return event_record, new_sources
