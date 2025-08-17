import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class URLScraper:
    def __init__(self):
        """Initialize URL scraper"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape(self, url):
        """Scrape a URL and extract text, URLs, and images"""
        try:
            # Send request to the URL
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove unwanted elements
            for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'svg']):
                tag.decompose()

            # Extract text content
            text = soup.get_text(separator=' ').strip()

            # Extract URLs
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            urls = set()
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Only process URLs that start with http
                if href.startswith('http'):
                    # Store the URL with its HTML tag context
                    context = str(a_tag)
                    urls.add((href, context))

            # Extract images
            images = set()
            for img_tag in soup.find_all('img', src=True):
                src = img_tag['src']
                # Convert relative URLs to absolute
                if src.startswith('http'):
                    img_url = src
                else:
                    img_url = urljoin(base_url, src)

                # Store the image URL with its HTML tag context
                context = str(img_tag)
                images.add((img_url, context))

            return {
                'scraped_text': text,
                'scraped_urls': list(urls),  # Convert set to list for JSON serialization
                'scraped_imgs': list(images)
            }

        except requests.exceptions.RequestException as e:
            print(f"Error scraping URL {url}: {str(e)}")
            return {
                'scraped_text': '',
                'scraped_urls': [],
                'scraped_imgs': []
            }
