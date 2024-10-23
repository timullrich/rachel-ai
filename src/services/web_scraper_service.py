import requests
from bs4 import BeautifulSoup


class WebScraperService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_page(self, url: str) -> BeautifulSoup:
        """
        Sends a request to the given URL and returns the parsed HTML content as a BeautifulSoup object.

        Args:
            url (str): The URL of the web page to scrape.

        Returns:
            BeautifulSoup: Parsed HTML content of the page.
        """
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        else:
            raise Exception(
                f"Failed to retrieve content from {url}, status code: {response.status_code}")

    def get_generic_titles(self, url: str, limit: int = 5) -> list:
        """
        Scrapes all <h1>, <h2>, and <h3> tags from a given URL and returns their text content.

        Args:
            url (str): The URL of the web page to scrape.
            limit (int): The maximum number of titles to return.

        Returns:
            list: A list of title texts found in <h1>, <h2>, and <h3> tags.
        """
        soup = self.scrape_page(url)
        titles = [tag.get_text().strip() for tag in soup.find_all(['h1', 'h2', 'h3'])]
        return titles[:limit]

    def get_generic_links(self, url: str, limit: int = 5) -> list:
        """
        Scrapes all <a> tags from a given URL and returns their href attributes.

        Args:
            url (str): The URL of the web page to scrape.
            limit (int): The maximum number of links to return.

        Returns:
            list: A list of URLs found in <a> tags.
        """
        soup = self.scrape_page(url)
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        return links[:limit]
