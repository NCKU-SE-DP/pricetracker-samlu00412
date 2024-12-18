from src.error_handlers.base import ExceptionsBase
from sentry_sdk import capture_exception
from typing import Optional, Union
from src.configs import Constants

class InternalServerError(ExceptionsBase):
    def __init__(self, error: Optional[Union[str, Exception]] = None):
        super().__init__()
        self.error = error
        self.handle_exceptions()

    def get_status_code(self) -> int:
        return Constants.System.ERROR_CODE
    
    def get_messages(self) -> str:
        return "Internal server having some problem, please try again later."
    