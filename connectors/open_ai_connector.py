from openai import OpenAI

class OpenAiConnector:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

