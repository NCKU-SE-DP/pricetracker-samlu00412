<<<<<<< HEAD
import aisuite as ai
from src.llm_client.base import LLMClientTemplate,Models

class OpenAIClient(LLMClientTemplate):

    def __init__(self,api_key:str):
        super().__init__(api_key)

    def  _initialize_client(self):    
        self.client = ai.Client({"openai":{"api_key": self.api_key}})
        self.model = Models.OPENAI


      
=======
import json
from openai import OpenAI
from typing import Optional
from src.llm_client.base import LLMClientBase,PromptInterface
from src.configs import Constants

class OpenAIClient(LLMClientBase):

    def __init__(self,api_key:str):
        self.client = OpenAI(api_key=api_key)

    def evaluate_relevance(self,news_title: str) -> str:
        return self._generate_completion(PromptInterface(system_content=Constants.GPT_RELEVANCE_PROMPT,
                                                        user_content=news_title))


    def generate_summary(self,prompt: str) -> Optional[dict[str, str]]:
        response =  self._generate_completion(PromptInterface(system_content=Constants.GPT_SUMMARY_PROMPT,
                                                        user_content=prompt))
        return json.loads(response)
        

    def extract_search_keywords(self,keywords: str) -> str:
        return self._generate_completion(PromptInterface(system_content=Constants.GPT_EXTRACT_PROMPT,
                                                        user_content=keywords))

    def _generate_completion(self, prompt: PromptInterface) -> str:
        #GPTprompt = prompt._make_prompt()
        completion = self.client.chat.completions.create(
            model=Constants.LLM_MODEL,
            messages=prompt.make_prompt
        )
        return completion.choices[0].message.content
        
            
>>>>>>> develop
