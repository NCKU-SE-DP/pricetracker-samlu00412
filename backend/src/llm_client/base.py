from abc import ABC, abstractmethod, ABCMeta
from pydantic import BaseModel, Field
from typing import Optional
import aisuite as ai
import json
from src.configs import Constants
from src.llm_client.exceptions import EvaluationFailure


class Models:
    OPENAI = "openai:gpt-3.5-turbo"
    ANTHROPIC = "anthropic:claude-3-5-sonnet-20240620"
    
class PromptInterface(BaseModel):
    system_content: str = Field(...)
    user_content: str = Field(...)
    
    @property
    def make_prompt(self):
        return [{"role": "system", "content": f"{self.system_content}"},
                {"role": "user", "content": f"{self.user_content}"}]

class LLMClientBase(metaclass=ABCMeta):
    client: ai.Client = ...
class LLMClientBase(metaclass=ABCMeta):
    client: ai.Client = ...
    
    @abstractmethod
    def _generate_completion(self, prompt: PromptInterface) -> str:
        return NotImplemented
    
class LLMClientTemplate(LLMClientBase, ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model: str = ...
        self._initialize_client()

    #initialize client function should be abstract
    @abstractmethod
    def _initialize_client(self):
        pass

    def evaluate_relevance(self,news_title: str) -> str:
        return self._generate_completion(PromptInterface(system_content=Constants.Prompt.GPT_RELEVANCE_PROMPT,
                                                        user_content=news_title))
    
    def generate_summary(self,prompt: str) -> Optional[dict[str, str]]:
        response = self._generate_completion(PromptInterface(system_content=Constants.Prompt.GPT_SUMMARY_PROMPT,
                                                        user_content=prompt))
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to generate a summary based on the prompt: {response}")

    def extract_search_keywords(self,keywords: str) -> str:
        return self._generate_completion(PromptInterface(system_content=Constants.Prompt.GPT_EXTRACT_PROMPT,
                                                        user_content=keywords))
    
    def _generate_completion(self, prompt: PromptInterface)-> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prompt.make_prompt
            )
            return response.choices[0].message.content
        except Exception as error:
            raise EvaluationFailure(f"An API error occurred: {error}")
        
