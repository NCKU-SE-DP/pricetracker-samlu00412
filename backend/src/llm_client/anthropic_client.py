import aisuite as ai

from src.llm_client.base import LLMClientTemplate,Models

class AnthropicClient(LLMClientTemplate):

    def _initialize_client(self):
        self.client = ai.Client({"anthropic": {"api_key": self.api_key}})
        self.model = Models.ANTHROPIC