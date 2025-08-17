from src.scrapers.url_scraper import URLScraper
from src.utils.llm_client import LLMClient

class URLWorkflow:
    def __init__(self, event_schema):
        """Initialize the URL workflow"""
        self.event_schema = event_schema
        self.url_scraper = URLScraper()
        self.llm_client = LLMClient()

    def process(self, url):
        """Process a URL and extract potential URLs for depth 1 scraping
        Note: This method returns potential depth 1 URLs, but the orchestrator
        decides whether to process them based on current depth"""
        # Skip empty URL
        if not url:
            return {}, []

        # Scrape the URL
        scrape_result = self.url_scraper.scrape(url)

        # Extract text, URLs, and images
        scraped_text = scrape_result.get('scraped_text', '')
        scraped_urls = [url[1] for url in scrape_result.get('scraped_urls', [])]
        scraped_imgs = scrape_result.get('scraped_imgs', [])

        # Log the size of extracted text and number of URLs
        print(f"URL {url}: Extracted {len(scraped_text)} characters of text, {len(scraped_urls)} raw URLs")

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

        # Note: URL tracking for לינקים נוספים is now handled by the orchestrator

        # Log the sources that will be returned for further processing
        new_urls = [data for type_, data in new_sources if type_ == 'url']
        new_images = [data for type_, data in new_sources if type_ == 'image']
        print(f"URL {url}: Returning {len(new_urls)} relevant URLs and {len(new_images)} relevant images for further processing")
        if new_urls:
            print(f"  Relevant URLs: {', '.join(new_urls)}")

        return event_record, new_sources
