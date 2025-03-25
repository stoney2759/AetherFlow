# tools/web_scraper_tool.py
import requests
from bs4 import BeautifulSoup
import logging
from .base_tool import BaseTool

class WebScraperTool(BaseTool):
    """Tool for scraping web content and extracting information."""
    
    def __init__(self, name="web_scraper", config=None):
        super().__init__(name, config or {})
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self, url, selector=None, parse_type="html"):
        """
        Scrape content from a URL.
        
        Args:
            url (str): The URL to scrape
            selector (str, optional): CSS selector to extract specific content
            parse_type (str): Parse as "html", "text", or "json"
            
        Returns:
            dict: The scraped content and metadata
        """
        try:
            self.logger.info(f"🌐 Scraping URL: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = {
                "status_code": response.status_code,
                "url": url,
                "content_type": response.headers.get('Content-Type', '')
            }
            
            if parse_type == "html":
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title and metadata
                result["title"] = soup.title.string if soup.title else None
                result["meta_description"] = soup.find("meta", attrs={"name": "description"})
                
                # Extract specific content if selector provided
                if selector:
                    selected_elements = soup.select(selector)
                    result["selected_content"] = [elem.get_text() for elem in selected_elements]
                    result["selected_html"] = [str(elem) for elem in selected_elements]
                else:
                    result["full_text"] = soup.get_text()
                    result["full_html"] = response.text
                    
            elif parse_type == "json":
                result["json_content"] = response.json()
                
            elif parse_type == "text":
                result["text_content"] = response.text
                
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Scraping failed: {e}")
            return {"error": str(e), "url": url}