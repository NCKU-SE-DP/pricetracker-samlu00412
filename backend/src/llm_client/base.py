import abc
from pydantic import BaseModel, Field


class MessagePassingInterfaceExample(BaseModel):
    key: str = Field(
        default=...,
        example="example",
        description="description"
    )
    
class PromptInterface(BaseModel):
    system_content: str = Field(...)
    user_content: str = Field(...)

    def _make_prompt(self):
        return [{"role": "system", "content": self.system_content},
                {"role": "user", "content": self.user_content}]

class LLMClientBase(metaclass=abc.ABCMeta):
    
    @abc.abstractmethod
    def evaluate_relevance(self,news_title: str) -> str:
        
        return NotImplemented
    
    @abc.abstractmethod
    def generate_summary(self,prompt: str) -> str:
        
        return NotImplemented
    
    
    @abc.abstractmethod
    def extract_search_keywords(self,keywords: str) -> str:
        
        return NotImplemented
    
    @abc.abstractmethod
    def _generate_completion(self, prompt: PromptInterface) -> str:
        
        return NotImplemented
    
    
    

    