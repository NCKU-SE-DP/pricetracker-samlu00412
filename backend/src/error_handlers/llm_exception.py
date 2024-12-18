from src.error_handlers.base import ExceptionsBase
from src.configs import Constants

class LLMErrorBase(ExceptionsBase):
    
    def get_status_code(self):
        return Constants.System.ERROR_CODE


class InvalidModelError(LLMErrorBase):
    def get_messages(self):
        return "Invalid Model"
    
class NoPromptError(LLMErrorBase):
    def get_messages(self):
        return "Please input the prompt"