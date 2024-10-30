"""
This module defines the WebScraperExecutor class, which implements the ExecutorInterface
to perform web scraping operations on a given URL, retrieving and parsing the HTML content.
"""

from typing import Any, Dict

from ._executor_interface import ExecutorInterface


class WebScraperExecutor(ExecutorInterface):
    """
    Executor class for handling web scraping operations.

    This class uses a scraper service to fetch and parse the HTML content of a given URL.
    It is intended for general web scraping tasks where full HTML content is required.

    Attributes:
        scraper_service (ScraperService): The service used to scrape and retrieve HTML content.
    """

    def __init__(self, scraper_service):
        self.scraper_service = scraper_service

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "generic_web_scraping",
                "description": "Scrapes the full HTML content from any web page.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL of the web page to scrape.",
                        }
                    },
                    "required": ["url"],
                },
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        url = arguments.get("url")

        try:
            # Use the scrape_page method to fetch and parse the entire page content
            page_text = self.scraper_service.scrape_page(url)

            return page_text
        except Exception as e:
            return f"Failed to retrieve content from {url}: {e}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return (
            "Analyze the user's request and provide the scraped web content as briefly as "
            "possible. If the user request indicates specific details or sections of the page, "
            "focus on those elements. If unsure whether further details are needed, ask the user. "
            f"Always respond in the language '{user_language}'."
        )
