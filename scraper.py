import requests
import re
from dotenv import load_dotenv
import os

load_dotenv()

class WebScrapper:
    """Simple web scraper wrapper for fetching and extracting links.

    This class provides minimal utilities used by the project to fetch
    pre-rendered page content (via `get_data`) and to extract http(s)
    links from arbitrary text (`get_links`).
    """

    def __init__(self, url):
        """Create a `WebScrapper` for a specific URL.

        Args:
            url (str): The target URL or identifier used by `get_data`.
        """
        self.url = url

    def get_links(self, content):
        """Extract http(s) links from a block of text.

        Filters out common image file extensions to avoid binary assets.

        Args:
            content (str): Text to search for links.

        Returns:
            List[str]: List of cleaned HTTP/HTTPS links found in `content`.
        """
        if content:
            links  = re.findall(r'https?://[^\s{\[()\]}]+', content)
            clean_links = [L for L in links if not L.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
            return clean_links
        return []
    def get_start_url(self):
        """Extract the base URL from the provided URL.

        This method assumes the input URL is in a format like
        'https://r.jina.ai/some/path' and extracts 'https://r.jina.ai'.

        Returns:
            str: The base URL extracted from `self.url`.
        """
        match = re.match(r'(https?://[^/]+)', self.url)
        return match.group(1) if match else None
    
    def is_url_doc(self, url):
        """Determine if the URL is likely a documentation page.

        This is a simple heuristic check that looks for common doc-related
        keywords in the URL path.

        Returns:
            bool: True if the URL appears to be a documentation page, False otherwise.
        """
        doc_keywords = ['docs', 'documentation', 'guide', 'manual', 'reference', 'api', 'developer', 'learn', 'getting-started', 'tutorial', 'examples', 'resources', 'support', 'help', 'faq']
        return any(keyword in url.lower() for keyword in doc_keywords)

    def get_data(self):
        """Fetch page content using a pre-rendering proxy service.

        Returns the raw HTML/text body returned by the proxy. The
        implementation uses a fixed Authorization header as in the
        original project (consider moving secrets to configuration).

        Returns:
            str: Response text from the GET request.
        """
        headers = {
            "Authorization": f"Bearer {os.getenv('JINA_API_KEY')}"
            }
        response = requests.get(f'https://r.jina.ai/{self.url}', headers=headers)
        return response.text
