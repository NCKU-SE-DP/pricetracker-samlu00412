from abc import ABC, abstractmethod
from fastapi.responses import JSONResponse
from sentry_sdk import capture_exception, configure_scope
from typing import Optional, Union

class ExceptionsBase(ABC, Exception):
    def __init__(self, error: Optional[Union[str, Exception]] = None):
        super().__init__(self.get_messages())
        if isinstance(error, str):
            self.details = error
        elif isinstance(error, Exception):
            self.details = str(error)
        else:
            self.details = None
        self.handle_exceptions()

    @abstractmethod
    def get_messages(self):
        return NotImplemented
    
    @abstractmethod
    def get_status_code(self):
        """
        Get the HTTP status code for this exception.
        Returns:
            int: The HTTP status code representing the error (e.g., 400, 404, 500).
        Note:
            This method must be implemented by subclasses.
        """
        return NotImplemented
    
    def handle_exceptions(self):
        capture_exception(self)

    def transfer_response_format(self) -> JSONResponse:
        """
        Returns:
            JSONResponse: 
                A JSON response containing the error message and additional details 
                (if available), with the appropriate HTTP status code.
        """
        response_content = {"error": self.get_messages()}
        if self.details:
            response_content["details"] = self.details
        
        return JSONResponse(
            status_code=self.get_status_code(),
            content=response_content,
        )
    
