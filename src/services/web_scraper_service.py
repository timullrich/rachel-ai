from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class WebScraperService:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape_page(self, url: str) -> str:
        """
        Sends a request to the given URL and returns a summarized text content of the main sections,
        including headlines and key links while avoiding menus and irrelevant sections.

        Args:
            url (str): The URL of the web page to scrape.

        Returns:
            str: Summarized text content of the main sections with key links included.
        """
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Extract main content, focusing on typical news-related tags and IDs
            main_content = []

            # Filter for main article sections with typical news structure
            for tag in soup.find_all(["h1", "h2", "h3", "p", "a"], recursive=True):
                if tag.name in ["h1", "h2", "h3"]:
                    main_content.append(f"\n**{tag.get_text().strip()}**")
                elif tag.name == "p":
                    main_content.append(tag.get_text().strip())
                elif tag.name == "a" and tag.get("href"):
                    link_text = tag.get_text().strip()
                    link_url = tag["href"].strip()

                    # Skip invalid links
                    if link_url.startswith("javascript") or link_url == "#":
                        continue

                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, link_url)
                    main_content.append(f"{link_text} ({absolute_url})")

            # Join the content with line breaks and apply a max length
            content_text = "\n".join(main_content)

            # Limit content length for readability
            max_length = 12000
            if len(content_text) > max_length:
                return content_text[:max_length] + "\n\n[Text truncated]"
            else:
                return content_text
        else:
            raise Exception(
                f"Failed to retrieve content from {url}, status code: {response.status_code}"
            )
