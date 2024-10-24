from typing import Dict, Any
from ._executor_interface import ExecutorInterface


class WebScraperExecutor(ExecutorInterface):
    def __init__(self, scraper_service):
        self.scraper_service = scraper_service

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "name": "generic_web_scraping",
            "description": "Scrapes titles or links from any web page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The web scraping operation to perform: 'get_titles' or 'get_links'.",
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL of the web page to scrape.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The maximum number of results to return (default: 5).",
                    },
                },
                "required": ["operation", "url"],
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        operation = arguments.get("operation")
        url = arguments.get("url")
        limit = arguments.get("limit", 5)  # Default to 5 if not provided

        if operation == "get_titles":
            titles = self.scraper_service.get_generic_titles(url, limit)
            return "\n".join(titles) if titles else "No titles found."

        elif operation == "get_links":
            links = self.scraper_service.get_generic_links(url, limit)
            return "\n".join(links) if links else "No links found."

        else:
            return f"Invalid operation: {operation}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return (
            f"Please summarize the result of the requested scraper operation and ask if the "
            f"user needs further actions."
            f"Please always answer in Language '{user_language}'"
        )
