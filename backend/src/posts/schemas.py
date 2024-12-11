from pydantic import BaseModel

class PromptRequest(BaseModel):
    prompt: str

class NewsSumaryRequestSchemaWithModel(BaseModel):
    content: str
    ai_model: str