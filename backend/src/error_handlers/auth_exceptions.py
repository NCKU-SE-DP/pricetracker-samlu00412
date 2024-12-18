from src.error_handlers.base import ExceptionsBase
from src.configs import Constants

class AuthErrorBase(ExceptionsBase):
    def get_status_code(self):
        return Constants.Auth.ERROR_CODE

class ExpiredError(AuthErrorBase):
    def get_messages(self):
        return "Authentication has expired."

class CreateTokenError(AuthErrorBase):
    def get_messages(self):
        return "Create token failed."
    